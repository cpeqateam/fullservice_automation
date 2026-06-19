# FULL Servis — Mimari ve Kod Hakimiyeti Rehberi (v2)

> Bu doküman, kodun **bugünkü** halinin nasıl çalıştığını ve birbiriyle nasıl
> haberleştiğini baştan sona açıklar. Her bölümde ilgili dosya/satıra link
> verilir — okurken kodu yan tarafta açıp takip edebilirsin. Amaç: 4 makine +
> DB + provisioning + dashboard arasındaki sistemin **zihinsel modelini**
> kurman. Görsel: [`MIMARI.drawio`](MIMARI.drawio).

---

## 1. 10.000 metreden bakış

| # | Bileşen | Dil / Çatı | Görev |
|---|---------|------------|-------|
| ① | **Sunucu (orkestratör)** | Python / FastAPI | Linux sunucuda çalışır. 4 düğümü yönetir, komut dağıtır, durumu birleştirir, logları toplar. **cpeqadb**'den marka/model/firmware listesi çeker. |
| ② | **Agent / Listener** | Python / FastAPI | Mac/Windows client makinelerinde **boot'tan itibaren** :7531 portunda çalışır. Sunucudan komut alır, testleri yerelde koşar, ilerlemeyi sunucuya **push** eder, logları sunucuya **upload** eder. |
| ③ | **Dashboard** | Vue 3 + Vuetify 3 | Türk Telekom temalı tek sayfa. Sunucudan `/api/state`'i 1 sn'de bir çeker, 4 düğümü canlı gösterir. **DeviceForm**'la marka/model/firmware + süre seçilir; **StatusPanel**'le aşamalı **Health-Check** yürütülür; "FULL Servis Başlat / Durdur" tuşlarıyla orkestrasyon tetiklenir. |
| ④ | **Provisioning** | shell / PowerShell | Her makineye **statik IP** atar ve listener'ı **boot autostart** olarak kurar (macOS launchd · Windows Görev Zamanlayıcı · Linux systemd). |
| ⑤ | **cpeqadb** (uzak) | PostgreSQL + SSL | GRK ile **paylaşılan** firmware veritabanı. Sertifikalar `fullservice-backend/certs/` altında; repoda yok. Bağlantı yoksa frontend serbest-metin'e düşer. |

Tüm haberleşme **HTTP/JSON** üzerinden (LAN içinde). Frontend ile backend
arasında WebSocket yok — basit 1 sn polling yeter (4 düğüm × ~6 test = düşük hacim).

```
              ┌────────────────────────────┐
              │ Modem (Türk Telekom CPE)   │       ← test altındaki cihaz
              └─────┬────┬────┬────┬───────┘
        Kablo ──────┘    │    │    └────────────────────── Wi-Fi
                       Kablo  └─────────── Wi-Fi
   ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐
   │  LINUX SUN. │  │  MAC (kablo) │  │ WIN (Wi-Fi) │  │ MAC (Wi-Fi) │
   │  :8770 API  │  │ listener:7531│  │listener:7531│  │listener:7531│
   └──────┬──────┘  └──────────────┘  └─────────────┘  └─────────────┘
          │ HTTP /api/*  (paralel fan-out, çift-yönlü push)
          │
          ▼
   ┌──────────────┐                           ┌──────────────┐
   │  Tarayıcı /  │   ◄─── 1 sn polling ───►  │   cpeqadb    │
   │  Dashboard   │                           │ (firmware DB)│
   └──────────────┘                           └──────────────┘
```

---

## 2. Klasör Haritası (güncel)

```
fullservice_automation/
├── fullservice-backend/
│   ├── config.json                          ← Topoloji + defaults + network (statik IP)
│   ├── common/
│   │   ├── config.py                        ← config.json okuyucu, dashboard path
│   │   ├── protocol.py                      ← HTTP sözleşmesi (pydantic, TestType)
│   │   ├── firmware_db.py                   ← cpeqadb erişimi (SSL, fallback'lı)
│   │   └── runners/                         ← Cross-platform test çalıştırıcılar
│   │       ├── base.py                      ←   RunContext + görünür terminal yardımcıları
│   │       ├── ping_runner.py               ←   ping_internet + ping_modem (canlı terminal)
│   │       ├── youtube_runner.py            ←   en yüksek kalite (Selenium/Chrome)
│   │       ├── youtube_util.py              ←   Selenium ile kalite menüsü zorlama
│   │       ├── iperf_runner.py              ←   iperf3 -c (Wi-Fi Mac)
│   │       ├── iperf_server_runner.py       ←   iperf3 -s (kablolu Mac)
│   │       ├── torrent_runner.py            ←   qBittorrent indirme döngüsü (gerçek)
│   │       ├── torrent_util.py              ←   qBittorrent Web API yardımcıları
│   │       ├── wifi_track_runner.py         ←   WLAN örnekleme (gerçek, canlı terminal)
│   │       ├── wifi_util.py                 ←   WLAN okuma/parse (Windows netsh + ortak)
│   │       ├── wifi_util_mac.py             ←   WLAN okuma (macOS system_profiler)
│   │       └── registry.py                  ←   TestType → runner eşlemesi
│   ├── agent/
│   │   ├── main.py                          ←   FastAPI /start /stop /health + register loop
│   │   └── test_executor.py                 ←   StartCommand → thread'ler → push/upload
│   ├── server/
│   │   ├── main.py                          ←   Tüm /api/* endpoint'leri + static mount
│   │   ├── orchestrator.py                  ←   Beyin: registry + aggregator + fan-out + health-check + reset
│   │   └── log_collector.py                 ←   logs/<BILGISAYAR>/<session>/ altına yazma
│   ├── provisioning/                        ← Statik IP + boot autostart
│   │   ├── README.md                        ←   Kullanım rehberi
│   │   ├── macos/   set-static-ip.sh · install-agent-launchd.sh · *.plist
│   │   ├── windows/ set-static-ip.ps1 · install-agent-task.ps1
│   │   └── linux/   set-static-ip.sh · install-server-systemd.sh · *.service
│   ├── run_server.py
│   └── run_agent.py
│
└── fullservice-frontend/
    └── src/
        ├── main.js · App.vue
        ├── plugins/vuetify.js               ← Türk Telekom tema
        ├── store/
        │   ├── index.js  (Pinia)
        │   └── app.js                       ← polling + firmware + health-check + actions
        ├── services/api.js                  ← axios: state/session/health-check/firmware
        ├── components/
        │   ├── LiquidBackground.vue
        │   ├── Topbar.vue                   ← TT logo + oturum chip + tema toggle
        │   ├── DeviceForm.vue               ← Marka/Model/Firmware + Süre + Başlat/Durdur
        │   ├── StatusPanel.vue              ← Aşamalı Health-Check + ışıklar
        │   ├── NodeCard.vue                 ← 4'lük gridin elemanı
        │   └── TestRow.vue                  ← Tek test ilerleme satırı
        └── assets/styles/main.scss
```

---

## 3. HTTP Sözleşmesi (Protokol)

Sunucu ↔ agent ↔ dashboard arasındaki tüm konuşmaların **dili** burada:
         [`common/protocol.py`](fullservice-backend/common/protocol.py)

### TestType (rol/test tipi enum'u)
```python
class TestType(str, Enum):
    PING_INTERNET = "ping_internet"
    PING_MODEM    = "ping_modem"
    YOUTUBE       = "youtube"
    IPERF_SERVER  = "iperf_server"   # kablolu Mac: iperf3 -s
    IPERF         = "iperf"          # Wi-Fi Mac: iperf3 -c
    TORRENT       = "torrent"
    WIFI_TRACK    = "wifi_track"
```

`config.json`'da her düğümün `roles` listesi bu değerlerden seçilir; agent
sadece kendine atanan rolleri çalıştırır.

### Üç ana mesaj tipi

| Model                 | Yön            | Ne taşır                                                          |
|-----------------------|----------------|-------------------------------------------------------------------|
| **`RegisterRequest`** | agent → sunucu | `node_id, hostname, platform, ip, agent_port` (kayıt + heartbeat) |
| **`StartCommand`**    | sunucu → agent | `session_id, tests: [TestType], params: TestParams`               |
| **`ProgressUpdate`**  | agent → sunucu | `node_id, session_id, task, progress (0..100), status, message`   |

`TestParams` tüm runner'ların ihtiyaç duyabileceği parametreleri **tek pakette**
taşır — her runner ihtiyacı olanı kullanır:
```python
class TestParams(BaseModel):
    modem_ip: str
    internet_ip: str
    youtube_link: str
    iperf_server: str      # Wi-Fi Mac buraya bağlanır = kablolu Mac'in LAN IP'si
    torrent_magnet: str    # qBittorrent'e eklenecek magnet (GTA5)
    iperf_port: int
    iperf_parallel: int
    duration: int
```

---

## 4. Sunucu API Uçları

Tümü [`server/main.py`](fullservice-backend/server/main.py) içinde tanımlı.
**Base URL:** `http://<linux_lan_ip>:8770`

### Çekirdek (agent ↔ sunucu)
| Method | URL                 | Çağıran   | İş                               |
|--------|---------------------|-----------|----------------------------------|
| POST   | `/api/register`     | agent     | Kayıt + heartbeat (10 sn'de bir) |
| POST   | `/api/progress`     | agent     | Anlık ilerleme bildirimi         |
| POST   | `/api/logs/upload`  | agent     | Log dosyası yükleme (multipart)  |

### Dashboard ↔ sunucu
| Method | URL                                          | İş                                                        |
|--------|----------------------------------------------|-----------------------------------------------------------|
| GET    | `/api/state`                                 | Birleşik durum (1 sn polling)                             |
| POST   | `/api/session/start`                         | Tüm düğümlere fan-out komut (override + device opsiyonel) |
| POST   | `/api/session/stop`                          | Tüm düğümleri durdur                                      |
| GET    | `/api/health-check`                          | **Aktif** probe: tüm düğümlere paralel GET /health        |
| GET    | `/api/firmware/brands`                       | Distinct marka listesi (cpeqadb · grk_firmware)           |
| GET    | `/api/firmware/models/{brand}`               | Markaya ait modeller                                      |
| GET    | `/api/firmware/versions/{brand}/{model}`     | Modele ait firmware'ler                                   |
| GET    | `/health`                                    | Sunucu sağlık kontrolü                                    |

### Agent uçları (her listener'da)
| Method | URL       | Çağıran  | İş                                    |
|--------|-----------|----------|---------------------------------------|
| POST   | `/start`  | sunucu   | `StartCommand` ile bu agent'ı tetikle |
| POST   | `/stop`   | sunucu   | Çalışan testleri durdur               |
| GET    | `/health` | herkes   | Health-Check probe'unun hedefi        |

---

## 5. Runner'lar — Testler nasıl çalışıyor?

Her test tipi tek bir Python modülüdür ve aynı sözleşmeyi uygular:

```python
def run(params: TestParams, ctx: RunContext) -> list[str]: ...
#   • ctx.progress(pct, status, message)  ← her saniye sunucuya yansır
#   • ctx.stop (threading.Event)          ← /stop gelirse temiz çıkar
#   • Dönüş: üretilen log dosyalarının yolları
```

`RunContext` tanımı: [`common/runners/base.py`](fullservice-backend/common/runners/base.py)

### 5.1 `ping_runner.py` — ping_internet & ping_modem
[`common/runners/ping_runner.py`](fullservice-backend/common/runners/ping_runner.py)

**Komut (cross-platform):**
- Windows : `ping -n {duration} -w 1000 {target}`
- Linux/macOS : `ping -c {duration} -W 1 {target}`

**Akış:**
1. Hedef = `params.modem_ip` (ping_modem) veya `params.internet_ip` (ping_internet).
2. `subprocess.Popen` → çıktı log dosyasına yazılır.
3. Saniyede bir döngüde:
   - `ctx.stop.is_set()` → `proc.terminate()`, status `stopped`.
   - `proc.poll() is not None` → süre dolmadan bitti, döngüden çık.
   - Aksi halde `ctx.progress((i+1)/duration*100, "running", "Ping i+1/duration → target")`.
4. Bitince `returncode` 0 ise `completed`, değilse `error`.

### 5.2 `youtube_runner.py` + `youtube_util.py` — en yüksek kalite
[`common/runners/youtube_runner.py`](fullservice-backend/common/runners/youtube_runner.py)

- Önce **Selenium** ([`youtube_util.py`](fullservice-backend/common/runners/youtube_util.py)):
  Chrome açar → videoyu oynatır → oynatıcı Ayarlar(⚙) → Kalite menüsünden **en üst**
  seçeneği tıklar → tam ekran. `detach=True` ile tarayıcı kişi kapatana kadar açık kalır.
- Selenium/Chrome yoksa **fallback**: `webbrowser.open(...)` (URL'de `vq=hd2160&hd=1` ipucu).
- Tek bildirim verir ("▶ YouTube oynatılıyor"); ilerleme saniye saniye izlenmez.

### 5.3 `iperf_runner.py` / `iperf_server_runner.py` — modeme **abanma**
[`iperf_runner.py`](fullservice-backend/common/runners/iperf_runner.py) ·
[`iperf_server_runner.py`](fullservice-backend/common/runners/iperf_server_runner.py)

**Topoloji (değişti):** Linux sunucu artık iperf server DEĞİL.
- **Kablolu Mac** (`iperf_server` rolü) → `iperf3 -s -p 5201` dinler.
- **Wi-Fi Mac** (`iperf` rolü) → `iperf3 -c <kablolu_mac_ip> -P 4` ile yük basar.
- Trafik iki Mac arasında **modem üzerinden** akar. Server adresini orkestratör
  `_iperf_server_ip()` ile çözer (kablolu Mac'in kayıtlı IP'si / config fallback).
- Client, server hazır olmayabilir diye **5 kez** yeniden bağlanmayı dener.

### 5.4 `torrent_runner.py` + `torrent_util.py` — qBittorrent (gerçek)
[`torrent_runner.py`](fullservice-backend/common/runners/torrent_runner.py) ·
[`torrent_util.py`](fullservice-backend/common/runners/torrent_util.py)

GRK `gbtorrent.py` portu: qBittorrent'i başlatır, Web UI'ye (admin/Admin123 @ :8080)
girer, `config.defaults.torrent_magnet` (GTA5) ekler, indirme %'sini dashboard'a
yansıtır, bitince silip yeniden ekler — durdurulana kadar. Sadece Windows'ta.

### 5.5 `wifi_track_runner.py` + `wifi_util*.py` — gerçek WLAN örnekleme
[`wifi_track_runner.py`](fullservice-backend/common/runners/wifi_track_runner.py) ·
[`wifi_util.py`](fullservice-backend/common/runners/wifi_util.py) ·
[`wifi_util_mac.py`](fullservice-backend/common/runners/wifi_util_mac.py)

GRK `functionBase_wifi` portu: saniyede bir WLAN'dan sinyal/kanal/rx-tx + sistem
kaynağı (CPU/RAM/pil) okuyup log'a yazar. Windows=`netsh`, macOS=`system_profiler`
(mac dosyası geçici; takım liderinden gerçek kod gelince değişecek). Ayrı bir
**canlı terminal** (log izleyici) açar.

> **Görünür terminaller:** ping ve wifi_track, `base.open_terminal_running` /
> `base.open_log_viewer` ile görünür pencere açar (Win=`cmd /k`, macOS=Terminal/
> osascript, Linux=gnome-terminal vb. script dosyası ile). Yalnızca giriş-yapılmış
> masaüstü oturumunda çalışır; servis/headless'ta sessizce atlanır.

### 5.6 Registry — TestType'ı runner'a bağlama
[`common/runners/registry.py`](fullservice-backend/common/runners/registry.py)

```python
RUNNERS = {
    "ping_internet": ping_runner.run_internet,
    "ping_modem":    ping_runner.run_modem,
    "youtube":       youtube_runner.run,
    "iperf_server":  iperf_server_runner.run,   # kablolu Mac
    "iperf":         iperf_runner.run,          # Wi-Fi Mac
    "torrent":       torrent_runner.run,
    "wifi_track":    wifi_track_runner.run,
}
```

Yeni test eklemek için: runner dosyasını yaz, `TestType`'a değer ekle, buraya
bir satır. Başka yeri değiştirmek **gerekmez**.

---

## 6. Sunucu Orkestratörü

[`server/orchestrator.py`](fullservice-backend/server/orchestrator.py)

`Orchestrator` tek örnektir; `server/main.py`'de oluşur. State bellektedir ve
`threading.RLock` ile korunur.

### 6.1 Düğüm registry
```python
self.nodes: dict[str, dict] = {}     # node_id → runtime durum
# her düğüm: { node_id, label, conn, is_server, roles, ip, agent_port,
#              platform, online, last_seen,
#              tests: { task: {progress,status,message,updated} } }
```
`config.json`'daki `nodes` listesinden başlatılır. Sunucu düğümü `is_server: true`
ile işaretli; `online` her zaman `true`.

### 6.2 Kayıt / heartbeat
Agent her 10 sn'de bir `POST /api/register` → IP/port/platform güncellenir,
`last_seen = datetime.now()`. Heartbeat 30 sn'den eskiyse `get_state`'te
**offline** sayılır.

### 6.3 Progress aggregator
- **Agent'lardan:** `POST /api/progress` → `update_progress(node_id, task, ...)`.
- **Sunucu yerel testlerden:** runner'ın `ctx.progress` callback'i **doğrudan**
  aggregator'ı çağırır (HTTP yok, in-process):
  ```python
  ctx = RunContext(
      node_id="server",
      progress=lambda p, s, m, _t=t: self.update_progress("server", _t, p, s, m),
      ...
  )
  ```

### 6.4 Oturum başlatma — fan-out
`POST /api/session/start` → `Orchestrator.start_session(overrides)`:

1. `session_id = "FS_YYYYMMDD_HHMMSS"`.
2. `TestParams` inşa edilir: config defaults + dashboard override'ları +
   `iperf_server = self._iperf_server_ip()` (kablolu Mac'in IP'si) +
   `torrent_magnet = defaults.torrent_magnet`.
3. `self.session.device = { brand, model, firmware }` — dashboard'dan gelen
   cihaz seçimi oturuma yapışır (log ve raporlar için).
4. Tüm düğümlerin test state'leri sıfırlanır.
5. iperf server'ı artık sunucu kaldırmaz — kablolu Mac'in agent'ı `iperf_server`
   rolüyle kendi `iperf3 -s`'ini fan-out ile başlatır.
6. Fan-out **paralel** thread'lerde (kapalı bir client diğerlerini beklemesin):
   - **Sunucu düğümü** için: rolleri in-process thread'lerde başlat.
   - **Diğer düğümler** için: `POST http://<ip>:<port>/start` ile `StartCommand`.
7. Dönüş: `{ session_id, dispatched: [...], skipped: [...] }`.

### 6.5 Durdurma / Sıfırlama
`POST /api/session/stop`:
- Sunucu-yerel testler için `self._server_stop.set()` (paylaşılan Event).
- Her online agent'a `POST http://<ip>:<port>/stop`.

`POST /api/session/reset` → `reset_session()`: önce `stop_session()`, sonra oturum
bilgisini ve tüm düğümlerin test ilerlemelerini başa alır (dashboard "Sıfırla"
butonu bunu çağırır; health-check durumu frontend'de ayrıca sıfırlanır).

### 6.6 Aktif Health-Check
[`Orchestrator.health_check()`](fullservice-backend/server/orchestrator.py)

Heartbeat-tabanlı `online`'dan **bağımsız**: sunucu her düğümün listener'ına
**paralel** `GET /health` atar (timeout 1.5 sn). Sonuç:
```json
{
  "checked_at": "2026-...",
  "results": {
    "server":    { "reachable": true,  "latency_ms": 0 },
    "mac_cable": { "reachable": true,  "latency_ms": 12 },
    "win_wifi":  { "reachable": false, "latency_ms": null }
  }
}
```
Dashboard bu sonuçla **kırmızı/yeşil ışıkları** yakar.

### 6.7 Log toplama
[`server/log_collector.py`](fullservice-backend/server/log_collector.py)

`POST /api/logs/upload` (multipart) → `logs/<BILGISAYAR>/<session_id>/<dosya>`.
`<BILGISAYAR>` her düğümün `config.json:log_name`'idir (server→LINUX, mac_cable→
MAC_ETH, mac_wifi→MAC_WIFI, win_wifi→WIN_WIFI; `config.node_log_folder()`).
Sunucunun kendi testleri de `logs/LINUX/<session>/` altına yazar.
Faz 5'te bu klasörler FTPS + PostgreSQL'e yollanacak.

---

## 7. Agent / Listener

[`agent/main.py`](fullservice-backend/agent/main.py)
[`agent/test_executor.py`](fullservice-backend/agent/test_executor.py)

### 7.1 Açılış
Env değişkenleri:
- `FS_NODE_ID` — bu agent hangi düğümü temsil ediyor (örn. `mac_cable`).
- `FS_SERVER_URL` — sunucu adresi.
- `FS_AGENT_PORT` — agent'ın dinleyeceği port (config.json'da varsayılan **7531**).

Açılışta `_register_loop` arka plan thread'i başlar — 10 sn'de bir kayıt POST'lar.
Listener boot autostart ile her açılışta otomatik kalkar
([`provisioning/`](fullservice-backend/provisioning/README.md)).

### 7.2 Komut alma
Sunucu `POST /start` çağırınca FastAPI handler `TestExecutor.start(cmd)`'i tetikler:
- Önceki çalışmayı durdurur (`self._stop.set()`).
- Yeni bir `threading.Event` oluşturur.
- `cmd.tests` listesindeki her test için ayrı thread başlatır.
- Test bitince üretilen logları `self._upload(file_path)` ile sunucuya gönderir.

### 7.3 Progress push
Her runner `ctx.progress(p, s, m)` çağırınca:
```python
requests.post(f"{server}/api/progress", json={
  "node_id": ..., "session_id": ..., "task": ...,
  "progress": ..., "status": ..., "message": ...
}, timeout=3)
```
Hata yutulur — sunucu erişilemez olsa bile test devam eder (best-effort).

---

## 8. Frontend (Dashboard)

[`fullservice-frontend/src/`](fullservice-frontend/src/)

### 8.1 Bootstrapping
[`main.js`](fullservice-frontend/src/main.js) → Vue + Pinia + Vuetify + global SCSS.

### 8.2 Store
[`store/app.js`](fullservice-frontend/src/store/app.js)

| Alan | Açıklama |
|------|----------|
| `session, nodes, testLabels, serverLanIp` | `/api/state`'ten gelen birleşik durum |
| `deviceInfo {brand, model, firmware}`     | DeviceForm'un seçimi |
| `overrides {duration, modem_ip, ...}`     | Opsiyonel parametre override'ları |
| `brandsData, firmwareOptions`             | DB'den çekilen combobox kaynakları |
| `brandsDbFailed, firmwareDbFailed`        | DB erişilemezse `true` → serbest metin moduna düş |
| `health { run, running, checkedAt, results }` | Health-Check durumu |
| `_hcTimer`                                | Aşamalı plan zamanlayıcısı |

**Eylemler (actions):** `refresh()`, `startPolling()`, `loadBrands()`,
`loadFirmwares()`, `onBrandChange()`, `onModelChange()`, `startTest()`,
`stopTest()`, `startHealthCheck()`, `stopHealthCheck()`, `toggleTheme()`.

### 8.3 Bileşenler
- [`App.vue`](fullservice-frontend/src/App.vue) — 2 kolon layout (12/lg-9 ana + 12/lg-3 sidebar).
- [`Topbar.vue`](fullservice-frontend/src/components/Topbar.vue) — Türk Telekom SVG logosu + "FULL SERVİS" başlığı + oturum chip + dark/light toggle.
- [`DeviceForm.vue`](fullservice-frontend/src/components/DeviceForm.vue) — Marka/Model/Firmware combobox + Süre + gelişmiş override + **Başlat/Durdur**. *(GRK Günlük Rutin Kontrol formuyla aynı UX.)*
- [`StatusPanel.vue`](fullservice-frontend/src/components/StatusPanel.vue) — sağ panel: her düğüm için ışık (yeşil/kırmızı/idle) + Health-Check butonu.
- [`NodeCard.vue`](fullservice-frontend/src/components/NodeCard.vue) — bir düğümün test listesi.
- [`TestRow.vue`](fullservice-frontend/src/components/TestRow.vue) — test ikonu + isim + yüzde + Vuetify `v-progress-linear`.
- [`LiquidBackground.vue`](fullservice-frontend/src/components/LiquidBackground.vue) — animasyonlu magenta-mavi blob arkaplan.

### 8.4 Tema
[`plugins/vuetify.js`](fullservice-frontend/src/plugins/vuetify.js)
- `primary = #E20074` (Türk Telekom magenta)
- `secondary = #0A84FF` (Apple blue ikincil vurgu)
- Dark/light, `localStorage` ile kalıcı.

---

## 9. Firmware DB (cpeqadb)

[`common/firmware_db.py`](fullservice-backend/common/firmware_db.py)

GRK'daki `app/database.py` + `device_controller.py` mantığının FULL Servis
sunucusu için sadeleştirilmiş portu:

- **Bağlantı:** `postgresql://cpeqateam:***@78.186.148.93:4749/cpeqadb`
  (ortam değişkeni `FS_FIRMWARE_DB_URL` ile override edilebilir).
- **SSL:** `verify-ca` modu. Sertifikalar `fullservice-backend/certs/` altında
  (`ca.crt`, `client.crt`, `client.key`) — **repoya konulmaz**.
- **Tablo:** `grk_firmware` (GRK ile paylaşılan).
- **Sorgular:** `get_brands()`, `get_models(brand)`, `get_versions(brand, model)`.
- **Düşürme (graceful degradation):** Bağlantı kurulamazsa `engine = None`
  kalır; uygulama çökmez. Sunucu endpoint'i `503` döner; frontend bunu yakalayıp
  combobox'ları **serbest-metin girişine** çevirir (GRK ile aynı davranış).

### Endpoint zinciri
```
Tarayıcı                Sunucu (FastAPI)              cpeqadb
   │ GET /api/firmware/brands  │                          │
   │ ────────────────────────► │  SELECT DISTINCT brand   │
   │                           │ ─────────────────────► │
   │                           │ ◄───────────────────── │
   │ ◄──────────────────────── │  → ["Huawei","ZTE",…]    │
```

---

## 10. Health-Check — aşamalı bağlantı kontrolü

Health-Check, **test başlatmanın ön koşulu**dur — kullanıcı önce sağ paneldeki
butona basmadan testi başlatamaz (DeviceForm.onStart içinde `requireHealthCheck()`
kontrolü vardır).

### 10.1 Plan
[`store/app.js`](fullservice-frontend/src/store/app.js) — `HC_SCHEDULE`:

| Aşama | Aralık | Kontrol sayısı |
|-------|--------|----------------|
| 1     | 1 sn   | 3              |
| 2     | 3 sn   | 3              |
| 3     | 5 sn   | 3              |
| 4     | 15 sn  | 1              |
| 5     | 30 sn  | 1              |
| 6     | 60 sn  | **∞** (program kapanana dek) |

> Neden `setInterval` değil de özyinelemeli `setTimeout`? Aralık aşamadan
> aşamaya değiştiği için tek sabit aralıklı interval işe yaramaz; her
> tick'ten sonra bir sonraki bekleme süresini yeniden hesaplayıp zincirliyoruz.

### 10.2 Sunucu tarafı
[`Orchestrator.health_check()`](fullservice-backend/server/orchestrator.py)
- Her düğümün son bilinen `ip:agent_port` adresine **paralel** `GET /health`.
- `reachable: bool` + `latency_ms: int|None` döner.
- Sunucu düğümü için reachable her zaman `true`, latency 0.

### 10.3 Dashboard tarafı
[`StatusPanel.vue`](fullservice-frontend/src/components/StatusPanel.vue) — her
düğüm için bir satır:
- **Yeşil (pulse animasyon):** reachable, gecikme ms olarak gösterilir.
- **Kırmızı:** ulaşılamıyor.
- **Gri:** henüz kontrol yapılmadı.

---

## 11. Provisioning — statik IP + boot listener

[`fullservice-backend/provisioning/`](fullservice-backend/provisioning/README.md)

Her makineye **tek seferlik** kurulum yapar. Tüm IP/arayüz değerleri
`config.json` → `network` bölümünden okunur:

```json
"network": {
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns": ["8.8.8.8", "8.8.4.4"],
  "assignments": {
    "server":    { "ip": "192.168.1.10", "interface": "eth0" },
    "mac_cable": { "ip": "192.168.1.11", "interface": "Ethernet" },
    "win_wifi":  { "ip": "192.168.1.13", "interface": "Wi-Fi" },
    "mac_wifi":  { "ip": "192.168.1.14", "interface": "Wi-Fi" }
  }
}
```

### Platform script'leri

| Platform | Statik IP | Boot autostart |
|----------|-----------|----------------|
| macOS    | `sudo provisioning/macos/set-static-ip.sh <node_id>` (networksetup) | `provisioning/macos/install-agent-launchd.sh <node_id> <server_url> <port>` (launchd · `com.tt.fullservice.agent.plist`) |
| Windows  | `provisioning\windows\set-static-ip.ps1 -NodeId <node_id>` (Yönetici PS) | `provisioning\windows\install-agent-task.ps1 -NodeId <node_id> -ServerUrl <url> -Port 7531` (Görev Zamanlayıcı) |
| Linux    | `sudo provisioning/linux/set-static-ip.sh <node_id>` | `sudo provisioning/linux/install-server-systemd.sh` (systemd · `fullservice-server.service`) |

> Aynı Mac'te iki düğüm (mac_cable + mac_wifi) çalıştıracaksanız launchd
> script'ini farklı port (örn. 7531 ve 7532) ile **iki kez** çalıştırın.

---

## 12. Uçtan-Uca Akış (kronolojik)

```
T-∞   ▶  Provisioning bir kez çalıştırıldı: statik IP'ler atandı,
         listener'lar boot autostart oldu.

T₀    ▶  Linux sunucu açıldı. systemd `fullservice-server.service` → run_server.py.
         Aggregator boş; "server" düğümü online; firmware_db SSL bağlantısı kurulur.

T₁    ▶  Mac/Windows açıldı. launchd/Görev Zamanlayıcı listener'ı tetikler.
         agent/main.py → register_loop → POST /api/register
         Orchestrator → nodes["mac_cable"].online = True, ip/port güncellenir.
         Dashboard 1 sn sonra GET /api/state → kart yeşil yanar.

T₂    ▶  Kullanıcı tarayıcıyla http://<linux_ip>:8770 açar.
         App.vue onMounted → store.startPolling(1000) + store.loadBrands().
         GET /api/firmware/brands → cpeqadb'den marka listesi → combobox dolu.
         (Bağlantı koparsa 503 → brandsDbFailed=true → serbest metin moduna düş.)

T₃    ▶  Kullanıcı DeviceForm'da Marka/Model/Firmware seçer (combobox).
         Marka değişince store.onBrandChange() → model listesi güncellenir.
         Model değişince store.onModelChange() → GET /api/firmware/versions/{b}/{m}.

T₄    ▶  Kullanıcı sağ paneldeki Health-Check butonuna basar.
         store.startHealthCheck() → HC_SCHEDULE yürür: GET /api/health-check
         Sunucu her düğümün listener'ına paralel /health probe atar.
         Sonuç dashboard'da kırmızı/yeşil ışıklarla yansır.

T₅    ▶  Kullanıcı "FULL Servis Başlat" tuşuna basar.
         DeviceForm.onStart() → store.requireHealthCheck() (zorunlu) →
         store.startTest() → POST /api/session/start (body: brand/model/firmware/override).

T₆    ▶  Orchestrator.start_session:
         (a) session_id, TestParams hazırlanır (iperf_server = kablolu Mac IP);
             session.device set edilir.
         (b) Sunucu kendi rolleri için in-process thread'ler başlatır.
         (c) PARALEL: POST http://<each_node_ip>:7531/start  StartCommand{...}
             → kablolu Mac iperf_server rolüyle iperf3 -s'i KENDİ başlatır.

T₆+ε  ▶  Her agent: TestExecutor.start → her testi bir thread'de koşar.
         Saniyede 1 → POST /api/progress (her test ayrı).

T₆→Tend ▶ Dashboard 1 sn polling ile bar'ları doldurur. 4 düğüm paralel —
          modem zorlanıyor.

Tend  ▶  Runner'lar sırayla "completed" yayar.
         Agent: her test bitince log dosyasını POST /api/logs/upload ile yollar.
         Sunucu: log_collector → logs/<BILGISAYAR>/<session>/<dosya>

         (Faz 5'te buradan FTPS + PostgreSQL + mail/Telegram tetiklenecek.)

Tstop ▶  Kullanıcı "Durdur" → /api/session/stop → server_stop.set() +
         her agent'a /stop. Tüm runner'lar ctx.stop görür, temiz çıkar.
```

---

## 13. Yeni bir test tipi eklemek

1. **Runner** yaz: `common/runners/<isim>_runner.py`. `def run(params, ctx) -> list[str]`.
2. **TestType** ekle: [`common/protocol.py`](fullservice-backend/common/protocol.py) → enum'a yeni satır + `TEST_LABELS` sözlüğüne insan-okunur etiket.
3. **Registry**'ye satır ekle: [`common/runners/registry.py`](fullservice-backend/common/runners/registry.py).
4. **config.json**'da ilgili düğümün `roles` listesine yeni test adını yaz.
5. **Frontend ikon** (opsiyonel): [`TestRow.vue`](fullservice-frontend/src/components/TestRow.vue) içindeki `testIcon` haritasına bir `mdi-*` ekle.

Hepsi bu kadar — eklenti tabanlı.

---

## 14. Güvenlik ve Gizlilik

Bu repo **hiçbir** üretim kimlik bilgisi içermez:
- DB şifresi / FTP parolası ❌
- SSL sertifikaları (`ca.crt`, `client.crt`, `client.key`) ❌
- Mail / Telegram tokenları ❌

| Sır türü | Nereden okunur | Repoda? |
|----------|----------------|---------|
| **cpeqadb URL** | `FS_FIRMWARE_DB_URL` env (varsayılan kod içinde, parola değiştirilir) | parola hash'siz; **PROD'da env override ŞART** |
| **DB SSL sertifikaları** | `fullservice-backend/certs/` (ca/client crt+key) | **HAYIR** — `.gitignore` |
| **FTP/Mail/Telegram (Faz 5)** | `.env` (henüz yok) | **HAYIR** |

Faz 5'te tüm sırlar `.env` üzerinden taşınacak; commit dışında tutulacak.
Repo içine asla sır yazılmaz.

---

## 15. Sık Sorulanlar

- **`/api/firmware/brands` neden 503 dönebilir?** → cpeqadb'ye SSL bağlantısı
  kurulamadı. Sertifikalar (`certs/ca.crt`, `client.crt`, `client.key`) eksik
  ya da DB sunucusu erişilemez. Frontend bunu yakalayıp combobox'ları **serbest
  metne** çevirir; akış kesilmez.
- **Health-Check başlatılmadan neden test başlatılmıyor?**
  → DeviceForm.onStart içindeki `requireHealthCheck()` koruması. Aktif
  bağlantı kanıtlanmadan modeme yük bindirmek istemiyoruz.
- **Listener port 7531 hardcoded mi?**
  → Hayır — `config.json:agent_port` (varsayılan 7531). Agent açılışta
  `FS_AGENT_PORT` env'i ile override edilebilir; aynı host'ta 2 agent için
  farklı port verilir.
- **Boot'ta listener kalkmazsa?**
  → macOS: `launchctl list | grep fullservice` · Windows: Görev Zamanlayıcı'da
  görev durumu · Linux: `systemctl status fullservice-server`. `provisioning/`
  altındaki kurulum script'leri bu hizmetleri ayağa kaldırır.
- **iperf nasıl çalışıyor?**
  → Kablolu Mac `iperf3 -s` (server, port 5201), Wi-Fi Mac `iperf3 -c` (client).
  Tek client → tek server olduğu için tek port yeterli. Trafik iki Mac arasında
  modem üzerinden akar.
- **State neden bellekte? Yeniden başlatınca kaybolur.**
  → Faz 5'te oturum kalıcılığı PostgreSQL'e taşınacak. Şimdilik bellek + log
  dosyaları yeterli.

---

## 16. Görsel — `MIMARI.drawio`

[`MIMARI.drawio`](MIMARI.drawio) dosyasını **app.diagrams.net** (web), **VS
Code → Draw.io Integration** eklentisi veya draw.io masaüstü uygulamasıyla
açabilirsin. İçinde:
- Modem + 4 düğüm (kablo/Wi-Fi linkleri ayrı renkte)
- Linux sunucu kutusu — tüm endpoint listesiyle
- Tarayıcı / Dashboard kutusu — bileşenler listelenmiş
- Provisioning kutusu (turuncu, tek seferlik kurulum okları)
- cpeqadb kutusu (SSL ile bağlantı oku)
- Faz 5 kutusu (dashed)
- Lejant

---

> Bu doküman canlıdır — yeni bir runner eklediğinde §5'e, yeni endpoint
> eklediğinde §4'e, yeni provisioning script'i için §11'e bir satır eklemek
> 60 saniye sürer ve gelecek-sen'in zihinsel modelini güncel tutar.
