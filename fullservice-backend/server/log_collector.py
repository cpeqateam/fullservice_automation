"""
Log toplayıcı — agent'lardan HTTP ile yüklenen log dosyalarını, GELDİĞİ
BİLGİSAYARIN klasörü altına yazar (kullanıcı isteri):

    logs/<LOG_NAME>/<session_id>/<dosya>

LOG_NAME her düğümün config.json'daki `log_name` değeridir:
    server→LINUX, mac_cable→MAC_ETH, mac_wifi→MAC_WIFI, win_wifi→WIN_WIFI

(Sunucunun kendi yerel testleri de orchestrator üzerinden aynı yapıya yazar.)
Faz 5'te bu klasörler FTP + DB'ye gönderilecek.
"""
import os
import shutil

from common.config import LOGS_DIR, load_config, node_log_folder

_CONFIG = load_config()


def node_session_dir(node_id: str, session_id: str) -> str:
    """logs/<LOG_NAME>/<session_id> yolunu döner."""
    folder = node_log_folder(node_id, _CONFIG)
    return os.path.join(LOGS_DIR, folder, session_id or "adhoc")


def save_upload(node_id: str, session_id: str, filename: str, fileobj) -> str:
    """Yüklenen dosyayı logs/<LOG_NAME>/<session>/ altına kaydeder, hedef yolu döner."""
    dest_dir = node_session_dir(node_id, session_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(filename))
    with open(dest, "wb") as out:
        shutil.copyfileobj(fileobj, out)
    print(f"[LOG] Toplandi: {dest}")
    return dest


def list_session_files(session_id: str) -> list[str]:
    """Bir oturuma ait, tüm bilgisayar klasörlerindeki log dosyalarının yollarını döner."""
    found = []
    if not os.path.isdir(LOGS_DIR):
        return found
    for node_folder in os.listdir(LOGS_DIR):
        sdir = os.path.join(LOGS_DIR, node_folder, session_id or "adhoc")
        if os.path.isdir(sdir):
            for dirpath, _, files in os.walk(sdir):
                for fn in files:
                    found.append(os.path.join(dirpath, fn))
    return found
