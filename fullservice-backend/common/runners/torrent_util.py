"""
qBittorrent Web API yardımcıları — FULL Servis torrent testi için.

GRK'daki `utils/pc_control/gbtorrent.py` mantığının sadeleştirilmiş portudur:
qBittorrent'i (kapalıysa) başlatır, Web UI'ye (http://127.0.0.1:8080) giriş yapar,
magnet ekler, tamamlanınca dosyaları silip yeniden ekleyerek sürekli indirme ile
modeme yük bindirir. Stres testi olduğu için indirme hız limiti UYGULANMAZ
(GRK'daki speedtest tabanlı limit atlandı — tam hız = daha çok yük).

Web UI kimlik bilgileri (kullanıcı isteri): admin / Admin123, port 8080.
Yalnızca Windows düğümünde (win_wifi) kullanılır.
"""
import os
import platform
import shutil
import socket
import subprocess
import sys
import time

import requests

NO_WINDOW = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

if sys.platform == "win32":
    import winreg


def find_qbittorrent_exe() -> str:
    """qbittorrent.exe yolunu bulur (ENV → PATH → Registry → bilinen klasörler)."""
    env = os.environ.get("QBTORRENT_PATH")
    if env and os.path.exists(env):
        return env

    path = shutil.which("qbittorrent.exe") or shutil.which("qbittorrent")
    if path:
        return path

    if sys.platform == "win32":
        uninstall_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for subkey in uninstall_keys:
                try:
                    reg = winreg.OpenKey(hive, subkey)
                except OSError:
                    continue
                for i in range(winreg.QueryInfoKey(reg)[0]):
                    try:
                        sub = winreg.OpenKey(reg, winreg.EnumKey(reg, i))
                        display = winreg.QueryValueEx(sub, "DisplayName")[0]
                        if "qBittorrent" in display:
                            try:
                                loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
                            except FileNotFoundError:
                                loc = None
                            if loc:
                                exe = os.path.join(loc, "qbittorrent.exe")
                                if os.path.exists(exe):
                                    return exe
                    except OSError:
                        continue

        for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if pf:
                exe = os.path.join(pf, "qBittorrent", "qbittorrent.exe")
                if os.path.exists(exe):
                    return exe

    return "qbittorrent.exe"


def wait_for_qbittorrent_ui(host="127.0.0.1", port=8080, timeout=30) -> bool:
    """Web UI portu açılana kadar (timeout) bekler."""
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            if time.time() - start > timeout:
                return False
            time.sleep(1)


def ensure_qbittorrent_running():
    """qBittorrent çalışmıyorsa başlatır ve Web UI'nin açılmasını bekler."""
    try:
        import psutil
        already = any(
            "qbittorrent" in (p.info.get("name") or "").lower()
            for p in psutil.process_iter(["name"])
        )
    except Exception:
        already = False

    if already:
        wait_for_qbittorrent_ui()
        return

    exe = find_qbittorrent_exe()
    try:
        subprocess.Popen([exe], creationflags=NO_WINDOW)
    except Exception as e:
        print(f"[TORRENT] qBittorrent baslatilamadi ({exe}): {e}")
        return
    wait_for_qbittorrent_ui()


def login_qbittorrent(qb_url, username, password):
    """Web UI'ye giriş yapar; başarılıysa requests.Session, değilse None döner."""
    session = requests.Session()
    try:
        resp = session.post(f"{qb_url}/api/v2/auth/login",
                            data={"username": username, "password": password},
                            timeout=10)
    except Exception as e:
        print(f"[TORRENT] Web UI'ye baglanilamadi: {e}")
        return None
    if resp.ok and resp.text.strip() == "Ok.":
        return session
    print(f"[TORRENT] Giris basarisiz: {resp.text}")
    return None


def add_torrent(session, qb_url, magnet):
    """Magnet linki qBittorrent'e ekler."""
    try:
        resp = session.post(f"{qb_url}/api/v2/torrents/add", data={"urls": magnet}, timeout=15)
        return resp.ok
    except Exception as e:
        print(f"[TORRENT] Ekleme hatasi: {e}")
        return False


def list_torrents(session, qb_url):
    """Eklenmiş torrentlerin listesini (info) döner."""
    try:
        resp = session.get(f"{qb_url}/api/v2/torrents/info", timeout=10)
        if resp.ok:
            return resp.json()
    except Exception as e:
        print(f"[TORRENT] info hatasi: {e}")
    return []


def remove_torrent_and_files(session, qb_url):
    """Tamamlanan (%100) torrentleri ve indirilen dosyaları siler."""
    for t in list_torrents(session, qb_url):
        if t.get("progress") == 1.0:
            try:
                session.post(f"{qb_url}/api/v2/torrents/delete",
                             data={"hashes": t["hash"], "deleteFiles": "true"}, timeout=10)
            except Exception as e:
                print(f"[TORRENT] silme hatasi: {e}")
