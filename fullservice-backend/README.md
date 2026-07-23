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
        │  • /api/logs/upload + /api/result → log/DB/FTP│
        │  • Yerel testler: ping, youtube              │
        └──┬──────────────┬──────────────┬────────────┘
   HTTP    │              │              │
        ┌──▼──┐        ┌──▼─┐         ┌──▼──┐
        │MAC  │        │WIN │         │MAC  │   listener=agent (FastAPI :7531)
        │kablo│        │WiFi│         │WiFi │
        │iperf│◄───────┼────┼─────────│iperf│   iperf3: kablolu Mac -s (server),
        │ -s  │        │    │         │ -c  │              Wi-Fi Mac -c (client)
        └─────┘        └────┘         └─────┘
```

> **iperf topolojisi:** Linux sunucu artık iperf server **DEĞİL**. Kablolu Mac
> `iperf3 -s` (server), Wi-Fi Mac client olur; trafik iki Mac arasında modem üzerinden akar.

Mevcut durum + sıradaki adımlar için repo kökündeki
[`CHANGELOG.md`](../CHANGELOG.md); kod gezisi için
[`KOD_HAKIMIYETI.md`](../KOD_HAKIMIYETI.md).

## Klasör yapısı

```
fullservice-backend/
├── config.json              # 4 düğüm topolojisi + varsayılan test parametreleri
├── requirements.txt
├── run_server.py            # python run_server.py
├── run_agent.py             # python run_agent.py <node_id> [server_url] [port]
├── common/                  # ortak: protokol + cross-platform test runner'lar
│   ├── config.py            #   config.json okuyucu, dashboard path, LAN IP, get_secret
│   ├── protocol.py          #   sunucu↔agent HTTP sözleşmesi (pydantic) + ResultReport
│   ├── firmware_db.py       #   Marka/Model/Firmware okuma (PostgreSQL/SSL)
│   └── runners/             #   her test tipi için ayrı runner modülü
│       ├── base.py          #     RunContext, ProgressCb, grk_style_filename, terminal yard.
│       ├── ping_runner.py   #     ping_internet + ping_modem (istatistik → DB)
│       ├── youtube_runner.py (+youtube_util.py)
│       ├── iperf_runner.py        #  iperf3 -c (client)
│       ├── iperf_server_runner.py #  iperf3 -s (server)
│       ├── torrent_runner.py (+torrent_util.py)   # qBittorrent Web API (gerçek)
│       ├── wifi_track_runner.py (+wifi_util.py / wifi_util_mac.py)  # gerçek WLAN
│       └── registry.py      #     TestType → runner eşlemesi
├── agent/                   # Mac/Windows client uygulaması (FastAPI)
│   ├── main.py              #   /start, /stop, /health + registration loop
│   └── test_executor.py     #   thread'li runner yürütücüsü + push/upload + /api/result
└── server/                  # Linux orkestratör (FastAPI)
    ├── main.py              #   tüm /api/* endpoint'leri + stdout→app.log Tee + uptime kilidi
    ├── orchestrator.py      #   registry + aggregator + fan-out + yerel testler + check_uptime
    ├── auth_service.py      #   login (cpeteam varsayılan + grk_users)
    ├── db_service.py        #   sonuçları copy_ tablolarına yazar
    ├── ftp_service.py       #   rapor dosyalarını FTP klasör yapısına yükler
    ├── notify.py / email_sender.py / notification_service.py  # Telegram (tek ZIP) + mail
    ├── log_capture.py       #   error_log dilimi → FTP
    ├── excel_service.py     #   wifi Excel + bilgisayar başına ping özet Excel
    ├── report_service.py    #   oturum sonu: her bilgisayar için ping özeti → FTP
    └── log_collector.py     #   yüklenen logları logs/<node>/<session>/ altına yazar
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
  "agent_port": 7531,
  "network":  { "subnet_mask": "255.255.255.0", "gateway": "192.168.1.1",
                "dns": ["8.8.8.8"],
                "assignments": { "server": {"ip":"192.168.1.10","interface":"eth0"}, "...": {} } },
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
# Mac (kablo) — listener varsayılan port 7531
python run_agent.py mac_cable http://<lan_ip>:8770

# Mac (Wi-Fi) — aynı host'ta 2. agent için farklı port
FS_AGENT_PORT=7532 python run_agent.py mac_wifi http://<lan_ip>:8770

# Windows (Wi-Fi)
python run_agent.py win_wifi http://<lan_ip>:8770
```

> **Listener = agent.** Boot'ta otomatik kalkması ve makinelere statik IP atanması
> için [`provisioning/`](provisioning/README.md) altındaki script'leri kullan
> (macOS launchd · Windows Görev Zamanlayıcı · Linux systemd).

Agent açılışta sunucuya kayıt olur, 10 sn'de bir heartbeat gönderir. Sunucu
"FULL Servis Başlat" komutu verince ataması olan testleri yerelde paralel
thread'lerde koşar, ilerlemeyi 1 sn'de bir sunucuya push eder, biten testin
log dosyasını sunucuya HTTP upload eder.

## API uçları (`http://<sunucu>:8770/api`)

| Method | URL                 | Kullanım                                              |
|--------|---------------------|-------------------------------------------------------|
| POST   | `/login`            | Kullanıcı girişi (cpeteam varsayılan + grk_users)     |
| POST   | `/register`         | Agent kaydı / heartbeat                               |
| POST   | `/progress`         | Agent → sunucu ilerleme bildirimi                     |
| POST   | `/result`           | Agent → sunucu test sonuç özeti (DB'ye yazılır)       |
| POST   | `/logs/upload`      | Agent → sunucu log dosyası yükleme (multipart)        |
| GET    | `/state`            | Birleşik durum (dashboard 1 sn polling)               |
| POST   | `/session/start`    | Testi başlat (override + brand/model/firmware gövde)  |
| POST   | `/session/stop`     | Testi durdur                                          |
| POST   | `/session/reset`    | Her şeyi başa al (testler + ilerleme + health-check)  |
| GET    | `/health-check`     | Tüm düğümlerin anlık erişilebilirliği (kırmızı/yeşil) |
| GET    | `/firmware/brands`  | DB'den marka listesi (yoksa 503 → serbest metin)      |
| GET    | `/firmware/models/{brand}`          | DB'den model listesi                  |
| GET    | `/firmware/versions/{brand}/{model}`| DB'den firmware sürümleri             |
| GET    | `/health`           | Sağlık kontrolü                                       |

## Şu anki durum

| Parça | Durum |
|------|------|
| Sunucu↔agent kayıt/komut/progress/log upload | ✅ gerçek |
| 4 düğümlü canlı dashboard (Vue 3 + Vuetify) | ✅ gerçek |
| Login (cpeteam varsayılan + GRK `grk_users`) + karşılama ekranı | ✅ gerçek |
| ping (internet/modem), youtube | ✅ gerçek |
| iperf3 (kablolu Mac server + Wi-Fi Mac client) | 🟡 gerçek — sahada doğrulanıyor |
| torrent (qBittorrent), wifi_track (gerçek WLAN, RX/TX) | ✅ gerçek |
| Marka/Model/Firmware combobox (cpeqadb, GRK ile aynı; yoksa serbest metin) | ✅ gerçek |
| Aşamalı Health-Check paneli (kırmızı/yeşil ışıklar) | ✅ gerçek |
| Statik IP + boot listener paketleme (`provisioning/`) | ✅ gerçek (launchd/Task Scheduler/systemd) |
| Log → FTP yükleme (klasör yapısı) | ✅ gerçek |
| Sonuç → PostgreSQL (`copy_` staging tabloları) | ✅ gerçek — sahada doğrulanıyor |
| Tamamlanınca mail + Telegram bildirimi | ✅ gerçek |
| error_log → FTP (bildirim yok) | ✅ gerçek |

## Yol haritası

- **DB birleştirme:** `copy_` staging tabloları doğrulanınca asıl tablolara taşınacak
  (Senaryo 3: `grk_*` rename + `test_name`/`node_name` + `iperf_test`). Detay:
  [`../CHANGELOG.md`](../CHANGELOG.md).
- **Saha doğrulaması:** iperf otomatik başlatma + FTP/DB yazımı 4 fiziksel makinede test.
- **Installer:** tek-tıklık kurulum paketi (statik IP + boot autostart zaten `provisioning/`).

> **Firmware DB:** Marka/Model/Firmware combobox'ları GRK ile aynı `cpeqadb`'den
> okunur (`grk_firmware`, SSL). Sertifikalar `fullservice-backend/certs/` altında
> aranır (repoda yok). Bağlantı yoksa alanlar serbest-metin'e düşer, sistem çalışmaya devam eder.

## Güvenlik notu
Bu repoda **hiçbir** üretim kimlik bilgisi (DB şifresi, FTP parolası, sertifika,
mail/Telegram token) yer almaz. Sırlar önce **ortam değişkeni**, yoksa gitignore'lu
`secrets.json` dosyasından okunur (`common.config.get_secret`). Gereken anahtarlar:
`FS_TELEGRAM_BOT_TOKEN`, `FS_TELEGRAM_CHAT_ID`, `FS_SMTP_USER`, `FS_SMTP_PASS`,
`FS_SMTP_FROM`. Sertifikalar `certs/` altında. Bu dosyalar repoya **asla** girmez,
sunucuya elle konur.
