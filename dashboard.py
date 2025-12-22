import requests
import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Vigilante Dashboard", page_icon=":eagle:", layout="wide")
st.title("Vigilante de Preços")

@st.cache_data
def carregar_dados_do_banco():
  try:
    conn = psycopg2.connect(
      host="localhost",
      user="postgres",
      password="admin",
      database="postgres"
    )

    querry = """
    SELECT 
        dim.nome_produto,
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
  except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return pd.DataFrame()

st.title("🦇 Monitor de Preços (PostgreSQL Real-Time)")
df = carregar_dados_do_banco()

if not df.empty:
  col1, col2, col3 = st.columns(3)
  col1.metric("Total de Coletas", len(df))
  col2.metric("Produto Mais Recente", df['nome_produto'].iloc[0])
  col3.metric("Último Preço", f"R$ {df['valor_coletado'].iloc[0]:.2f}")

  st.subheader("Evolução dos Preços")

  produtos = df["nome_produto"].unique()
  produto_selecionado = st.selectbox("Selecione o Produto: ", produtos)

  df_filtrado = df[df["nome_produto"] == produto_selecionado]

  st.line_chart(df_filtrado, x="data_coleta", y="valor_coletado")

  st.divider()
  st.subheader("Dados Brutos")

  st.dataframe(df)
else:
    st.warning("Banco de dados vazio ou sem conexão.")