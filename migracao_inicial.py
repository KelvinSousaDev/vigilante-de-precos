import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

PRODUTOS_LEGADO = [
    {
        "nome": "Lego MP4/40",
        "url": "https://www.mercadolivre.com.br/lego-icons-tributo-ayrton-senna-mclaren-mp44-693-pc-10330/p/MLB34191654",
        "loja": "Mercado Livre",
        "meta_preco": 250.00
    },
    {
        "nome": "Café Baggio",
        "url": "https://www.mercadolivre.com.br/cafe-gourmet-torradomoido-100-arabica-aromas-baggio-250gr-aroma-chocolate-com-avel/p/MLB19558358",
        "loja": "Mercado Livre",
        "meta_preco": 30.00
    },
    {
        "nome": "Notebook ASUS TUF - RTX 3050",
        "url": "https://www.mercadolivre.com.br/notebook-gamer-asus-tuf-gaming-a15-amd-ryzen-7-7435hs-31-ghz-rtx3050-16gb-ram-512gb-ssd-windows-11-home-tela-156-144hz-ips-fhd-graphite-black-fa506ncr-hn088w/p/MLB45998098",
        "loja": "Mercado Livre",
        "meta_preco": 4500.00
    },
    {
        "nome": "Café Baggio",
        "url": "https://a.co/d/3TkFdEo",
        "loja": "Amazon",
        "meta_preco": 30.00
    }
]

def migrar():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
         conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")
    else:
         conn = psycopg2.connect(db_url)
         
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("🦇 Iniciando Migração Tática...")

    try:
        print("🔨 Atualizando tabela dim_produtos...")
        cursor.execute("ALTER TABLE dim_produtos ADD COLUMN IF NOT EXISTS meta_preco NUMERIC(10, 2);")
        print("✅ Coluna 'meta_preco' verificada/criada.")
    except Exception as e:
        print(f"⚠️ Aviso no Schema: {e}")

    print("🌱 Semeando produtos iniciais...")
    novos = 0
    for p in PRODUTOS_LEGADO:
        try:
            cursor.execute("SELECT id FROM dim_produtos WHERE url_produto = %s", (p['url'],))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute("""
                    INSERT INTO dim_produtos (nome_produto, url_produto, loja, meta_preco)
                    VALUES (%s, %s, %s, %s)
                """, (p['nome'], p['url'], p['loja'], p['meta_preco']))
                novos += 1
            else:
                cursor.execute("""
                    UPDATE dim_produtos SET meta_preco = %s WHERE url_produto = %s
                """, (p['meta_preco'], p['url']))
                
        except Exception as e:
            print(f"❌ Erro ao inserir {p['nome']}: {e}")

    print(f"🦇 Migração Concluída! {novos} novos produtos cadastrados.")
    conn.close()

if __name__ == "__main__":
    migrar()