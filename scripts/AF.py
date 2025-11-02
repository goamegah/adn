import os
import psycopg2
import pandas as pd

# === Paramètres Cloud SQL ===
DB_USER = os.getenv("DB_USER", "adn_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ChangeThisSuperSecurePassword")
DB_NAME = os.getenv("DB_NAME", "adn_emergency_db")
DB_HOST = "127.0.0.1"
DB_PORT = 5433


print(f"🔌 Tentative de connexion à {DB_HOST}:{DB_PORT} / DB={DB_NAME}")

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        connect_timeout=10,
    )


    print("✅ Connexion établie avec succès à la base Cloud SQL !")

    # Exemple : lire 5 patients
    query = "SELECT subject_id, gender, dob, dod FROM patients LIMIT 5;"
    df = pd.read_sql(query, conn)

    print("\n📋 Extrait de la table 'patients':")
    print(df.to_string(index=False))

    conn.close()
    print("\n🔒 Connexion fermée proprement.")

except Exception as e:
    print(f"❌ Erreur lors de la connexion ou de la lecture : {e}")
