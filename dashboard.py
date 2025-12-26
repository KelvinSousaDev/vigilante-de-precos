import streamlit as st
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Vigilante Dashboard", page_icon=":eagle:", layout="wide")
st.title("Vigilante de Preços")

@st.cache_data
def carregar_dados_do_banco():
  DATABASE_URL = os.getenv("DATABASE_URL")
  try:
    if DATABASE_URL:
      conn = psycopg2.connect(DATABASE_URL)
    else:
      conn = psycopg2.connect(
                host="localhost", 
                user="postgres", 
                password="admin", 
                database="postgres"
            )

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
  except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return pd.DataFrame()

st.title("🦇 Monitor de Preços (PostgreSQL Real-Time)")
df = carregar_dados_do_banco()

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