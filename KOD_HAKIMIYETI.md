# FULL Servis — Kod Hakimiyeti Rehberi (Java'dan gelenler için)

Bu doküman, projedeki **Python** kodunu açar.

> Mevcut durum + sıradaki adımlar için: [`CHANGELOG.md`](CHANGELOG.md).
> Bu dosya **kodu okuma** rehberidir. Kurulum için: `fullservice-backend/KURULUM_SAHA_4_MAKINE.md`.

---

## 0. 30 saniyede zihin haritası

- **Java projesi gibi düşün:** `common/` = ortak kütüphane (model + util), `server/`
  = orkestratör (Spring Boot Controller gibi), `agent/` = her client makinede koşan
  küçük servis. `fullservice-frontend/` = ayrı bir Vue (JavaScript) uygulaması.
- **Çalışan iki program var:** `run_server.py` (Linux'ta, beyin) ve `run_agent.py`
  (her Mac/Windows'ta, kol-bacak). Aralarında **HTTP/JSON** konuşurlar (REST gibi).
- **Bir "test"** (ping, youtube, iperf, torrent, wifi_track) = `common/runners/`
  altında tek bir `run(params, ctx)` fonksiyonu. Hepsi aynı sözleşmeye uyar
  (Java'daki bir `interface` gibi, ama Python'da yazılı sözleşme = aynı imza).

---

## 1. Python ↔ Java sözlüğü (en çok karıştıranlar)

| Python                         |                            Java karşılığı / açıklaması                              |
|--------------------------------|-------------------------------------------------------------------------------------|
| `def f(a, b): ...`             | `... f(a, b) { ... }` — dönüş tipi zorunlu değil.                                   |
| `self`                         | `this` — ama **açıkça** ilk parametre olarak yazılır: `def m(self, x)`.             |
| `__init__(self, ...)`          | Constructor.                                                                        |
| Girinti (indent)               | `{ }` yerine **boşluk girintisi** blok belirler. Süslü parantez YOK.                |
| `x: int = 5`                   | Tip ipucu (`int x = 5`). **Çalışma zamanında zorlanmaz**, sadece okunabilirlik/IDE. |
| `None`                         | `null`.                                                                             |
| `True / False`                 | `true / false`.                                                                     |
| `dict` `{ "a": 1 }`            | `Map<String,Object>` (HashMap).                                                     |
| `list` `[1, 2]`                | `List` (ArrayList).                                                                 |
| `tuple` `(1, 2)`               | Değişmez (immutable) liste; sabit demet.                                            |
| `f"merhaba {ad}"`              | String template: `"merhaba " + ad`. (f-string)                                      |
| `# yorum`                      | `// yorum`. `"""..."""` = çok satırlı yorum/doküman (Javadoc gibi).                 |
| `import x` / `from p import f` | `import` (paket = klasör; her klasörde `__init__.py`).                              |
| `raise X(...)` / `try/except`  | `throw` / `try/catch` (`except` = `catch`).                                         |
| `with open(...) as f:`         | try-with-resources: blok bitince dosya otomatik kapanır.                            |
| `lambda p, s, m: ...`          | Lambda: `(p, s, m) -> ...`.                                                         |
| `@dataclass`, `@app.get(...)`  | **Anotasyon gibi görünür ama "decorator"dır** (aşağıda).                            |
| `[t for t in xs if cond]`      | Stream: `xs.stream().filter(cond).collect(...)`. (list comprehension)               |
| `a or b`                       | `a != null/0/""/[] ? a : b` — "ilk doğru/dolu olan".                                |
| `*args, **kwargs`              | Değişken sayıda argüman (varargs) + isimli argüman sözlüğü.                         |

---

## 2. Sık geçen Python "sihirleri" (kodda görünce şaşırma)

### 2.1 Decorator (`@...`)
```python
@app.get("/api/state")
def state():
    return orch.get_state()
```
`@app.get(...)` bir **decorator**'dır: alttaki fonksiyonu alır, sarmalar, ekstra
davranış ekler. Burada FastAPI'ye "bu fonksiyon `GET /api/state` isteğini karşılar"
der — Spring'deki `@GetMapping("/api/state")` ile **birebir** aynı mantık.

### 2.2 `with` bloğu (try-with-resources)
```python
with open(log_file, "w", encoding="utf-8") as f:
    f.write("...")
# blok bitince f otomatik kapanır (finally gerekmez)
```

### 2.3 `or` ile varsayılan değer
```python
duration = overrides.get("duration") or self.defaults.get("duration", 60)
```
"Soldaki **boş/None/0 değilse** onu, değilse sağdakini kullan." Java'da:
`overrides.getDuration() != null ? overrides.getDuration() : 60`.

### 2.4 List comprehension (mini for-döngüsü)
```python
online = [n for n in self.nodes.values() if n["online"]]
```
= "nodes içinden online olanları topla". Java Stream:
`nodes.values().stream().filter(n -> n.online).toList()`.

### 2.5 `dict` her yerde
Python'da konfig, durum, JSON gövdeleri hep `dict` (Map). `node["roles"]`,
`node.get("ip")` (anahtar yoksa None döner — `getOrDefault` gibi). Java'daki tipli
sınıflar yerine çoğu yerde Map kullanılır; tip güvenliği yoktur, dikkat.

### 2.6 İş parçacıkları (threads)
```python
threading.Thread(target=self._worker, daemon=True).start()
ctx.stop = threading.Event()   # ortak "dur" bayrağı
if ctx.stop.is_set(): return    # döngü içinde durmayı kontrol et
```
`threading.Thread` = `new Thread(runnable).start()`. `threading.Event` = paylaşılan
boolean bayrak (`AtomicBoolean` gibi); `.set()` = true yap, `.is_set()` = oku.
`daemon=True` = ana program kapanınca bu thread de ölsün.

---

## 3. Dosya dosya gezinti (okuma sırası)

> İpucu: Kodu "çalışma sırasına" göre oku. Aşağıda bir testin baştan sona izlediği
> yol var. Java'daki "main → controller → service → util" zincirini düşün. 


### 3.1 Giriş noktaları (main)
- [`fullservice-backend/run_server.py`](fullservice-backend/run_server.py) — Linux'ta
  çalışan **sunucu** main'i. `uvicorn.run(app, ...)` = gömülü web sunucusunu başlatır
  (Spring Boot'un `SpringApplication.run` gibi). `app`, `server/main.py`'den gelir.
- [`fullservice-backend/run_agent.py`](fullservice-backend/run_agent.py) — her
  client'ta çalışan **agent** main'i. Argümanları (node_id, server_url, port) ortam
  değişkenine koyup `agent/main.py`'deki `app`'i başlatır.
- [`launchers/build/server_app.py`](launchers/build/server_app.py) +
  [`agent_app.py`](launchers/build/agent_app.py) — **son kullanıcının çift tıkladığı**
  paketlenmiş uygulamaların giriş noktaları (PyInstaller). Yukarıdaki iki `run_*.py`'nin
  "terminalsiz" hali: eski örneği kapatır, agent kimliğini **dosya adından** çözer,
  sunucuda paneli tarayıcıda açar. Derleme/kurulum: [`launchers/KURULUM.md`](launchers/KURULUM.md).

### 3.2 Sunucu tarafı (`server/`)
- [`server/main.py`](fullservice-backend/server/main.py) — **Controller katmanı.**
  Tüm `@app.get/@app.post` endpoint'leri burada (`/api/login`, `/api/register`,
  `/api/progress`, `/api/result`, `/api/logs/upload`, `/api/state`, `/api/session/start`,
  `/api/session/stop`, `/api/session/reset`, `/api/health-check`, `/api/firmware/...`).
  Her endpoint ince; işi `orch`'a (orchestrator) veya ilgili servise devreder. Ayrıca
  stdout/stderr'i `logs/app.log`'a aynalayan bir `_Tee` kurar (error_log için). En sonda
  `app.mount("/")` ile Vue arayüzünü (statik dosyalar) servis eder.
- [`server/orchestrator.py`](fullservice-backend/server/orchestrator.py) — **Beyin
  (Service katmanı).** Düğüm kaydı, ilerleme toplama, "başlat/durdur/sıfırla"
  komutlarını tüm agent'lara dağıtma (fan-out), health-check. Tüm durum bellekte bir
  `dict`'te tutulur, `threading.RLock` ile korunur (Java'daki `synchronized` gibi).
  Test sonuçlarını (`record_result`) DB'ye + log'u FTP'ye yazar; tüm testler bitince
  (kenar-yakalama) bildirim + error_log tetikler.
- [`server/auth_service.py`](fullservice-backend/server/auth_service.py) — **Login.**
  `login(username, password)`: önce `cpeteam/cpeteam` varsayılanı, sonra `grk_users`
  tablosu (bcrypt/md5/sha256/düz metin). DB kapalıyken bile varsayılan hesap çalışır.
- [`server/db_service.py`](fullservice-backend/server/db_service.py) — **DB yazma.**
  `create_session` / `update_session_end` / `save_ping` / `save_iperf` / `save_wifi`.
  Şu an `copy_` staging tablolarına yazar; tablo adları en üstteki sabitlerde (birleştirme
  tek noktadan). DB yoksa sessizce atlar.
- [`server/ftp_service.py`](fullservice-backend/server/ftp_service.py) — **FTP yükleme.**
  `<MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<Bilgisayar>/` klasör yapısına
  (gerekirse oluşturarak) log yükler; arka planda (daemon thread).
- [`server/notify.py`](fullservice-backend/server/notify.py) +
  [`email_sender.py`](fullservice-backend/server/email_sender.py) +
  [`notification_service.py`](fullservice-backend/server/notification_service.py) —
  **Bildirim.** Telegram (mesaj + özet log dosyaları) ve mail (sadece mesaj). GRK ile
  birebir. Test bitince `send_completion` çağrılır. Sırlar `get_secret`'tan gelir.
- [`server/log_capture.py`](fullservice-backend/server/log_capture.py) — **error_log.**
  `logs/app.log`'un oturum dilimini kesip `FULL_Service_errorlog_<...>.log` olarak
  FTP'ye yükler (bildirim YOK).
- [`server/excel_service.py`](fullservice-backend/server/excel_service.py) — Ping/Wifi
  için Excel üretir (başka oturumda eklendi).
- [`server/log_collector.py`](fullservice-backend/server/log_collector.py) —
  Agent'lardan gelen log dosyalarını `logs/<BILGISAYAR>/<session>/` altına yazar.

### 3.3 Agent tarafı (`agent/`)
- [`agent/main.py`](fullservice-backend/agent/main.py) — Küçük bir FastAPI servisi.
  Açılışta sunucuya kayıt olur + 10 sn'de bir heartbeat (`_register_loop`). Sunucudan
  `POST /start` gelince testleri başlatır, `POST /stop` ile durdurur.
- [`agent/test_executor.py`](fullservice-backend/agent/test_executor.py) — Sunucudan
  gelen komuttaki her testi **ayrı thread**'de koşar, ilerlemeyi sunucuya iter
  (`POST /api/progress`), test bitince log dosyasını yükler.

### 3.4 Ortak sözleşme + testler (`common/`)
- [`common/protocol.py`](fullservice-backend/common/protocol.py) — **Modeller (DTO).**
  `TestType` (enum: ping/youtube/iperf/...), `TestParams` (test parametre paketi),
  `RegisterRequest`, `StartCommand`, `ProgressUpdate`. Bunlar **pydantic** modelleridir
  = otomatik JSON ↔ nesne doğrulaması (Java'da Jackson + Bean Validation gibi).
- [`common/config.py`](fullservice-backend/common/config.py) — `config.json`'u okur;
  `node_log_folder()`, `detect_lan_ip()` gibi yardımcılar. Ayrıca **`get_secret(key)`**:
  sırları önce ortam değişkeninden, yoksa gitignore'lu `secrets.json`'dan okur (kodda
  asla hardcoded sır yok). **Paketlenmiş modda** (`IS_FROZEN`) yollar `app_dir()` ile
  exe'nin yanındaki `ayarlar/` + `logs/` klasörlerine çözülür; `resolve_node_id()`
  agent'ın kimliğini uygulamanın dosya adından bulur.
- [`common/app_boot.py`](fullservice-backend/common/app_boot.py) — çift tıklanan
  uygulamaların açılış yardımcıları: `free_port()` (eski örneği kapat),
  `open_browser_later()` (paneli aç), `banner()`, `hold_on_error()`.
- [`common/firmware_db.py`](fullservice-backend/common/firmware_db.py) — Marka/Model/
  Firmware için PostgreSQL erişimi (SSL). Bağlantı kurulamazsa **çökmez**, üst katman
  serbest-metne düşer.
- [`common/runners/`](fullservice-backend/common/runners/) — **Her test bir runner.**
  Hepsi aynı **sözleşmeyi** uygular (Java `interface` gibi):
  ```python
  def run(params: TestParams, ctx: RunContext) -> list[str]:
      # testi çalıştır, ctx.progress(...) ile ilerleme bildir,
      # ctx.stop.is_set() ise temiz çık, ürettiğin log dosyası yollarını döndür
  ```
  - `base.py` → `RunContext` (log klasörü + stop bayrağı + progress callback) +
    görünür terminal yardımcıları (`open_terminal_running`, `open_log_viewer`).
  - `ping_runner.py`, `youtube_runner.py`(+`youtube_util.py`), `iperf_runner.py`,
    `iperf_server_runner.py`, `torrent_runner.py`(+`torrent_util.py`),
    `wifi_track_runner.py`(+`wifi_util.py`/`wifi_util_mac.py`).
  - `registry.py` → `"test adı" → run fonksiyonu` sözlüğü (Java'da `Map<String,
    Runner>` veya bir factory). Yeni test eklemek = runner yaz + buraya 1 satır.

### 3.5 `RunContext` — "interface" yerine geçen sözleşme nesnesi
```python
@dataclass
class RunContext:
    node_id: str
    session_id: str
    log_dir: str
    progress: ProgressCb          # (yüzde, durum, mesaj) -> None  (callback)
    stop: threading.Event         # "dur" bayrağı
```
`@dataclass` = Java'da Lombok `@Data`/record gibi; alanlardan otomatik constructor
üretir. `progress` bir **fonksiyon referansı**dır (callback) — runner ilerlemeyi
bununla bildirir; sunucu-yerelde doğrudan belleğe, agent'ta HTTP'ye gider. Java'da
bunu bir `interface ProgressCallback { void report(...) }` ile yapardın; Python'da
fonksiyonu doğrudan parametre olarak geçiyoruz.

---

## 4. Bir testin baştan sona yolu (uçtan uca)

1. **Dashboard** "Başlat" → `POST /api/session/start` (`server/main.py`).
2. `orchestrator.start_session()` → `TestParams` hazırlar, kendi (sunucu) rollerini
   in-process thread'lerde başlatır, **diğer düğümlere** `POST /start` atar.
3. Her agent (`test_executor.py`) komuttaki testleri thread'lerde koşar →
   `registry.get_runner("ping_modem")` → `ping_runner.run_modem(params, ctx)`.
4. Runner çalışırken `ctx.progress(yüzde, "running", "mesaj")` çağırır →
   agent bunu `POST /api/progress` ile sunucuya iter → dashboard 1 sn'de bir çekip
   barı doldurur.
5. Test bitince runner log dosyası yolunu döner → agent `POST /api/logs/upload` ile
   sunucuya yükler → `log_collector` `logs/<BILGISAYAR>/<session>/` altına yazar.
6. "Durdur" → `ctx.stop.set()` → runner döngüleri `if ctx.stop.is_set(): return`
   ile temiz çıkar.

---

## 5. "Şunu nerede değiştiririm?" hızlı dizin

| İstediğin | Bak buraya |
|-----------|-----------|
| Yeni bir test türü eklemek | `common/runners/<yeni>_runner.py` yaz + `protocol.TestType`'a değer + `registry.RUNNERS`'a 1 satır + config'de düğüm `roles`'üne ekle |
| Hangi makine hangi testi koşar | `config.json` → `nodes[].roles` |
| Statik IP / arayüz / log klasör adı | `config.json` → `network.assignments`, `nodes[].log_name` |
| Varsayılan süre / youtube linki / magnet | `config.json` → `defaults` |
| Bir endpoint eklemek/düzeltmek | `server/main.py` (+ mantık `orchestrator.py`) |
| Log dosya adı standardı | `common/runners/base.py` → `grk_style_filename`, `RunContext.grk_log_path` |
| DB'ye hangi tabloya yazılıyor (birleştirme) | `server/db_service.py` → en üstteki tablo adı sabitleri (`T_SESSION`…) |
| FTP klasör yapısı / test tipi eşlemesi | `server/ftp_service.py` → `build_target_dir`, `test_type_from_*` |
| Bildirim metni / alıcılar / tetikleme | `server/notification_service.py` (metin), `orchestrator._on_session_complete` (tetik) |
| Login / şifre doğrulama | `server/auth_service.py` (varsayılan hesap + `grk_users`) |
| Sırlar (Telegram/SMTP) | `secrets.json` veya ortam değişkeni; okuyucu `common/config.get_secret` |
| Test ilerleme/renk/etiket (arayüz) | `fullservice-frontend/src/components/TestRow.vue`, `protocol.TEST_LABELS` |
| Login / karşılama (arayüz) | `components/Login.vue`, `components/Welcome.vue`, `store/auth.js` |
| Sol form / oturum özeti (arayüz) | `fullservice-frontend/src/components/DeviceForm.vue` |
| Sağ panel / health-check (arayüz) | `fullservice-frontend/src/components/StatusPanel.vue`, `store/app.js` |

---

## 6. Kod yazım stili notu

Bu projedeki Python çoğunlukla **deyimsel (idiomatic) Python**'dır — kısa ve yoğun.
Java'dan gelen biri için bazı satırlar "fazla sihirli" gelebilir; yukarıdaki Bölüm
1–2 bu kalıpları çözer. Bundan sonra eklenecek kodda, okunabilirlik için mümkün
olduğunca **açık** (Java'ya yakın: erken-return, anlamlı değişken adları, tek satıra
sıkıştırmadan) yazmaya çalışacağız. Mevcut kod da gerektikçe bu yönde sadeleştirilebilir.
```
İpucu: Bir dosyayı okurken önce en üstteki """...""" açıklamasını oku (her dosyada
       Türkçe "ne işe yarar" özeti var), sonra fonksiyon imzalarına bak, en son
       gövdeye in. Java'da sınıfın Javadoc'unu okuyup metod imzalarına bakman gibi.
```
