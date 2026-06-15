# Kod Hakimiyeti Rehberi — FULL Servis

Bu dosya, kodu **hangi sırayla okursan en hızlı hakim olursun** sorusunun cevabıdır.
Amaç: dosyaları rastgele açıp kaybolmadan, "bir isteğin baştan sona nasıl aktığını"
takip ederek öğrenmek. Her bölümde **ne okuyacağın**, **neden** ve **dikkat edeceğin
anahtar fonksiyon** yazılı.

> Derinlemesine runner içyüzü ve mimari kararlar için ayrıca [`MIMARI.md`](MIMARI.md).
> Bu rehber "okuma rotası"dır; MIMARI.md "referans"tır.

---

## 0. Önce zihinsel model (5 dakika, kod okumadan)

Sistem 3 parçadan oluşur:

```
   [ Linux Sunucu ]  ←──HTTP──  [ Agent'lar: Mac/Win/Mac ]
   orkestratör + dashboard       listener (boot'ta açılır)
        │                              │
        │ /start fan-out               │ /start gelince runner'ları koşar
        ▼                              ▼
   tarayıcıdaki Vue arayüz       ping / youtube / iperf / torrent / wifi_track
```

- **Sunucu** beyindir: düğümleri tanır, "başlat" komutunu herkese dağıtır,
  ilerlemeyi toplar, dashboard'ı servis eder.
- **Agent = listener**: her client makinede açılışta çalışan küçük bir FastAPI.
  Sunucudan komut gelince kendine atanan testleri (runner'lar = "executer") koşar.
- **Frontend** sadece sunucuyla `/api/...` üzerinden konuşur; mantık taşımaz,
  durumu gösterir + kullanıcı girdisini toplar.

Tek cümle: **"Sunucu dağıtır, agent koşar, frontend gösterir."**

---

## 1. Ortak dil — `common/` (BURADAN BAŞLA)

Sunucu ve agent aynı "sözleşmeyi" paylaşır. Bunu anlamadan gerisi havada kalır.

| Sıra | Dosya | Neden önce bu? | Anahtar |
|------|-------|----------------|---------|
| 1 | [`fullservice-backend/common/protocol.py`](fullservice-backend/common/protocol.py) | Sistemin "dili": hangi test tipleri var, sunucu↔agent mesaj formatları (pydantic) | `TestType`, `TestStatus`, `RegisterRequest`, `StartCommand`, `ProgressUpdate`, `TestParams` |
| 2 | [`fullservice-backend/common/config.py`](fullservice-backend/common/config.py) | Topoloji + portlar + statik IP planı buradan okunur | `load_config()`, `detect_lan_ip()`, `_FALLBACK` |
| 3 | [`fullservice-backend/config.json`](fullservice-backend/config.json) | Gerçek değerler: 4 düğüm, roller, `agent_port: 7531`, `network` bölümü | `nodes`, `network.assignments` |
| 4 | [`fullservice-backend/common/runners/base.py`](fullservice-backend/common/runners/base.py) | Her testin uyduğu sözleşme: `run(params, ctx) -> list[str]` | `RunContext`, `log_path()` |
| 5 | [`fullservice-backend/common/runners/registry.py`](fullservice-backend/common/runners/registry.py) | Test adı → runner fonksiyonu eşlemesi | `get_runner()` |

Sonra bir-iki somut runner'a göz at (hepsini okuma, deseni gör):
[`ping_runner.py`](fullservice-backend/common/runners/ping_runner.py) (en sade) ve
[`iperf_runner.py`](fullservice-backend/common/runners/iperf_runner.py).
**Dikkat:** her runner sonunda `return [log_file]` ile ürettiği log dosyasının
yolunu döndürür — bu, log toplama akışının (Bölüm 4) kalbidir.

---

## 2. Sunucu — `server/` (sistemin beyni)

| Sıra | Dosya | Ne öğrenirsin | Anahtar |
|------|-------|---------------|---------|
| 6 | [`fullservice-backend/server/main.py`](fullservice-backend/server/main.py) | Tüm `/api/*` uçları tek yerde — sistemin "kapısı" | `register`, `progress`, `session_start/stop`, `health_check`, `firmware_*` |
| 7 | [`fullservice-backend/server/orchestrator.py`](fullservice-backend/server/orchestrator.py) | Asıl mantık: registry, progress toplama, fan-out, health-check | `register()`, `update_progress()`, `start_session()`, `health_check()`, `get_state()` |
| 8 | [`fullservice-backend/server/log_collector.py`](fullservice-backend/server/log_collector.py) | Agent'lardan gelen logların `logs/<session>/<node>/` altına yazılması | `save_upload()` |
| 9 | [`fullservice-backend/server/iperf_server.py`](fullservice-backend/server/iperf_server.py) | iperf3 sunucusunun gerektiğinde kaldırılması | `ensure_running()` |

`main.py`'yi okurken şunu fark et: **API uçları, en sona konan statik dosya
mount'undan (`StaticFiles` "/" ) ÖNCE tanımlanır** ki `/api/...` gölgelenmesin.

---

## 3. Agent — `agent/` (listener + executer)

| Sıra | Dosya | Ne öğrenirsin | Anahtar |
|------|-------|---------------|---------|
| 10 | [`fullservice-backend/agent/main.py`](fullservice-backend/agent/main.py) | Listener: `/health`, `/start`, `/stop` + sunucuya kayıt/heartbeat döngüsü | `_register_loop()`, `start()` |
| 11 | [`fullservice-backend/agent/test_executor.py`](fullservice-backend/agent/test_executor.py) | Executer: atanan testleri thread'lerde koşar, progress push + log upload | `start()`, `_run_one()`, `_push()`, `_upload()` |

Burada **"listener vs executer"** netleşir: `agent/main.py` dinler, gelen `/start`
komutuyla `test_executor` runner'ları (executer) ayağa kaldırır.

`run_server.py` ve `run_agent.py` sadece kısayol başlatıcılardır; en sona bakılır.

---

## 4. İKİ KRİTİK AKIŞI uçtan uca izle (asıl hakimiyet burada kurulur)

Yukarıdaki dosyaları tek tek değil, **akış halinde** birleştir:

### Akış A — "Başlat"a basınca ne oluyor?
1. Frontend `POST /api/session/start` → `main.py:session_start`
2. → `orchestrator.start_session()`: session_id üretir, test durumlarını sıfırlar,
   **online agent'lara paralel** `/start` gönderir (fan-out), sunucunun kendi
   rollerini in-process thread'de koşar.
3. Agent `main.py:start` → `test_executor.start()` → her test için `_run_one()`
4. `_run_one` runner'ı çağırır → runner `ctx.progress(...)` ile ilerleme bildirir
   → `_push()` `POST /api/progress` ile sunucuya iter.
5. Test bitince runner `[log_file]` döner → `_upload()` `POST /api/logs/upload`
   → `log_collector.save_upload()` `logs/<session>/<node>/` altına yazar.
6. Frontend 1 sn'de bir `GET /api/state` çekip ilerlemeyi canlı gösterir.

### Akış B — Aşamalı Health-Check (kullanıcının özellikle sorduğu)
- **Karar (ne sıklıkta):** frontend [`store/app.js`](fullservice-frontend/src/store/app.js)
  → `HC_SCHEDULE` tablosu + `startHealthCheck()`. Özyinelemeli `setTimeout` ile
  1sn×3 → 3sn×3 → 5sn×3 → 15sn → 30sn → sürekli 60sn yürütülür.
- **Ölçüm (tek anlık kontrol):** her tick `GET /api/health-check`
  → `orchestrator.health_check()` her düğümün `:7531/health`'ine **paralel** istek
  atıp `{node_id: {reachable, latency_ms}}` döner.
- **Gösterim:** sonuç `store.health.results`'a yazılır; hem sağ panel
  ([`StatusPanel.vue`](fullservice-frontend/src/components/StatusPanel.vue)) hem
  ortadaki kartlar ([`NodeCard.vue`](fullservice-frontend/src/components/NodeCard.vue))
  **aynı** veriden beslenir → periyotlar otomatik birebir aynı.
- **Ön koşul:** health-check başlatılmadan test başlamaz —
  `store.requireHealthCheck()` + `DeviceForm.onStart` kontrolü.

---

## 5. Firmware DB — combobox kaynağı

| Sıra | Dosya | Ne öğrenirsin | Anahtar |
|------|-------|---------------|---------|
| 12 | [`fullservice-backend/common/firmware_db.py`](fullservice-backend/common/firmware_db.py) | GRK ile aynı PostgreSQL'e SSL bağlantı + marka/model/sürüm sorguları; bağlantı yoksa **çökmez** | `db_available()`, `get_brands/get_models/get_versions` |

`main.py`'deki `/api/firmware/*` uçları bunu sarar; DB yoksa **503** döner.
Frontend bu 503'ü yakalayıp combobox'ı **serbest-metin**e düşürür (graceful degrade).

---

## 6. Frontend — `fullservice-frontend/src/`

Sunucuyu anladıktan sonra frontend kolaydır; sadece API'yi tüketir.

| Sıra | Dosya | Ne öğrenirsin | Anahtar |
|------|-------|---------------|---------|
| 13 | [`services/api.js`](fullservice-frontend/src/services/api.js) | Tüm HTTP çağrıları tek dosyada (axios) | `fetchState`, `startSession`, `healthCheck`, `getBrands/getVersions` |
| 14 | [`store/app.js`](fullservice-frontend/src/store/app.js) | Tüm durum + eylemler (Pinia): polling, firmware yükleme, **health-check zamanlayıcı**, startTest | `refresh()`, `startPolling()`, `loadBrands()`, `startHealthCheck()`, `startTest()` |
| 15 | [`App.vue`](fullservice-frontend/src/App.vue) | İskelet: sol ana içerik + sağ panel düzeni, lifecycle | `onMounted` (polling + loadBrands), `onBeforeUnmount` |
| 16 | [`components/DeviceForm.vue`](fullservice-frontend/src/components/DeviceForm.vue) | GRK Günlük Rutin sekmesi örnek: Marka/Model/Firmware + Süre + Başlat (ön koşul kontrolü) | `onStart()` |
| 17 | [`components/StatusPanel.vue`](fullservice-frontend/src/components/StatusPanel.vue) | Sağ panel: Health-Check butonu + kırmızı/yeşil ışıklar | `onHealthCheck()`, `dotClass()` |
| 18 | [`components/NodeCard.vue`](fullservice-frontend/src/components/NodeCard.vue) + [`TestRow.vue`](fullservice-frontend/src/components/TestRow.vue) | Tek düğüm kartı + tek test ilerleme satırı; online ışığı health'ten beslenir | `dotClass`, `stateText` |

(`Topbar.vue`, `LiquidBackground.vue` sadece görseldir; en sona, merak edersen.)

---

## 7. Saha kurulumu — `provisioning/`

Kod mantığı değil, işletim sistemi entegrasyonu. En sona bırak.

- [`provisioning/README.md`](fullservice-backend/provisioning/README.md) — özet.
- Statik IP: `macos/set-static-ip.sh`, `windows/set-static-ip.ps1`, `linux/set-static-ip.sh`
  (hepsi `config.json`'un `network` bölümünü okur).
- Boot listener: `macos/*launchd*`, `windows/install-agent-task.ps1`, `linux/*systemd*`.

---

## Önerilen toplam rota (özet)

```
common/protocol.py  →  config.py + config.json  →  runners/base.py + registry.py
   →  bir runner (ping)  →  server/main.py  →  server/orchestrator.py
   →  server/log_collector.py  →  agent/main.py  →  agent/test_executor.py
   →  [AKIŞ A'yı kafanda birleştir]  →  firmware_db.py
   →  frontend: api.js → store/app.js → App.vue → DeviceForm/StatusPanel/NodeCard
   →  [AKIŞ B'yi kafanda birleştir]  →  provisioning/
```

İlk turda **Akış A** ve **Akış B**'yi kağıda çizerek takip et; gerisi detaydır.
Takıldığın her noktada ilgili dosyanın başındaki docstring'i oku — her dosya
"ben ne işe yararım" diye kendini anlatır.
