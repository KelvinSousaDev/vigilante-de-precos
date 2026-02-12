import asyncio
from extract.amazon_scraper import coletar_amazon
from extract.ml_scraper import coletar_ml
from transform.parsers import limpar_preco
from load.postgres import conectar_banco, carregar_produtos, desconectar_banco, salvar_no_banco
from playwright.async_api import async_playwright

async def main():
  await conectar_banco()
  try:
    print("🦇 Vigilante iniciado...")
    
    produtos = await carregar_produtos()
    semaforo = asyncio.Semaphore(3)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )

        tarefas = []
        for produto in produtos:
            nome = produto['nome']
            url = produto['url']
            tarefas.append(processar_produto(semaforo, context, nome, url))
        
        await asyncio.gather(*tarefas)
  except Exception as e:
        print(f"❌ Erro fatal no main: {e}")
  finally:
    await desconectar_banco()
    print("🦇 Vigilante encerrado.")

async def processar_produto(semaforo, context, nome, url):
   preco_sujo = None
   loja_detectada = "Desconhecida"

   if "amazon" in url or "amzn" in url or "a.co" in url:
        loja_detectada = "Amazon"
        preco_sujo = await coletar_amazon(semaforo, context, nome, url)
   elif "mercadolivre" in url:
        loja_detectada = "Mercado Livre"
        preco_sujo = await coletar_ml(semaforo, context, nome, url)
   
   if preco_sujo:
      preco_limpo = limpar_preco(preco_sujo)
      print(f"💰 {nome}: {preco_limpo}")

      await salvar_no_banco(nome, url, preco_limpo, loja_detectada)
      
   else:
      print(f"⚠️ Falha ao extrair preço de: {nome} (URL: {url})")


if __name__ == "__main__":
    asyncio.run(main())