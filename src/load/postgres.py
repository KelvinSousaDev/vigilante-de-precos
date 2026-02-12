from dotenv import load_dotenv
import asyncpg
import os

load_dotenv()

pool_conexao = None

async def conectar_banco():
    """Inicia a Pool Global"""
    global pool_conexao
    print("🔌 Iniciando Pool de Conexões...")
    DATABASE_URL = os.getenv("DATABASE_URL")
    pool_conexao = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    print("✅ Pool Conectado.")

async def desconectar_banco():
    """Encerra a Pool"""
    global pool_conexao
    if pool_conexao:
        await pool_conexao.close()
        print("🔒 Pool Encerrado.")

async def carregar_produtos():
    """
    Usa a função de pool Global para buscar os produtos no banco
    """
    global pool_conexao
    if not pool_conexao:
        raise Exception("❌ O Pool não foi iniciado! Chame conectar_banco() primeiro.")
    try:
        async with pool_conexao.acquire() as conn:
            query = "SELECT nome_produto, url_produto, loja, meta_preco FROM dim_produtos"
            produtos_retornados = await conn.fetch(query)
            lista_produtos = []

            for item in produtos_retornados:
                novo_produto = {
                    "nome": item['nome_produto'],       
                    "url": item['url_produto'],        
                    "loja": item['loja'],       
                    "meta_preco": float(item['meta_preco']) if item['meta_preco'] else 0.0
                    }
                lista_produtos.append(novo_produto)

            print(f"🦇 Configuração atualizada: {len(lista_produtos)} alvos carregados.")
            return lista_produtos

    except Exception as e:
        print(f"❌ Erro ao carregar produtos do banco: {e}")
        return []

async def salvar_no_banco(nome, url, preco, loja):
    """
    Persiste os dados coletados no Data Warehouse, garantindo integridade referencial.

    Responsabilidades:
    1. Gerencia a conexão transacional (Commit/Rollback) com o NeonDB.
    2. Implementa lógica de 'Idempotência': Verifica se o produto já existe na dimensão (`dim_produtos`) antes de criar.
    3. Registra o novo ponto de dados na tabela de fatos (`fato_precos`) vinculada ao ID único do produto.
    """
    global pool_conexao
    if not pool_conexao:
        raise Exception("❌ O Pool não foi iniciado! Chame conectar_banco() primeiro.")
    
    try:
        async with pool_conexao.acquire() as conn:
            async with conn.transaction():
                query_check = "SELECT id FROM dim_produtos WHERE url_produto = $1"
                produto_id = await conn.fetchval(query_check, url)

                if not produto_id:
                        print(f"🆕 Produto Novo detectado: {nome} ({loja})")
                        query_insert_prod = """
                        INSERT INTO dim_produtos (nome_produto, url_produto, loja) 
                        VALUES ($1, $2, $3) 
                        RETURNING id
                        """
                        produto_id = await conn.fetchval(query_insert_prod, nome, url, loja)

                query_insert_price = """
                    INSERT INTO fato_precos (produto_id, valor_coletado) 
                    VALUES ($1, $2)
                    """
                await conn.execute(query_insert_price, produto_id, preco)

                print(f"💾 Preço de R$ {preco} salvo no PostgreSQL para o ID {produto_id}")

    except Exception as e:
        print(f"❌ Erro ao salvar no Banco: {e}")


# Bloco de teste Seguro
if __name__ == "__main__":
    import asyncio
    
    async def teste_rapido():
        await conectar_banco()
        items = await carregar_produtos()
        print(items)
        await desconectar_banco() 
        
    asyncio.run(teste_rapido())
    