# 🦇 Vigilante de Preços v2.0 - Monitoramento Multi-Loja

[![Deploy on Render](https://img.shields.io/badge/Deploy-Online-success?style=for-the-badge&logo=render)](https://vigilante-api.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Cloud-336791?style=for-the-badge&logo=postgresql)](https://render.com/)

> **Status:** Produção (Híbrido) | 🛍️ Suporte: **Amazon Brasil** & **Mercado Livre**

Sistema de Engenharia de Dados ponta-a-ponta para monitoramento competitivo de preços. O projeto utiliza técnicas avançadas de scraping para superar bloqueios de WAF (Web Application Firewalls), normaliza dados de diferentes estruturas HTML e persiste histórico em Data Warehouse na nuvem para análise de tendências.

![Dashboard Vigilante v2]![alt text](image.png)
_(Visualização em tempo real comparando variação de preços entre concorrentes)_

---

## 🏗️ Arquitetura do Sistema (ETL Híbrido)

O sistema opera em um modelo **On-Premises + Cloud**, garantindo resiliência contra bloqueios de IP de Data Centers e mantendo o Dashboard acessível publicamente.

```mermaid
graph LR
    subgraph Coleta [Agente Local / Ingestão]
    A[Robô Python] -->|Bypass WAF| B(Mercado Livre)
    A -->|Headers Rotativos| C(Amazon Brasil)
    end

    subgraph Cloud [Nuvem Render]
    A -->|Persistência Segura| D[(PostgreSQL DW)]
    D -->|Query SQL| E[Dashboard Streamlit]
    end
```

## 🛡️ Desafios de Engenharia Superados

### 1. O Desafio Multi-Tenant (Polimorfismo)

Cada loja (Amazon vs ML) possui estruturas HTML e proteções anti-bot completamente diferentes.

- **Solução:** Implementação de uma arquitetura de extração modular (Strategy Pattern). O robô identifica a origem da URL e seleciona a estratégia de parsing adequada, normalizando dados não estruturados (como "R$ 1.200" vs "1200 + span 00") em um formato único no banco.

### 2. O Bloqueio de WAF/IP

Requisições de servidores cloud (AWS/Azure) são frequentemente bloqueadas por e-commerces.

- **Solução:** Uso da biblioteca `curl_cffi` para falsificar a assinatura TLS (JA3 Fingerprint), simulando um navegador Chrome 120 real, rodando em ambiente residencial para garantir IP confiável.

## 🔧 Tecnologias e Ferramentas

- **Ingestão:** Python 3.12, `curl_cffi` (para simulação de TLS Fingerprint).
- **Armazenamento:** PostgreSQL (Hospedado no Render.com).
- **Visualização:** Streamlit (Consumindo dados históricos do banco).
- **Automação:** Windows Task Scheduler (Execução agendada autônoma).
- **Notificação:** Integração com API do Telegram.

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.12+
- PostgreSQL (Local ou Cloud)

### Instalação

```bash
git clone [https://github.com/KelvinSousaDev/vigilante-de-precos](https://github.com/KelvinSousaDev/vigilante-de-precos)
cd vigilante-de-precos
pip install -r requirements.txt
```

### Configuração (.env)

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgres://usuario:senha@host-do-render/nome_do_banco
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_id
```

### Execução

Para iniciar o agente de coleta:

```bash
python vigilante.py
```

Para iniciar o dashboard visual:

```bash
streamlit run app.py
```

---

## 👨‍💻 Autor

Feito por **Kelvin Sousa** durante sua jornada para Engenharia de Dados.
[LinkedIn](https://www.linkedin.com/in/okelvinsousa)
