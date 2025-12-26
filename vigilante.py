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
    self.lista_produtos = [
      {
      "nome": "Lego MP4/40",
      "url": "https://www.mercadolivre.com.br/lego-icons-tributo-ayrton-senna-mclaren-mp44-693-pc-10330/p/MLB34191654",
      "loja": "Mercado Livre",
      "meta_preco": 250.00
      },
      {
      "nome": "Café Baggio",
      "url": "https://www.mercadolivre.com.br/cafe-gourmet-torradomoido-100-arabica-aromas-baggio-250gr-aroma-chocolate-com-avel/p/MLB19558358",
      "loja": "Mercado Livre",
      "meta_preco": 30.00
      },
      {
      "nome": "Notebook ASUS TUF - RTX 3050",
      "url": "https://www.mercadolivre.com.br/notebook-gamer-asus-tuf-gaming-a15-amd-ryzen-7-7435hs-31-ghz-rtx3050-16gb-ram-512gb-ssd-windows-11-home-tela-156-144hz-ips-fhd-graphite-black-fa506ncr-hn088w/p/MLB45998098",
      "loja": "Mercado Livre",
      "meta_preco": 4500.00
      },
      {
      "nome": "Café Baggio",
      "url": "https://a.co/d/3TkFdEo",
      "loja": "Amazon",
      "meta_preco": 30.00
      }
    ]

  def salvar_no_postgres(self, nome, url, preco):
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
              print(f"🆕 Produto Novo detectado: {nome}")
              cursor.execute(
                  "INSERT INTO dim_produtos (nome_produto, url_produto) VALUES (%s, %s) RETURNING id",
                  (nome, url)
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
        self.salvar_no_postgres(item['nome'], item['url'], preco)

        if preco <= item['meta_preco']:
          msg = f"🚨 PROMOÇÃO DETECTADA!\nProduto: {item['nome']}\nPreço Atual: R$ {preco}\nLink: {item['url']}"
          enviar_telegram(msg)
      else:
        print("❌ Falha ao obter preço.")
      print("Aguardando...")
      time.sleep(5)

if __name__ == "__main__":
    bot = Vigilante()
    bot.rodar()
