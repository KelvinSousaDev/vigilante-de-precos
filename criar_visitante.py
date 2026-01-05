import psycopg2
import os
import bcrypt
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

senha_plana = "visitante".encode('utf-8')
salt = bcrypt.gensalt()
senha_hash = bcrypt.hashpw(senha_plana, salt)

comando = "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)"
valores = ('visitante', 'demo@vigilante.com', senha_hash.decode('utf-8'))

cursor.execute(comando, valores)
conn.commit()
cursor.close()
conn.close()
print("🦇 Visitante registrado")