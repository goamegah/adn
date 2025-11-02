import os
import sys
import json
import pandas as pd
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import agent_tool


# ============================================================
# COLLECTEUR AGENT - Classes et fonctions
# ============================================================

class AgentCollecteur:
    """Agent 1 : Collecte les données patient depuis Cloud SQL (MIMIC-III importée)."""

    def __init__(
        self,
        db_user: str = os.getenv("DB_USER", "adn_admin"),
        db_password: str = os.getenv("DB_PASSWORD", "ChangeThisSuperSecurePassword"),
        db_name: str = os.getenv("DB_NAME", "adn_emergency_db"),
        db_host: str = os.getenv("DB_HOST", "34.186.39.96"),
        db_port: int = int(os.getenv("DB_PORT", "5432")),
        instance_conn_name: str = os.getenv(
            "INSTANCE_CONNECTION_NAME",
            "ai-diagnostic-navigator-475316:us-east4:adn-postgres-us4",
        ),
    ):
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.db_host = db_host
        self.db_port = db_port
        self.instance_conn_name = instance_conn_name

        # Détection intelligente du mode de connexion
        connection_uri = None
        ssl_mode = None

        print("🔍 Détection du mode de connexion Cloud SQL...")

        try:
            # 1️⃣ Mode Cloud Run / Vertex (socket Unix)
            socket_path = f"/cloudsql/{self.instance_conn_name}"
            if os.path.exists(socket_path):
                connection_uri = (
                    f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}"
                    f"?host={socket_path}"
                )
                ssl_mode = "disable"
                print(f"🔗 Mode Cloud Run détecté (socket Unix) : {socket_path}")

            # 2️⃣ Mode proxy local (port 5432 ou 5433)
            elif self._is_port_open("127.0.0.1", 5433):
                connection_uri = (
                    f"postgresql+psycopg2://{db_user}:{db_password}@127.0.0.1:5433/{db_name}"
                )
                ssl_mode = "disable"
                print("🧩 Cloud SQL Proxy détecté sur le port 5433")
            elif self._is_port_open("127.0.0.1", 5432):
                connection_uri = (
                    f"postgresql+psycopg2://{db_user}:{db_password}@127.0.0.1:5432/{db_name}"
                )
                ssl_mode = "disable"
                print("🧩 Cloud SQL Proxy détecté sur le port 5432")

            # 3️⃣ Fallback – IP publique avec SSL obligatoire
            else:
                connection_uri = (
                    f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
                )
                ssl_mode = "require"
                print(f"🌐 Connexion via IP publique : {db_host}:{db_port}")

            # Création du moteur SQLAlchemy
            self.engine = create_engine(connection_uri, pool_pre_ping=True)

            # Vérification de la connexion
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Connexion Cloud SQL réussie (SSL={ssl_mode}).")

        except Exception as e:
            print(f"❌ Erreur de connexion à Cloud SQL : {e}")
            raise

    @staticmethod
    def _is_port_open(host: str, port: int) -> bool:
        """Vérifie si un port TCP est ouvert (utile pour détecter le proxy local)."""
        import socket
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            return False

    def _load_table(self, name: str, limit: Optional[int] = 1000) -> pd.DataFrame:
        """Charge une table depuis Cloud SQL"""
        try:
            query = f"SELECT * FROM {name}"
            if limit:
                query += f" LIMIT {limit}"
            df = pd.read_sql(text(query), self.engine)
            print(f"📊 Table {name} chargée ({len(df)} lignes).")
            return df
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement de {name}: {e}")
            return pd.DataFrame()

    def collecter_donnees_patient(self, subject_id: Optional[int] = None, texte_medical: Optional[str] = None) -> Dict[str, Any]:
        if texte_medical:
            print("🧾 Mode texte médical.")
            return self._collecter_depuis_texte(texte_medical)
        if subject_id is None:
            raise ValueError("Il faut fournir soit subject_id soit texte_medical")
        print(f"🩺 Collecte en cours pour patient {subject_id} ...")
        try:
            result = self._collecter_depuis_mimic(subject_id)
            print(f"✅ Collecte terminée pour patient {subject_id}.")
            return {"status": "ok", "subject_id": subject_id, "patient_normalized": result["patient_normalized"]}
        except Exception as e:
            print(f"❌ Erreur collecte patient {subject_id}: {e}")
            return {"status": "error", "error": str(e), "subject_id": subject_id}

    def _collecter_depuis_mimic(self, subject_id: int) -> Dict[str, Any]:
        """Collecte depuis Cloud SQL (tables MIMIC-III importées)"""
        patient = self._load_table("patients").query(f"subject_id == {subject_id}").iloc[0]
        admissions = self._load_table("admissions").query(f"subject_id == {subject_id}")
        
        if len(admissions) == 0:
            raise ValueError(f"Aucune admission trouvée pour patient {subject_id}")
        
        admission = admissions.iloc[-1]
        hadm_id = admission['hadm_id']
        
        # Charger les autres tables
        icustays = self._load_table("icustays").query(f"subject_id == {subject_id}")
        diagnoses = self._load_table("diagnoses_icd").query(f"hadm_id == {hadm_id}")
        procedures = self._load_table("procedures_icd").query(f"hadm_id == {hadm_id}")
        prescriptions = self._load_table("prescriptions").query(f"subject_id == {subject_id}")
        labevents = self._load_table("labevents").query(f"subject_id == {subject_id}").tail(20)
        chartevents = self._load_table("chartevents").query(f"subject_id == {subject_id}").tail(50)
        microevents = self._load_table("microbiologyevents").query(f"subject_id == {subject_id}")
        
        # Normalisation (inchangée)
        data_normalized = {
            "patient_normalized": {
                "id": str(subject_id),
                "source_type": "MIMIC_III_CLOUDSQL",
                "age": self._calculate_age(patient['dob'], admission['admittime']),
                "sex": "homme" if patient['gender'] == 'M' else "femme",
                
                "admission": {
                    "type": admission['admission_type'],
                    "chief_complaint": admission['diagnosis'],
                    "date": admission['admittime'],
                    "location": admission['admission_location'],
                },
                
                "vitals_current": self._extract_vitals(chartevents),
                "labs": self._extract_labs(labevents),
                "cultures": self._extract_cultures(microevents),
                "diagnoses_icd": self._extract_diagnoses(diagnoses),
                "procedures_icd": self._extract_procedures(procedures),
                "medications_current": self._extract_medications(prescriptions),
                
                "medical_history": {
                    "known_conditions": self._extract_conditions(diagnoses),
                    "icu_stays": len(icustays),
                },
                
                "death_info": {
                    "expired": bool(patient['expire_flag']),
                    "dod": str(patient['dod']) if pd.notna(patient['dod']) else None,
                    "hospital_expire": bool(admission['hospital_expire_flag']),
                }
            }
        }
        
        return data_normalized

    def _collecter_depuis_texte(self, texte: str) -> Dict[str, Any]:
        return {
            "patient_normalized": {
                "id": "TEXT_INPUT",
                "source_type": "TEXTE_MEDICAL",
                "texte_brut": texte,
                "age": None,
                "sex": None,
                "admission": {"type": "TEXTE_LIBRE", "chief_complaint": "Voir texte brut", "date": None},
                "vitals_current": {},
                "labs": [],
                "cultures": [],
                "diagnoses_icd": [],
                "procedures_icd": [],
                "medications_current": [],
                "medical_history": {"known_conditions": []},
            }
        }
    
    def _calculate_age(self, dob, admittime):
        try:
            dob = pd.to_datetime(dob)
            admit = pd.to_datetime(admittime)
            age = (admit - dob).days // 365
            return max(0, age)
        except:
            return None
    
    def _extract_vitals(self, chartevents: pd.DataFrame) -> Dict:
        vitals = {}
        vital_mapping = {
            220045: "heart_rate",
            220179: "systolic_bp",
            220180: "diastolic_bp",
            220210: "respiratory_rate",
            223761: "temperature",
            220277: "spo2"
        }
        for _, row in chartevents.iterrows():
            item_id = row.get('itemid')
            if item_id in vital_mapping:
                name = vital_mapping[item_id]
                val = row.get('valuenum')
                if pd.notna(val):
                    vitals[name] = {
                        "value": float(val),
                        "unit": row.get('valueuom', ''),
                        "charttime": str(row.get('charttime'))
                    }
        return vitals
    
    def _extract_labs(self, labevents: pd.DataFrame) -> list:
        labs = []
        for _, row in labevents.iterrows():
            labs.append({
                "itemid": int(row['itemid']),
                "charttime": str(row['charttime']),
                "value": str(row['value']),
                "valuenum": float(row['valuenum']) if pd.notna(row['valuenum']) else None,
                "valueuom": str(row['valueuom']) if pd.notna(row['valueuom']) else None,
                "flag": str(row['flag']) if pd.notna(row['flag']) else None,
            })
        return labs

    def _extract_cultures(self, microevents: pd.DataFrame) -> list:
        cultures = []
        for _, row in microevents.iterrows():
            cultures.append({
                "charttime": str(row['charttime']),
                "spec_type": str(row['spec_type_desc']),
                "organism": str(row['org_name']) if pd.notna(row['org_name']) else None,
                "status": "POSITIVE" if pd.notna(row['org_name']) else "NEGATIVE",
                "antibiotic": str(row['ab_name']) if pd.notna(row['ab_name']) else None,
                "interpretation": str(row['interpretation']) if pd.notna(row['interpretation']) else None,
            })
        return cultures

    def _extract_diagnoses(self, diagnoses: pd.DataFrame) -> list:
        return [{"icd9_code": str(r['icd9_code']), "seq_num": int(r['seq_num'])} for _, r in diagnoses.iterrows()]

    def _extract_procedures(self, procedures: pd.DataFrame) -> list:
        return [{"icd9_code": str(r['icd9_code']), "seq_num": int(r['seq_num'])} for _, r in procedures.iterrows()]

    def _extract_medications(self, prescriptions: pd.DataFrame) -> list:
        meds = []
        for _, r in prescriptions.tail(10).iterrows():
            meds.append({
                "drug": str(r['drug']),
                "dose": str(r['dose_val_rx']) if pd.notna(r['dose_val_rx']) else None,
                "route": str(r['route']) if pd.notna(r['route']) else None,
                "startdate": str(r['startdate']) if pd.notna(r['startdate']) else None,
            })
        return meds

    def _extract_conditions(self, diagnoses: pd.DataFrame) -> list:
        try:
            icd_diag = self._load_table("d_icd_diagnoses")
            conditions = []
            for _, row in diagnoses.iterrows():
                match = icd_diag[icd_diag['icd9_code'] == row['icd9_code']]
                if len(match) > 0:
                    conditions.append(match.iloc[0]['short_title'])
            return conditions[:5]
        except:
            return []


collecteur = AgentCollecteur()


def tool_collecter_par_id(subject_id: int) -> Dict[str, Any]:
    """Tool: collecte les données patient depuis MIMIC-III"""
    return collecteur.collecter_donnees_patient(subject_id=subject_id)


def tool_collecter_depuis_texte(texte_medical: str) -> Dict[str, Any]:
    """Tool: collecte les données patient depuis texte libre"""
    return collecteur.collecter_donnees_patient(texte_medical=texte_medical)


collecteur_agent = LlmAgent(
    name="collecteur_agent",
    model="gemini-2.0-flash",
    description="Agent de collecte de données cliniques depuis MIMIC-III ou texte libre.",
    instruction="""
Tu es un agent de collecte de données médicales. 
Tu peux appeler les outils pour récupérer des données patient :
- `tool_collecter_par_id(subject_id)` pour les patients du dataset MIMIC-III
- `tool_collecter_depuis_texte(texte_medical)` pour les textes libres

Retourne toujours les données dans un format JSON normalisé 
sous la clé 'patient_normalized'.
""",
    tools=[tool_collecter_par_id, tool_collecter_depuis_texte],
    output_key="donnees_patient"
)


# ============================================================
# SYNTHETISEUR AGENT - Schemas et agent
# ============================================================

class CriticalAlert(BaseModel):
    type: Literal[
        "MISSING_DATA",
        "INCONSISTENCY",
        "DELAYED_ACTION",
        "TREATMENT_MISMATCH",
        "SILENT_DETERIORATION"
    ] = Field(..., description="Category of the detected alert.")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(..., description="Severity level of the alert.")
    finding: str = Field(..., description="Precise description of the problem or inconsistency found.")
    action_required: str = Field(..., description="Recommended immediate action to mitigate the issue.")


class DataInconsistency(BaseModel):
    field_1: str = Field(..., description="First data field name involved in inconsistency.")
    value_1: str = Field(..., description="Value of the first field.")
    field_2: str = Field(..., description="Second data field name involved in inconsistency.")
    value_2: str = Field(..., description="Value of the second field.")
    explanation: str = Field(..., description="Explanation of why these values are inconsistent.")


class ReliabilityAssessment(BaseModel):
    dossier_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness ratio of the patient dossier (0.0-1.0).")
    confidence_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Overall confidence in data reliability.")
    critical_data_missing: List[str] = Field(default_factory=list, description="List of critical missing data elements.")
    data_quality_issues: List[str] = Field(default_factory=list, description="Detected issues affecting data quality.")


class ClinicalScore(BaseModel):
    score_name: str = Field(..., description="Name of the clinical score (SOFA, qSOFA, NEWS, GCS, etc.)")
    value: str = Field(..., description="Numerical or qualitative value of the score.")
    interpretation: str = Field(..., description="Interpretation of the score result.")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence for the calculated score.")


class DeteriorationAnalysis(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(..., description="Predicted risk level of deterioration.")
    warning_signs: List[str] = Field(default_factory=list, description="Clinical warning signs indicating potential deterioration.")
    predicted_timeline: Optional[str] = Field(None, description="Estimated time frame for possible deterioration.")
    evidence: List[str] = Field(default_factory=list, description="Clinical evidence supporting the prediction.")


class SynthetiseurOutput(BaseModel):
    """Structured output for the Synthétiseur (Jekyll/Hyde) agent."""
    
    critical_alerts: List[CriticalAlert] = Field(default_factory=list, description="List of identified critical alerts.")
    data_inconsistencies: List[DataInconsistency] = Field(default_factory=list, description="Detected inconsistencies between data points.")
    reliability_assessment: ReliabilityAssessment = Field(..., description="Global assessment of data reliability and completeness.")
    clinical_scores: List[ClinicalScore] = Field(default_factory=list, description="Calculated clinical scores with interpretations.")
    deterioration_analysis: DeteriorationAnalysis = Field(..., description="Predicted deterioration risks and evidence.")


synthetiseur_agent = LlmAgent(
    name="synthetiseur_agent",
    model="gemini-2.0-flash",
    description="Medical synthesis and self-criticism agent using the Jekyll/Hyde method.",
    instruction="""Your RUTHLESS SELF-CRITICISM mission:
1. Look for what is MISSING in the data
2. Find INCONSISTENCIES between data points
3. Detect ABNORMAL DELAYS
4. Identify UNMENTIONED RISKS
5. Spot INAPPROPRIATE TREATMENTS

Output strictly as JSON matching the defined schema.""",
    output_schema=SynthetiseurOutput,
    output_key="synthese_clinique"
)


# ============================================================
# EXPERT AGENT - Schemas et agent
# ============================================================

class EvidenceItem(BaseModel):
    source: Optional[str] = Field(None, description="Source de l'information ou référence clinique.")
    statement: str = Field(..., description="Élément de preuve clinique (POUR ou CONTRE le diagnostic).")


class DifferentialDiagnosis(BaseModel):
    diagnosis: str = Field(..., description="Nom du diagnostic différentiel.")
    probability: Literal["LOW", "MEDIUM", "HIGH", "VERY_HIGH"] = Field(..., description="Probabilité estimée du diagnostic.")
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Confiance dans l'évaluation du diagnostic.")
    supporting_evidence: List[EvidenceItem] = Field(default_factory=list, description="Éléments soutenant le diagnostic.")
    contradicting_evidence: List[EvidenceItem] = Field(default_factory=list, description="Éléments s'opposant au diagnostic.")


class GuidelineValidation(BaseModel):
    alert_type: str = Field(..., description="Type d'alerte ou problème évalué.")
    guideline_source: str = Field(..., description="Nom de la guideline utilisée (ex: Surviving Sepsis, AHA, ESC, etc.).")
    recommendation: str = Field(..., description="Recommandation issue de la guideline.")
    compliance: Literal["COMPLIANT", "PARTIAL", "NON_COMPLIANT"] = Field(..., description="Niveau de conformité de la prise en charge.")
    evidence_strength: Literal["LOW", "MODERATE", "HIGH", "STRONG"] = Field(..., description="Force de l'évidence selon la source.")
    references: List[str] = Field(default_factory=list, description="Références bibliographiques ou liens vers guidelines.")


class RiskScore(BaseModel):
    score_name: str = Field(..., description="Nom du score (SOFA, qSOFA, APACHE II, GRACE, TIMI, etc.)")
    value: str = Field(..., description="Valeur calculée du score.")
    interpretation: str = Field(..., description="Signification clinique du score obtenu.")
    guideline_reference: Optional[str] = Field(None, description="Référence guideline associée au score (optionnelle).")


class ActionItem(BaseModel):
    action: str = Field(..., description="Description de l'action à entreprendre.")
    priority: Literal["IMMEDIATE", "URGENT", "ROUTINE"] = Field(..., description="Niveau de priorité de l'action.")
    rationale: Optional[str] = Field(None, description="Justification clinique ou guideline de cette action.")
    time_window: Optional[str] = Field(None, description="Fenêtre temporelle recommandée (ex: '<15 min', '<1h', etc.).")


class ActionPlan(BaseModel):
    immediate_actions: List[ActionItem] = Field(default_factory=list, description="Actions vitales à entreprendre immédiatement (<15 min).")
    urgent_actions: List[ActionItem] = Field(default_factory=list, description="Actions importantes à entreprendre rapidement (<1h).")
    diagnostic_workup: List[ActionItem] = Field(default_factory=list, description="Examens complémentaires ou investigations à prioriser.")


class EvidenceSummary(BaseModel):
    key_findings: List[str] = Field(default_factory=list, description="Résumés des points cliniques majeurs.")
    references_used: List[str] = Field(default_factory=list, description="Liste complète des références citées ou consultées.")
    methodology_note: Optional[str] = Field(None, description="Notes sur la méthodologie d'évaluation ou sur les limites de l'analyse.")


class ExpertAgentOutput(BaseModel):
    """
    Sortie structurée de l'agent expert (validation clinique + diagnostic différentiel)
    suivant le processus en 5 phases.
    """
    differential_diagnoses: List[DifferentialDiagnosis] = Field(default_factory=list, description="Diagnostics différentiels générés.")
    guideline_validations: List[GuidelineValidation] = Field(default_factory=list, description="Validation des alertes selon les guidelines.")
    risk_scores: List[RiskScore] = Field(default_factory=list, description="Scores de risque pertinents calculés.")
    action_plan: ActionPlan = Field(..., description="Plan d'action clinique priorisé.")
    evidence_summary: EvidenceSummary = Field(..., description="Synthèse finale des preuves et références utilisées.")


expert_agent = LlmAgent(
    name="expert_agent",
    model="gemini-2.0-flash",
    description="""
Agent médical expert en validation clinique et diagnostics différentiels.
Analyse les alertes de l'Agent Synthétiseur, valide contre les guidelines médicales,
génère des diagnostics différentiels et propose des plans d'action sourcés.
""",
    instruction="""
Tu es un professeur de médecine expert en médecine d'urgence et infectiologie.
Analyse la synthèse clinique et suis rigoureusement le processus en 5 phases :
1. Diagnostics différentiels
2. Validation des guidelines
3. Scores de risque
4. Plan d'action
5. Synthèse des preuves
Retourne la sortie STRICTEMENT au format JSON conforme au schéma spécifié.
""",
    output_schema=ExpertAgentOutput,
    output_key="validation_expert"
)


# ============================================================
# PIPELINE ET ROOT AGENT
# ============================================================

# Wrapping des agents comme outils ADK
collecteur_tool = agent_tool.AgentTool(agent=collecteur_agent)
synthetiseur_tool = agent_tool.AgentTool(agent=synthetiseur_agent)
expert_tool = agent_tool.AgentTool(agent=expert_agent)

# Pipeline complet : Collecte → Synthèse → Validation
pipeline_clinique = SequentialAgent(
    name="pipeline_clinique",
    sub_agents=[collecteur_agent, synthetiseur_agent, expert_agent],
)

pipeline_tool = agent_tool.AgentTool(agent=pipeline_clinique)

root_agent = LlmAgent(
    name="root_agent_clinique",
    model="gemini-2.0-flash",
    description="""
    Agent coordinateur principal du système clinique multi-agent.
    Il orchestre la collecte, la synthèse et la validation médicale des données patients.
    """,
    instruction="""
Tu es le coordinateur clinique principal d'un système multi-agent médical.
Ton rôle est de diriger intelligemment les sous-agents disponibles selon le type de demande utilisateur.

=========================
🧠 RÔLE GLOBAL
=========================
Tu dois déterminer dynamiquement quelles étapes du raisonnement clinique exécuter :
- Si le contexte contient un **identifiant patient (subject_id)** → exécute le pipeline complet `pipeline_clinique`.
- Si le contexte contient un **texte médical brut** (compte rendu, observation, courrier, etc.) → exécute aussi `pipeline_clinique`.
- Si la demande concerne uniquement une **vérification, une validation ou un avis clinique** et que la synthèse existe déjà (`synthese_clinique` dans le contexte) → appelle uniquement `expert_agent`.
- Si la demande concerne la **génération d'une synthèse clinique à partir de données déjà collectées** (`donnees_patient` présentes dans le contexte) → appelle `synthetiseur_agent`.
- Si la demande concerne **la simple collecte de données patient** → appelle `collecteur_agent`.

=========================
🩺 PIPELINE CLINIQUE
=========================
Le pipeline complet `pipeline_clinique` exécute dans l'ordre :
1️⃣ `collecteur_agent` — collecte les données patient depuis MIMIC-III ou texte libre.  
2️⃣ `synthetiseur_agent` — produit une synthèse clinique (mode Jekyll/Hyde).  
3️⃣ `expert_agent` — valide la synthèse et produit les recommandations médicales.  

Si l'utilisateur demande une **analyse complète** (par exemple :  
> "Analyse complète du patient 12548"  
ou  
> "Analyse complète du patient suivant : [texte médical]")  
alors tu dois **appeler `pipeline_clinique` directement** avec les bons paramètres.

=========================
⚙️ OUTILS DISPONIBLES
=========================
- `pipeline_clinique(subject_id=..., texte_medical=...)`
  → Exécute tout le pipeline (Collecte → Synthèse → Validation).
- `collecteur_agent(subject_id=..., texte_medical=...)`
  → Collecte uniquement les données patient.
- `synthetiseur_agent(donnees_patient=...)`
  → Produit une synthèse clinique et une auto-critique.
- `expert_agent(synthese_clinique=...)`
  → Fait la validation experte et les diagnostics différentiels.

=========================
💡 DIRECTIVES
=========================
- Tu dois toujours répondre avec un ton professionnel et structuré.
- Résume les conclusions cliniques finales du pipeline de façon claire.
- Si un outil échoue ou manque de contexte (ex. synthèse non trouvée),
  propose automatiquement l'étape précédente pour reconstituer le contexte.
- N'invente jamais de données patient : tu dois te baser sur les sorties des outils.
- Termine toujours ta réponse par une **conclusion clinique synthétique**.

=========================
📝 EXEMPLES
=========================
🧩 Exemple 1 :
Utilisateur : "Analyse complète du patient 14532"
→ Appelle `pipeline_clinique(subject_id=14532)`

🧩 Exemple 2 :
Utilisateur : "Voici un texte médical à analyser : ..."
→ Appelle `pipeline_clinique(texte_medical="...")`

🧩 Exemple 3 :
Utilisateur : "Valide la synthèse clinique précédente."
→ Appelle `expert_agent(synthese_clinique={synthese_clinique?})`

🧩 Exemple 4 :
Utilisateur : "Montre-moi seulement les données patient du sujet 125."
→ Appelle `collecteur_agent(subject_id=125)`

=========================
🎯 OBJECTIF FINAL
=========================
Fournir une réponse clinique complète, logique et hiérarchisée :
- Résumé patient
- Synthèse médicale (Jekyll)
- Auto-critique (Hyde)
- Validation experte
- Plan d'action et recommandations
""",
    tools=[pipeline_tool, collecteur_tool, synthetiseur_tool, expert_tool],
)