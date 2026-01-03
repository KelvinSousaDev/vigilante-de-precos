import psycopg2
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

def migrar_banco_fase3():
  DATABASE_URL = os.getenv("DATABASE_URL")

  if not DATABASE_URL:
      print("❌ Erro: Cadê a DATABASE_URL no .env?")
      return
  
  try:
     conn = psycopg2.connect(DATABASE_URL)
     conn.autocommit = True
     cursor = conn.cursor()
     print("🦇 Conectado! Iniciando a Reforma...")

    # Criar a Tabela dos Usuários

     print("🔨 Criando tabela 'usuarios'...")
     cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome VARCHAR(100),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
     
     # Definir o Primeiro Usuário (ADMIN)

     print("👤 Configuração do Admin")
     senha_plana = input("Digite a senha que deseja para o Admin: ")

     # Caso o usuário clique acidentalmente no enter, antes de digitar a senha
     if not senha_plana:
        print("⚠️ Senha vazia! Usando 'admin123' como fallback temporário.")
        senha_plana = "admin123"

     # Testando o bcrypt para a criptrografia de senhas

     salt = bcrypt.gensalt()
     senha_hash = bcrypt.hashpw(senha_plana.encode('utf-8'), salt).decode('utf-8')

     print(f"🔄 Gerando hash seguro e salvando no banco...")

     # Inserir o Usuário registrado no banco (Se o usuário já existir, ignora)

     cursor.execute("""
        INSERT INTO usuarios (email, senha_hash, nome)
        VALUES ('admin@vigilante.com', %s, 'Admin Supremo')
        ON CONFLICT (email) DO NOTHING;
    """, (senha_hash,))
     
     cursor.execute("SELECT id FROM usuarios WHERE email = 'admin@vigilante.com'")
     admin_id = cursor.fetchone()[0]
     print(f"✅ Admin identificado com ID: {admin_id}")

     # Modificar a Tabela de Produtos para acrescentar um Dono a Eles

     print("🔗 Adicionando coluna 'usuario_id' em 'dim_produtos'...")
     cursor.execute("""
        ALTER TABLE dim_produtos 
        ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);
    """)
     
     # O Admin vai adotar todos os produtos ja existentes nessa altura

     print(f"Adotando produtos antigos para o Admin (ID {admin_id})...")
     cursor.execute("""
        UPDATE dim_produtos 
        SET usuario_id = %s 
        WHERE usuario_id IS NULL;
    """, (admin_id,))
     
     print("✅ Reforma Concluída! O Sistema agora é Multi-Tenant.")

  except Exception as e:
     print(f"Deu ruim: {e}")
  finally:
     if 'conn' in locals(): conn.close()

if __name__ == "__main__":
   migrar_banco_fase3()
