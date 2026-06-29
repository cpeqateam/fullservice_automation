"""
Telegram Bot API sarmalayici — metin mesaji ve dosya gonderir.

GRK app/utils/notify.py'nin BIREBIR AYNISIDIR (ayni bot, ayni grup/CHAT_ID).
notification_service tarafindan cagrilir; dogrudan kullanilmaz.

Fonksiyon ozeti:
  send_telegram(text)              Gruba HTML formatli metin gonderir.
  send_document(path, caption)     Dosyayi gruba yukler.
"""
import requests

from common.config import get_secret

# Sırlar repoya KONMAZ — ortam değişkeni ya da gitignore'lu secrets.json'dan gelir.
BOT_TOKEN = get_secret("FS_TELEGRAM_BOT_TOKEN")
try:
    CHAT_ID = int(get_secret("FS_TELEGRAM_CHAT_ID", "0"))
except (TypeError, ValueError):
    CHAT_ID = 0


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    resp = requests.post(url, data=payload, timeout=15)
    if not resp.ok:
        print(f"❌ Telegram mesaj hatası: {resp.status_code} {resp.text}")


def send_document(document_path: str, caption: str = None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    data = {"chat_id": CHAT_ID}
    if caption:
        data["caption"] = caption
        data["parse_mode"] = "HTML"
    with open(document_path, "rb") as f:
        files = {"document": f}
        resp = requests.post(url, data=data, files=files, timeout=60)
    if not resp.ok:
        print(f"❌ Telegram belge hatası: {resp.status_code} {resp.text}")
