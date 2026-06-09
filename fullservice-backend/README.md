# FULL Servis — Backend (FastAPI)

Türk Telekom CPE QA ekibi için **dağıtık modem stres test** sisteminin sunucu
ve agent tarafı. 4 düğümden eşzamanlı yük bindirerek modeme **abanır**; modem
hata vermeden dayanırsa firmware başarılı sayılır.

Frontend (Vue 3 + Vuetify 3): kardeş klasör [`../fullservice-frontend/`](../fullservice-frontend/)

## Mimari (özet)

```
        ┌──────── LINUX SUNUCU (orkestratör) ────────┐
        │  FastAPI :8770                              │
        │  • Düğüm registry + merkezi progress         │
        │  • /api/session/start  → tüm düğümlere fan-out│
        │  • /api/state          → dashboard polling   │
        │  • /api/logs/upload    → log toplama         │
        │  • iperf3 server                             │
        │  • Yerel testler: ping, youtube              │
        └──┬──────────────┬──────────────┬────────────┘
   HTTP    │              │              │
        ┌──▼─┐         ┌──▼─┐         ┌──▼─┐
        │MAC │         │WIN │         │MAC │   agent (FastAPI :8771+)
        │kbl │         │WiFi│         │WiFi│
        └────┘         └────┘         └────┘
```

Detaylı akış için repo kökündeki [`MIMARI.md`](../MIMARI.md).

## Klasör yapısı

```
fullservice-backend/
├── config.json              # 4 düğüm topolojisi + varsayılan test parametreleri
├── requirements.txt
├── run_server.py            # python run_server.py
├── run_agent.py             # python run_agent.py <node_id> [server_url] [port]
├── common/                  # ortak: protokol + cross-platform test runner'lar
│   ├── config.py            #   config.json okuyucu, dashboard path, LAN IP tespiti
│   ├── protocol.py          #   sunucu↔agent HTTP sözleşmesi (pydantic)
│   └── runners/             #   her test tipi için ayrı runner modülü
│       ├── base.py          #     ortak: RunContext, ProgressCb, NO_WINDOW
│       ├── ping_runner.py   #     ping_internet + ping_modem
│       ├── youtube_runner.py
│       ├── iperf_runner.py
│       ├── torrent_runner.py     (Faz 4: simülasyon)
│       ├── wifi_track_runner.py  (Faz 4: simülasyon)
│       └── registry.py      #     TestType → runner eşlemesi
├── agent/                   # Mac/Windows client uygulaması (FastAPI)
│   ├── main.py              #   /start, /stop, /health + registration loop
│   └── test_executor.py     #   thread'li runner yürütücüsü + push/upload
└── server/                  # Linux orkestratör (FastAPI)
    ├── main.py              #   tüm /api/* endpoint'leri
    ├── orchestrator.py      #   registry + aggregator + fan-out + yerel testler
    ├── iperf_server.py      #   iperf3 -s yaşam döngüsü
    └── log_collector.py     #   yüklenen logları logs/<session>/<node>/ altına yazar
```

## Kurulum

Her makinede (sunucu + 3 client) **Python 3.10+** ve:

```bash
# Sanal ortam (yeni Ubuntu ve genel iyi pratik)
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

pip install -r requirements.txt

# iperf testleri için:
#   Linux : sudo apt install iperf3
#   macOS : brew install iperf3
#   Windows ARM : binary indirilip PATH'e eklenir
```

## Çalıştırma

### 1. `config.json` — 4 düğüm + varsayılanlar
```json
{
  "server":   { "host": "0.0.0.0", "port": 8770, "lan_ip": "192.168.x.x" },
  "agent_port": 8771,
  "defaults": { "modem_ip": "192.168.1.1", "internet_ip": "8.8.8.8",
                "youtube_link": "...", "iperf_port": 5201, "iperf_parallel": 4,
                "duration": 60 },
  "nodes":    [ { "id": "server",    "is_server": true,  "roles": ["ping_internet","ping_modem","youtube"] },
                { "id": "mac_cable", "roles": ["youtube","ping_modem","ping_internet","iperf"] },
                { "id": "win_wifi",  "roles": ["youtube","ping_modem","ping_internet","torrent","wifi_track"] },
                { "id": "mac_wifi",  "roles": ["youtube","ping_modem","ping_internet","iperf","wifi_track"] } ]
}
```

`lan_ip`'i Linux sunucunun gerçek LAN IP'siyle değiştir.

### 2. Sunucu (Linux)
```bash
python run_server.py
# http://<lan_ip>:8770 üzerinden API + dashboard (build varsa)
```

### 3. Agent (her client)
```bash
# Mac (kablo)
python run_agent.py mac_cable http://<lan_ip>:8770

# Mac (Wi-Fi) — aynı host'ta 2. agent için farklı port
FS_AGENT_PORT=8772 python run_agent.py mac_wifi http://<lan_ip>:8770

# Windows (Wi-Fi)
python run_agent.py win_wifi http://<lan_ip>:8770
```

Agent açılışta sunucuya kayıt olur, 10 sn'de bir heartbeat gönderir. Sunucu
"FULL Servis Başlat" komutu verince ataması olan testleri yerelde paralel
thread'lerde koşar, ilerlemeyi 1 sn'de bir sunucuya push eder, biten testin
log dosyasını sunucuya HTTP upload eder.

## API uçları (`http://<sunucu>:8770/api`)

| Method | URL                 | Kullanım                                              |
|--------|---------------------|-------------------------------------------------------|
| POST   | `/register`         | Agent kaydı / heartbeat                               |
| POST   | `/progress`         | Agent → sunucu ilerleme bildirimi                     |
| POST   | `/logs/upload`      | Agent → sunucu log dosyası yükleme (multipart)        |
| GET    | `/state`            | Birleşik durum (dashboard 1 sn polling)               |
| POST   | `/session/start`    | Testi başlat (opsiyonel override gövde)               |
| POST   | `/session/stop`     | Testi durdur                                          |
| GET    | `/health`           | Sağlık kontrolü                                       |

## Şu anki durum (Faz 1–3)

| Parça | Durum |
|------|------|
| Sunucu↔agent kayıt/komut/progress/log upload | ✅ gerçek |
| 4 düğümlü canlı dashboard (Vue 3 + Vuetify) | ✅ gerçek |
| ping (internet/modem), youtube | ✅ gerçek |
| iperf3 (Linux server + Mac client) | ✅ gerçek |
| torrent, wifi_track | 🟡 simülasyon (Faz 4: gerçek) |
| Log → FTPS + PostgreSQL + bildirim | ⏳ Faz 5 |
| Cross-platform paketleme (kurulum kolaylığı) | ⏳ Faz 6 |

## Yol haritası

- **Faz 4:** torrent (qBittorrent Web API), wifi_track (platforma özgü WLAN okuma + Excel); 2 Mac iperf için çoklu port.
- **Faz 5:** oturum bitince `logs/<session>/` → FTPS + PostgreSQL (SSL) + mail/Telegram. Sertifika ve kimlik bilgileri ortam değişkeniyle taşınır (kod içinde değil).
- **Faz 6:** her makinede systemd / Windows service / launchd ile agent'ı kalıcı çalıştırma.

## Güvenlik notu
Bu repoda **hiçbir** üretim kimlik bilgisi (DB şifresi, FTP parolası, sertifika,
mail/Telegram token) yer almaz. Faz 5'e geçildiğinde tüm sırlar `.env` /
ortam değişkenleri üzerinden taşınacak; bu repoda asla commit'lenmez.
