# scripts/test_connection.py
import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "adn_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "adn_database")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")

if not DB_PASSWORD:
    raise ValueError("❌ DB_PASSWORD manquant")

if not DB_HOST:
    raise ValueError("❌ DB_HOST manquant")

# 🔥 ENCODAGE DU MOT DE PASSE
# Caractères spéciaux comme @, :, /, etc. doivent être encodés
encoded_password = quote_plus(DB_PASSWORD)
encoded_user = quote_plus(DB_USER)

connection_uri = (
    f"postgresql+psycopg2://{encoded_user}:{encoded_password}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)

print(f"Test de connexion à: {DB_HOST}:{DB_PORT}/{DB_NAME}")
print(f"User: {DB_USER}")
print(f"Password: {'*' * len(DB_PASSWORD)}")

try:
    engine = create_engine(
        connection_uri,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10}
    )

    with engine.connect() as conn:
        # Test 1: Version PostgreSQL
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Connexion réussie!")
        print(f"📌 PostgreSQL version: {version[:80]}...")
        
        # Test 2: Lister les tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"\n📋 Tables disponibles ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")
        
        # Test 3: Compter les patients (si la table existe)
        if 'patients' in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM patients"))
            count = result.fetchone()[0]
            print(f"\n👥 Nombre de patients: {count}")
            
            if count > 0:
                result = conn.execute(text("SELECT subject_id FROM patients LIMIT 5"))
                sample_ids = [row[0] for row in result]
                print(f"📝 Exemples de subject_id: {sample_ids}")
        
except Exception as e:
    print(f"\n❌ Erreur de connexion: {type(e).__name__}")
    print(f"📄 Message: {e}")
    
    if "timeout" in str(e).lower():
        print("\n💡 Solutions:")
        print("   1. Vérifiez que votre IP est autorisée dans Cloud SQL")
        print("   2. Utilisez Cloud SQL Proxy (recommandé)")
    elif "password authentication failed" in str(e).lower():
        print("\n💡 Vérifiez vos identifiants (user/password)")
    elif "translate host name" in str(e).lower():
        print("\n💡 Problème d'encodage du mot de passe")
        print("   Le mot de passe contient des caractères spéciaux (@, :, /, etc.)")