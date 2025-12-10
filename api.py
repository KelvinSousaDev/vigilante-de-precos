from fastapi import FastAPI
import sqlite3

app = FastAPI()

@app.get("/")
async def index():
  return{"status": "Vigilante ON"}

@app.get("/historico")
async def historico():
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