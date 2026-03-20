from datetime import datetime, timedelta
from airflow.decorators import dag, task
import sys
import os
import asyncio

sys.path.insert(0, '/opt/airflow/src')

from main import main as ronda_vigilante

@dag(
  dag_id='Vigilante_pipeline',
  default_args={
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1)
  },
  description='Pipeline ETL - Vigilante',
  schedule='0 */1 * * *',
  start_date=datetime(2026, 3, 20),
  catchup=False,
  tags=['vigilante', 'etl', 'preços']
)

def vigilante_pipeline():
    
    @task
    def patrulha_de_preços():
        """
        Tarefa única que dispara toda a infraestrutura assíncrona do Vigilante.
        O asyncio.run() cria o loop de eventos que o Playwright e o async/await exigem.
        """
        print("🦇 Acionando o sinal. Iniciando varredura via Airflow...")

        asyncio.run(ronda_vigilante())

    patrulha_de_preços()

dag_obj = vigilante_pipeline()
          