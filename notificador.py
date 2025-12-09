import requests
import os
from dotenv import load_dotenv

load_dotenv()

def enviar_telegram(msg):
  token = os.getenv("TELEGRAM_TOKEN")
  chat_id = os.getenv("TELEGRAM_CHAT_ID")

  url = f"https://api.telegram.org/bot{token}/sendMessage"

  payload = {
    "chat_id": chat_id,
    "text": msg
  }

  requests.post(url, payload)
  print('Mensagem Enviada!')

if __name__ == "__main__":
    enviar_telegram("Testando: O Robô está vivo!")