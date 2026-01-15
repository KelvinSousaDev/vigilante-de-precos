import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

db_url = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True 
    cursor = conn.cursor()
    print("🦇 Conexão estabelecida com sucesso!")

    print("Criando tabela dim_produtos...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_produtos (
            id SERIAL PRIMARY KEY,
            nome_produto VARCHAR(200) NOT NULL,
            loja VARCHAR(100),
            url_produto TEXT UNIQUE -- Garante que não duplicamos o mesmo link
        );
    """)

    print("Criando tabela fato_precos...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fato_precos (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER REFERENCES dim_produtos(id), -- Chave Estrangeira (O Link)
            valor_coletado NUMERIC(10, 2),
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("✅ Sucesso! Tabelas 'dim_produtos' e 'fato_precos' criadas.")

except Exception as e:
    print(f"❌ Erro fatal: {e}")

finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()