def create_msg(nome, url, preco_limpo, loja_detectada, meta):
  msg =(f"""
  # 💸 **OFERTA ENCONTRADA!** 💸

  ### 📦 **{nome}**

  * 🔥 **Preço Atual:** `R$ {preco_limpo}`
  * 🎯 **Sua Meta era:** ~~R$ {meta}~~
  * 🏪 **Loja:** {loja_detectada}

  ---
  
  🚀 **ESTÁ ABAIXO DA SUA META!**
  👉 [**CLIQUE AQUI PARA COMPRAR**]({url})
  """)
  return msg
