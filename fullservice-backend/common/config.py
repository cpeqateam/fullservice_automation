"""
Merkezi yapılandırma okuyucu — config.json'u bulur, okur ve yardımcılar sunar.

Hem sunucu hem agent bu modülü kullanır. config.json proje kökünde (bu dosyanın
iki üst klasörü) aranır; ortam değişkeni FULLSERVICE_CONFIG ile override edilebilir.

GRK'daki config.py'nin (yol sabitleri) dağıtık karşılığıdır; ek olarak 4 düğümlü
topolojiyi ve varsayılan test parametrelerini tutar.
"""
import json
import os
import socket

# Bu dosya: <kök>/common/config.py  →  kök = iki üst klasör
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.environ.get(
    "FULLSERVICE_CONFIG",
    os.path.join(_BASE_DIR, "config.json"),
)

# Loglar kök/logs altında toplanır (sunucu: tüm düğümlerin logları; agent: kendi logları)
LOGS_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Dashboard statik dosyaları — Vue 3 + Vuetify build çıktısı (sunucu sunar).
# Üretimde: kardeş klasör `fullservice-frontend/` içinde `npm run build` ile
# üretilen `dist/`. Yerel olarak da `fullservice-backend/dashboard_dist/`
# aranır (manuel bir build kopyalanmışsa). Bulunamazsa sunucu sadece API
# döner (geliştirme sırasında Vite ayrı port'ta çalışır, /api'yi proxy'ler).
_REPO_ROOT = os.path.dirname(_BASE_DIR)
_FRONTEND_DIST = os.path.join(_REPO_ROOT, "fullservice-frontend", "dist")
_LOCAL_DIST = os.path.join(_BASE_DIR, "dashboard_dist")
DASHBOARD_DIR = _FRONTEND_DIST if os.path.isdir(_FRONTEND_DIST) else _LOCAL_DIST

# Sertifikalar (FTP + DB için; Faz 5'te kullanılacak). Önce kök/certs, yoksa GRK'nınki.
CERT_DIR = os.path.join(_BASE_DIR, "certs")


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
        "duration": 60,
    },
    "nodes": [
        {"id": "server", "label": "Linux Sunucu (Kablo)", "conn": "cable", "is_server": True,
         "roles": ["ping_internet", "ping_modem", "youtube"]},
        {"id": "mac_cable", "label": "MAC (Kablo)", "conn": "cable",
         "roles": ["youtube", "ping_modem", "ping_internet", "iperf_server"]},
        {"id": "win_wifi", "label": "WINDOWS (Wi-Fi)", "conn": "wifi",
         "roles": ["youtube", "ping_modem", "ping_internet", "torrent", "wifi_track"]},
        {"id": "mac_wifi", "label": "MAC (Wi-Fi)", "conn": "wifi",
         "roles": ["youtube", "ping_modem", "ping_internet", "iperf", "wifi_track"]},
    ],
}
