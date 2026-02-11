import asyncio
from extract.amazon_scraper import coletar_amazon
from transform.parsers import limpar_preco
from load.postgres import carregar_produtos_do_banco
from playwright.async_api import async_playwright

async def main():
  print("🦇 Vigilante 4.0 Iniciando Ronda...")

  produtos = carregar_produtos_do_banco()
  semaforo = asyncio.Semaphore(3)

  async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
      context = await browser.new_context(
          user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
      )

      tarefas = []
      for nome, url in produtos:
          tarefas.append(processar_produto(semaforo, context, nome, url))
      
      await asyncio.gather(*tarefas)

async def processar_produto(semaforo, context, nome, url):
   preco_sujo = await coletar_amazon(semaforo, context, nome, url)
   if preco_sujo:
      preco_limpo = limpar_preco(preco_sujo)
      print(f"💰 {nome}: {preco_limpo}")

      # await salvar_no_banco(nome, preco_limpo)

if __name__ == "__main__":
    asyncio.run(main())