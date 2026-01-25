import time
from bs4 import BeautifulSoup
from notificador import enviar_telegram
import os
import psycopg2
import asyncio
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv
import random

load_dotenv()

class Vigilante:
  def __init__(self):
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
      "Referer": "https://www.google.com/",
      "Connection": "keep-alive"
    }
    self.lista_produtos = [] 
    self.carregar_produtos_do_banco()

  async def main_async(self):
     semaforo = asyncio.Semaphore(2)

     async with AsyncSession(impersonate="chrome120") as session:
        tarefas = []
        for produto in self.lista_produtos:
          tarefas.append(self.processar_produto(semaforo, session, produto))
        
        print("🚀Tarefas Criadas, Iniciando Vigilante")
        resultados = await asyncio.gather(*tarefas)

        return [r for r in resultados if r is not None]

  def carregar_produtos_do_banco(self):
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

        self.lista_produtos = []

        for item in produtos_retornados:
           novo_produto = {
                "nome": item[0],       
                "url": item[1],        
                "loja": item[2],       
                "meta_preco": float(item[3]) if item[3] is not None else 0.0
                }
           self.lista_produtos.append(novo_produto)

        print(f"🦇 Configuração atualizada: {len(self.lista_produtos)} alvos carregados do DB.")
        conn.close()
     except Exception as e:
        print(f"❌ Erro ao carregar produtos do banco: {e}")
        self.lista_produtos = []

  def salvar_no_postgres(self, nome, url, preco, loja):
      DATABASE_URL = os.getenv("DATABASE_URL")
      try:
          if DATABASE_URL:
             conn = psycopg2.connect(DATABASE_URL)
          else:
             conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")
            
          cursor = conn.cursor()

          cursor.execute("SELECT id FROM dim_produtos WHERE url_produto = %s", (url,))
          resultado = cursor.fetchone()

          if resultado:
              produto_id = resultado[0]
          else:
              print(f"🆕 Produto Novo detectado: {nome} ({loja})")
              cursor.execute(
                  "INSERT INTO dim_produtos (nome_produto, url_produto, loja) VALUES (%s, %s, %s) RETURNING id",
                  (nome, url, loja)
              )
              produto_id = cursor.fetchone()[0]

          cursor.execute(
              "INSERT INTO fato_precos (produto_id, valor_coletado) VALUES (%s, %s)",
              (produto_id, preco)
          )
          
          conn.commit()
          print(f"💾 Preço de R$ {preco} salvo no PostgreSQL para o ID {produto_id}")

      except Exception as e:
          print(f"❌ Erro ao salvar no Banco: {e}")
      finally:
          if 'conn' in locals(): conn.close()

  async def verificar_mercadolivre(self, session, url):
    MAX_TENTATIVAS = 3
    for tentativa in range(MAX_TENTATIVAS):
      try:
        espera = random.uniform(0.5, 2.0) + (tentativa * 1.5)
        await asyncio.sleep(espera)

        if tentativa > 0:
          print(f"🔁 Tentativa {tentativa+1} para {url[-10:]}...")

        resposta = await session.get(url, impersonate="chrome120")
        print(f"📡 Status HTTP: {resposta.status_code}")

        if resposta.status_code != 200:
          print(f"⚠️ Erro HTTP {resposta.status_code}. Retentando...")
          continue

        if "account-verification" in resposta.url:
            print("🚨 ALERTA: Redirecionado para verificação de segurança.")
            return None

        soup = BeautifulSoup(resposta.content, 'html.parser')

        elemento_meta = soup.find("meta", itemprop="price")
        if elemento_meta:
          valor_limpo = float(elemento_meta['content'])
          return valor_limpo
        
        #Se não pegar no meta, pegamos na classe
        elemento_visual = soup.find(class_="andes-money-amount__fraction")
        if elemento_visual:
          preco_texto = elemento_visual.get_text().replace('.', '').replace(',', '.')
          return float(preco_texto)
        
        print(f"❌ Falha ao obter preço. Título: {soup.title.string if soup.title else 'Sem título'}")
        continue
          
      except Exception as e:
          print(f"Erro ao ler ML: {e}")
          await asyncio.sleep(1)
          
    print(f"💀 Falha total após {MAX_TENTATIVAS} tentativas: {url[-10:]}")
    return None
  
  async def verificar_amazon(self,session, url):
    MAX_TENTATIVAS = 3
    for tentativa in range(MAX_TENTATIVAS):
      try:
          espera = random.uniform(0.5, 2.0) + (tentativa * 1.5)
          await asyncio.sleep(espera)

          if tentativa > 0:
            print(f"🔁 Tentativa {tentativa+1} para {url[-10:]}...")

          resposta = await session.get(url, headers=self.headers, impersonate="chrome120")
          print(f"📡 Status HTTP: {resposta.status_code}")

          if resposta.status_code != 200:
            print(f"⚠️ Erro HTTP {resposta.status_code}. Retentando...")
            continue

          soup = BeautifulSoup(resposta.content, 'html.parser')

          if "api-services-support@amazon.com" in resposta.text:
                print("👮 Captcha detectado. Retentando...")
                continue

          real = soup.find(class_="a-price-whole")
          cents = soup.find(class_="a-price-fraction")
          if real and cents:
            real_texto = real.get_text().replace('.', '').replace(',', '.')
            cents_texto = cents.get_text().strip()
            texto_final = f"{real_texto}{cents_texto}"

            return float(texto_final)
          
          print(f"❌ Falha ao obter preço. Título: {soup.title.string if soup.title else 'Sem título'}")
          continue

      except Exception as e:
          print(f"Erro ao ler Amazon: {e}")
          await asyncio.sleep(1)
          
    print(f"💀 Falha total após {MAX_TENTATIVAS} tentativas: {url[-10:]}")
    return None

  async def processar_produto(self, semaforo, session, produto):
     async with semaforo:
        preco = None

        if produto['loja'] == "Amazon":
          preco = await self.verificar_amazon(session, produto['url'])
        
        if produto['loja'] == "Mercado Livre":
          preco = await self.verificar_mercadolivre(session, produto['url'])

        if preco:
          return{
            "nome": produto['nome'],
            "preco_achado": preco,
            "meta": produto['meta_preco'],
            "url": produto['url'],
            "loja": produto['loja']
          }

  def rodar(self):
    print("👀 Iniciando ronda de preços...")
    self.registrar_log("INICIANDO", "Começando a Ronda...")

    try:
      resultados = asyncio.run(self.main_async())
      for item in resultados:
         self.salvar_no_postgres(
            item['nome'], 
            item['url'], 
            item['preco_achado'], 
            item['loja']
         )

    except Exception as e:
      msg_erro = f"Erro Fatal: {str(e)}"
      print(msg_erro)
      self.registrar_log("ERRO", msg_erro)

  def registrar_log(self, status, detalhes):
    DATABASE_URL = os.getenv("DATABASE_URL")
    try:
      if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
      
      cursor = conn.cursor()
      cursor.execute("INSERT INTO logs_execucao (status, detalhes) VALUES (%s, %s)", (status, detalhes))
      conn.commit()

    except Exception as e:
      print(f"❌ Erro ao salvar no Banco: {e}")
    finally:
      if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    bot = Vigilante()
    bot.rodar()
