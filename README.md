# 🦇 Vigilante de Preços - Arquitetura Híbrida de Monitoramento

[![Deploy on Render](https://img.shields.io/badge/Deploy-Online-success?style=for-the-badge&logo=render)](https://vigilante-api.onrender.com/docs)

Este projeto é um sistema de **Engenharia de Dados** focado em monitoramento de preços (Scraping), projetado para superar bloqueios modernos de WAF (Web Application Firewalls) e persistir dados históricos na nuvem.

## 🏗️ Arquitetura do Sistema

O sistema opera em um modelo híbrido **On-Premises + Cloud**, garantindo resiliência contra bloqueios de IP de Data Centers.

```mermaid
graph LR
    A["Agente Local (Python/Windows)"] -->|"Bypass WAF (curl_cffi)"| B("Mercado Livre")
    A -->|"Persistência (SQL)"| C["Banco de Dados PostgreSQL (Render Cloud)"]
    C -->|"Leitura (FastAPI)"| D["Dashboard Streamlit"]
```

## 🔧 Tecnologias Utilizadas

- **Ingestão:** Python 3.12, `curl_cffi` (para simulação de TLS Fingerprint e bypass de bloqueios).
- **Automação:** Windows Task Scheduler (Execução agendada autônoma).
- **Armazenamento:** PostgreSQL (Hospedado no Render.com).
- **Visualização:** Streamlit (Consumindo dados históricos do banco).
- **Notificação:** Integração com API do Telegram.

## 🛡️ Desafios de Engenharia Superados

### O Problema do Bloqueio de IP

Durante o desenvolvimento, identificou-se que requisições vindas de IPs de Data Centers (GitHub Actions/Azure) eram bloqueadas ou redirecionadas para verificação de identidade (CAPTCHA).

### A Solução

Implementou-se uma **estratégia de coleta local**:

1.  O script roda em ambiente residencial (IP confiável).
2.  Uso da biblioteca `curl_cffi` para falsificar a assinatura TLS (JA3 Fingerprint), simulando um navegador Chrome 120 real.
3.  Os dados coletados são enviados criptografados para o banco na nuvem, desacoplando a coleta da visualização.

## ⚙️ Funcionalidades

- [x] **Coleta Automática:** Acessa a página do produto e extrai o preço atual "escondido" no HTML.
- [x] **Tratamento de Dados:** Limpa formatações (R$, pontos, vírgulas) convertendo para _float_.
- [x] **Alertas:** Envia mensagem no Telegram caso o preço esteja abaixo do valor estipulado.
- [x] **API de Consulta:** Disponibiliza o histórico de preços em formato JSON via endpoint HTTP.

## 🚀 Como Executar

### Pré-requisitos

- Python 3.12+
- PostgreSQL (Local ou Cloud)

### Instalação

```bash
git clone [https://github.com/KelvinSousaDev/vigilante-de-precos]
pip install -r requirements.txt
```

### Configuração (.env)

Crie um arquivo `.env` na raiz:

```env
DATABASE_URL=postgres://user:pass@host/db
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_id
```

### Execução

```bash
python vigilante.py
```

## 👨‍💻 Autor

Feito por **Kelvin Sousa** durante sua jornada para Engenharia de Dados.
[LinkedIn](https://www.linkedin.com/in/okelvinsousa)
