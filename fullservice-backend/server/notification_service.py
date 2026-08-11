"""
FULL Servis bildirim servisi — test bitince Telegram + mail gönderir.

GRK app/services/notification_service.py ile AYNI davranış:
  • Telegram (aynı grup): tamamlanma mesajı (GRK formatı) + ÖZET dosyalar.
  • Mail (aynı adresler): yalnızca mesaj, DOSYA EKİ YOK.
Telegram 50 MB üstü dosya gönderilmez, yerine uyarı mesajı atılır.

Telegram'a NE gider (kullanıcı isteri — ham .txt yığını gönderilmez):
  • Ping özet Excel'leri     (bilgisayar başına tek dosya, adı bilgisayarı içerir)
  • Wi-Fi analiz Excel'leri  (bilgisayar başına, adı bilgisayarı içerir)
  • iperf .txt raporları
Bunların HEPSİ TEK BİR ZIP'te toplanıp öyle gönderilir (fullServis_raporlar_...zip)
— Telegram tek tek dosyaya boğulmasın. Diğer ham loglar (ping/youtube/torrent/wifi
.txt) yalnızca FTP'ye ve sunucunun logs/ klasörüne yazılır, Telegram'a gönderilmez.

Tetikleme: orchestrator.stop_session() — test bitince (kullanıcı "Durdur" dediğinde)
arka planda çağrılır. Agent log upload'larının tamamlanması için kısa bir bekleme
(GRACE_SECONDS) sonrası oturumun tüm log dosyaları toplanıp gönderilir.

Devre dışı: ortam değişkeni FS_NOTIFY_DISABLE=1.
"""
from __future__ import annotations

import os
import tempfile
import threading
import time
import zipfile
from datetime import datetime
from typing import List, Optional

from server import notify, report_service

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
    # "sametozabaci@gmail.com",
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


def send_completion(device: dict, session_id: str, start_time,
                    db_session_id=None, server_node_name: str | None = None):
    """Test bitince bildirim gönderimini ARKA PLANDA başlatır."""
    if os.environ.get("FS_NOTIFY_DISABLE"):
        print("[NOTIFY] FS_NOTIFY_DISABLE ayarli — bildirim atlandi.")
        return
    threading.Thread(
        target=_worker,
        args=(dict(device), session_id, start_time, db_session_id, server_node_name),
        daemon=True,
    ).start()


def _zip_reports(paths: List[str], device: dict) -> Optional[str]:
    """Telegram'a gidecek ÖZET EXCEL'leri TEK bir .zip'te toplar (ping özet, iperf
    özet, wifi analiz). Ham .txt loglar Telegram'a GİTMEZ — hepsi FTP'de ve
    sunucunun logs/ klasöründe tek tek indirilebilir halde durur.
    Zip yolunu döner; dosya yoksa None. Zip adı FULL Servis standardında:
        fullServis_raporlar_<marka>_<model>_<fw>_<YYYYMMDD_HHMMSS>.zip
    (kullanıcı isteri: Telegram'a tek tek dosya değil, tek zip gitsin)."""
    files = [p for p in (paths or []) if p and os.path.exists(p)]
    if not files:
        return None

    def _np(s):
        return (str(s).strip() if s else "").replace(" ", "") or "Unknown"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = (f"fullServis_raporlar_{_np(device.get('brand'))}_{_np(device.get('model'))}"
            f"_{_np(device.get('firmware'))}_{ts}.zip")
    zip_path = os.path.join(tempfile.gettempdir(), name)
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                zf.write(p, os.path.basename(p))   # arşivde düz dosya adı (klasörsüz)
        print(f"[NOTIFY] {len(files)} rapor tek zip'te toplandi: {name}")
        return zip_path
    except Exception as e:
        print(f"[NOTIFY] Zip olusturulamadi: {e}")
        return None


def _worker(device: dict, session_id: str, start_time,
            db_session_id=None, server_node_name: str | None = None):
    """Arka plan iş parçacığı: kısa bekleyip (log upload'ları için) oturumu
    sonlandırır — özet Excel'leri üretir, TÜM dosyaları FTP'ye yükler, DB'deki
    ftp_file_path'leri gerçek dosya yoluyla günceller — sonra dönen Excel'leri TEK
    ZIP yapıp mail (metin) + Telegram (metin + tek zip) gönderir."""
    # Agent'ların son log upload'larını tamamlaması için kısa bekleme
    time.sleep(GRACE_SECONDS)

    # Özet Excel üretimi + FTP yüklemesi + DB ftp_file_path güncellemesi.
    # Telegram'a gidecek Excel listesini döner.
    excels: List[str] = []
    try:
        excels = report_service.finalize_session(
            session_id, device, start_time, db_session_id, server_node_name)
    except Exception as e:
        print(f"[NOTIFY] Oturum raporlari tamamlanamadi: {e}")

    end_time = datetime.now()
    body = _build_body(device, start_time, end_time)

    # Özet Excel'leri tek zip'te topla
    zip_path = None
    try:
        zip_path = _zip_reports(excels, device)
    except Exception as e:
        print(f"[NOTIFY] Rapor dosyalari toplanamadi: {e}")

    _send_email(body)             # mail: yalnızca metin (dosyasız)
    _send_telegram(body, zip_path)  # telegram: metin + TEK zip
    # Gönderim sonrası geçici zip'i temizle
    if zip_path:
        try:
            os.remove(zip_path)
        except OSError:
            pass


def _send_email(body: str):
    """Tamamlanma metnini TO/CC adreslerine mail olarak gönderir (yalnızca metin, ek YOK)."""
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


def _send_telegram(body: str, zip_path: Optional[str]):
    """Tamamlanma metnini Telegram grubuna, ardından TEK rapor zip'ini gönderir
    (50 MB üstü ise gönderilmez, yerine uyarı mesajı atılır — dosyalar FTP + logs/'ta var)."""
    try:
        notify.send_telegram(body)
        if not zip_path or not os.path.exists(zip_path):
            print("[NOTIFY] Gonderilecek rapor zip'i yok (yalniz metin gonderildi).")
            return
        basename = os.path.basename(zip_path)
        try:
            size = os.path.getsize(zip_path)
        except OSError:
            size = 0
        if size > TELEGRAM_DOC_LIMIT:
            msg = (
                f"⚠️ <b>{basename}</b> {size / 1024 / 1024:.1f} MB — Telegram 50 MB "
                f"sinirini astigi icin gonderilemedi.\nRaporlar FTP sunucusunda ve "
                f"sunucunun <code>logs/</code> klasorunde mevcut."
            )
            print(f"[NOTIFY] Zip cok buyuk ({size} byte), Telegram'a yuklenmiyor.")
            try:
                notify.send_telegram(msg)
            except Exception as e:
                print(f"[NOTIFY] Buyuk-dosya uyarisi gonderilemedi: {e}")
            return
        try:
            notify.send_document(zip_path, caption=f"[RAPORLAR] {basename}")
            print("[NOTIFY] Telegram rapor zip'i gonderildi.")
        except Exception as e:
            print(f"[NOTIFY] Telegram zip gonderim hatasi: {e}")
    except Exception as e:
        print(f"[NOTIFY] Telegram bildirim hatasi: {e}")
