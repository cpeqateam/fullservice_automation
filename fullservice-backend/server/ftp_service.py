"""
FTP yükleme servisi (FULL Servis, sunucu tarafı) — toplanan log dosyalarını
FTP sunucusuna aktarır.

GRK app/services/ftp_service.py'nin portudur (aynı sunucu, aynı bağlantı mantığı:
önce TLS, olmazsa düz FTP; hedef klasör katman katman otomatik oluşturulur).

Klasör şeması (kullanıcı isteri):
  <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<Bilgisayar>/
örn:
  ZYXEL/EX5601/v1.0/FULLSERVIS/Ping/MAC_WIFI/
  ZYXEL/EX5601/v1.0/FULLSERVIS/Iperf/MAC_WIFI/
  ZYXEL/EX5601/v1.0/FULLSERVIS/Wifi/WIN_WIFI/

TestTipi: Ping / Iperf / Wifi / Youtube / Torrent (log dosya adından çözülür)
Bilgisayar: node'un log adı (LINUX / MAC_ETH / MAC_WIFI / WIN_WIFI)

NOT: Hedef klasörler ilk yüklemede _ensure_dir_recursive ile OTOMATİK oluşturulur;
FTP sunucusunda elle klasör açmaya GEREK YOK (FTP kullanıcısının MKD yetkisi olmalı —
GRK zaten klasör açtığı için bu yetki mevcut).
"""
from __future__ import annotations

import os
import re
import ssl
import threading
from ftplib import FTP_TLS, FTP

from common.config import CERT_DIR

# GRK ile aynı FTP sunucusu. Ortam değişkeniyle override edilebilir.
FTP_ADDRESSES = os.environ.get("FS_FTP_ADDRESSES", "78.186.148.93,192.168.1.44").split(",")
FTP_PORT = int(os.environ.get("FS_FTP_PORT", "4421"))
FTP_USER = os.environ.get("FS_FTP_USER", "testuser")
FTP_PASS = os.environ.get("FS_FTP_PASS", "testpass")


# ── Hedef klasör yolu yardımcıları ──────────────────────────────────────
def _san(s) -> str:
    """FTP klasör adı için güvenli hale getir (boşsa Unknown, sorunlu karakterleri _)."""
    s = (str(s).strip() if s is not None else "") or "Unknown"
    return re.sub(r'[\\/:*?"<>|]+', "_", s)


def _test_type_from_token(token: str) -> str:
    """Dosya adının TEST ADI alanından test tipini çözer; tanınmazsa boş döner."""
    t = (token or "").lower()
    if t.startswith("iperf"):                      # iperf, iperfServer, iperfOzet
        return "Iperf"
    if t.startswith("ping"):                       # ping, pingOzet
        return "Ping"
    if t.startswith("wifi") or t.startswith("wlan"):   # wifiAnaliz
        return "Wifi"
    if t.startswith("youtube"):
        return "Youtube"
    if t.startswith("torrent"):
        return "Torrent"
    return ""


def test_type_from_filename(filename: str) -> str:
    """Log dosya adından test tipi klasörünü çözer (Ping/Iperf/Wifi/Youtube/Torrent).

    ÖNCE dosya adının TEST ADI alanına bakar. FULL Servis standardı (bkz.
    base.grk_style_filename):
        fullServis_<testAdi>_<bilgisayar>_<marka>_<model>_<fw>..._<ts>.<uzanti>
    Yani test adı 2. alandır. Bu şart: bilgisayar adları "macWifi"/"winWifi"
    içerdiği için, tüm ada bakan basit bir arama `..._youtube_macWifi_...` gibi
    bir dosyayı yanlışlıkla Wifi sayardı.

    Standart dışı/eski adlarda tüm ada bakan yedek arama kullanılır; orada da
    "wifi"/"wlan" EN SONA bırakılır (aynı nedenle — yalnızca gerçekten başka
    hiçbir tipe uymayan adlar Wifi sayılsın)."""
    name = os.path.basename(filename or "")
    parts = os.path.splitext(name)[0].split("_")
    if len(parts) >= 2:
        by_token = _test_type_from_token(parts[1])
        if by_token:
            return by_token

    n = name.lower()
    for key, val in (("iperf", "Iperf"), ("ping", "Ping"),
                     ("youtube", "Youtube"), ("torrent", "Torrent"),
                     ("wifi", "Wifi"), ("wlan", "Wifi")):
        if key in n:
            return val
    return "Diger"


def test_type_from_kind(kind: str) -> str:
    """DB sonuç tipinden (ping/iperf/wifi) test tipi klasörünü verir."""
    return {"ping": "Ping", "iperf": "Iperf", "wifi": "Wifi"}.get(kind, "Diger")


def build_target_dir(brand, model, firmware, test_type, node_name) -> str:
    """<MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<Bilgisayar> yolunu üretir."""
    return "/".join([
        _san(brand), _san(model), _san(firmware),
        "FULLSERVIS", _san(test_type), _san(node_name),
    ])


# ── TLS bağlantı (GRK ile aynı) ─────────────────────────────────────────
class ImplicitSessionFTP_TLS(FTP_TLS):
    """Veri kanalında kontrol kanalının TLS oturumunu yeniden kullanan FTP_TLS
    (bazı FTPS sunucuları bunu şart koşar)."""

    def ntransfercmd(self, cmd, rest=None):
        """Veri bağlantısını, kontrol kanalının TLS oturumuyla sarmalayarak açar."""
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def _make_ssl_context():
    """certs/ca.crt varsa doğrulamalı, yoksa doğrulamasız TLS bağlamı."""
    ca_crt_path = os.path.join(os.path.abspath(CERT_DIR), "ca.crt")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.options |= ssl.OP_IGNORE_UNEXPECTED_EOF
    try:
        ctx.load_verify_locations(cafile=ca_crt_path)
        ctx.verify_mode = ssl.CERT_REQUIRED
    except (FileNotFoundError, OSError):
        print(f"[FTP] ca.crt bulunamadi ({ca_crt_path}), sertifika dogrulamasi devre disi.")
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _connect_ftps_secure():
    """Adres listesini sırayla deneyerek güvenli (TLS) FTPS bağlantısı kurar; olmazsa None."""
    ctx = _make_ssl_context()
    ftps = ImplicitSessionFTP_TLS(context=ctx)
    for addr in FTP_ADDRESSES:
        addr = addr.strip()
        try:
            ftps.connect(addr, FTP_PORT, timeout=30)
            ftps.login(FTP_USER, FTP_PASS)
            ftps.set_pasv(True)
            ftps.trust_server_pasv_ipv4_address = True
            ftps.prot_p()
            print(f"[FTP] Guvenli baglanti kuruldu: {addr}")
            return ftps
        except Exception as e:
            print(f"[FTP] {addr} guvenli baglanti basarisiz: {e}")
    return None


def _connect_ftp_plain():
    """TLS kurulamazsa yedek: düz (şifresiz) FTP bağlantısı kurar; olmazsa None."""
    ftp = FTP()
    for addr in FTP_ADDRESSES:
        addr = addr.strip()
        try:
            ftp.connect(addr, FTP_PORT, timeout=10)
            ftp.login(FTP_USER, FTP_PASS)
            ftp.set_pasv(True)
            print(f"[FTP] Duz baglanti kuruldu: {addr}")
            return ftp
        except Exception as e:
            print(f"[FTP] {addr} duz baglanti basarisiz: {e}")
    return None


def _ensure_dir_recursive(ftp, dir_path: str):
    """İç içe klasör yolunu segment segment oluşturur ve hedefe cwd yapar."""
    try:
        ftp.cwd('/')
    except Exception:
        pass
    for seg in [s for s in dir_path.replace('\\', '/').split('/') if s]:
        try:
            ftp.cwd(seg)
        except Exception:
            try:
                ftp.mkd(seg)
                ftp.cwd(seg)
                print(f"[FTP] Alt dizin olusturuldu: {seg}")
            except Exception as e:
                print(f"[FTP] Alt dizin olusturulamadi ({seg}): {e}")
                raise


def upload_files_to_ftp(file_paths: list, target_dir: str):
    """Verilen dosyaları target_dir (FTP köküne göre göreli) altına yükler.
    Önce TLS, olmazsa düz FTP. Hedef klasör yoksa oluşturulur. Hata olursa
    sessizce loglar ve döner (test akışını bozmaz)."""
    if os.environ.get("FS_FTP_DISABLE"):
        print("[FTP] FS_FTP_DISABLE ayarli — yukleme atlandi.")
        return
    file_paths = [p for p in (file_paths or []) if p]
    if not file_paths:
        return

    ftp = _connect_ftps_secure() or _connect_ftp_plain()
    if ftp is None:
        print("[FTP] HATA: Hicbir sunucuya baglanilamadi (yukleme atlandi).")
        return

    try:
        try:
            _ensure_dir_recursive(ftp, target_dir)
        except Exception as e:
            print(f"[FTP] Hedef klasor hazirlanamadi ({target_dir}): {e}")
            return
        for fp in file_paths:
            if not os.path.exists(fp):
                print(f"[FTP] Dosya yok, atlandi: {fp}")
                continue
            name = os.path.basename(fp)
            try:
                with open(fp, 'rb') as f:
                    ftp.storbinary(f'STOR {name}', f, blocksize=8192)
                print(f"[FTP] Gonderildi: {target_dir}/{name}")
            except Exception as e:
                print(f"[FTP] Gonderim hatasi ({name}): {e}")
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


def upload_async(file_paths: list, target_dir: str):
    """upload_files_to_ftp'yi arka planda (daemon thread) çalıştırır — çağıran
    bloke olmasın (FTP bağlantısı yavaş olabilir)."""
    threading.Thread(
        target=upload_files_to_ftp, args=(file_paths, target_dir), daemon=True
    ).start()
