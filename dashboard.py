import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
from datetime import time

load_dotenv()

st.set_page_config(page_title="Vigilante Dashboard", page_icon=":eagle:", layout="wide")

def get_connection():
     DATABASE_URL = os.getenv("DATABASE_URL")
     if DATABASE_URL:
       return psycopg2.connect(DATABASE_URL)
     else:
       return psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")


def carregar_dados():
  conn = get_connection()
  querry = """
  SELECT 
      dim.nome_produto,
      dim.loja,
      fato.valor_coletado,
      fato.data_coleta
  FROM 
      fato_precos fato
  JOIN 
      dim_produtos dim ON fato.produto_id = dim.id
  ORDER BY
      fato.data_coleta DESC
    """

  df = pd.read_sql_query(querry, conn)
  conn.close()
  return df

def carregar_produtos_cadastrados():
    try:
      conn = get_connection()
      query = "SELECT id, nome_produto, loja, meta_preco, url_produto FROM dim_produtos ORDER BY id ASC"
      df = pd.read_sql_query(query, conn)
      conn.close()
      return df
    except Exception as e:
      st.error(f"Erro ao carregar lista de produtos: {e}")
      return pd.DataFrame()
    
def adicionar_produto(nome, url, loja, meta):
    try:
      conn = get_connection()
      cursor = conn.cursor()

      query = """
          INSERT INTO dim_produtos(nome_produto, url_produto, loja, meta_preco)
          VALUES (%s, %s, %s, %s)
      """
      cursor.execute(query, (nome, url, loja, meta))
      conn.commit()
      conn.close
      return True
    except Exception as e:
      st.error(f"Erro ao Adicionar: {e}")
      return False

def deletar_produto(produto_id):
    try:
      conn = get_connection
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
tab1, tab2 = st.tabs(["📊 Dashboard", "⚙️ Gerenciar"])

with tab1:
  df = carregar_dados()

  if not df.empty:
    st.markdown("### 📈 Status do Sistema")
    col1, col2 = st.columns(2)
    col1.metric("Total de Coletas", len(df))
    col2.metric("Produtos Monitorados", len(df['nome_produto'].unique()))

    st.divider()
    st.markdown("### 🔍 Análise Detalhada")

    produtos = df["nome_produto"].unique()
    produto_selecionado = st.selectbox("Selecione o Produto: ", produtos)
    df_filtrado = df[df["nome_produto"] == produto_selecionado]

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
with tab2:
   st.header("Cadastrar Novo Alvo")

   with st.form("form_cadastro"):
      col_a, col_b = st.columns(2)
      novo_nome = col_a.text_input("Nome do Produto")
      nova_loja = col_b.selectbox("Loja", ["Amazon", "Mercado Livre"])
      nova_url = st.text_input("URL do Produto")
      novo_meta = st.number_input("Preço Alvo (R$)", min_value=0.0, format="%.2f")

      if st.form_submit_button("💾 Salvar"):
         if adicionar_produto(novo_nome, nova_url, nova_loja, novo_meta):
            st.sucess("Produto Salvo!")
            time.sleep(1)
            st.rerun
            
   st.divider()
   st.subheader("🗑️ Remover Produtos")

   df_produtos = carregar_produtos_cadastrados()
   if not df_produtos.empty:
      opcoes = df_produtos.apply(lambda x: f"{x['id']} - {x['nome_produto']} - {x['loja']}", axis=1)
      escolha = st.selectbox("Selecione para remover:", opcoes)

      if st.button("❌ Remover"):
         id_para_deletar = int(escolha.split(" - ")[0])
         if deletar_produto(id_para_deletar):
            st.success("Removido com Sucesso.")
            time.sleep(1)
            st.rerun()
