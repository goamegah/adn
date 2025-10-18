import psycopg2

conn = psycopg2.connect(
    host="35.241.219.137",
    database="adn_emergency_db",
    user="adn_admin",
    password="ChangeThisSuperSecurePassword"  # ton mot de passe
)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM users;")
print(cur.fetchone())

cur.close()
conn.close()
