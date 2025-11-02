import pandas as pd
from sqlalchemy import create_engine
from tqdm import tqdm

# === Configuration Cloud SQL (us-east4) ===
DB_USER = "adn_admin"
DB_PASSWORD = "ChangeThisSuperSecurePassword"
DB_NAME = "adn_emergency_db"
DB_HOST = "34.186.39.96"   # ✅ IP publique Cloud SQL (us-east4)
DB_PORT = 5432

# === Dossier local contenant les CSV MIMIC-III ===
DATA_DIR = "/home/bao/adn/data/MIMIC 3 DATASET"

# === Création du moteur SQLAlchemy ===
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    connect_args={"connect_timeout": 10}
)

# === Tables MIMIC-III à importer ===
TABLES = [
    "ADMISSIONS", "CALLOUT", "CAREGIVERS", "CHARTEVENTS", "CPTEVENTS",
    "DATETIMEEVENTS", "D_CPT", "DIAGNOSES_ICD", "D_ICD_DIAGNOSES",
    "D_ICD_PROCEDURES", "D_ITEMS", "D_LABITEMS", "DRGCODES", "ICUSTAYS",
    "INPUTEVENTS_CV", "INPUTEVENTS_MV", "LABEVENTS", "MICROBIOLOGYEVENTS",
    "NOTEEVENTS", "OUTPUTEVENTS", "PATIENTS", "PRESCRIPTIONS",
    "PROCEDUREEVENTS_MV", "PROCEDURES_ICD", "SERVICES", "TRANSFERS"
]

print("🚀 Importation des tables MIMIC-III vers Cloud SQL (us-east4)...\n")

for table in tqdm(TABLES, desc="📥 Importation en cours"):
    path = f"{DATA_DIR}/{table}.csv"
    try:
        print(f"\n=== Importation de {table} ===")
        df = pd.read_csv(path, low_memory=False)
        df.to_sql(table.lower(), engine, if_exists="replace", index=False, method="multi", chunksize=5000)
        print(f"✅ {table} importée ({len(df):,} lignes).")
    except Exception as e:
        print(f"⚠️ Erreur sur {table}: {e}")

print("\n🎉 Importation terminée avec succès sur la base Cloud SQL (us-east4) !")
