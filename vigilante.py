import time
from bs4 import BeautifulSoup
from notificador import enviar_telegram
import os
import psycopg2
import asyncio
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv
import random

load_dotenv()

class Vigilante:
  def __init__(self):
    """
    Inicializa o Agente Vigilante e configura o ambiente de coleta.

    Responsabilidades:
    1. Define Headers HTTP (User-Agent) para simular um navegador real e evitar bloqueios (WAF).
    2. Estabelece conexão inicial com o Banco de Dados.
    3. Carrega a lista de produtos monitorados para a memória do robô.
    """
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
      "Referer": "https://www.google.com/",
      "Connection": "keep-alive"
    }
    self.lista_produtos = [] 
    self.carregar_produtos_do_banco()

  async def main_async(self):
     """
     Orquestra o ciclo de vida assíncrono da coleta de dados.

     Responsabilidades:
     1. Instancia um Semáforo para limitar a concorrência (evita sobrecarga/bloqueio).
     2. Gerencia a sessão HTTP de alta performance (AsyncSession).
     3. Consolida e retorna os resultados de todas as tarefas de scraping.
     """
     semaforo = asyncio.Semaphore(2)

     async with AsyncSession(impersonate="chrome120") as session:
        tarefas = []
        for produto in self.lista_produtos:
          tarefas.append(self.processar_produto(semaforo, session, produto))
        
        print("🚀Tarefas Criadas, Iniciando Vigilante")
        resultados = await asyncio.gather(*tarefas)

        return [r for r in resultados if r is not None]

  def carregar_produtos_do_banco(self):
     """
     Sincroniza a memória do agente com a base de dados central (Neon/Postgres).

     Responsabilidades:
     1. Estabelece conexão segura com o Data Warehouse.
     2. Executa query DQL para recuperar os alvos de monitoramento ativos.
     3. Popula a fila de execução (self.lista_produtos) para o ciclo de extração.
     """
     DATABASE_URL = os.getenv("DATABASE_URL")
     try:
        if DATABASE_URL:
           conn = psycopg2.connect(DATABASE_URL)
        else:
           conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")
        
        cursor = conn.cursor()

        query = "SELECT nome_produto, url_produto, loja, meta_preco FROM dim_produtos"
        cursor.execute(query)
        produtos_retornados = cursor.fetchall()

        self.lista_produtos = []

        for item in produtos_retornados:
           novo_produto = {
                "nome": item[0],       
                "url": item[1],        
                "loja": item[2],       
                "meta_preco": float(item[3]) if item[3] is not None else 0.0
                }
           self.lista_produtos.append(novo_produto)

        print(f"🦇 Configuração atualizada: {len(self.lista_produtos)} alvos carregados do DB.")
        conn.close()
     except Exception as e:
        print(f"❌ Erro ao carregar produtos do banco: {e}")
        self.lista_produtos = []

  def salvar_no_postgres(self, nome, url, preco, loja):
      """
      Persiste os dados coletados no Data Warehouse, garantindo integridade referencial.

      Responsabilidades:
      1. Gerencia a conexão transacional (Commit/Rollback) com o NeonDB.
      2. Implementa lógica de 'Idempotência': Verifica se o produto já existe na dimensão (`dim_produtos`) antes de criar.
      3. Registra o novo ponto de dados na tabela de fatos (`fato_precos`) vinculada ao ID único do produto.
      """
      DATABASE_URL = os.getenv("DATABASE_URL")
      try:
          if DATABASE_URL:
             conn = psycopg2.connect(DATABASE_URL)
          else:
             conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="admin")
            
          cursor = conn.cursor()

          cursor.execute("SELECT id FROM dim_produtos WHERE url_produto = %s", (url,))
          resultado = cursor.fetchone()

          if resultado:
              produto_id = resultado[0]
          else:
              print(f"🆕 Produto Novo detectado: {nome} ({loja})")
              cursor.execute(
                  "INSERT INTO dim_produtos (nome_produto, url_produto, loja) VALUES (%s, %s, %s) RETURNING id",
                  (nome, url, loja)
              )
              produto_id = cursor.fetchone()[0]

          cursor.execute(
              "INSERT INTO fato_precos (produto_id, valor_coletado) VALUES (%s, %s)",
              (produto_id, preco)
          )
          
          conn.commit()
          print(f"💾 Preço de R$ {preco} salvo no PostgreSQL para o ID {produto_id}")

      except Exception as e:
          print(f"❌ Erro ao salvar no Banco: {e}")
      finally:
          if 'conn' in locals(): conn.close()

  @staticmethod
  def limpar_preco(texto_bruto):
     """
     Recebe o texto sujo do HTML (ex: 'R$ 1.200,50\\n') e converte para float (1200.50).
     
     Remove quebras de linha, R$ e converte pontuação do padrão BRL para Python.
     Retorna 0.0 se houver erro de conversão.
     """
     if not texto_bruto:
        return 0.0
     
     texto = texto_bruto.replace("R$", "").strip()
     # Remove caracteres invisíveis que a Amazon costuma mandar
     texto = texto.replace("\n", "").replace("\r", "").replace("\t", "")
     texto = texto.replace(".", "")
     texto = texto.replace(",", ".")

     try:
       return float(texto)
     except ValueError:
        return 0.0

  async def verificar_mercadolivre(self, session, url):
    """
    Executa a estratégia de extração (Scraping) otimizada para o Mercado Livre.

    Responsabilidades:
    1. Implementa 'Retry Pattern' (3 tentativas) com Backoff Exponencial para tolerância a falhas.
    2. Aplica 'Jitter' (atraso aleatório) para humanizar a requisição e evadir detecção de WAF.
    3. Realiza Parsing Hierárquico: Prioriza metadados estruturados (Microdata) e faz fallback para seletores CSS visuais.
    """
    MAX_TENTATIVAS = 3
    for tentativa in range(MAX_TENTATIVAS):
      try:
        espera = random.uniform(0.5, 2.0) + (tentativa * 1.5)
        await asyncio.sleep(espera)

        if tentativa > 0:
          print(f"🔁 Tentativa {tentativa+1} para {url[-10:]}...")

        resposta = await session.get(url, impersonate="chrome120")
        print(f"📡 Status HTTP: {resposta.status_code}")

        if resposta.status_code != 200:
          print(f"⚠️ Erro HTTP {resposta.status_code}. Retentando...")
          continue

        if "account-verification" in resposta.url:
            print("🚨 ALERTA: Redirecionado para verificação de segurança.")
            return None

        soup = BeautifulSoup(resposta.content, 'html.parser')

        elemento_meta = soup.find("meta", itemprop="price")
        if elemento_meta:
          valor_limpo = float(elemento_meta['content'])
          return valor_limpo
        
        #Se não pegar no meta, pegamos na classe
        elemento_visual = soup.find(class_="andes-money-amount__fraction")
        if elemento_visual:
          return self.limpar_preco(elemento_visual.get_text())
        
        print(f"❌ Falha ao obter preço. Título: {soup.title.string if soup.title else 'Sem título'}")
        continue
          
      except Exception as e:
          print(f"Erro ao ler ML: {e}")
          await asyncio.sleep(1)
          
    print(f"💀 Falha total após {MAX_TENTATIVAS} tentativas: {url[-10:]}")
    return None
  
  async def verificar_amazon(self,session, url):
    """
    Executa a estratégia de extração (Scraping) específica para a estrutura da Amazon.

    Responsabilidades:
    1. Gerencia tolerância a falhas com 'Retry Pattern' e Backoff Exponencial.
    2. Utiliza 'Header Rotation' e 'Jitter' para simular comportamento humano (Bypass de WAF).
    3. Realiza Parsing Fragmentado: Reconstrói o preço final unificando componentes DOM separados (parte inteira e fracionária) para garantir precisão decimal.
    """
    MAX_TENTATIVAS = 3
    for tentativa in range(MAX_TENTATIVAS):
      try:
          espera = random.uniform(0.5, 2.0) + (tentativa * 1.5)
          await asyncio.sleep(espera)

          if tentativa > 0:
            print(f"🔁 Tentativa {tentativa+1} para {url[-10:]}...")

          resposta = await session.get(url, headers=self.headers, impersonate="chrome120")
          print(f"📡 Status HTTP: {resposta.status_code}")

          if resposta.status_code != 200:
            print(f"⚠️ Erro HTTP {resposta.status_code}. Retentando...")
            continue

          soup = BeautifulSoup(resposta.content, 'html.parser')

          if "api-services-support@amazon.com" in resposta.text:
                print("👮 Captcha detectado. Retentando...")
                continue

          real = soup.find(class_="a-price-whole")
          cents = soup.find(class_="a-price-fraction")
          if real and cents:
            texto_real = real.get_text().strip()
            texto_cents = cents.get_text().strip()
            # Remove Virgulas que a Amazon costuma enviar
            if texto_real.endswith(','):
              texto_real = texto_real[:-1]

            valor_montado = f"{texto_real},{texto_cents}"
            return self.limpar_preco(valor_montado)
          
          print(f"❌ Falha ao obter preço. Título: {soup.title.string if soup.title else 'Sem título'}")
          continue

      except Exception as e:
          print(f"Erro ao ler Amazon: {e}")
          await asyncio.sleep(1)
          
    print(f"💀 Falha total após {MAX_TENTATIVAS} tentativas: {url[-10:]}")
    return None

  async def processar_produto(self, semaforo, session, produto):
     """
     Atua como 'Dispatcher' tático, roteando a execução para a estratégia de coleta adequada.

     Responsabilidades:
     1. Controle de Concorrência: Adquire o semáforo global para limitar requisições simultâneas e evitar Rate Limiting.
     2. Strategy Pattern: Seleciona dinamicamente o algoritmo de extração específico (Amazon/ML) com base na origem do produto.
     3. Normalização (DTO): Consolida os dados brutos em um objeto estruturado padrão pronto para persistência.
     """
     async with semaforo:
        preco = None

        if produto['loja'] == "Amazon":
          preco = await self.verificar_amazon(session, produto['url'])
        
        if produto['loja'] == "Mercado Livre":
          preco = await self.verificar_mercadolivre(session, produto['url'])

        if preco:
          return{
            "nome": produto['nome'],
            "preco_achado": preco,
            "meta": produto['meta_preco'],
            "url": produto['url'],
            "loja": produto['loja']
          }

  def rodar(self):
    """
    Ponto de entrada (Entrypoint) que executa o Pipeline ETL completo (Extração, Carga e Notificação).

    Responsabilidades:
    1. Orquestração: Inicializa o Event Loop do AsyncIO para disparar a coleta massiva.
    2. Persistência: Recebe os dados brutos e chama o método de salvamento (Load) no Data Warehouse.
    3. Motor de Regras: Compara Preço Coletado vs. Meta do Usuário e dispara alertas via Telegram (Push Notification).
    4. Resiliência: Captura exceções globais para garantir que falhas não derrubem o container sem registro.
    """
    print("👀 Iniciando ronda de preços...")
    self.registrar_log("INICIANDO", "Começando a Ronda...")

    try:
      resultados = asyncio.run(self.main_async())
      for item in resultados:
         self.salvar_no_postgres(
            item['nome'], 
            item['url'], 
            item['preco_achado'], 
            item['loja']
         )
         if item['preco_achado'] <= item['meta']:
            print(f"🚨 PROMOÇÃO: {item['nome']} (R$ {item['preco_achado']})")

            msg = (
              f"🚨 *ALERTA DE PROMOÇÃO!* 🚨\n\n"
              f"📦 *Produto:* {item['nome']}\n"
              f"💰 *Preço Atual:* R$ {item['preco_achado']}\n"
              f"🎯 *Sua Meta:* R$ {item['meta']}\n"
              f"🏪 *Loja:* {item['loja']}\n\n"
              f"🔗 [Comprar Agora]({item['url']})"
              )
            enviar_telegram(msg)

    except Exception as e:
      msg_erro = f"Erro Fatal: {str(e)}"
      print(msg_erro)
      self.registrar_log("ERRO", msg_erro)

  def registrar_log(self, status, detalhes):
    """
    Módulo de Telemetria e Observabilidade do sistema.

    Responsabilidades:
    1. Trilha de Auditoria: Persiste eventos críticos (Início, Sucesso, Erro Fatal) na tabela 'logs_execucao'.
    2. Monitoramento Remoto: Alimenta os dados que permitem ao Dashboard saber se o agente está 'Online' ou 'Offline'.
    3. Isolamento de Falha: Abre uma conexão dedicada para garantir que o log de erro seja salvo mesmo se a conexão principal cair.
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    try:
      if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
      
      cursor = conn.cursor()
      cursor.execute("INSERT INTO logs_execucao (status, detalhes) VALUES (%s, %s)", (status, detalhes))
      conn.commit()

    except Exception as e:
      print(f"❌ Erro ao salvar no Banco: {e}")
    finally:
      if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    bot = Vigilante()
    bot.rodar()
