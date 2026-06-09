# FULL Servis — Mimari ve Kod Hakimiyeti Rehberi

Bu doküman, kodun **nasıl çalıştığını** ve **birbiriyle nasıl haberleştiğini**
baştan sona açıklar. Her bölümde ilgili dosya/satıra link verilir — okurken kodu
yan tarafta açıp takip edebilirsin. Amaç: 4 makine arasındaki sistemin
**zihinsel modelini** kurman.

---

## 1. 10.000 metreden bakış

Sistem **3 bileşenden** oluşur:

| # | Bileşen | Dil | Görev |
|---|---------|-----|-------|
| ① | **Sunucu (orkestratör)** | Python / FastAPI | Linux sunucuda çalışır. 4 düğümü yönetir, komut dağıtır, durumu birleştirir, logları toplar. |
| ② | **Agent** | Python / FastAPI | Mac/Windows client makinelerinde çalışır. Sunucudan komut alır, testleri yerelde koşar, ilerlemeyi sunucuya **push** eder, logları sunucuya **upload** eder. |
| ③ | **Dashboard** | Vue 3 + Vuetify | Türk Telekom temalı tek sayfa. Sunucudan `/api/state`'i 1 sn'de bir çeker, 4 düğümü canlı gösterir. "Başlat / Durdur" tuşlarıyla orkestrayı tetikler. |

Tüm haberleşme **HTTP/JSON** üzerinden (LAN içinde). Frontend ile backend
arasında WebSocket yok — basit 1 sn polling yeter (4 düğüm × ~6 test = düşük hacim).

```
Tarayıcı ── HTTP ──▶ Sunucu ──┬── HTTP ──▶ Mac (agent)
                              ├── HTTP ──▶ Win (agent)
                              └── HTTP ──▶ Mac (agent)
                              + Sunucu kendi rollerini in-process çalıştırır
```

Görsel için: [`MIMARI.drawio`](MIMARI.drawio).

---

## 2. Klasör Haritası

```
fullservice_automation/
├── fullservice-backend/
│   ├── config.json                    ← Topoloji (4 düğüm) + varsayılan parametreler
│   ├── common/                        ← Sunucu VE agent'ın paylaştığı çekirdek
│   │   ├── config.py                  ← config.json okuyucu, LAN IP, yol sabitleri
│   │   ├── protocol.py                ← HTTP sözleşmesi (pydantic modeller, TestType enum)
│   │   └── runners/                   ← Cross-platform test çalıştırıcılar
│   │       ├── base.py                ←   RunContext (log_dir + stop + progress)
│   │       ├── ping_runner.py         ←   ping_internet, ping_modem
│   │       ├── youtube_runner.py
│   │       ├── iperf_runner.py
│   │       ├── torrent_runner.py      ←   Faz 4: simülasyon
│   │       ├── wifi_track_runner.py   ←   Faz 4: simülasyon
│   │       └── registry.py            ←   TestType → runner eşlemesi
│   ├── agent/                         ← Client tarafı
│   │   ├── main.py                    ←   FastAPI app + /start /stop /health + register loop
│   │   └── test_executor.py           ←   StartCommand → thread'ler → push/upload
│   ├── server/                        ← Sunucu tarafı
│   │   ├── main.py                    ←   FastAPI app + /api/* endpoint'ler + dashboard mount
│   │   ├── orchestrator.py            ←   ASIL BEYİN: registry + aggregator + fan-out
│   │   ├── iperf_server.py            ←   iperf3 -s yaşam döngüsü
│   │   └── log_collector.py           ←   Yüklenen logları logs/<session>/<node>/ altına yazar
│   ├── run_server.py                  ← `python run_server.py`
│   └── run_agent.py                   ← `python run_agent.py <node_id> [url] [port]`
│
└── fullservice-frontend/
    └── src/
        ├── main.js                    ← Vue + Pinia + Vuetify bootstrap
        ├── App.vue                    ← Layout: arkaplan + topbar + control + grid
        ├── store/app.js               ← Pinia: nodes/session, 1 sn polling, actions
        ├── services/api.js            ← Axios: fetchState / startSession / stopSession
        └── components/
            ├── LiquidBackground.vue   ← Animasyonlu blob'lar (TT magenta)
            ├── Topbar.vue             ← Logo + başlık + oturum chip + tema toggle
            ├── ControlBar.vue         ← Parametre inputları + Başlat/Durdur
            ├── NodeCard.vue           ← 4'lük gridin elemanı (tek düğüm)
            └── TestRow.vue            ← Düğüm içindeki tek test satırı (progress bar)
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
    IPERF         = "iperf"
    TORRENT       = "torrent"
    WIFI_TRACK    = "wifi_track"
```

`config.json`'da her düğümün `roles` listesi bu değerlerden seçilir; agent
sadece kendine atanan rolleri çalıştırır.

### Üç ana mesaj tipi (pydantic modelleri)

| Model | Yön | Ne taşır |
|-------|-----|----------|
| **`RegisterRequest`** | agent → sunucu | `node_id, hostname, platform, ip, agent_port` (kayıt + heartbeat) |
| **`StartCommand`**    | sunucu → agent | `session_id, tests: [TestType], params: TestParams` |
| **`ProgressUpdate`**  | agent → sunucu | `node_id, session_id, task, progress (0..100), status, message` |

`TestParams` tüm runner'ların ihtiyaç duyduğu parametreleri **tek pakette**
taşır (her runner ihtiyacı olanı kullanır):
```python
class TestParams(BaseModel):
    modem_ip: str
    internet_ip: str
    youtube_link: str
    iperf_server: str   # Mac'ler buraya bağlanır = Linux sunucu LAN IP
    iperf_port: int
    iperf_parallel: int
    duration: int
```

### API uçları (sunucu, `/api/...`)
| Method | URL | Çağıran | İş |
|--------|-----|---------|----|
| POST | `/register`      | agent     | Kayıt + heartbeat |
| POST | `/progress`      | agent     | Anlık ilerleme bildirimi |
| POST | `/logs/upload`   | agent     | Log dosyası yükleme (multipart) |
| GET  | `/state`         | dashboard | Birleşik durum (1 sn polling) |
| POST | `/session/start` | dashboard | Tüm düğümlere fan-out komut |
| POST | `/session/stop`  | dashboard | Tüm düğümleri durdur |
| GET  | `/health`        | herkes    | Sağlık kontrolü |

### Agent uçları
| Method | URL | Çağıran | İş |
|--------|-----|---------|----|
| POST | `/start`  | sunucu | `StartCommand` ile bu agent'ı tetikle |
| POST | `/stop`   | sunucu | Çalışan testleri durdur |
| GET  | `/health` | herkes | Sağlık kontrolü |

---

## 4. Runner'lar — Testler nasıl çalışıyor?

Her test tipi tek bir Python modülüdür ve aynı sözleşmeyi uygular:

```python
def run(params: TestParams, ctx: RunContext) -> list[str]: ...
#   • ctx.progress(pct, status, message)  ← her saniye sunucuya yansır
#   • ctx.stop (threading.Event)          ← /stop gelirse temiz çıkar
#   • Dönüş: üretilen log dosyalarının yolları
```

`RunContext` tanımı: [`common/runners/base.py`](fullservice-backend/common/runners/base.py)

### 4.1 `ping_runner.py` — ping_internet & ping_modem
[`common/runners/ping_runner.py`](fullservice-backend/common/runners/ping_runner.py)

**Komut (cross-platform):**
- Windows : `ping -n {duration} -w 1000 {target}`
- Linux/macOS : `ping -c {duration} -W 1 {target}`

**Akış:**
1. Hedef = `params.modem_ip` (ping_modem) veya `params.internet_ip` (ping_internet).
2. `subprocess.Popen` → çıktı log dosyasına yazılır (`logs/<session>/<node>/full_<node>_ping_<label>_<ip>_<ts>.txt`).
3. Saniyede bir döngüde:
   - `ctx.stop.is_set()` ise → `proc.terminate()`, status `stopped`.
   - `proc.poll() is not None` ise → süre dolmadan bitti, döngüden çık.
   - Aksi halde `ctx.progress((i+1)/duration*100, "running", "Ping i+1/duration → target")`.
4. Bitince `returncode` 0 ise `completed`, değilse `error`.

### 4.2 `youtube_runner.py`
[`common/runners/youtube_runner.py`](fullservice-backend/common/runners/youtube_runner.py)

**Mantık:**
- Link, `youtu` içeriyorsa sonuna `&vq=hd1080` eklenir (1080p zorlama).
- `webbrowser.open(quality_link)` → makinenin **varsayılan tarayıcısı** o sekmede video açar (HD bant kullanır → modeme yük).
- Test, `duration` saniye boyunca "oynuyor" sayılır; her saniye `ctx.progress` ile dashboard'a yansıtılır.
- `ctx.stop` gelirse erken biter (sekme açık kalır — kapatma OS'a göre güvenilmez; abanma sırasında zaten istenen davranış).

### 4.3 `iperf_runner.py` — modeme **abanma**nın motoru
[`common/runners/iperf_runner.py`](fullservice-backend/common/runners/iperf_runner.py)

**Komut:**
```
iperf3 -c <iperf_server> -p <iperf_port> -t <duration> -P <iperf_parallel>
```

- `iperf_server` = Linux sunucunun LAN IP'si (orkestratör otomatik doldurur).
- `-P 4` paralel akış → modemin switch/Wi-Fi/yönlendirme katmanı zorlanır.

**Akış:**
1. `Popen(cmd)` → stdout log dosyasına gider.
2. `FileNotFoundError` yakalanır → "iperf3 kurulu değil" mesajıyla `error`.
3. Süre boyunca saniyede bir `ctx.progress`.
4. `ctx.stop` → `terminate`.
5. Bitince log'un içinden son `sender/receiver` Mbits/sec özetini regex'le çıkarıp mesaja koyar:
   `"iperf bitti — gönderen 940 Mbits/sec, alıcı 936 Mbits/sec"`

**Sunucu tarafı** ([`server/iperf_server.py`](fullservice-backend/server/iperf_server.py)):
- Oturum başlarken `ensure_running(port)` ile `iperf3 -s -p 5201` ayağa kaldırılır.
- `iperf3 -s` kurulu değilse log atar, Mac'lerin agent'ı bu durumda `error` gösterir.

### 4.4 `torrent_runner.py` — **Faz 4: simülasyon**
[`common/runners/torrent_runner.py`](fullservice-backend/common/runners/torrent_runner.py)

Şu an `duration` boyunca sahte ilerleme üretir; pipeline bütünlüğünü
kanıtlamak için yeterli. Hedef: GRK'nın `gbtorrent.py` mantığını
(qBittorrent Web API ile sonsuz indirme döngüsü) buraya port etmek.

### 4.5 `wifi_track_runner.py` — **Faz 4: simülasyon**
[`common/runners/wifi_track_runner.py`](fullservice-backend/common/runners/wifi_track_runner.py)

Hedef: platforma özgü WLAN okuma
(`netsh wlan show interfaces` / `system_profiler SPAirPortDataType`) ile
saniyelik sinyal/kanal/rx-tx örnekleme + Excel çıktısı.

### 4.6 Registry — TestType'ı runner'a bağlama
[`common/runners/registry.py`](fullservice-backend/common/runners/registry.py)

```python
RUNNERS = {
    "ping_internet": ping_runner.run_internet,
    "ping_modem":    ping_runner.run_modem,
    "youtube":       youtube_runner.run,
    "iperf":         iperf_runner.run,
    "torrent":       torrent_runner.run,
    "wifi_track":    wifi_track_runner.run,
}
```

Yeni test eklemek için: runner dosyasını yaz, `TestType`'a değer ekle, buraya bir satır. Başka yeri değiştirmek **gerekmez**.

---

## 5. Sunucu (Orkestratör)

[`server/orchestrator.py`](fullservice-backend/server/orchestrator.py)
[`server/main.py`](fullservice-backend/server/main.py)

`Orchestrator` tek örnektir; `server/main.py`'de oluşur. **State'i bellektedir** ve
`threading.RLock` ile korunur.

### 5.1 Düğüm registry'si
```python
self.nodes: dict[str, dict] = {}     # node_id → runtime durum
# her düğüm: { node_id, label, conn, is_server, roles, ip, agent_port,
#              platform, online, last_seen, tests: { task: {progress,status,message,updated} } }
```

`config.json`'daki `nodes` listesinden başlatılır. Sunucu düğümü `is_server: true` ile işaretli; ona ait `online` her zaman `true`.

### 5.2 Kayıt (register)
Agent her 10 sn'de bir `POST /api/register`:
- IP, port, platform güncellenir.
- `last_seen = datetime.now()`.
- Heartbeat > 30 sn ise `get_state` o düğümü `offline` döner.

### 5.3 Progress aggregator
Agent her saniyede bir `POST /api/progress` atar → `update_progress(node_id, task, ...)` → `self.nodes[node_id]["tests"][task]` güncellenir.

Sunucu kendi yerel testleri için: runner'ın `ctx.progress` callback'i **doğrudan** aggregator'ı çağırır (HTTP yok, in-process):
```python
ctx = RunContext(
    node_id="server",
    progress=lambda p, s, m, _t=t: self.update_progress("server", _t, p, s, m),
    ...
)
```

### 5.4 Oturum başlatma — fan-out
`POST /api/session/start` → `Orchestrator.start_session(overrides)`:

1. `session_id = "FS_YYYYMMDD_HHMMSS"`.
2. `TestParams` inşa edilir: config defaults + dashboard override'ları + `iperf_server = self.server_lan_ip`.
3. Tüm düğümlerin test state'leri **sıfırlanır** (`progress=0, status=idle`).
4. Hangi düğümde "iperf" rolü varsa → `iperf_server.ensure_running()`.
5. Fan-out (**paralel** thread'lerde, biri offline ise diğerleri beklemesin):
   - **Sunucu düğümü** için: rolleri in-process thread'lerde başlat (runner çağrısı).
   - **Diğer düğümler** için: `POST http://<agent_ip>:<agent_port>/start` ile `StartCommand` gönder.
6. Dönüş: `{ session_id, dispatched: [...], skipped: [...] }`.

### 5.5 Durdurma
`POST /api/session/stop`:
- Sunucu-yerel testler için `self._server_stop.set()` (paylaşılan `threading.Event`).
- Her online agent'a `POST http://<ip>:<port>/stop`.

### 5.6 Log toplama
[`server/log_collector.py`](fullservice-backend/server/log_collector.py)

Agent `POST /api/logs/upload` (multipart: `node_id`, `session_id`, `file`):
```
logs/<session_id>/<node_id>/<dosya>
```
Sunucunun kendi yerel testleri zaten aynı klasöre (`logs/<session_id>/server/`)
yazar (`_run_server_local`'da `log_dir = LOGS_DIR/session_id/server`).

> Faz 5'te bu oturum klasörü FTPS + PostgreSQL'e yollanacak.

---

## 6. Agent

[`agent/main.py`](fullservice-backend/agent/main.py)
[`agent/test_executor.py`](fullservice-backend/agent/test_executor.py)

### 6.1 Açılış
`agent/main.py` env değişkenlerini okur:
- `FS_NODE_ID` — bu agent hangi düğümü temsil ediyor (örn. `mac_cable`).
- `FS_SERVER_URL` — sunucu adresi.
- `FS_AGENT_PORT` — agent'ın dinleyeceği port (varsayılan 8771).

Açılışta `_register_loop` arka plan thread'i başlar — 10 sn'de bir kayıt POST'lar.

### 6.2 Komut alma
Sunucu `POST /start` çağırınca FastAPI handler `TestExecutor.start(cmd)`'i tetikler.

[`TestExecutor`](fullservice-backend/agent/test_executor.py):
- Önceki çalışmayı durdurur (`self._stop.set()`).
- Yeni bir `threading.Event` oluşturur.
- `cmd.tests` listesindeki her test için ayrı thread başlatır:
  - `runner = get_runner(test)` — registry'den.
  - `RunContext(progress=callback, stop=event, log_dir=...)`.
  - `runner(params, ctx)` → log dosya yolları döner.
- Test bitince üretilen logları `self._upload(file_path)` ile sunucuya gönderir.

### 6.3 Progress push
Her runner `ctx.progress(p, s, m)` çağırınca:
```python
requests.post(f"{server}/api/progress", json={
  "node_id": ..., "session_id": ..., "task": ...,
  "progress": ..., "status": ..., "message": ...
}, timeout=3)
```
Hata yutulur — sunucu erişilemez olsa bile test devam eder (best-effort).

---

## 7. Frontend (Dashboard)

[`fullservice-frontend/src/`](fullservice-frontend/src/)

### 7.1 Bootstrapping
`main.js` → Vue + Pinia + Vuetify + global SCSS.

### 7.2 Store (`store/app.js`)
- State: `session, nodes, testLabels, serverLanIp, connected, overrides{...}`.
- `startPolling(1000ms)` → her saniye `fetchState()` → state tazelenir.
- `startTest()` → boş bırakılan override'ları gönderme, `POST /api/session/start`.

### 7.3 Bileşenler
- `App.vue` — üst layout (LiquidBackground + Topbar + ControlBar + grid).
- `Topbar.vue` — Türk Telekom SVG logosu + "FULL SERVİS" başlığı + oturum durumu chip + dark/light toggle.
- `ControlBar.vue` — 4 input (süre, modem IP, internet IP, YouTube linki) + Başlat (`primary`) + Durdur (`error`).
- `NodeCard.vue` — bir düğümün başlık + meta + test listesi.
- `TestRow.vue` — test ikonu + isim + yüzde + Vuetify `v-progress-linear` (status'a göre renk) + mesaj.

### 7.4 Tema
[`plugins/vuetify.js`](fullservice-frontend/src/plugins/vuetify.js):
- `primary = #E20074` (Türk Telekom magenta)
- `secondary = #0A84FF` (Apple blue, ikincil vurgu)
- Dark/light, `localStorage` ile kalıcı.

`LiquidBackground.vue` arkada 4 animasyonlu "blob" + blur overlay; magenta-mavi
gradient. Cam (glass-card) görünümü için kartlarda `backdrop-filter: blur(...)`.

---

## 8. Uçtan-Uca Akış (kronolojik)

```
T-∞   ▶  Linux sunucu açık, `python run_server.py` çalışıyor.
         Aggregator boş; "server" düğümü online.

T₀    ▶  Mac'te `python run_agent.py mac_cable http://LINUX:8770` başlatılır.
         agent/main.py → register_loop → POST /api/register
         Orchestrator → nodes["mac_cable"].online = True, ip/port güncellenir
         Dashboard 1 sn sonra GET /api/state → kart yeşil yanar.

T₁    ▶  win_wifi + mac_wifi de aynı şekilde register.

T₂    ▶  Kullanıcı tarayıcıdan "FULL Servis Başlat" tuşuna basar.
         ControlBar.onStart() → store.startTest() → POST /api/session/start

T₃    ▶  Orchestrator.start_session:
         (a) session_id, TestParams hazırlanır.
         (b) iperf rolü var → iperf3 -s ayağa kalkar.
         (c) Sunucu kendi rolleri (ping_internet, ping_modem, youtube) için thread'ler başlatır.
         (d) PARALEL:
             POST http://mac_cable_ip:8771/start  StartCommand{...}
             POST http://win_wifi_ip:8771/start   StartCommand{...}
             POST http://mac_wifi_ip:8772/start   StartCommand{...}

T₃+ε  ▶  Her agent: TestExecutor.start → her testi bir thread'de koşar.
         Saniyede 1 → POST /api/progress (her test ayrı).

T₃→T₃+duration ▶  Dashboard 1 sn polling ile bar'ları doldurur. Tüm 4 düğüm
                  paralel — modem zorlanıyor.

Tend  ▶  Runner'lar sırayla "completed" yayar.
         Agent: her test bitince log dosyasını POST /api/logs/upload ile yollar.
         Sunucu: log_collector → logs/<session>/<node>/<dosya>

         (Faz 5'te buradan FTPS + PostgreSQL + mail/Telegram tetiklenecek.)

Tstop ▶  Kullanıcı "Durdur" → /api/session/stop → server_stop.set() + her agent'a /stop.
         Tüm runner'lar ctx.stop görür, temiz çıkar, "stopped" yayar.
```

---

## 9. Yeni bir test tipi eklemek

1. **Runner** yaz: `common/runners/<isim>_runner.py`. `def run(params, ctx) -> list[str]`.
2. **TestType** ekle: [`common/protocol.py`](fullservice-backend/common/protocol.py) → enum'a yeni satır + `TEST_LABELS` sözlüğüne insan-okunur etiket.
3. **Registry**'ye satır ekle: [`common/runners/registry.py`](fullservice-backend/common/runners/registry.py).
4. **config.json**'da ilgili düğümün `roles` listesine yeni test adını yaz.
5. **Frontend ikon** (opsiyonel): [`TestRow.vue`](fullservice-frontend/src/components/TestRow.vue) içindeki `testIcon` haritasına bir mdi-* ekle.

Hepsi bu kadar. Diğer kod değişmeden çalışır — eklenti tabanlı.

---

## 10. Sık sorulanlar

- **iperf3 paralel iki Mac aynı port'a bağlanırsa ne olur?** Şimdilik tek port; biri kuyruğa alınır. Faz 4'te her Mac'e ayrı port (5201/5202) vereceğiz.
- **Agent kapanırsa?** Heartbeat 30 sn'de bir → 30+ sn sessiz ise dashboard'da `offline`. Sunucu sessizce skip eder, log atar.
- **Sunucu çökerse agent'lar ne yapar?** Testler devam eder (yerel `Popen`); push başarısız olur ama yutulur. Sunucu geri gelince register loop tekrar bağlanır.
- **State neden bellekte? Yeniden başlatınca kaybolur.** Faz 5'te oturum kalıcılığı PostgreSQL'e taşınacak. Şimdilik bellek + log dosyaları yeterli.

---

## 11. Test Etmek

Tek-makinede entegrasyon testi (örnek):
- `fullservice-backend/` altında: `python run_server.py`.
- Aynı makinede 3 terminal, farklı `FS_AGENT_PORT` ile 3 agent.
- Dashboard'u `http://localhost:5173` (dev) veya `http://localhost:8770` (build).

Üretim (4 fiziksel makine) için: [`fullservice-backend/KURULUM_TEST.md`](fullservice-backend/KURULUM_TEST.md).

---

> Bu doküman canlıdır — yeni bir runner eklediğinde §4'e, yeni endpoint eklediğinde §3'e bir satır eklemek 60 saniye sürer ve gelecek-sen'in zihinsel modelini güncel tutar.
