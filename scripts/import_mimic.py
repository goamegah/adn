#!/usr/bin/env python3
"""
Script d'import MIMIC-III vers Cloud SQL
Version simplifiée pour votre cas d'usage
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from google.cloud import storage, secretmanager
import google.auth
from tqdm import tqdm
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

db_host_config = {
    "adn-app-chn-staging": "adn-app-chn-staging:europe-west1:adn-app-db-staging",
    "adn-app-chn-prod": "adn-app-chn-prod:europe-west1:adn-app-db-prod",
}

def get_db_host(project_id):
    return db_host_config.get(project_id, db_host_config["adn-app-chn-staging"])

_, project_id = google.auth.default()
os.environ.setdefault("DB_HOST", get_db_host(project_id))
os.environ.setdefault("DB_USER", "adn_user")
os.environ.setdefault("DB_NAME", "adn_database")
os.environ.setdefault("DB_PORT", "5432")


# Tables MIMIC-III
TABLES = [
    "ADMISSIONS", "CALLOUT", "CAREGIVERS", "CHARTEVENTS", "CPTEVENTS",
    "DATETIMEEVENTS", "D_CPT", "DIAGNOSES_ICD", "D_ICD_DIAGNOSES",
    "D_ICD_PROCEDURES", "D_ITEMS", "D_LABITEMS", "DRGCODES", "ICUSTAYS",
    "INPUTEVENTS_CV", "INPUTEVENTS_MV", "LABEVENTS", "MICROBIOLOGYEVENTS",
    "NOTEEVENTS", "OUTPUTEVENTS", "PATIENTS", "PRESCRIPTIONS",
    "PROCEDUREEVENTS_MV", "PROCEDURES_ICD", "SERVICES", "TRANSFERS"
]

def get_secret(project_id: str, secret_id: str) -> str:
    """Récupère un secret depuis Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def create_db_engine(env: str, project_id: str):
    """Crée le moteur SQLAlchemy"""
    db_user = os.getenv("DB_USER", "adn_user")
    db_name = os.getenv("DB_NAME", "adn_database")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    
    # Récupérer le password depuis Secret Manager
    secret_id = f"adn-app-db-password-{env}"
    db_password = get_secret(project_id, secret_id)
    
    connection_string = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    
    return create_engine(
        connection_string,
        connect_args={"connect_timeout": 30}
    )

def download_from_gcs(bucket_name: str, blob_name: str, local_path: Path):
    """Télécharge un fichier depuis GCS"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.download_to_filename(str(local_path))
    logger.info(f"✅ Téléchargé: {blob_name}")

def import_csv_table(engine, csv_path: Path, table_name: str):
    """Import un CSV dans PostgreSQL"""
    try:
        logger.info(f"📥 Import de {table_name}...")
        
        # Lire le CSV
        df = pd.read_csv(csv_path, low_memory=False)
        logger.info(f"  • {len(df):,} lignes détectées")
        
        # Normaliser les noms de colonnes
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Import par chunks
        df.to_sql(
            table_name.lower(),
            engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=5000
        )
        
        logger.info(f"✅ {table_name}: {len(df):,} lignes importées")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur sur {table_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Import MIMIC-III vers Cloud SQL")
    parser.add_argument("--env", required=True, choices=["staging", "prod"], default="staging")
    parser.add_argument("--project-id", required=True, default="adn-app-chn-staging")
    parser.add_argument("--bucket", required=True, default="adn-app-chn-staging-mimic-data")
    parser.add_argument("--subset", type=int, help="Nombre de tables à importer (test)")
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info(f"🚀 Import MIMIC-III vers Cloud SQL ({args.env})")
    logger.info("=" * 80)
    
    # Créer le moteur DB
    engine = create_db_engine(args.env, args.project_id)
    
    # Dossier temporaire
    temp_dir = Path("/tmp/mimic_import")
    temp_dir.mkdir(exist_ok=True)
    
    # Déterminer les tables à importer
    tables_to_import = TABLES[:args.subset] if args.subset else TABLES
    
    # Import de chaque table
    success_count = 0
    failed_tables = []
    
    for table in tqdm(tables_to_import, desc="📊 Import des tables"):
        csv_filename = f"{table}.csv"
        local_path = temp_dir / csv_filename
        
        try:
            # Télécharger depuis GCS
            download_from_gcs(args.bucket, csv_filename, local_path)
            
            # Importer dans Cloud SQL
            if import_csv_table(engine, local_path, table):
                success_count += 1
            else:
                failed_tables.append(table)
            
            # Nettoyer
            local_path.unlink()
            
        except Exception as e:
            logger.error(f"❌ Erreur globale sur {table}: {e}")
            failed_tables.append(table)
    
    # Résumé
    logger.info("=" * 80)
    logger.info(f"✅ Import terminé: {success_count}/{len(tables_to_import)} tables")
    if failed_tables:
        logger.warning(f"⚠️  Tables échouées: {', '.join(failed_tables)}")
    logger.info("=" * 80)
    
    return 0 if not failed_tables else 1

if __name__ == "__main__":
    sys.exit(main())