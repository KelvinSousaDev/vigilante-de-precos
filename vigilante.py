import requests
from bs4 import BeautifulSoup
import sqlite3
from notificador import enviar_telegram

class Vigilante:
  def __init__(self):
    self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    self.lista_produtos = [
      {
        "nome": "Lego MP4/40",
       "url": "https://www.mercadolivre.com.br/lego-icons-tributo-ayrton-senna-mclaren-mp44-693-pc-10330/p/MLB34191654",
       "loja": "Mercado Livre",
       "meta_preco": 250.00
      }
    ]
  
  def salvar_no_banco(self, produto, valor, loja):
    conn = sqlite3.connect('precos.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO historico_precos(produto, valor, loja) VALUES(?, ?, ?)", (produto, valor, loja))
    conn.commit()
    conn.close()
    print(f"💾 Salvo: {produto} - R$ {valor}")

  def verificar_mercadolivre(self, url):
    try:
      resposta = requests.get(url, headers=self.headers)
      soup = BeautifulSoup(resposta.content, 'html.parser')
      
      elemento_meta = soup.find("meta", itemprop="price")
      if elemento_meta:
        valor_limpo = float(elemento_meta['content'])
        return valor_limpo
      
      #Se não pegar no meta, pegamos na classe
      elemento_visual = soup.find(class_="andes-money-amount__fraction")
      if elemento_visual:
        return float(elemento_visual.get_text().replace('.', '').replace(',', '.'))
      return None
        
    except Exception as e:
      print(f"Erro ao ler ML: {e}")
      return None
    
  def rodar(self):
    print("👀 Iniciando ronda de preços...")
    for item in self.lista_produtos:
      print(f"Verificando: {item['nome']}...")

      preco = None
      if item['loja'] == "Mercado Livre":
        preco = self.verificar_mercadolivre(item['url'])
      if preco:
        self.salvar_no_banco(item['nome'], preco, item['loja'])

        if preco <= item['meta_preco']:
          msg = f"🚨 PROMOÇÃO DETECTADA!\nProduto: {item['nome']}\nPreço Atual: R$ {preco}\nLink: {item['url']}"
          enviar_telegram(msg)
      else:
        print("❌ Falha ao obter preço.")

if __name__ == "__main__":
    bot = Vigilante()
    bot.rodar()
