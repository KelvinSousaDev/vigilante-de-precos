from fastapi import FastAPI
import sqlite3
import os
import psycopg2

app = FastAPI()

@app.get("/")
async def index():
  return{"status": "Vigilante ON"}

@app.get("/historico")
async def historico():
  db_url = os.getenv("DATABASE_URL")
  query_segura = """
      SELECT 
          f.id, 
          p.nome_produto AS produto, 
          f.valor_coletado AS valor, 
          p.loja, 
          f.data_coleta AS data_hora 
      FROM 
          fato_precos f
      JOIN 
          dim_produtos p ON f.produto_id = p.id
      ORDER BY 
          f.data_coleta DESC;
      """
  resultados = []

  if db_url:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute(query_segura)
    resultados = cursor.fetchall()
    conn.close()
  else:
    conn = sqlite3.connect('precos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM historico_precos")
    resultados = cursor.fetchall()
    conn.close()

  dados_formatados = []
  for item in resultados:
    dados = {
      "id": item[0],
      "produto": item[1],
      "valor": item[2],
      "loja": item[3],
      "data_hora": item[4]
    }
    dados_formatados.append(dados)
  return dados_formatados