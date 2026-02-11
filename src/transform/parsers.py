def limpar_preco(texto_bruto):
    """
    Recebe o texto sujo do HTML (ex: 'R$ 1.200,50\\n') e converte para float (1200.50).
    
    Remove quebras de linha, R$ e converte pontuação do padrão BRL para Python.
    Retorna 0.0 se houver erro de conversão.
    """
    if not texto_bruto:
      return 0.0
    
    texto = texto_bruto.replace("R$", "").strip()
    # Remove caracteres invisíveis que a Amazon costuma mandar
    texto = texto.replace("\n", "").replace("\r", "").replace("\t", "")
    texto = texto.replace(".", "")
    texto = texto.replace(",", ".")

    try:
      return float(texto)
    except ValueError:
      return 0.0
