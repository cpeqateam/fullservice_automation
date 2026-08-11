"""
error_log üretimi — sunucunun app.log'unun test aralığındaki dilimini FTP'ye yükler.

GRK app/utils/error_log_capture.py mantığının portudur. Bildirim (Telegram/mail)
OLARAK gönderilmez; yalnızca FTP'ye konur ki herhangi bir hata ihtimaline karşı
loglar incelenebilsin.

Akış:
  • Sunucu açılışında main.py, stdout/stderr'i logs/app.log'a da yansıtır (Tee).
  • Oturum başında orchestrator app.log boyutunu (offset) kaydeder.
  • Test bitince app.log[offset:EOF] dilimi bir dosyaya yazılıp FTP'ye yüklenir:
      <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/Errorlog/

Dağıtık not: Bu dilim SUNUCU tarafı logları içerir (orkestrasyon, sunucu-yerel
testler, DB/FTP/bildirim). Agent makinelerin hataları kendi konsollarındadır.
"""
from __future__ import annotations

import os
import re
import threading
from datetime import datetime

from common.config import LOGS_DIR
from server import ftp_service


def _s(v) -> str:
    """FTP klasör adı için güvenli hale getir (boşsa Unknown)."""
    v = (str(v).strip() if v is not None else "") or "Unknown"
    return re.sub(r'[\\/:*?"<>|]+', "_", v)

APP_LOG_PATH = os.path.join(LOGS_DIR, "app.log")


def current_size() -> int:
    """app.log'un anlık byte boyutu (oturum başı offset'i). Yoksa 0."""
    try:
        return os.path.getsize(APP_LOG_PATH)
    except OSError:
        return 0


def _slice_to(dest_path: str, start_offset: int) -> bool:
    """app.log[start_offset:EOF] kısmını dest_path'e yazar."""
    try:
        if not os.path.exists(APP_LOG_PATH):
            return False
        with open(APP_LOG_PATH, "rb") as src:
            src.seek(max(0, int(start_offset or 0)))
            data = src.read()
        with open(dest_path, "wb") as dst:
            dst.write(data)
        return True
    except Exception as e:
        print(f"[LOG_CAPTURE] Dilim cikartilamadi: {e}")
        return False


def finalize_async(device: dict, session_id: str, start_time, start_offset: int,
                   db_session_id=None):
    """error_log dilimini arka planda üretip FTP'ye yükler (bildirim YOK) ve
    DB'deki test_session.error_log_ftp_path'i tam dosya yoluyla günceller."""
    threading.Thread(
        target=_worker,
        args=(dict(device or {}), session_id, start_time, start_offset, db_session_id),
        daemon=True,
    ).start()


def _worker(device: dict, session_id: str, start_time, start_offset: int,
            db_session_id=None):
    """Arka plan iş parçacığı: app.log'un bu oturuma ait dilimini `FULL_Service_errorlog_...`
    dosyasına yazıp FTP'deki Errorlog klasörüne yükler (bildirim göndermez), sonra
    DB'ye tam FTP yolunu yazar ki platformdan indirilebilsin."""
    brand    = device.get("brand") or "Unknown"
    model    = device.get("model") or "Unknown"
    firmware = device.get("firmware") or "Unknown"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FULL_Service_errorlog_{brand}_{model}_{firmware}_{ts}.log".replace(" ", "")
    local_path = os.path.join(LOGS_DIR, filename)

    if not _slice_to(local_path, start_offset):
        print("[LOG_CAPTURE] app.log bulunamadi/dilim bos — error_log atlandi.")
        return

    # Hedef: <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/Errorlog  (makine alt klasörü yok)
    target_dir = "/".join([_s(brand), _s(model), _s(firmware), "FULLSERVIS", "Errorlog"])
    remote_path = f"{target_dir}/{filename}"

    try:
        ftp_service.upload_files_to_ftp([local_path], target_dir)
        print(f"[LOG_CAPTURE] error_log FTP'ye gonderildi: {remote_path}")
    except Exception as e:
        print(f"[LOG_CAPTURE] FTP yukleme hatasi: {e}")
        return                      # yüklenemediyse DB'ye yol yazma (indirme kirilmasin)

    # DB: "Error Log İndir" butonu bu tam yolu kullanır.
    if db_session_id:
        try:
            from server import db_service
            db_service.update_session_error_log(db_session_id, remote_path)
        except Exception as e:
            print(f"[LOG_CAPTURE] error_log DB yolu yazilamadi: {e}")
