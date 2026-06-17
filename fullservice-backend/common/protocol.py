"""
Sunucu ↔ Agent HTTP sözleşmesi (pydantic modeller) + ortak sabitler.

Bu modül, dağıtık sistemin "dili"dir: hangi test tipleri var, agent sunucuya
nasıl kayıt olur, sunucu agent'a nasıl "başlat" der, agent ilerlemeyi nasıl
bildirir. Hem server/ hem agent/ bunu import eder.

GRK'da progress tek makinede bir dict'ti; burada her mesaj ağ üzerinden
gittiği için tipli (pydantic) modellerle taşınır.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class TestType(str, Enum):
    """FULL Servis'te koşulabilen test tipleri (düğüm rolleri bunlardan oluşur)."""
    PING_INTERNET = "ping_internet"
    PING_MODEM = "ping_modem"
    YOUTUBE = "youtube"
    IPERF_SERVER = "iperf_server"   # kablolu Mac: iperf3 -s (dinler)
    IPERF = "iperf"                 # wifi Mac: iperf3 -c (kablolu Mac'e yük basar)
    TORRENT = "torrent"
    WIFI_TRACK = "wifi_track"


# İnsan-okunur etiketler (dashboard'da gösterim için)
TEST_LABELS: Dict[str, str] = {
    "ping_internet": "Ping → İnternet",
    "ping_modem": "Ping → Modem",
    "youtube": "YouTube",
    "iperf_server": "iperf (Server)",
    "iperf": "iperf (Client)",
    "torrent": "Torrent",
    "wifi_track": "Wi-Fi Track",
}


class TestStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


# ─────────────────────────────────────────────────────────────
# Agent → Sunucu: kayıt
# ─────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    """Agent açılışta sunucuya kendini tanıtır."""
    node_id: str               # config.json'daki düğüm id'si (ör. "mac_cable")
    hostname: str
    platform: str              # "Windows" | "Darwin" | "Linux"
    ip: str                    # agent'ın LAN IP'si (sunucu komut göndermek için kullanır)
    agent_port: int            # agent'ın dinlediği port


# ─────────────────────────────────────────────────────────────
# Sunucu → Agent: test başlat / durdur
# ─────────────────────────────────────────────────────────────
class TestParams(BaseModel):
    """Tüm testlerin ihtiyaç duyabileceği parametreler (tek pakette taşınır)."""
    modem_ip: str = "192.168.1.1"
    internet_ip: str = "8.8.8.8"
    youtube_link: str = ""
    iperf_server: str = ""     # Client Mac buraya bağlanır = iperf server rolündeki (kablolu) Mac'in LAN IP'si
    iperf_port: int = 5201
    iperf_parallel: int = 4
    torrent_magnet: str = ""   # Windows torrent testi için magnet link (qBittorrent'e eklenir)
    duration: int = 60         # saniye (ping paket sayısı / test süresi)
    extra: Dict[str, Any] = {}


class StartCommand(BaseModel):
    """Sunucunun bir agent'a gönderdiği başlatma komutu."""
    session_id: str
    tests: List[str]           # bu düğümün koşacağı TestType değerleri
    params: TestParams


# ─────────────────────────────────────────────────────────────
# Agent → Sunucu: ilerleme bildirimi
# ─────────────────────────────────────────────────────────────
class ProgressUpdate(BaseModel):
    """Agent, bir testin anlık durumunu sunucuya iter (saniyede ~1 kez)."""
    node_id: str
    session_id: str
    task: str                  # TestType değeri
    progress: float            # 0..100
    status: str                # TestStatus değeri
    message: str = ""
    details: Optional[Any] = None
