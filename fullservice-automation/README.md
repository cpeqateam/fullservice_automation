# FULL Servis — Dağıtık Modem Stres Test Sistemi

> Türk Telekom CPE ekibi için. GRK'nın (Günlük Rutin Kontrol) **çok-makineli** kardeşi.
> Amaç: modeme aynı anda 4 cihazdan yük bindirip ("abanma") sınırlarını zorlamak.
> Modem fail olmadan dayanıyorsa yazılım başarılı sayılır.

> ⚠️ Bu proje `grk-automation/` koduna **dokunmaz**; ondan bağımsızdır.
> Bu, üzerine birlikte geliştireceğimiz **çalışan ilk iskelet (Faz 1–3)**.

## Mimari

```
┌──────────── LINUX SUNUCU (orkestratör + beyin) ─────────────┐
│ • Koordinatör API + tek dashboard (herkes buraya bağlanır)  │
│ • Merkezi progress aggregator (4 düğümü birleştirir)        │
│ • Log toplama → (Faz 5) FTP + DB                            │
│ • iperf3 server  • Yerel testler: ping internet/modem, yt   │
└───────┬──────────────────┬──────────────────┬──────────────┘
        │ HTTP komut/progress                  │
   ┌────▼─────┐      ┌──────▼──────┐    ┌──────▼──────┐
   │ MAC kablo│      │ WIN  Wi-Fi  │    │ MAC  Wi-Fi  │   ← her biri "agent"
   │ yt,ping, │      │ yt,ping,    │    │ yt,ping,    │
   │ iperf    │      │ torrent,wt  │    │ iperf,wt    │
   └──────────┘      └─────────────┘    └─────────────┘
```

- **Sunucu**, online agent'lara ve kendine "başlat" komutunu dağıtır (fan-out).
- **Agent**, testleri **yerelde** koşar, ilerlemeyi sunucuya **push** eder, biten
  testin loglarını sunucuya **HTTP upload** eder.
- **Dashboard** sunucuda barınır; her makine tarayıcıdan sunucu adresine girer ve
  4 düğümü **tek ekranda canlı** izler.

## Klasör yapısı

```
fullservice-automation/
├── config.json            # 4 düğüm topolojisi + varsayılan parametreler (IP, süre...)
├── common/                # ortak: protokol + cross-platform test çalıştırıcılar
│   ├── config.py          #   config.json okuyucu, LAN IP tespiti
│   ├── protocol.py        #   sunucu↔agent HTTP sözleşmesi (pydantic)
│   └── runners/           #   ping / youtube / iperf (gerçek) · torrent / wifi_track (sim)
├── agent/                 # Mac/Windows ajan (FastAPI)
├── server/                # Linux orkestratör (FastAPI) + dashboard sunumu
│   ├── orchestrator.py    #   registry + aggregator + fan-out + yerel testler
│   ├── iperf_server.py    #   iperf3 -s yaşam döngüsü
│   └── log_collector.py   #   yüklenen logları logs/<session>/<node>/ altına yazar
├── dashboard/             # tek arayüz (build gerektirmez: HTML + JS + CSS)
├── run_server.py          # python run_server.py
└── run_agent.py           # python run_agent.py <node_id> [server_url]
```

## Kurulum

Her makinede (sunucu + 3 client) Python 3.10+ ve:

```bash
pip install -r requirements.txt
# iperf testleri için:  Linux: sudo apt install iperf3   ·   macOS: brew install iperf3
```

## Çalıştırma

1. **config.json**'u düzenle: `server.lan_ip` (Linux sunucunun LAN IP'si), `defaults`
   içindeki `modem_ip`, `internet_ip`, `youtube_link`, `duration`.

2. **Sunucu (Linux):**
   ```bash
   python run_server.py
   ```
   Dashboard: `http://<server-lan-ip>:8770`

3. **Her client'ta agent:**
   ```bash
   python run_agent.py mac_cable                       # config'deki lan_ip'i kullanır
   python run_agent.py win_wifi  http://192.168.1.10:8770
   python run_agent.py mac_wifi  http://192.168.1.10:8770
   ```
   Agent açılınca sunucuya kayıt olur; dashboard'da düğüm yeşil yanar.

4. Herhangi bir makineden tarayıcıyla `http://<server-lan-ip>:8770` aç →
   **FULL Servis Başlat**. 4 düğümün testleri eşzamanlı koşar, panelde canlı izlersin.

## Şu an ne çalışıyor (Faz 1–3)

| Parça | Durum |
|------|------|
| Sunucu↔agent kayıt, komut, progress, log upload | ✅ |
| 4 düğümlü canlı dashboard | ✅ |
| ping (internet/modem), youtube | ✅ gerçek |
| iperf3 (Linux server + Mac client) | ✅ gerçek (iperf3 kurulu olmalı) |
| torrent, wifi_track | 🟡 **simülasyon** (sahte ilerleme) |
| Log → FTP + DB + bildirim | ⏳ Faz 5 (GRK servisleri uyarlanacak) |
| Paketleme (her makineye kurulum) | ⏳ Faz 6 |

## Sıradaki adımlar (birlikte)

- **Faz 4:** torrent (GRK qBittorrent) ve wifi_track (GRK WLAN okuma + Excel) gerçeğe çevir; iperf eş-zamanlı 2 Mac için çoklu port.
- **Faz 5:** oturum bitince `logs/<session>/` → FTPS + PostgreSQL + mail/Telegram (GRK servisleri uyarlanır; `database.py` Linux için `wintypes` bağımlılığından arındırılır).
- **Faz 6:** agent'ı her makinede servis/uygulama olarak paketleme; dashboard'u istenirse Vue+Vuetify'a taşıma.
