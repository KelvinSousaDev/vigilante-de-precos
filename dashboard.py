import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
import time
import bcrypt

load_dotenv()

st.set_page_config(page_title="Vigilante Dashboard", page_icon=":eagle:", layout="wide")

def get_connection():
     DATABASE_URL = os.getenv("DATABASE_URL")
     if DATABASE_URL:
       return psycopg2.connect(DATABASE_URL)
     else:
       return psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")

def validar_usuario(email, senha):
   conn = get_connection()
   if not conn:
      return None
   
   try:
    cursor = conn.cursor()

    query = "SELECT id, nome, senha_hash FROM usuarios WHERE email = %s"

    cursor.execute(query, (email,))
    resultado = cursor.fetchone()
    if resultado is None:
          return None
    
    user_id, nome_banco, senha_hash_banco = resultado

    if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_banco.encode('utf-8')):
       return (user_id, nome_banco)
    else:
       return None
       
   except Exception as e:
      st.error(f"Erro na validação: {e}")
   finally:
      conn.close()

def carregar_dados(usuario_id=None):
  conn = get_connection()
  if not conn:
     return pd.DataFrame()
  
  if not usuario_id:
    conn.close()
    return pd.DataFrame()
  
  query = """
      SELECT
        p.id, 
        p.nome_produto, 
        p.loja, 
        p.url_produto, 
        p.meta_preco,
        f.valor_coletado, 
        f.data_coleta
      FROM dim_produtos p
      JOIN fato_precos f ON p.id = f.produto_id
      WHERE p.usuario_id = %s
      ORDER BY f.data_coleta DESC
    """
  try:
    df = pd.read_sql_query(query, conn, params=(usuario_id,))
  except Exception as e:
    st.error(f"Erro no SQL: {e}")
    df = pd.DataFrame()
  finally:
        conn.close()
  return df

def carregar_produtos_cadastrados(usuario_id):
    try:
      conn = get_connection()
      query = "SELECT id, nome_produto, loja, meta_preco, url_produto FROM dim_produtos WHERE usuario_id = %s ORDER BY id ASC"
      df = pd.read_sql_query(query, conn, params=(usuario_id,))
      conn.close()
      return df
    except Exception as e:
      st.error(f"Erro ao carregar lista de produtos: {e}")
      return pd.DataFrame()
    
def verificar_saude_agente():
   conn = get_connection()
   if not conn:
      return None, None
   
   try:
      query = "SELECT data_hora, status FROM logs_execucao ORDER BY id DESC LIMIT 1"
      df = pd.read_sql_query(query, conn)

      if not df.empty:
         return df.iloc[0]['data_hora'], df.iloc[0]['status']
   except Exception as e:
      return None, None
   
   finally:
        conn.close()

   return None, None

def adicionar_produto(nome, url, loja, meta, usuario_id):
    conn = get_connection()
    if not conn:
        return False
      
    try:
      cursor = conn.cursor()

      cursor.execute("SELECT COUNT(*) FROM dim_produtos WHERE usuario_id = %s", (usuario_id,))
      qtd_atual = cursor.fetchone()[0]
      if qtd_atual >= 5:
         st.error("🚫 Limite de segurança atingido! No Modo Demo, o limite é de 5 produtos por usuário.")
         return False

      query = """
          INSERT INTO dim_produtos(nome_produto, url_produto, loja, meta_preco, usuario_id)
          VALUES (%s, %s, %s, %s, %s)
      """
      cursor.execute(query, (nome, url, loja, meta, usuario_id))
      conn.commit()
      st.success(f"Produto '{nome}' monitorado com sucesso!")
      return True
    
    except Exception as e:
      st.error(f"Erro ao Adicionar: {e}")
      return False
    finally:
       conn.close()

def deletar_produto(produto_id):
    try:
      conn = get_connection()
      cursor = conn.cursor()

      query_limpeza = "DELETE FROM fato_precos WHERE produto_id = %s"
      cursor.execute(query_limpeza, (produto_id,))

      query_final = "DELETE FROM dim_produtos WHERE ID = %s"
      cursor.execute(query_final, (produto_id,))

      conn.commit()
      conn.close()
      return True
    except Exception as e:
      st.error(f"Erro Ao Deletar: {e}")
      return False


st.title("🦇 Vigilante de Preços v2.0")

# Sistema de login usando session_state (Se o usuario não iniciou sessão ainda, aparece a tela de login, e bloqueia as informações)

if 'usuario_id' not in st.session_state:
  st.info("🔒 Acesso restrito. Identifique-se.")
  col_login, col_vazia = st.columns([1, 2])

  with col_login:
     with st.form("form_login_global"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Acessar Sistema")

        if btn_entrar:
           resultado = validar_usuario(email, senha)
           if resultado:
              user_id, user_nome = resultado
              st.session_state['usuario_id'] = user_id
              st.session_state['usuario_nome'] = user_nome
              st.success(f"Bem-vindo, {user_nome}!")
              time.sleep(1)
              st.rerun()
           else:
              st.error("Credenciais inválidas! 🦇")

     st.divider()
     st.subheader("Apenas visitando?")
     if st.button("🚀 Modo Visitante", use_container_width=True):
        conn = get_connection()
        if conn:
          try:
            cursor = conn.cursor()

            query = "SELECT id, nome FROM usuarios WHERE email = %s"
            cursor.execute(query, ('demo@vigilante.com',))

            resultado = cursor.fetchone()
            if resultado is not None:
              user_id, user_nome = resultado
              st.session_state['usuario_id'] = user_id
              st.session_state['usuario_nome'] = user_nome
              st.success(f"Entrando como {user_nome}...")
              time.sleep(1)
              st.rerun()
            else:
               st.error("Erro: Usuário Visitante não encontrado no banco.")
          except Exception as e:
            st.error(f"Erro na conexão: {e}")
          finally:
            conn.close()

  st.stop()

with st.sidebar:
  st.image("https://img.icons8.com/color/96/batman-new.png", width=50)
  st.markdown(f"Olá, **{st.session_state['usuario_nome']}**")

  if st.button("Sair (Logout)", type="primary", use_container_width=True):
     del st.session_state['usuario_id']
     st.rerun()

  st.divider()
  st.caption("Sistema Vigilante v2.0")

tab1, tab2 = st.tabs(["📊 Dashboard", "⚙️ Gerenciar"])

# Tela Principal de Métricas ------------------------------------------------------

with tab1:
   ultima_data, ultimo_status = verificar_saude_agente()
   if ultima_data:
      agora = pd.Timestamp.utcnow().tz_localize(None)
      diff = agora - pd.to_datetime(ultima_data)
      horas_atras = diff.total_seconds() / 3600

      status_container = st.container()

      if horas_atras < 6 and ultimo_status == "SUCESSO":
        status_container.success(f"🟢 Agente Local: Online (Última ronda há {horas_atras:.1f}h)")
      elif horas_atras > 24:
        status_container.error(f"🔴 Agente Local: OFFLINE (Sem sinal há {horas_atras:.1f}h). Verifique seu computador!")
      elif ultimo_status == 'ERRO':
        status_container.error(f"⚠️ Agente Local: Erro na última execução ({horas_atras:.1f}h atrás). Verifique os logs.")
      else:
        status_container.warning(f"🟡 Agente Local: Ocioso ({horas_atras:.1f}h atrás)")

   else:
    st.info("⚪ Agente Local: Nenhum registro de atividade ainda.")
  
  
   df = carregar_dados(st.session_state['usuario_id'])

   if not df.empty:
    st.markdown("### 📈 Status do Sistema")
    col1, col2 = st.columns(2)
    col1.metric("Total de Coletas", len(df))
    col2.metric("Produtos Monitorados", len(df['nome_produto'].unique()))

    st.divider()
    st.markdown("### 🔍 Análise Detalhada")

    df['item_identificador'] = df["nome_produto"] + " - " + df['loja']
    produtos_unicos = df["item_identificador"].unique()
    produto_selecionado = st.selectbox("Selecione o Produto: ", produtos_unicos)
    df_filtrado = df[df["item_identificador"] == produto_selecionado]

    preco_atual = df_filtrado['valor_coletado'].iloc[0]
    menor_preco_historico = df_filtrado['valor_coletado'].min()
    media_preco = df_filtrado['valor_coletado'].mean()
    delta_media = preco_atual - media_preco
    data_atual = pd.to_datetime(df_filtrado['data_coleta'].iloc[0]).strftime('%d/%m %H:%M')

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric(
      label="Preço Atual",
      value=f"R$ {preco_atual:.2f}",
      delta=f"{delta_media:.2f}",
      delta_color="inverse"
      )

    kpi2.metric(
      label="Menor Preço Histórico",
      value=f"R$ {menor_preco_historico:.2f}"
      )

    kpi3.metric(
      label="Média de Preço",
      value=f"R$ {media_preco:.2f}"
      )

    kpi4.metric(
      label="Última Atualização",
      value=data_atual
      )

    st.line_chart(df_filtrado, x="data_coleta", y="valor_coletado")

    with st.expander(f"Ver dados brutos de {produto_selecionado}"):
            st.dataframe(df_filtrado)
   else:
    st.warning("Banco de dados vazio ou sem conexão.")

# Tela de Gestão do usuário ------------------------------------------------------

with tab2:
   st.header("⚙️ Gerenciar Produtos")

   st.divider()
   st.subheader("➕ Adicionar Produtos")

   with st.form("form_cadastro"):
      col_a, col_b = st.columns(2)
      novo_nome = col_a.text_input("Nome do Produto")
      nova_loja = col_b.selectbox("Loja", ["Amazon", "Mercado Livre"])
      nova_url = st.text_input("URL do Produto")
      novo_meta = st.number_input("Preço Alvo (R$)", min_value=0.0, format="%.2f")

      if st.form_submit_button("💾 Salvar"):
         if adicionar_produto(novo_nome, nova_url, nova_loja, novo_meta, st.session_state['usuario_id']):
            st.success("Produto Salvo!")
            time.sleep(1)
            st.rerun()

   st.divider()
   st.subheader("🗑️ Remover Produtos")

   df_produtos = carregar_produtos_cadastrados(st.session_state['usuario_id'])
   if not df_produtos.empty:
      opcoes = df_produtos.apply(lambda x: f"{x['id']} - {x['nome_produto']} - {x['loja']}", axis=1)
      escolha = st.selectbox("Selecione para remover:", opcoes)

      if st.button("❌ Remover"):
         id_para_deletar = int(escolha.split(" - ")[0])
         if deletar_produto(id_para_deletar):
            st.success("Removido com Sucesso.")
            time.sleep(1)
            st.rerun()
