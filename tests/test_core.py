from vigilante import Vigilante

def test_limpeza_padrao_br():
    # Cenário: Preço normal (R$ 50,00)
    assert Vigilante.limpar_preco("R$ 50,00") == 50.00
    assert Vigilante.limpar_preco("50,00") == 50.00

def test_limpeza_milhar():
    # Cenário: Preço alto com ponto (1.200,50)
    assert Vigilante.limpar_preco("R$ 1.200,50") == 1200.50
    # O caso do seu debug (11.658,37)
    assert Vigilante.limpar_preco("11.658,37") == 11658.37

def test_precos_amazon_sujos():
    # Simula: "35" + "\n" + "," + "90"
    entrada_suja = "35\n,90" 
    assert Vigilante.limpar_preco(entrada_suja) == 35.90
    
    # Simula espaços extras e tabs
    entrada_tab = "  R$ 10,00 \t "
    assert Vigilante.limpar_preco(entrada_tab) == 10.00

def test_entrada_invalida():
    # Se vier lixo, devolve 0.0 (não quebra)
    assert Vigilante.limpar_preco(None) == 0.0
    assert Vigilante.limpar_preco("Preço Indisponível") == 0.0