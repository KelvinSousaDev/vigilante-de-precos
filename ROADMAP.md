# 🗺️ Roadmap 2026: Vigilante de Preços

> **Objetivo:** Transformação total de Script Local para SaaS Multi-tenancy em 30 dias.

---

## 🗓️ Semana 1: A Libertação dos Dados (01/01 - 07/01)

_Foco: Parar de editar código para adicionar produtos._

- [ ] **Database First:**
  - Alterar `vigilante.py` para ler produtos da tabela `dim_produtos` ao invés da lista fixa (`self.lista_produtos`).
- [ ] **CRUD no Dashboard:**
  - Criar aba "Gerenciar Produtos" no Streamlit.
  - Formulário para adicionar (Nome, URL, Meta Preço) e botão para deletar produtos do banco.

---

## 🗓️ Semana 2: A Nuvem Autônoma (08/01 - 14/01)

_Foco: O robô rodar enquanto você dorme._

- [ ] **Containerização Real:**
  - Configurar GitHub Actions ou Render Cron Jobs usando a imagem Docker já criada.
  - O robô deve rodar sozinho a cada 1h na nuvem.
- [ ] **Desligamento Local:**
  - Remover a tarefa do Windows Task Scheduler.

---

## 🗓️ Semana 3: Identidade e Segurança (15/01 - 21/01)

_Foco: O sistema precisa saber QUEM é o dono._

- [ ] **Sistema de Login:**
  - Implementar tela de bloqueio no Streamlit (Biblioteca `streamlit-authenticator`).
  - Criar tabela `usuarios` no Postgres.
- [ ] **Proteção de Rotas:**
  - Ninguém acessa o Dashboard sem senha.

---

## 🗓️ Semana 4: O Multi-Tenant (22/01 - 31/01)

_Foco: Preparar para escalar._

- [ ] **Isolamento de Dados:**
  - Alterar tabela `dim_produtos` para ter uma coluna `user_id`.
  - O robô lê TODOS os produtos de TODOS os usuários de uma vez, mas o Dashboard só mostra os SEUS.
- [ ] **Launch v3.0:**
  - Deploy final da versão SaaS.

---

## 🔮 Fevereiro

- [ ] Marketing? Divulgar para amigos? (A definir)
