#!/usr/bin/env python3
"""
Script d'import MIMIC-III vers Cloud SQL
Version simplifiée pour votre cas d'usage
"""

import os
import sys
import argparse
import re
from pathlib import Path
from urllib.parse import quote_plus  # ✅ AJOUT IMPORTANT
import pandas as pd
from sqlalchemy import create_engine
from google.cloud import storage, secretmanager
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tables MIMIC-III
TABLES = [
    "ADMISSIONS", "CALLOUT", "CAREGIVERS", "CHARTEVENTS", "CPTEVENTS",
    "DATETIMEEVENTS", "D_CPT", "DIAGNOSES_ICD", "D_ICD_DIAGNOSES",
    "D_ICD_PROCEDURES", "D_ITEMS", "D_LABITEMS", "DRGCODES", "ICUSTAYS",
    "INPUTEVENTS_CV", "INPUTEVENTS_MV", "LABEVENTS", "MICROBIOLOGYEVENTS",
    "NOTEEVENTS", "OUTPUTEVENTS", "PATIENTS", "PRESCRIPTIONS",
    "PROCEDUREEVENTS_MV", "PROCEDURES_ICD", "SERVICES", "TRANSFERS"
]

def clean_db_host(db_host: str) -> str:
    """Nettoie et valide l'IP/hostname de la base de données"""
    if not db_host:
        raise ValueError("❌ DB_HOST est vide")
    
    # Extraire seulement l'IP si elle contient des caractères parasites
    # Chercher un pattern IP valide (xxx.xxx.xxx.xxx)
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    match = re.search(ip_pattern, db_host)
    
    if match:
        clean_ip = match.group(0)
        if clean_ip != db_host:
            logger.warning(f"⚠️  DB_HOST nettoyé: '{db_host}' → '{clean_ip}'")
        return clean_ip
    
    # Si pas de pattern IP trouvé, retourner tel quel (peut être un hostname)
    return db_host

def get_secret(project_id: str, secret_id: str) -> str:
    """Récupère un secret depuis Secret Manager"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du secret {secret_id}: {e}")
        raise

def create_db_engine(env: str, project_id: str):
    """Crée le moteur SQLAlchemy"""
    db_user = os.getenv("DB_USER", "adn_user")
    db_name = os.getenv("DB_NAME", "adn_database")
    db_host_raw = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    
    if not db_host_raw:
        raise ValueError("❌ DB_HOST n'est pas défini dans les variables d'environnement")
    
    # Nettoyer l'IP
    db_host = clean_db_host(db_host_raw)
    
    logger.info(f"🔗 Connexion à la base de données:")
    logger.info(f"  • Host (raw): {db_host_raw}")
    logger.info(f"  • Host (clean): {db_host}")
    logger.info(f"  • Port: {db_port}")
    logger.info(f"  • Database: {db_name}")
    logger.info(f"  • User: {db_user}")
    
    # Récupérer le password depuis Secret Manager
    secret_id = f"adn-app-db-password-{env}"
    logger.info(f"🔑 Récupération du mot de passe depuis Secret Manager ({secret_id})...")
    db_password = get_secret(project_id, secret_id)
    
    # ✅ ENCODER le mot de passe pour gérer les caractères spéciaux (@, :, /, etc.)
    db_password_encoded = quote_plus(db_password)
    logger.info(f"🔒 Mot de passe encodé pour URL (longueur: {len(db_password_encoded)} caractères)")
    
    connection_string = (
        f"postgresql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}"
    )
    
    logger.info("✅ Création du moteur SQLAlchemy...")
    return create_engine(
        connection_string,
        connect_args={"connect_timeout": 30},
        pool_pre_ping=True,
        echo=False
    )

def download_from_gcs(bucket_name: str, blob_name: str, local_path: Path):
    """Télécharge un fichier depuis GCS"""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            raise FileNotFoundError(f"❌ Le fichier {blob_name} n'existe pas dans le bucket {bucket_name}")
        
        blob.download_to_filename(str(local_path))
        file_size_mb = local_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Téléchargé: {blob_name} ({file_size_mb:.2f} MB)")
    except Exception as e:
        logger.error(f"❌ Erreur lors du téléchargement de {blob_name}: {e}")
        raise

def import_csv_table(engine, csv_path: Path, table_name: str):
    """Import un CSV dans PostgreSQL"""
    try:
        logger.info(f"📥 Import de {table_name}...")
        
        # Lire le CSV
        df = pd.read_csv(csv_path, low_memory=False)
        logger.info(f"  • {len(df):,} lignes détectées")
        logger.info(f"  • {len(df.columns)} colonnes: {', '.join(df.columns[:5].tolist())}{'...' if len(df.columns) > 5 else ''}")
        
        # Normaliser les noms de colonnes
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Import par chunks
        logger.info(f"  • Import en cours...")
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
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(description="Import MIMIC-III vers Cloud SQL")
    parser.add_argument("--env", required=True, choices=["staging", "prod"])
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--subset", type=int, help="Nombre de tables à importer (test)")
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info(f"🚀 Import MIMIC-III vers Cloud SQL ({args.env})")
    logger.info(f"📦 Project ID: {args.project_id}")
    logger.info(f"🗄️  Bucket: {args.bucket}")
    logger.info("=" * 80)
    
    # Afficher les variables d'environnement pour debug
    logger.info("🔍 Variables d'environnement:")
    logger.info(f"  • DB_HOST (env): {os.getenv('DB_HOST', 'NOT SET')}")
    logger.info(f"  • DB_PORT (env): {os.getenv('DB_PORT', 'NOT SET')}")
    logger.info(f"  • DB_NAME (env): {os.getenv('DB_NAME', 'NOT SET')}")
    logger.info(f"  • DB_USER (env): {os.getenv('DB_USER', 'NOT SET')}")
    logger.info("")
    
    # Créer le moteur DB
    try:
        engine = create_db_engine(args.env, args.project_id)
        # Test de connexion
        with engine.connect() as conn:
            logger.info("✅ Connexion à la base de données réussie")
    except Exception as e:
        logger.error(f"❌ Impossible de se connecter à la base de données: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    # Dossier temporaire
    temp_dir = Path("/tmp/mimic_import")
    temp_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Dossier temporaire: {temp_dir}")
    
    # Déterminer les tables à importer
    tables_to_import = TABLES[:args.subset] if args.subset else TABLES
    logger.info(f"📊 Nombre de tables à importer: {len(tables_to_import)}")
    logger.info("")
    
    # Import de chaque table
    success_count = 0
    failed_tables = []
    
    for i, table in enumerate(tables_to_import, 1):
        logger.info(f"{'=' * 80}")
        logger.info(f"📊 Table {i}/{len(tables_to_import)}: {table}")
        logger.info(f"{'=' * 80}")
        
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
            if local_path.exists():
                local_path.unlink()
                logger.info(f"🗑️  Fichier temporaire supprimé")
            
        except Exception as e:
            logger.error(f"❌ Erreur globale sur {table}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            failed_tables.append(table)
            
            # Nettoyer en cas d'erreur
            if local_path.exists():
                local_path.unlink()
        
        logger.info("")
    
    # Résumé
    logger.info("=" * 80)
    logger.info("📊 RÉSUMÉ DE L'IMPORT")
    logger.info("=" * 80)
    logger.info(f"✅ Tables importées avec succès: {success_count}/{len(tables_to_import)}")
    
    if failed_tables:
        logger.warning(f"⚠️  Tables échouées ({len(failed_tables)}): {', '.join(failed_tables)}")
        logger.info("=" * 80)
        return 1
    else:
        logger.info("🎉 Toutes les tables ont été importées avec succès !")
        logger.info("=" * 80)
        return 0

if __name__ == "__main__":
    sys.exit(main())