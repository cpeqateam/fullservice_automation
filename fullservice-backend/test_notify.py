#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bildirim modulu TEK-BASINA testi (Telegram + mail).

Amac: gercek bir stres testi baslatmadan, sadece bildirim modulunun
(notify.py + email_sender.py) secrets.json'daki ayarlarla Telegram'a ve mail'e
gonderim yapip yapamadigini gormek.

  - Burada CALISIYORSA  → modul ve secrets saglam. Sahada bildirim gelmiyorsa
    sorun test ortamindadir (tetikleme / log toplama / test bitmemis olmasi).
  - Burada HATA verirse  → sorun bildirim modulunde / secrets.json'da. Once burayi coz.

Kullanim (fullservice-backend klasorunde):
    python test_notify.py                 # telegram + mail (mail: kendine = FS_SMTP_FROM)
    python test_notify.py ad@mail.com     # mail'i ayrica bu adrese de gonder
"""
import os
import sys
import tempfile
from datetime import datetime

# run_server.py ile AYNI: bu klasoru import yoluna ekle (server/ ve common/ bulunsun)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from common.config import get_secret
from server import notify
from server.email_sender import EmailSender


def _mask(v: str) -> str:
    """Sirri loga basarken gizle: ilk 4 + son 3 karakter."""
    if not v:
        return "(BOS)"
    return v[:4] + "..." + v[-3:] if len(v) > 8 else "***"


def check_secrets() -> bool:
    print("=== 1) secrets kontrolu (env -> secrets.json) ===")
    keys = ["FS_TELEGRAM_BOT_TOKEN", "FS_TELEGRAM_CHAT_ID",
            "FS_SMTP_USER", "FS_SMTP_PASS", "FS_SMTP_FROM"]
    ok = True
    for k in keys:
        val = get_secret(k)
        if not val:
            ok = False
        print(f"  [{'OK   ' if val else 'EKSIK'}] {k} = {_mask(val)}")
    if not ok:
        print("  ! Bazi anahtarlar BOS. secrets.json yok olabilir ya da yanlis klasorde.")
    print()
    return ok


def test_telegram() -> bool:
    print("=== 2) Telegram testi ===")
    token = get_secret("FS_TELEGRAM_BOT_TOKEN")
    chat = get_secret("FS_TELEGRAM_CHAT_ID", "0")
    if not token:
        print("  ❌ BOT_TOKEN bos — secrets.json okunamadi.\n")
        return False

    # a) Token gecerli mi? (getMe)
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
        data = r.json()
        if not (r.ok and data.get("ok")):
            print(f"  ❌ Token GECERSIZ: {r.status_code} {r.text}\n")
            return False
        print(f"  bot dogrulandi: @{data['result'].get('username')}  (chat_id={chat})")
    except Exception as e:
        print(f"  ❌ Telegram'a ulasilamadi (ag/proxy?): {e}\n")
        return False

    # b) Gercek gonderim: mesaj + ornek dosya (notify.py'nin AYNISI)
    stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    notify.send_telegram(
        f"[TEST] FULL Servis bildirim modulu testi — {stamp}\n"
        "Bu bir test mesajidir; gercek bir stres testi CALISMADI."
    )
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as f:
            f.write("FULL Servis bildirim testi — ornek log dosyasi\n")
            tmp = f.name
        notify.send_document(tmp, caption="[TEST] ornek log dosyasi")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    print("  -> Gonderildi. Telegram grubuna mesaj + dosya DUSTU MU kontrol et.")
    print("     (Hata olduysa yukarida '❌ Telegram ...' satiri gorunur.)\n")
    return True


def test_mail(extra_to: str = None) -> bool:
    print("=== 3) Mail testi ===")
    from_addr = get_secret("FS_SMTP_FROM", "cpetestteam@gmail.com")
    if not get_secret("FS_SMTP_PASS"):
        print("  ❌ FS_SMTP_PASS bos — secrets.json okunamadi.\n")
        return False
    stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    try:
        sender = EmailSender()
        sender.set_subject(f"[TEST] FULL Servis bildirim modulu — {stamp}")
        sender.set_body("Bu bir TEST mailidir. Bildirim modulu calisiyor.\n\n"
                        "Gercek bir stres testi calismadi.")
        sender.add_to_address(from_addr)          # kendine: ekibi spamlemeden dene
        if extra_to:
            sender.add_to_address(extra_to)
        sender.send_email()
        print(f"  -> Mail gonderildi: {from_addr}" + (f" + {extra_to}" if extra_to else ""))
        print("     Gelen kutusunu (ve SPAM klasorunu) kontrol et.\n")
        return True
    except Exception as e:
        print(f"  ❌ Mail HATA: {e}\n")
        return False


if __name__ == "__main__":
    extra = sys.argv[1] if len(sys.argv) > 1 else None
    print("\nFULL Servis — Bildirim Modulu Tek-Basina Testi\n")
    secrets_ok = check_secrets()
    tg = test_telegram()
    ml = test_mail(extra)
    print("=== SONUC ===")
    print(f"  secrets : {'tam' if secrets_ok else 'EKSIK'}")
    print(f"  Telegram: {'OK' if tg else 'HATA'}")
    print(f"  Mail    : {'OK' if ml else 'HATA'}")
    print("\nIkisi de OK ise modul saglam → sahada gelmiyorsa sorun test ortaminda.")
    sys.exit(0 if (tg and ml) else 1)
