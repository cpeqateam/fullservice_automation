"""
Log toplayıcı — agent'lardan HTTP ile yüklenen log dosyalarını oturum klasörüne
yazar. Tüm düğümlerin logları tek yerde toplanır:

    logs/<session_id>/<node_id>/<dosya>

(Sunucunun kendi yerel testleri de aynı yapıya RunContext üzerinden yazar.)
Faz 5'te bu oturum klasörü FTP + DB'ye gönderilecek.
"""
import os
import shutil

from common.config import LOGS_DIR


def session_dir(session_id: str) -> str:
    return os.path.join(LOGS_DIR, session_id or "adhoc")


def save_upload(node_id: str, session_id: str, filename: str, fileobj) -> str:
    """Yüklenen dosyayı logs/<session>/<node>/ altına kaydeder, hedef yolu döner."""
    dest_dir = os.path.join(session_dir(session_id), node_id or "unknown")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(filename))
    with open(dest, "wb") as out:
        shutil.copyfileobj(fileobj, out)
    print(f"[LOG] Toplandi: {dest}")
    return dest


def list_session_files(session_id: str) -> list[str]:
    """Bir oturuma ait toplanmış tüm log dosyalarının yollarını döner."""
    root = session_dir(session_id)
    found = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            found.append(os.path.join(dirpath, fn))
    return found
