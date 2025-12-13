import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Vigilante Dashboard", page_icon=":eagle:", layout="centered")
st.title("Vigilante de Preços")

URL_API = "https://vigilante-api.onrender.com/historico"

@st.cache_data
def carregar_dados():
  response = requests.get(URL_API)
  return response.json()

dados = carregar_dados()

if dados:
  df = pd.DataFrame(dados)

  df['data_hora'] = pd.to_datetime(df['data_hora'])
  df['valor'] = pd.to_numeric(df['valor'])

  col1, col2, col3 = st.columns(3)

  atual = df['valor'].iloc[-1]
  minimo = df['valor'].min()
  media = df['valor'].mean()

  variacao = 0

  if df['valor'].count() >= 2:
    anterior = df['valor'].iloc[-2]
    variacao = atual - anterior

  col1.metric("Preço Atual", f"R$ {atual:.2f}", delta=f"{variacao:.2f}", delta_color="inverse")
  col2.metric("Preço Minimo", f"R$ {minimo:.2f}")
  col3.metric("Preço Médio", f"R$ {media:.2f}")

  st.subheader("Evolução do Preço")
  st.line_chart(df, x="data_hora", y="valor")

  with st.expander("Ver Dados Brutos"):
        st.dataframe(df.sort_values(by="data_hora", ascending=False))

else:
    st.error("Erro: Não foi possível carregar os dados da API.")