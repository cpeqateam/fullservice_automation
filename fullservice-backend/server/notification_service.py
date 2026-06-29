"""
FULL Servis bildirim servisi — test bitince Telegram + mail gönderir.

GRK app/services/notification_service.py ile AYNI davranış:
  • Telegram (aynı grup): tamamlanma mesajı (GRK formatı) + özet log dosyaları.
  • Mail (aynı adresler): yalnızca mesaj, DOSYA EKİ YOK.
Telegram 50 MB üstü dosya gönderilmez, yerine uyarı mesajı atılır.

Tetikleme: orchestrator.stop_session() — test bitince (kullanıcı "Durdur" dediğinde)
arka planda çağrılır. Agent log upload'larının tamamlanması için kısa bir bekleme
(GRACE_SECONDS) sonrası oturumun tüm log dosyaları toplanıp gönderilir.

Devre dışı: ortam değişkeni FS_NOTIFY_DISABLE=1.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from typing import List, Optional

from server import notify, log_collector

# GRK ile AYNI alıcılar
TO_ADDRESSES = [
    "erisimcihazlari@turktelekom.com.tr",
    "samet.ozabaci@turktelekom.com.tr",
    "aliimran.atabey@partner.turktelekom.com.tr",
    "ibrahim.sevinc@partner.turktelekom.com.tr",
    "faruk.ozer@partner.turktelekom.com.tr",
]
CC_ADDRESSES = [
    "aliimranatabey@gmail.com",
    "sametozabaci@gmail.com",
    "farukozerr28@gmail.com",
    "ttibrahimsevinc@gmail.com",
]

TELEGRAM_DOC_LIMIT = 50 * 1024 * 1024   # 50 MB — Telegram API hard limiti
GRACE_SECONDS = 10                      # agent log upload'ları için kısa bekleme


def _fmt(dt) -> str:
    """ISO string ya da datetime'ı GRK formatına çevirir (dd-mm-YYYY HH:MM:SS)."""
    if not dt:
        return "?"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    return dt.strftime("%d-%m-%Y %H:%M:%S")


def _build_body(device: dict, start_time, end_time) -> str:
    """GRK bildirim metniyle AYNI format (yalnızca 'GRK' yerine 'FULL Servis')."""
    brand        = device.get("brand") or "?"
    model        = device.get("model") or "?"
    firmware     = device.get("firmware") or "?"
    server       = device.get("server") or "FULL Servis"
    duration     = device.get("duration", "?")
    user_name    = device.get("user_name", "") or ""
    user_surname = device.get("user_surname", "") or ""
    full_name    = f"{user_name} {user_surname}".strip() or "Bilinmeyen Kullanıcı"

    return (
        f"FULL Servis Görevimiz Tamamlandı 🚀✨\n\n"
        f"{server} sunucularında <b>{full_name}</b> kullanıcısı tarafından "
        f"{_fmt(start_time)} tarihinde "
        f"<b>{brand} {model} {firmware}</b> bilgilerine sahip cihaz ile başlatılan "
        f"{duration} saniyelik test başarıyla tamamlanmıştır.\n\n"
        f"Test Cihazı: {brand} {model}\n"
        f"Cihaz Firmware: {firmware}\n"
        f"Sunucu: {server}\n"
        f"Test Süresi: {duration} Saniye\n"
        f"Test Başlangıç Zamanı: {_fmt(start_time)}\n"
        f"Test Bitiş Zamanı: {_fmt(end_time)}\n\n"
        "Otomatik mesajdır."
    )


def send_completion(device: dict, session_id: str, start_time):
    """Test bitince bildirim gönderimini ARKA PLANDA başlatır."""
    if os.environ.get("FS_NOTIFY_DISABLE"):
        print("[NOTIFY] FS_NOTIFY_DISABLE ayarli — bildirim atlandi.")
        return
    threading.Thread(
        target=_worker, args=(dict(device), session_id, start_time), daemon=True
    ).start()


def _worker(device: dict, session_id: str, start_time):
    # Agent'ların son log upload'larını tamamlaması için kısa bekleme
    time.sleep(GRACE_SECONDS)
    end_time = datetime.now()
    body = _build_body(device, start_time, end_time)

    logs = []
    try:
        logs = log_collector.list_session_files(session_id)
    except Exception as e:
        print(f"[NOTIFY] Log dosyalari toplanamadi: {e}")

    _send_email(body)             # mail: yalnızca metin (dosyasız)
    _send_telegram(body, logs)    # telegram: metin + log dosyaları


def _send_email(body: str):
    try:
        from server.email_sender import EmailSender
        sender = EmailSender()
        sender.set_subject("FULL Servis Testi") \
              .set_body(body) \
              .add_to_address(TO_ADDRESSES) \
              .add_cc_address(CC_ADDRESSES)
        sender.send_email()
        print("[NOTIFY] FULL Servis test maili gonderildi.")
    except Exception as e:
        print(f"[NOTIFY] Mail gonderim hatasi: {e}")


def _send_telegram(body: str, logs: List[str]):
    try:
        notify.send_telegram(body)
        for path in (logs or []):
            basename = os.path.basename(path)
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            if size > TELEGRAM_DOC_LIMIT:
                msg = (
                    f"⚠️ <b>{basename}</b> dosyasi {size / 1024 / 1024:.1f} MB — "
                    f"Telegram 50 MB sinirini astigi icin gonderilemedi.\n"
                    f"Dosya FTP sunucusuna ve sunucunun <code>logs/</code> klasorune "
                    f"yine de yazildi."
                )
                print(f"[NOTIFY] {basename} cok buyuk ({size} byte), Telegram'a yuklenmiyor.")
                try:
                    notify.send_telegram(msg)
                except Exception as e:
                    print(f"[NOTIFY] Buyuk-dosya uyarisi gonderilemedi: {e}")
                continue
            try:
                notify.send_document(path, caption=f"[DOSYA] {basename}")
            except Exception as e:
                print(f"[NOTIFY] Telegram dosya gonderim hatasi ({basename}): {e}")
        print("[NOTIFY] Telegram bildirimleri gonderildi.")
    except Exception as e:
        print(f"[NOTIFY] Telegram bildirim hatasi: {e}")
