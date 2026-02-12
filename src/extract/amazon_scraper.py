import asyncio

async def coletar_amazon(semaforo, context, nome, url):
    print(f"🔄 Iniciando acesso ao: {nome}")

    async with semaforo: 
      print(f"🚦 Sinal verde para: {nome}")
      page = await context.new_page()
      
      try:
          await page.goto(url, wait_until="domcontentloaded")
          
          print(f"✅ Sucesso em {nome}")

          real = await page.inner_text(".a-price-whole")
          cents = await page.inner_text(".a-price-fraction")

          if real and cents:
              if real.endswith(','):
                real = real[:-1]
              valor_montado = f"{real},{cents}"
              return valor_montado
          
      except Exception as e:
          print(f"❌ Erro em {nome}: {e}")
      finally:
          await page.close()

