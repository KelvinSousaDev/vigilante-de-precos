from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

def carregar_produtos_do_banco():
  """
  Sincroniza a memória do agente com a base de dados central (Neon/Postgres).

  Responsabilidades:
  1. Estabelece conexão segura com o Data Warehouse.
  2. Executa query DQL para recuperar os alvos de monitoramento ativos.
  3. Popula a fila de execução (self.lista_produtos) para o ciclo de extração.
  """
  DATABASE_URL = os.getenv("DATABASE_URL")
  try:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")
    
    cursor = conn.cursor()

    query = "SELECT nome_produto, url_produto, loja, meta_preco FROM dim_produtos"
    cursor.execute(query)
    produtos_retornados = cursor.fetchall()

    lista_produtos = []

    for item in produtos_retornados:
        novo_produto = {
            "nome": item[0],       
            "url": item[1],        
            "loja": item[2],       
            "meta_preco": float(item[3]) if item[3] is not None else 0.0
            }
        lista_produtos.append(novo_produto)
    
    print(f"🦇 Configuração atualizada: {len(lista_produtos)} alvos carregados do DB.")
    conn.close()
    return lista_produtos
  except Exception as e:
    print(f"❌ Erro ao carregar produtos do banco: {e}")
    lista_produtos = []
    return lista_produtos