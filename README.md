# 🦅 Vigilante de Preços

> Um robô de monitoramento de preços (ETL & Web Scraping) integrado com Telegram e API.

O **Vigilante de Preços** é uma solução de Engenharia de Dados desenvolvida para monitorar oscilações de valores em grandes e-commerces (como Mercado Livre). O sistema coleta os dados automaticamente, armazena o histórico em banco de dados e notifica o usuário via Telegram quando o preço atinge o alvo desejado.

Além disso, o projeto conta com uma **API REST (FastAPI)** para expor os dados coletados para outras aplicações ou dashboards.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+** (Linguagem Principal)
- **BeautifulSoup4** (Web Scraping e Extração de HTML)
- **SQLite** (Banco de Dados Relacional para persistência)
- **FastAPI** (Criação da API para consumo de dados)
- **Requests** (Comunicação HTTP)
- **Telegram API** (Sistema de Notificação em Tempo Real)

---

## ⚙️ Funcionalidades

- [x] **Coleta Automática:** Acessa a página do produto e extrai o preço atual "escondido" no HTML.
- [x] **Tratamento de Dados:** Limpa formatações (R$, pontos, vírgulas) convertendo para _float_.
- [x] **Persistência:** Salva cada coleta com _Timestamp_ no banco de dados SQLite (`precos.db`).
- [x] **Alertas:** Envia mensagem no Telegram caso o preço esteja abaixo do valor estipulado.
- [x] **API de Consulta:** Disponibiliza o histórico de preços em formato JSON via endpoint HTTP.

---

## 🚀 Como Rodar o Projeto

### 1. Pré-requisitos

Certifique-se de ter o Python instalado. Clone o repositório e instale as dependências:

```bash
# Clone o repositório
git clone [https://github.com/KelvinSousaDev/vigilante-de-precos]

# Instale as bibliotecas necessárias
pip install requests beautifulsoup4 fastapi uvicorn
```

### 2. Configurando o Alvo

No arquivo vigilante.py (ou main.py), configure a URL do produto que deseja monitorar e o seu Token do Telegram.

### 3. Executando o Robô (Coleta)

Para rodar a extração de dados e verificar o preço atual:

```bash
python vigilante.py
```

Isso irá criar o banco de dados precos.db automaticamente se não existir.

### 4. Rodando a API (Servidor)

Para visualizar os dados coletados no navegador:

```bash
uvicorn api:app --reload
```

Acesse a Documentação: http://127.0.0.1:8000/docs

Veja o Histórico: http://127.0.0.1:8000/historico

## 📂 Estrutura do Projeto

```text
VigilantePrecos/
│
├── api.py           # Servidor FastAPI (Rotas e Consultas)
├── vigilante.py     # Lógica Principal (Classe Vigilante)
├── notificador.py   # Módulo de Envio (Telegram)
├── precos.db        # Banco de Dados SQLite (Gerado automaticamente)
└── README.md        # Documentação
```

## 👨‍💻 Autor

Feito por **Kelvin Sousa** durante sua jornada para Engenharia de Dados.
[LinkedIn](https://www.linkedin.com/in/okelvinsousa)
