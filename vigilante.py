import time
from bs4 import BeautifulSoup
from notificador import enviar_telegram
import os
import psycopg2
from curl_cffi import requests as cffi_requests
from dotenv import load_dotenv

load_dotenv()

class Vigilante:
  def __init__(self):
    self.headers = None
    self.lista_produtos = [] 
    self.carregar_produtos_do_banco()

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

  def verificar_mercadolivre(self, url):
    try:
      resposta = cffi_requests.get(
                url, 
                impersonate="chrome120", 
                timeout=30
            )
      print(f"📡 Status HTTP: {resposta.status_code}")
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
      return None
        
    except Exception as e:
      print(f"Erro ao ler ML: {e}")
      return None
  
  def verificar_amazon(self,url):
     try:
        resposta = cffi_requests.get(
            url,
            impersonate="chrome120",
            timeout=30
        )
        print(f"📡 Status HTTP: {resposta.status_code}")

        soup = BeautifulSoup(resposta.content, 'html.parser')

        real = soup.find(class_="a-price-whole")
        cents = soup.find(class_="a-price-fraction")
        if real and cents:
           real_texto = real.get_text().replace('.', '').replace(',', '.')
           cents_texto = cents.get_text().strip()
           texto_final = f"{real_texto}{cents_texto}"

           return float(texto_final)
        
        print(f"❌ Falha ao obter preço. Título: {soup.title.string if soup.title else 'Sem título'}")
        return None

     except Exception as e:
        print(f"Erro ao ler Amazon: {e}")
        return None


  def rodar(self):
    print("👀 Iniciando ronda de preços...")
    self.registrar_log("INICIANDO", "Começando a Ronda...")

    try:
      contador_sucesso = 0

      for item in self.lista_produtos:
        print(f"Verificando: {item['nome']}...")
        preco = None
        # --- LOJAS ---
        if item['loja'] == "Mercado Livre":
          preco = self.verificar_mercadolivre(item['url'])
        
        if item['loja'] == "Amazon":
          preco = self.verificar_amazon(item['url'])
        # -------------
        if preco:
          self.salvar_no_postgres(item['nome'], item['url'], preco, item['loja'])
          contador_sucesso += 1

          if preco <= item['meta_preco']:
            msg = f"🚨 PROMOÇÃO DETECTADA!\nProduto: {item['nome']}\nPreço Atual: R$ {preco}\nLink: {item['url']}"
            enviar_telegram(msg)
        else:
          print("❌ Falha ao obter preço.")
        time.sleep(5)

      self.registrar_log("SUCESSO", f"Ronda finalizada. {contador_sucesso} preços coletados.")
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
