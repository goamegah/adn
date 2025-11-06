import os
import pandas as pd
from typing import Dict, Any, Optional, List, Literal
import google.auth
from sqlalchemy import create_engine, text
import logging
from dotenv import load_dotenv
from urllib.parse import quote_plus
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import agent_tool

from pydantic import BaseModel, Field

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_password_from_secret_manager(project_id: str) -> str:
    """Récupère la chaîne de connexion DB depuis Google Cloud Secret Manager"""
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"adn-app-db-password-{'staging' if 'staging' in project_id else 'prod'}"
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

def get_cloudsql_db_host(project_id: str) -> str:
    """Récupère l'IP publique de l'instance Cloud SQL depuis Google Cloud SQL Admin API"""
    from googleapiclient import discovery

    sqladmin = discovery.build('sqladmin', 'v1beta4')
    instance_name = f"adn-app-db-{'staging' if 'staging' in project_id else 'prod'}"
    request = sqladmin.instances().get(project=project_id, instance=instance_name)
    response = request.execute()
    ip_addresses = response.get('ipAddresses', [])
    for ip_info in ip_addresses:
        if ip_info.get('type') == 'PRIMARY':
            return ip_info.get('ipAddress')
    raise ValueError("Aucune IP publique trouvée pour l'instance Cloud SQL")


_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

os.environ.setdefault("DB_USER", "adn_user")
os.environ.setdefault("DB_NAME", "adn_database")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_HOST", get_cloudsql_db_host(project_id))
os.environ.setdefault("DB_PASSWORD", get_db_password_from_secret_manager(project_id))

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
        self.engine = None

        # Mode MOCK pour les tests (PR checks, unit tests)
        self.use_mock = os.getenv("USE_MOCK_DB", "false").lower() == "true"
        
        if self.use_mock:
            logger.info("MODE MOCK ACTIVÉ - Pas de connexion réelle à Cloud SQL")
            self.engine = None
            return
        
        # Configuration réelle pour staging/prod
        self.db_user = db_user or os.getenv("DB_USER", "adn_user")
        self.db_password = db_password or os.getenv("DB_PASSWORD")
        self.db_name = db_name or os.getenv("DB_NAME", "adn_database")
        self.db_host = db_host or os.getenv("DB_HOST")
        self.db_port = db_port or int(os.getenv("DB_PORT", "5432"))
        self.instance_conn_name = instance_conn_name or os.getenv("INSTANCE_CONNECTION_NAME")

        # CORRECTION: Vérification uniquement en mode non-mock
        if not self.db_password:
            logger.warning("DB_PASSWORD manquant - tentative de connexion sans mot de passe")
            # Ne pas raise si on est en développement local
            if os.getenv("ENVIRONMENT") == "prod":
                raise ValueError("DB_PASSWORD requis en mode production")

        # Connexion dynamique Cloud SQL / local
        self._setup_connection()

    def _setup_connection(self):
        """Configure la connexion à Cloud SQL"""
        try:
            # DEBUG: Afficher la configuration
            logger.info("=" * 60)
            logger.info("CONFIGURATION DE CONNEXION")
            logger.info(f"DB_USER: {self.db_user}")
            logger.info(f"DB_PASSWORD: {'***' if self.db_password else 'MANQUANT'}")
            logger.info(f"DB_NAME: {self.db_name}")
            logger.info(f"DB_HOST: {self.db_host or 'NON DÉFINI'}")
            logger.info(f"DB_PORT: {self.db_port}")
            logger.info(f"INSTANCE_CONNECTION_NAME: {self.instance_conn_name or 'NON DÉFINI'}")
            logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'NON DÉFINI')}")
            logger.info("=" * 60)
            
            connection_uri = self._build_connection_uri()
            
            if not connection_uri:
                logger.error("connection_uri est None - aucune méthode de connexion configurée")
                return

            # Masquer le mot de passe dans les logs
            safe_uri = connection_uri.replace(self.db_password, '***') if self.db_password else connection_uri
            logger.info(f"URI de connexion: {safe_uri}")
            
            self.engine = create_engine(
                connection_uri,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                echo=False,
                connect_args={
                    "connect_timeout": 10,
                    "sslmode": "require" if self.db_host else "disable"
                }
            )
            
            # Test de connexion avec plus de détails
            logger.info("Test de connexion à la base...")
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"Connexion Cloud SQL réussie - {version[:50]}...")
                
                # Test de lecture des tables
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    LIMIT 5
                """))
                tables = [row[0] for row in result]
                logger.info(f"Tables disponibles: {', '.join(tables)}")
                    
        except Exception as e:
            logger.error(f"Erreur de connexion à Cloud SQL : {type(e).__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            if os.getenv("ENVIRONMENT") == "prod":
                raise
            logger.warning("Continuation en mode dégradé sans connexion DB")
            self.engine = None

    def _build_connection_uri(self) -> Optional[str]:
        """Construit l'URI de connexion selon l'environnement"""
        
        # ENCODER les caractères spéciaux
        encoded_user = quote_plus(self.db_user) if self.db_user else ""
        encoded_password = quote_plus(self.db_password) if self.db_password else ""
        
        logger.info(f"instance_conn_name: {self.instance_conn_name}")
        logger.info(f"db_host: {self.db_host}")
        
        # PRIORITÉ 1 : IP publique (choix explicite de l'utilisateur)
        # Si DB_HOST est défini, on l'utilise directement
        # C'est le cas pour développement local avec firewall ouvert (0.0.0.0/0)
        if self.db_host:
            logger.info(f"Connexion IP publique: {self.db_host}:{self.db_port}")
            logger.info("Pour utiliser Cloud SQL Proxy, retirez DB_HOST du .env")
            return (
                f"postgresql+psycopg2://{encoded_user}:{encoded_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require"
            )
        
        # PRIORITÉ 2 : Cloud SQL Proxy / Unix socket
        # Utilisé seulement si DB_HOST n'est PAS défini
        elif self.instance_conn_name:
            # Cas 1: Unix socket (Cloud Run avec sidecar proxy)
            socket_path = f"/cloudsql/{self.instance_conn_name}"
            if os.path.exists(socket_path):
                logger.info(f"Connexion via Unix socket: {socket_path}")
                return (
                    f"postgresql+psycopg2://{encoded_user}:{encoded_password}"
                    f"@/{self.db_name}?host={socket_path}"
                )
            
            # Cas 2: Cloud SQL Proxy local (développement avec proxy)
            else:
                logger.info("Connexion via Cloud SQL Proxy local (127.0.0.1:5432)")
                logger.warning("Assurez-vous que cloud-sql-proxy est démarré !")
                logger.info(f"Commande: cloud-sql-proxy --port 5432 {self.instance_conn_name}")
                return (
                    f"postgresql+psycopg2://{encoded_user}:{encoded_password}"
                    f"@127.0.0.1:5432/{self.db_name}"
                )
        
        # Aucune configuration trouvée
        else:
            logger.error("Aucune configuration de connexion trouvée")
            logger.error("Définissez soit DB_HOST (IP publique) soit INSTANCE_CONNECTION_NAME (proxy)")
            return None

    def _load_table(self, name: str, limit: Optional[int] = 1000) -> pd.DataFrame:
        """Charge une table depuis Cloud SQL ou retourne des données mock"""
        if self.use_mock:
            logger.info(f"MOCK : Retour de données factices pour {name}")
            return self._get_mock_data(name)
        
        # CORRECTION: Gérer le cas où engine est None
        if self.engine is None:
            logger.warning(f"Pas de connexion DB disponible, utilisation de données mock pour {name}")
            return self._get_mock_data(name)
        
        try:
            # CORRECTION: Normaliser le nom de table (minuscules)
            table_name = name.lower()
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"
            
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn)
            
            logger.info(f"Table {table_name} chargée ({len(df)} lignes)")
            return df
            
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de {name}: {e}")
            # CORRECTION: Fallback sur mock en cas d'erreur
            logger.info(f"Fallback sur données mock pour {name}")
            return self._get_mock_data(name)

    def _get_mock_data(self, table_name: str) -> pd.DataFrame:
        """Retourne des données mock pour les tests"""
        # Normaliser le nom de table
        table_name = table_name.lower()
        
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
            logger.info("Mode texte médical")
            return self._collecter_depuis_texte(texte_medical)
        
        if subject_id is None:
            raise ValueError("Il faut fournir soit subject_id soit texte_medical")
        
        # En mode mock, utiliser un subject_id par défaut
        if self.use_mock and subject_id not in [12345, 12346, 12347]:
            logger.warning(f"Subject {subject_id} non disponible en mode mock, utilisation de 12345")
            subject_id = 12345
            
        logger.info(f"Collecte en cours pour patient {subject_id}...")
        
        try:
            result = self._collecter_depuis_mimic(subject_id)
            logger.info(f"Collecte terminée pour patient {subject_id}")
            return {
                "status": "ok",
                "subject_id": subject_id,
                "patient_normalized": result["patient_normalized"]
            }
        except Exception as e:
            logger.error(f"Erreur collecte patient {subject_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "subject_id": subject_id
            }

    def _collecter_depuis_mimic(self, subject_id: int) -> Dict[str, Any]:
        """Collecte depuis Cloud SQL (tables MIMIC-III importées)"""
        patient_df = self._load_table("patients")
        
        # print(patient_df.head())

        # CORRECTION: Gérer le cas où le DataFrame est vide
        if patient_df.empty:
            raise ValueError(f"Table patients vide ou inaccessible")
        
        patient_filtered = patient_df.query(f"subject_id == {subject_id}")
        if patient_filtered.empty:
            raise ValueError(f"Patient {subject_id} non trouvé dans la base")
        
        patient = patient_filtered.iloc[0]
        
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
        
        # CORRECTION: Déterminer la source des données
        source_type = "MOCK_DATA" if self.use_mock or self.engine is None else "MIMIC_III_CLOUDSQL"
        
        # Normalisation
        data_normalized = {
            "patient_normalized": {
                "id": str(subject_id),
                "source_type": source_type,
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
        if chartevents.empty:
            return {}
        
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
        if labevents.empty:
            return []
        
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
        if microevents.empty:
            return []
        
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
        if diagnoses.empty:
            return []
        
        return [
            {"icd9_code": str(r['icd9_code']), "seq_num": int(r['seq_num'])}
            for _, r in diagnoses.iterrows()
        ]

    def _extract_procedures(self, procedures: pd.DataFrame) -> list:
        if procedures.empty:
            return []
        
        return [
            {"icd9_code": str(r['icd9_code']), "seq_num": int(r['seq_num'])}
            for _, r in procedures.iterrows()
        ]

    def _extract_medications(self, prescriptions: pd.DataFrame) -> list:
        if prescriptions.empty:
            return []
        
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
        if diagnoses.empty:
            return []
        
        try:
            icd_diag = self._load_table("d_icd_diagnoses")
            if icd_diag.empty:
                return []
            
            conditions = []
            for _, row in diagnoses.iterrows():
                match = icd_diag[icd_diag['icd9_code'] == row['icd9_code']]
                if len(match) > 0:
                    conditions.append(match.iloc[0]['short_title'])
            return conditions[:5]
        except:
            return []


# CORRECTION: Initialisation sécurisée du collecteur
try:
    collecteur = AgentCollecteur()
    logger.info("AgentCollecteur initialisé avec succès")
except Exception as e:
    logger.error(f"Erreur d'initialisation de AgentCollecteur: {e}")
    # En mode mock, continuer quand même
    if os.getenv("USE_MOCK_DB", "false").lower() == "true":
        collecteur = AgentCollecteur()
    else:
        raise



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

# Pipeline complet : Collecte -> Synthèse -> Validation
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
RÔLE GLOBAL
=========================
Tu dois déterminer dynamiquement quelles étapes du raisonnement clinique exécuter :
- Si le contexte contient un **identifiant patient (subject_id)** -> exécute le pipeline complet `pipeline_clinique`.
- Si le contexte contient un **texte médical brut** (compte rendu, observation, courrier, etc.) -> exécute aussi `pipeline_clinique`.
- Si la demande concerne uniquement une **vérification, une validation ou un avis clinique** et que la synthèse existe déjà (`synthese_clinique` dans le contexte) -> appelle uniquement `expert_agent`.
- Si la demande concerne la **génération d'une synthèse clinique à partir de données déjà collectées** (`donnees_patient` présentes dans le contexte) -> appelle `synthetiseur_agent`.
- Si la demande concerne **la simple collecte de données patient** -> appelle `collecteur_agent`.

=========================
PIPELINE CLINIQUE
=========================
Le pipeline complet `pipeline_clinique` exécute dans l'ordre :
1. `collecteur_agent` — collecte les données patient depuis MIMIC-III ou texte libre.  
2. `synthetiseur_agent` — produit une synthèse clinique (mode Jekyll/Hyde).  
3. `expert_agent` — valide la synthèse et produit les recommandations médicales.  

Si l'utilisateur demande une **analyse complète** (par exemple :  
> "Analyse complète du patient 12548"  
ou  
> "Analyse complète du patient suivant : [texte médical]")  
alors tu dois **appeler `pipeline_clinique` directement** avec les bons paramètres.

=========================
OUTILS DISPONIBLES
=========================
- `pipeline_clinique(subject_id=..., texte_medical=...)`
  -> Exécute tout le pipeline (Collecte -> Synthèse -> Validation).
- `collecteur_agent(subject_id=..., texte_medical=...)`
  -> Collecte uniquement les données patient.
- `synthetiseur_agent(donnees_patient=...)`
  -> Produit une synthèse clinique et une auto-critique.
- `expert_agent(synthese_clinique=...)`
  -> Fait la validation experte et les diagnostics différentiels.

=========================
DIRECTIVES
=========================
- Tu dois toujours répondre avec un ton professionnel et structuré.
- Résume les conclusions cliniques finales du pipeline de façon claire.
- Si un outil échoue ou manque de contexte (ex. synthèse non trouvée),
  propose automatiquement l'étape précédente pour reconstituer le contexte.
- N'invente jamais de données patient : tu dois te baser sur les sorties des outils.
- Termine toujours ta réponse par une **conclusion clinique synthétique**.

=========================
EXEMPLES
=========================
Exemple 1 :
Utilisateur : "Analyse complète du patient 14532"
-> Appelle `pipeline_clinique(subject_id=14532)`

Exemple 2 :
Utilisateur : "Voici un texte médical à analyser : ..."
-> Appelle `pipeline_clinique(texte_medical="...")`

Exemple 3 :
Utilisateur : "Valide la synthèse clinique précédente."
-> Appelle `expert_agent(synthese_clinique={synthese_clinique?})`

Exemple 4 :
Utilisateur : "Montre-moi seulement les données patient du sujet 125."
-> Appelle `collecteur_agent(subject_id=125)`

=========================
OBJECTIF FINAL
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