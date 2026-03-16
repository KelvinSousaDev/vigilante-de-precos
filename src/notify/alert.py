import requests
import os
from dotenv import load_dotenv

load_dotenv()

def notify_discord(msg):
  url = os.getenv("BOT_ID")

  payload = {
    "content": msg
  }
  requests.post(url, json=payload)
