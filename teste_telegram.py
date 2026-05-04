import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
dados = {
    "chat_id": CHAT_ID,
    "text": "Esta a funcionar"
}

requests.post(url, data=dados)
print("Comando enviado. vai ver o telemovel")