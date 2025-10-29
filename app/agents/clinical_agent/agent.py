import os
import sys
import json
import pandas as pd
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import agent_tool
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentCollecteur:
    """Agent 1 : Collecte les données patient depuis Cloud SQL (MIMIC-III importée)"""

    def __init__(
        self,
        db_user: str = None,
        db_password: str = None,
        db_name: str = None,
        db_host: str = None,
        db_port: int = None,
        instance_conn_name: str = None,
    ):
        # 🔥 Mode MOCK pour les tests (PR checks, unit tests)
        self.use_mock = os.getenv("USE_MOCK_DB", "false").lower() == "true"
        
        if self.use_mock:
            logger.info("🧪 MODE MOCK ACTIVÉ - Pas de connexion réelle à Cloud SQL")
            self.engine = None
            return
        
        # Configuration réelle pour staging/prod
        self.db_user = db_user or os.getenv("DB_USER", "app_user")
        self.db_password = db_password or os.getenv("DB_PASSWORD")
        self.db_name = db_name or os.getenv("DB_NAME", "app_db")
        self.db_host = db_host or os.getenv("DB_HOST")
        self.db_port = db_port or int(os.getenv("DB_PORT", "5432"))
        self.instance_conn_name = instance_conn_name or os.getenv("INSTANCE_CONNECTION_NAME")

        # Vérification des variables requises
        if not self.db_password:
            raise ValueError("❌ DB_PASSWORD requis en mode production")

        # 🔗 Connexion dynamique Cloud SQL / local
        self._setup_connection()

    def _setup_connection(self):
        """Configure la connexion à Cloud SQL"""
        try:
            # Priorité 1: Unix socket (Cloud Run avec Cloud SQL Proxy)
            socket_path = f"/cloudsql/{self.instance_conn_name}"
            if self.instance_conn_name and os.path.exists(socket_path):
                connection_uri = (
                    f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                    f"@/{self.db_name}?host={socket_path}"
                )
                logger.info(f"🔗 Cloud SQL socket détecté : {self.instance_conn_name}")
            
            # Priorité 2: IP publique avec SSL
            elif self.db_host:
                connection_uri = (
                    f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                    f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require"
                )
                logger.info(f"🌐 Connexion IP publique : {self.db_host}:{self.db_port}")
            
            else:
                raise ValueError("❌ Ni socket Cloud SQL ni DB_HOST configuré")

            # Création du pool de connexions
            self.engine = create_engine(
                connection_uri,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                echo=False
            )
            
            # Test de connexion
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"✅ Connexion Cloud SQL réussie - {version}")
                
        except Exception as e:
            logger.error(f"❌ Erreur de connexion à Cloud SQL : {e}")
            raise

    def _load_table(self, name: str, limit: Optional[int] = 1000) -> pd.DataFrame:
        """Charge une table depuis Cloud SQL ou retourne des données mock"""
        if self.use_mock:
            logger.info(f"🧪 MOCK : Retour de données factices pour {name}")
            return self._get_mock_data(name)
        
        try:
            query = f"SELECT * FROM {name}"
            if limit:
                query += f" LIMIT {limit}"
            
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn)
            
            logger.info(f"📊 Table {name} chargée ({len(df)} lignes)")
            return df
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du chargement de {name}: {e}")
            return pd.DataFrame()

    def _get_mock_data(self, table_name: str) -> pd.DataFrame:
        """Retourne des données mock pour les tests"""
        mock_data = {
            "patients": pd.DataFrame({
                "subject_id": [12345, 12346, 12347],
                "gender": ["M", "F", "M"],
                "dob": ["1970-01-01", "1985-06-15", "1992-11-30"],
                "expire_flag": [0, 0, 1],
                "dod": [None, None, "2024-03-15"]
            }),
            "admissions": pd.DataFrame({
                "subject_id": [12345, 12346, 12347],
                "hadm_id": [100001, 100002, 100003],
                "admittime": ["2024-01-01 10:00:00", "2024-01-02 14:30:00", "2024-01-03 08:15:00"],
                "admission_type": ["EMERGENCY", "ELECTIVE", "EMERGENCY"],
                "admission_location": ["EMERGENCY ROOM", "PHYSICIAN REFERRAL", "EMERGENCY ROOM"],
                "diagnosis": ["Chest pain", "Scheduled surgery", "Septic shock"],
                "hospital_expire_flag": [0, 0, 1]
            }),
            "icustays": pd.DataFrame({
                "subject_id": [12345, 12347],
                "hadm_id": [100001, 100003],
                "intime": ["2024-01-01 11:00:00", "2024-01-03 09:00:00"],
                "outtime": ["2024-01-02 08:00:00", "2024-01-03 20:00:00"]
            }),
            "diagnoses_icd": pd.DataFrame({
                "hadm_id": [100001, 100001, 100003],
                "icd9_code": ["410.71", "401.9", "038.9"],
                "seq_num": [1, 2, 1]
            }),
            "procedures_icd": pd.DataFrame({
                "hadm_id": [100001, 100003],
                "icd9_code": ["99.04", "96.72"],
                "seq_num": [1, 1]
            }),
            "prescriptions": pd.DataFrame({
                "subject_id": [12345, 12345, 12347],
                "hadm_id": [100001, 100001, 100003],
                "drug": ["Aspirin", "Metoprolol", "Norepinephrine"],
                "dose_val_rx": ["325", "50", "0.1"],
                "route": ["PO", "PO", "IV"],
                "startdate": ["2024-01-01", "2024-01-01", "2024-01-03"]
            }),
            "labevents": pd.DataFrame({
                "subject_id": [12345, 12345, 12347, 12347],
                "itemid": [50912, 50971, 50912, 51221],
                "charttime": ["2024-01-01 11:00:00", "2024-01-01 11:00:00", 
                             "2024-01-03 09:30:00", "2024-01-03 09:30:00"],
                "value": ["140", "4.2", "180", "1.8"],
                "valuenum": [140.0, 4.2, 180.0, 1.8],
                "valueuom": ["mg/dL", "mmol/L", "mg/dL", "mg/dL"],
                "flag": [None, None, "abnormal", "abnormal"]
            }),
            "chartevents": pd.DataFrame({
                "subject_id": [12345, 12345, 12347, 12347],
                "itemid": [220045, 220179, 220045, 220179],
                "charttime": ["2024-01-01 11:00:00", "2024-01-01 11:00:00",
                             "2024-01-03 09:30:00", "2024-01-03 09:30:00"],
                "valuenum": [85.0, 120.0, 125.0, 80.0],
                "valueuom": ["bpm", "mmHg", "bpm", "mmHg"]
            }),
            "microbiologyevents": pd.DataFrame({
                "subject_id": [12347],
                "charttime": ["2024-01-03 10:00:00"],
                "spec_type_desc": ["BLOOD"],
                "org_name": ["Staphylococcus aureus"],
                "ab_name": ["Vancomycin"],
                "interpretation": ["S"]
            }),
            "d_icd_diagnoses": pd.DataFrame({
                "icd9_code": ["410.71", "401.9", "038.9"],
                "short_title": ["AMI anterior wall", "Hypertension NOS", "Septicemia NOS"]
            })
        }
        return mock_data.get(table_name, pd.DataFrame())

    def collecter_donnees_patient(
        self, 
        subject_id: Optional[int] = None, 
        texte_medical: Optional[str] = None
    ) -> Dict[str, Any]:
        """Point d'entrée principal de collecte"""
        if texte_medical:
            logger.info("🧾 Mode texte médical")
            return self._collecter_depuis_texte(texte_medical)
        
        if subject_id is None:
            raise ValueError("Il faut fournir soit subject_id soit texte_medical")
        
        # En mode mock, utiliser un subject_id par défaut
        if self.use_mock and subject_id not in [12345, 12346, 12347]:
            logger.warning(f"⚠️ Subject {subject_id} non disponible en mode mock, utilisation de 12345")
            subject_id = 12345
            
        logger.info(f"🩺 Collecte en cours pour patient {subject_id}...")
        
        try:
            result = self._collecter_depuis_mimic(subject_id)
            logger.info(f"✅ Collecte terminée pour patient {subject_id}")
            return {
                "status": "ok",
                "subject_id": subject_id,
                "patient_normalized": result["patient_normalized"]
            }
        except Exception as e:
            logger.error(f"❌ Erreur collecte patient {subject_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "subject_id": subject_id
            }

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
        
        # Normalisation
        data_normalized = {
            "patient_normalized": {
                "id": str(subject_id),
                "source_type": "MIMIC_III_CLOUDSQL" if not self.use_mock else "MOCK_DATA",
                "age": self._calculate_age(patient['dob'], admission['admittime']),
                "sex": "homme" if patient['gender'] == 'M' else "femme",
                
                "admission": {
                    "type": admission['admission_type'],
                    "chief_complaint": admission['diagnosis'],
                    "date": str(admission['admittime']),
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
                "admission": {
                    "type": "TEXTE_LIBRE",
                    "chief_complaint": "Voir texte brut",
                    "date": None
                },
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
        return [
            {"icd9_code": str(r['icd9_code']), "seq_num": int(r['seq_num'])}
            for _, r in diagnoses.iterrows()
        ]

    def _extract_procedures(self, procedures: pd.DataFrame) -> list:
        return [
            {"icd9_code": str(r['icd9_code']), "seq_num": int(r['seq_num'])}
            for _, r in procedures.iterrows()
        ]

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


# Initialisation du collecteur
collecteur = AgentCollecteur()


def tool_collecter_par_id(subject_id: int) -> Dict[str, Any]:
    """Tool: collecte les données patient depuis MIMIC-III"""
    return collecteur.collecter_donnees_patient(subject_id=subject_id)


def tool_collecter_depuis_texte(texte_medical: str) -> Dict[str, Any]:
    """Tool: collecte les données patient depuis texte libre"""
    return collecteur.collecter_donnees_patient(texte_medical=texte_medical)


# Configuration des agents ADK
collecteur_agent_adk = LlmAgent(
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


synthetiseur_agent = LlmAgent(
    name="synthetiseur_agent",
    model="gemini-2.0-flash",
    description="""
Medical synthesis and self-criticism agent using the Jekyll/Hyde method.
Analyzes patient data, creates a synthesis then self-criticizes to detect
inconsistencies, critical alerts and silent deteriorations.
""",
    instruction="""
You are an expert medical agent in clinical analysis with two modes of operation:

JEKYLL MODE (Synthesis):
- Creates clear and structured clinical summaries
- Identifies patient key problems
- Evaluates severity and clinical trajectory

HYDE MODE (Critique):
- Ruthlessly challenges data and conclusions
- Detects inconsistencies and missing data
- Identifies non-obvious risks
- Calculates relevant clinical scores
- Predicts potential deteriorations

ACCEPTED FORMATS:
1. Hospital format: {"patient_normalized": {...}}
2. EMS format: {"input": {"text": "..."}, "expected_output": {...}}
3. Free text: "Patient aged X years, ..."

ANALYSIS PROCESS:
1. Normalize input (automatically detect format)
2. Jekyll Phase: Create a complete and structured synthesis
3. Hyde Phase: Self-criticize to find flaws
4. Return a complete analysis with priority alerts

IMPORTANT: Use the output_key to store your synthesis for the next agent.
""",
    output_key="synthese_clinique"
)


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

Tu reçois la synthèse clinique de l'agent précédent dans {synthese_clinique}.

PROCESSUS EN 5 PHASES :

PHASE 1 - DIAGNOSTICS DIFFÉRENTIELS :
- Génère une liste complète et pertinente de diagnostics
- Pour chaque diagnostic : probabilité, confiance, preuves POUR/CONTRE

PHASE 2 - VALIDATION GUIDELINES :
PRINCIPES :
- Toujours privilégier la sécurité patient
- Base toutes tes recommandations sur des guidelines reconnues
- Cite systématiquement tes sources avec force de l'évidence

PHASE 3 - SCORES DE RISQUE :
- Calcule scores pertinents selon diagnostics (SOFA, qSOFA, APACHE II, GRACE, TIMI, etc.)

PHASE 4 - PLAN D'ACTION :
- IMMEDIATE (< 15 min) : actions vitales
- URGENT (< 1h) : actions importantes
- Workup diagnostique priorisé

PHASE 5 - SYNTHÈSE PREUVES :
- Compilation de toutes les références utilisées
""",
    output_key="validation_expert"
)


# Configuration du pipeline
collecteur_tool = agent_tool.AgentTool(agent=collecteur_agent_adk)
synthetiseur_tool = agent_tool.AgentTool(agent=synthetiseur_agent)
expert_tool = agent_tool.AgentTool(agent=expert_agent)

pipeline_clinique = SequentialAgent(
    name="pipeline_clinique",
    sub_agents=[collecteur_agent_adk, synthetiseur_agent, expert_agent],
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

=========================
⚙️ OUTILS DISPONIBLES
=========================
- `pipeline_clinique(subject_id=..., texte_medical=...)`
- `collecteur_agent(subject_id=..., texte_medical=...)`
- `synthetiseur_agent(donnees_patient=...)`
- `expert_agent(synthese_clinique=...)`

=========================
💡 DIRECTIVES
=========================
- Tu dois toujours répondre avec un ton professionnel et structuré.
- Résume les conclusions cliniques finales du pipeline de façon claire.
- Si un outil échoue ou manque de contexte, propose automatiquement l'étape précédente.
- N'invente jamais de données patient : tu dois te baser sur les sorties des outils.
- Termine toujours ta réponse par une **conclusion clinique synthétique**.
""",
    tools=[pipeline_tool, collecteur_tool, synthetiseur_tool, expert_tool],
)