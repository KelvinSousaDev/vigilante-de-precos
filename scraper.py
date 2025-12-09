import requests
from bs4 import BeautifulSoup

#Agente de Usuário
headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
  "Referer": "https://www.google.com/"
  }

def buscar_amazon(url):
  resposta = requests.get(url, headers=headers)

  if resposta.status_code == 200:
    soup = BeautifulSoup(resposta.content, 'html.parser')

    titulo = soup.find('h1', class_='ui-pdp-title')
    print(f"📦 Produto: {titulo.get_text()}")

    elemento = soup.select_one("div.ui-pdp-price__second-line span.andes-money-amount__fraction")
    if elemento:
      valor_texto = elemento.get_text()
      print(f"Encontrei bruto: {valor_texto}")

      valor_limpo = valor_texto.replace("R$", "").replace(" ", "")
      return float(valor_limpo)
    else:
      return "Preço não encontrado (Classe mudou?)"

  else:
     print(f"Erro na conexão: {resposta.status_code}")

print(buscar_amazon('https://www.mercadolivre.com.br/lego-icons-tributo-ayrton-senna-mclaren-mp44-693-pc-10330/p/MLB34191654?pdp_filters=item_id%3AMLB4006241653#origin%3Dshare%26sid%3Dshare%26wid%3DMLB4006241653'))