import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    print("🦇 Conectado! Criando Nova Tabela")

  # Criar a Tabela dos Logs

    print("🔨 Criando tabela 'logs_execucao'...")
    cursor.execute("""
      CREATE TABLE IF NOT EXISTS logs_execucao (
          id SERIAL PRIMARY KEY,
          data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          status VARCHAR(50),
          detalhes TEXT
          );
      """)
    
except Exception as e:
  print(f"Deu ruim: {e}")
finally:
  if 'conn' in locals(): conn.close()