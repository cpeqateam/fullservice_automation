"""
Merkezi yapılandırma okuyucu — config.json'u bulur, okur ve yardımcılar sunar.

Hem sunucu hem agent bu modülü kullanır. GRK'daki config.py'nin (yol sabitleri)
dağıtık karşılığıdır; ek olarak 4 düğümlü topolojiyi ve varsayılan test
parametrelerini tutar.

İKİ ÇALIŞMA MODU (aynı kod, farklı yol çözümü):

  1) KAYNAKTAN (geliştirme):  python run_server.py / run_agent.py
     Kök = bu dosyanın iki üst klasörü (fullservice-backend/).

  2) PAKETLENMİŞ (son kullanıcı): PyInstaller ile üretilen tek dosya uygulama.
     Kod ve dashboard exe'nin İÇİNDE (sys._MEIPASS), ama ayar/log/sertifika
     exe'nin YANINDA durur — böylece USB ile güncellenebilir, sır exe'ye gömülmez:

         FULLSERVIS/
         ├── FULLSERVIS-SUNUCU(.exe)      ← çift tıklanan uygulama
         ├── ayarlar/                     ← DIŞ ayarlar (varsa öncelikli)
         │   ├── config.json
         │   ├── secrets.json
         │   └── certs/
         └── logs/                        ← uygulama burayı kendisi oluşturur

Arama sırası her dosya için: ortam değişkeni → exe yanındaki `ayarlar/` →
exe yanındaki kök → uygulamanın içine gömülü kopya → kaynak ağacı.
"""
from __future__ import annotations

import json
import os
import socket
import sys

# Bu dosya: <kök>/common/config.py  →  kaynaktan çalışırken kök = iki üst klasör.
# Paketlenmiş modda bu yol exe'nin açıldığı geçici klasördür (sys._MEIPASS).
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IS_FROZEN = bool(getattr(sys, "frozen", False))


def app_dir() -> str:
    """Uygulamanın YANINDAKİ (kalıcı, yazılabilir) klasör.

    Paketlenmiş modda çalıştırılabilir dosyanın bulunduğu klasördür; macOS `.app`
    paketinde `Contents/MacOS` içinden çıkılıp `.app`'in bulunduğu klasör döner.
    Kaynaktan çalışırken proje köküdür (fullservice-backend/)."""
    if not IS_FROZEN:
        return _BASE_DIR
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    # .../FULLSERVIS-MAC-WIFI.app/Contents/MacOS  →  .app'in bulunduğu klasör
    parts = exe_dir.replace("\\", "/").split("/")
    if len(parts) >= 3 and parts[-1] == "MacOS" and parts[-2] == "Contents":
        return os.path.dirname(os.path.dirname(os.path.dirname(exe_dir)))
    return exe_dir


APP_DIR = app_dir()
# Dış ayar klasörü — son kullanıcıda uygulamanın yanında durur (USB ile güncellenir)
SETTINGS_DIR = os.path.join(APP_DIR, "ayarlar")


def _first_existing(*candidates: str) -> str | None:
    """Verilen yollardan var olan İLKİNİ döner; hiçbiri yoksa None."""
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def resolve_path(name: str, default_dir: str | None = None) -> str:
    """Bir ayar dosyası/klasörünü arama sırasına göre çözer:
    exe yanındaki `ayarlar/` → exe yanındaki kök → uygulamaya gömülü kopya →
    kaynak ağacı. Hiçbiri yoksa (yazılacaksa) `default_dir` altındaki yolu döner."""
    found = _first_existing(
        os.path.join(SETTINGS_DIR, name),
        os.path.join(APP_DIR, name),
        os.path.join(_BASE_DIR, name),
    )
    return found or os.path.join(default_dir or APP_DIR, name)


CONFIG_PATH = os.environ.get("FULLSERVICE_CONFIG") or resolve_path("config.json")

# Loglar UYGULAMANIN YANINDA toplanır (paketlenmiş modda exe'nin içi salt-okunurdur):
# sunucu → tüm düğümlerin logları; agent → kendi logları.
LOGS_DIR = os.environ.get("FS_LOGS_DIR") or os.path.join(APP_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Dashboard statik dosyaları — Vue 3 + Vuetify build çıktısı (sunucu sunar).
# Paketlenmiş modda uygulamanın İÇİNE gömülür (_MEIPASS/dashboard). Kaynaktan
# çalışırken kardeş klasör `fullservice-frontend/dist`, yoksa `dashboard_dist/`.
# Hiçbiri yoksa sunucu sadece API döner (geliştirmede Vite ayrı portta çalışır).
_REPO_ROOT = os.path.dirname(_BASE_DIR)
DASHBOARD_DIR = (
    _first_existing(
        os.path.join(_BASE_DIR, "dashboard"),                       # exe içine gömülü
        os.path.join(_REPO_ROOT, "fullservice-frontend", "dist"),   # kaynak ağacı
        os.path.join(_BASE_DIR, "dashboard_dist"),                  # elle kopyalanmış
    )
    or os.path.join(_BASE_DIR, "dashboard_dist")
)

# Sertifikalar (FTP + DB). Önce ayarlar/certs, sonra uygulama yanı, sonra kaynak ağacı.
CERT_DIR = resolve_path("certs")


# Sırlar (Telegram token, SMTP şifresi vb.) — ASLA repoya/exe'ye konmaz. Önce ortam
# değişkeni, yoksa gitignore'lu secrets.json'dan okunur. Hiçbiri yoksa boş döner.
_SECRETS_PATH = resolve_path("secrets.json")
_secrets_cache: dict | None = None


def get_secret(key: str, default: str = "") -> str:
    """Sır değerini getirir: önce ortam değişkeni, sonra secrets.json, sonra default."""
    val = os.environ.get(key)
    if val:
        return val
    global _secrets_cache
    if _secrets_cache is None:
        try:
            with open(_SECRETS_PATH, "r", encoding="utf-8") as f:
                _secrets_cache = json.load(f)
        except Exception:
            _secrets_cache = {}
    v = _secrets_cache.get(key, default)
    return v if v is not None else default


def load_config() -> dict:
    """config.json'u okuyup dict döner. Dosya yoksa makul varsayılanlarla çalışır."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[CONFIG] {CONFIG_PATH} bulunamadi, gomulu varsayilanlar kullaniliyor.")
        return _FALLBACK
    except Exception as e:
        print(f"[CONFIG] config.json okunamadi ({e}), gomulu varsayilanlar kullaniliyor.")
        return _FALLBACK


def get_node(config: dict, node_id: str) -> dict | None:
    """Topolojiden node_id'ye karşılık gelen düğüm tanımını döner."""
    for node in config.get("nodes", []):
        if node.get("id") == node_id:
            return node
    return None


def node_log_folder(node_id: str, config: dict | None = None) -> str:
    """
    Bir düğümün, Linux sunucudaki log klasör adını döner (config'deki `log_name`;
    yoksa node_id'nin büyük harfli hali). Sunucuda loglar şu yapıya yazılır:
        logs/<log_name>/<session_id>/<dosya>
    Örn: server→LINUX, mac_cable→MAC_ETH, mac_wifi→MAC_WIFI, win_wifi→WIN_WIFI.
    """
    if config is None:
        config = load_config()
    node = get_node(config, node_id)
    if node and node.get("log_name"):
        return node["log_name"]
    return (node_id or "UNKNOWN").upper()


# ─────────────────────────────────────────────────────────────────────────────
# Agent kimliği — paketlenmiş uygulama "hangi bilgisayardayım"ı kendisi bulur
# ─────────────────────────────────────────────────────────────────────────────
# Her makineye O MAKİNEYE AİT isimli uygulama konur; node_id uygulamanın DOSYA
# ADINDAN çözülür. Böylece son kullanıcı ne parametre yazar ne ayar dosyası açar:
#     FULLSERVIS-MAC-WIFI(.exe/.app)      → mac_wifi
#     FULLSERVIS-MAC-KABLO(.exe/.app)     → mac_cable
#     FULLSERVIS-WINDOWS-WIFI.exe         → win_wifi
# Dosya adı değiştirilirse diye `ayarlar/agent.json` ve FS_NODE_ID hâlâ geçerlidir.
_NODE_ALIASES = {
    "mac_wifi":  ("macwifi", "macwireless", "macwlan"),
    "mac_cable": ("mackablo", "maceth", "maccable", "macethernet", "mackablolu"),
    "win_wifi":  ("winwifi", "windowswifi", "windows", "win"),
    "server":    ("sunucu", "linux", "server"),
}


def _normalize(text: str) -> str:
    """Karşılaştırma için sadeleştirir: küçük harf + harf/rakam dışını at
    ('FULLSERVIS-MAC-WIFI.exe' → 'fullservismacwifiexe')."""
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def load_agent_settings() -> dict:
    """Uygulamanın yanındaki `ayarlar/agent.json`'u okur (yoksa boş sözlük).
    İçerik: {"node_id": "...", "server_url": "http://...:8770", "agent_port": 7531}"""
    path = _first_existing(
        os.path.join(SETTINGS_DIR, "agent.json"),
        os.path.join(APP_DIR, "agent.json"),
    )
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        print(f"[CONFIG] agent.json okunamadi ({e}), yok sayiliyor.")
        return {}


def node_id_from_name(name: str, config: dict | None = None) -> str | None:
    """Bir dosya/uygulama adından node_id çözer (en uzun eşleşme kazanır).
    Örn: 'FULLSERVIS-MAC-KABLO.exe' → 'mac_cable'. Eşleşme yoksa None."""
    norm = _normalize(name)
    if not norm:
        return None
    config = config if config is not None else load_config()

    # Her düğüm için aday etiketler: node id, log_name ve elle yazılmış eş adlar
    candidates: list[tuple[str, str]] = []          # (etiket, node_id)
    for node in config.get("nodes", []):
        nid = node.get("id", "")
        for label in (nid, node.get("log_name", "")) + _NODE_ALIASES.get(nid, ()):
            if label:
                candidates.append((_normalize(label), nid))

    # Uzun etiketten kısaya bak: 'macwifi' varken 'mac' yanlış eşleşmesin
    for label, nid in sorted(candidates, key=lambda c: -len(c[0])):
        if label and label in norm:
            return nid
    return None


def resolve_node_id(explicit: str | None = None, config: dict | None = None) -> str | None:
    """Bu makinenin node_id'sini şu sırayla çözer:
       1) açıkça verilen değer (komut satırı argümanı)
       2) FS_NODE_ID ortam değişkeni
       3) `ayarlar/agent.json` içindeki "node_id"
       4) çalıştırılan uygulamanın/scriptin DOSYA ADI
    Hiçbiri çözülemezse None döner (çağıran anlaşılır bir hata gösterir)."""
    config = config if config is not None else load_config()
    known = {n.get("id") for n in config.get("nodes", [])}

    for value in (explicit, os.environ.get("FS_NODE_ID"), load_agent_settings().get("node_id")):
        if value:
            value = value.strip()
            if value in known:
                return value
            print(f"[CONFIG] Bilinmeyen node_id '{value}' yok sayildi.")

    exe_name = os.path.basename(sys.executable if IS_FROZEN else sys.argv[0])
    return node_id_from_name(exe_name, config)


def resolve_server_url(config: dict | None = None) -> str:
    """Agent'ın kaydolacağı sunucu adresini çözer: FS_SERVER_URL → `ayarlar/agent.json`
    → config.json'daki server.lan_ip:port. Son kullanıcıda genelde config.json yeter."""
    env = os.environ.get("FS_SERVER_URL")
    if env:
        return env.rstrip("/")
    from_settings = load_agent_settings().get("server_url")
    if from_settings:
        return str(from_settings).rstrip("/")
    config = config if config is not None else load_config()
    srv = config.get("server", {})
    return f"http://{srv.get('lan_ip', '127.0.0.1')}:{srv.get('port', 8770)}"


def detect_lan_ip() -> str:
    """
    Makinenin yerel ağ (LAN) IP'sini tahmin eder. iperf server adresi ve agent'ın
    kendini sunucuya bildirmesi için kullanılır. Dış bağlantı kurmaz, sadece
    yönlendirme tablosundan hangi arayüzün kullanılacağını öğrenir.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


# config.json hiç yoksa diye gömülü yedek (config.json ile aynı olmalı)
_FALLBACK = {
    "server": {"host": "0.0.0.0", "port": 8770, "lan_ip": detect_lan_ip()},
    "agent_port": 7531,
    "network": {
        "subnet_mask": "255.255.255.0",
        "gateway": "192.168.1.1",
        "dns": ["8.8.8.8", "8.8.4.4"],
        "assignments": {
            "server":    {"ip": "192.168.1.10", "interface": "eth0"},
            "mac_cable": {"ip": "192.168.1.11", "interface": "Ethernet"},
            "win_wifi":  {"ip": "192.168.1.13", "interface": "Wi-Fi"},
            "mac_wifi":  {"ip": "192.168.1.14", "interface": "Wi-Fi"},
        },
    },
    "defaults": {
        "modem_ip": "192.168.1.1",
        "internet_ip": "8.8.8.8",
        "youtube_link": "https://youtu.be/uXNU0XgGZhs",
        "iperf_port": 5201,
        "iperf_parallel": 4,
        "torrent_magnet": "",
        "torrent_recycle_gb": 5,
        "duration": 60,
    },
    "nodes": [
        {"id": "server", "label": "Linux Sunucu (Kablo)", "conn": "cable", "is_server": True,
         "log_name": "LINUX",
         "roles": ["ping_internet", "ping_modem", "youtube"]},
        {"id": "mac_cable", "label": "MAC (Kablo)", "conn": "cable",
         "log_name": "MAC_ETH",
         "roles": ["youtube", "ping_modem", "ping_internet", "iperf_server"]},
        {"id": "win_wifi", "label": "WINDOWS (Wi-Fi)", "conn": "wifi",
         "log_name": "WIN_WIFI",
         "roles": ["youtube", "ping_modem", "ping_internet", "torrent", "wifi_track"]},
        {"id": "mac_wifi", "label": "MAC (Wi-Fi)", "conn": "wifi",
         "log_name": "MAC_WIFI",
         "roles": ["youtube", "ping_modem", "ping_internet", "iperf", "wifi_track"]},
    ],
}
