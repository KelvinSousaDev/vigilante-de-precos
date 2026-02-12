import asyncio

async def coletar_ml(semaforo, context, nome, url):
    print(f"🔄 Iniciando acesso ao: {nome}")

    async with semaforo: 
      print(f"🚦 Sinal verde para: {nome}")
      page = await context.new_page()
      
      try:
        await page.goto(url, wait_until="domcontentloaded")
          
        print(f"✅ Sucesso em {nome}")
        meta_tag = page.locator('meta[itemprop="price"]')
        if await meta_tag.count() > 0:
            valor = await meta_tag.get_attribute('content')
            return valor
        
        container_preco = page.locator(".ui-pdp-price__second-line .andes-money-amount").first
        if await container_preco.count() > 0:
            real = await container_preco.locator(".andes-money-amount__fraction").inner_text()
            cents_locator = container_preco.locator(".andes-money-amount__cents")
            cents = "00"
            if await cents_locator.count() > 0:
                cents = await cents_locator.inner_text()

            valor_montado = f"{real},{cents}"
            return valor_montado
        
        print(f"❌ Não foi possível extrair preço de {nome}")
        return None
          
      except Exception as e:
          print(f"❌ Erro em {nome}: {e}")
      finally:
          await page.close()

