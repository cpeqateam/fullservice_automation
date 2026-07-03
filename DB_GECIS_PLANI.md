# DB Geçiş Planı — Gerçek Birleşik Tablolar (Senaryo 3)

> **Nasıl kullanılır:** Aşağıyı **fazlar hâlinde** çalıştır. Her adımın sonunda
> **✅ Beklenen** kutusu var — çıktın ona uyuyorsa devam et, uymuyorsa bana yaz.
> SQL'ler pgAdmin'den; kod güncellemeleri ilgili Claude Code'lara (prompt'lar en altta).
> Amaç: yapboz çözmeden, satır satır okuyup ilerlemen.

---

## 0. Sistemin haritası (önce bunu anla)

| Katman | Ne | Kim kullanıyor |
|--------|----|----|
| `grk_*` tablolar | Asıl GRK verisi | **GRK** doğrudan yazar/okur (canlı) |
| **View'lar** (`firmware`,`users`,`test_session`,`ping_test`,`wifi_analysis`,`speed_test`) | `SELECT * FROM grk_*` geçişi | **grk-test-platform** (okuma paneli) `test_session/ping_test/wifi_analysis/speed_test`'i okur |
| `copy_*` tablolar | FULL Servis staging | FULL Servis yazar |

**Doğrulandı:** GRK kodu view'ları HİÇ kullanmıyor (`grk_firmware`, `grk_test_session`…
doğrudan). Yani **view'ları silmek GRK'yı etkilemez.** Sadece grk-test-platform bu
view'ları okuyordu → onu yeni tablolara yönlendireceğiz.

**Hedef:** View'ları sil → `copy_*`'i gerçek birleşik tablolara yükselt → GRK verisini
taşı → 3 kod tabanını (FULL, grk-test-platform, GRK) yeni tablolara çevir.

---

## 1. Hedef son durum

- **Gerçek tablolar:** `firmware`, `users`, `test_session`, `ping_test`, `wifi_analysis`,
  `speed_test`, `iperf_test`.
- Her sonuç satırında `test_name` ('GRK' / 'FULL_SERVIS') + `node_name` (makine ya da setup).
- **GRK + FULL** bu tablolara yazar; **grk-test-platform** bunlardan okur.
- `grk_*` ve `copy_*` en sonda emekli olur.

---

## 2. Fazlar (özet)

| Faz | Ne | Nasıl |
|-----|----|----|
| 0 | Yedek al | SQL-0 |
| 1 | `firmware` + `users` gerçek tablo | SQL-1 |
| 2 | Sonuç tablolarını kur (view sil + copy_ terfi) | SQL-2 |
| 3 | GRK verisini taşı | SQL-3 |
| 4 | FULL Servis kodu | Prompt B + sunucu restart |
| 5 | grk-test-platform kodu | Prompt C + docker rebuild |
| 6 | **Cutover (sonra):** GRK'yı geçir | Prompt A + FK/delta |

> **Sıra önemli:** 0→1→2→3 (DB), sonra 4 ve 5 (kod). Faz 6 en son.
> **Bilinçli not (Faz 5 sonrası, Faz 6 öncesi):** grk-test-platform yeni tabloları
> okuduğunda GRK'nın geçmişi + FULL verisi görünür; ama GRK **yeni** testleri hâlâ
> `grk_*`'a yazdığı için Faz 6'ya kadar panelde görünmez. Bu boşluğu Faz 6 kapatır.

---

# 📜 SQL Komutları (Faz 0–3)

> Neden `copy_*` rename? Sıfırdan `CREATE TABLE test_session (... SERIAL ...)` yapsak,
> Postgres `test_session_session_id_seq` adlı sequence'ı kurmaya çalışır — ama o ad
> `grk_test_session`'a ait, zaten var → çakışır. `copy_*` rename'i bunu çözer (kendi
> `copy_..._seq` sequence'ları çakışmaz).

## SQL-0 — Yedek

```sql
CREATE TABLE yedek_grk_firmware      AS SELECT * FROM grk_firmware;
CREATE TABLE yedek_grk_users         AS SELECT * FROM grk_users;
CREATE TABLE yedek_grk_test_session  AS SELECT * FROM grk_test_session;
CREATE TABLE yedek_grk_ping_test     AS SELECT * FROM grk_ping_test;
CREATE TABLE yedek_grk_wifi_analysis AS SELECT * FROM grk_wifi_analysis;
CREATE TABLE yedek_grk_speed_test    AS SELECT * FROM grk_speed_test;
```
> ✅ **Beklenen:** 6 `yedek_*` tablosu oluştu; her biri kaynağıyla **AYNI sayıda** satır.
> (Kesin sayıyı önceden bilemeyiz — istatistikler yaklaşık; `COUNT(*)` kesindir.)
> ```sql
> SELECT (SELECT count(*) FROM yedek_grk_test_session) AS yedek_ts,
>        (SELECT count(*) FROM grk_test_session)        AS kaynak_ts,   -- yedek_ts ile EŞİT
>        (SELECT count(*) FROM yedek_grk_ping_test)      AS yedek_ping,
>        (SELECT count(*) FROM grk_ping_test)            AS kaynak_ping; -- yedek_ping ile EŞİT
> ```

## SQL-1 — firmware + users gerçek tablo (view'ı sil, tablo kur)

```sql
BEGIN;
DROP VIEW IF EXISTS firmware;
DROP VIEW IF EXISTS users;

CREATE TABLE firmware AS SELECT * FROM grk_firmware;
ALTER TABLE firmware ADD PRIMARY KEY (firmware_id);

CREATE TABLE users AS SELECT * FROM grk_users;
ALTER TABLE users ADD PRIMARY KEY (user_id);
COMMIT;
```
> ✅ **Beklenen:** `firmware`/`users` artık VIEW değil TABLE. Kontrol:
> ```sql
> SELECT table_name, table_type FROM information_schema.tables
> WHERE table_schema='public' AND table_name IN ('firmware','users');
> -- ikisi de table_type='BASE TABLE' olmalı (artık VIEW değil)
> SELECT (SELECT count(*) FROM firmware) AS fw,
>        (SELECT count(*) FROM grk_firmware) AS grk_fw;   -- EŞİT olmalı (kopya)
> ```
> Not: `firmware`/`users`'ı şu an hiçbir kod okumuyor; Faz 6'da (cutover) asıl olacaklar.

## SQL-2 — Sonuç tablolarını kur (view'ları sil + copy_ terfi)

```sql
BEGIN;
-- grk-test-platform'un okuduğu view'ları kaldır (yerine gerçek tablo gelecek)
DROP VIEW IF EXISTS test_session;
DROP VIEW IF EXISTS ping_test;
DROP VIEW IF EXISTS wifi_analysis;
DROP VIEW IF EXISTS speed_test;

-- copy_ staging tablolarını final adlara yükselt (yapıları hazır, sequence'ları çakışmaz)
ALTER TABLE copy_test_session  RENAME TO test_session;
ALTER TABLE copy_ping_test     RENAME TO ping_test;
ALTER TABLE copy_wifi_analysis RENAME TO wifi_analysis;
ALTER TABLE copy_speed_test    RENAME TO speed_test;
ALTER TABLE copy_iperf_test    RENAME TO iperf_test;

-- test_session'a eksik iki kolon (node_name = setup/makine, has_iperf_test)
ALTER TABLE test_session ADD COLUMN IF NOT EXISTS node_name      VARCHAR(50);
ALTER TABLE test_session ADD COLUMN IF NOT EXISTS has_iperf_test BOOLEAN DEFAULT FALSE;
COMMIT;
```
> ✅ **Beklenen:** 5 ad artık gerçek TABLE (view değil). Asıl kontrol bu:
> ```sql
> SELECT table_name, table_type FROM information_schema.tables
> WHERE table_schema='public'
>   AND table_name IN ('test_session','ping_test','wifi_analysis','speed_test','iperf_test')
> ORDER BY table_name;   -- 5 satır, hepsi table_type='BASE TABLE'
> ```
> Satır sayıları şu an sadece FULL staging kadardır (copy_'den geldiği kadar; kesin sayı
> önemli değil, GRK verisi henüz gelmedi).

## SQL-3 — GRK verisini taşı (FULL staging SİLİNMEZ; GRK satırları yeni id alır)

```sql
BEGIN;

-- GRK satırlarını YENİ id ile ekliyoruz (FULL staging'e dokunmadan). Çocuk tabloların
-- bağı için geçici eşleme kolonu: _old_session_id = kaydın eski grk session_id'si.
ALTER TABLE test_session ADD COLUMN _old_session_id INTEGER;

-- 1) GRK oturumları → test_session (session_id OTOMATİK yeni; station_name → node_name)
INSERT INTO test_session
    (_old_session_id, firmware_id, test_name, node_name, session_start_time, session_end_time,
     test_duration, has_ping_test, has_speedtest, has_wifi_analysis, has_iperf_test,
     ftp_file_path, error_log_ftp_path, created_at)
SELECT session_id, firmware_id, 'GRK', station_name, session_start_time, session_end_time,
       test_duration, has_ping_test, has_speedtest, has_wifi_analysis, FALSE,
       ftp_file_path, error_log_ftp_path, created_at
FROM grk_test_session;

-- 2) GRK ping → ping_test (node_name = setup = ts.node_name)
INSERT INTO ping_test
    (session_id, test_name, node_name, target_ip, ip_version, total_pings,
     successful_pings, failed_pings, success_rate, packet_loss_percent,
     min_time, max_time, avg_time, median_time, std_dev_time,
     ftp_file_path, test_start_time, test_end_time, created_at)
SELECT ts.session_id, 'GRK', ts.node_name, p.target_ip, p.ip_version, p.total_pings,
       p.successful_pings, p.failed_pings, p.success_rate, p.packet_loss_percent,
       p.min_time, p.max_time, p.avg_time, p.median_time, p.std_dev_time,
       p.ftp_file_path, p.test_start_time, p.test_end_time, p.created_at
FROM grk_ping_test p
JOIN test_session ts ON ts._old_session_id = p.session_id;

-- 3) GRK wifi → wifi_analysis
INSERT INTO wifi_analysis
    (session_id, test_name, node_name, total_samples, disconnected_count, connected_count,
     channel, wifi_protocol, bssid, avg_signal_percentage, min_signal_percentage,
     max_signal_percentage, avg_rx_rate, avg_tx_rate, avg_cpu_usage, avg_ram_usage,
     ftp_file_path, test_start_time, test_end_time, created_at)
SELECT ts.session_id, 'GRK', ts.node_name, w.total_samples, w.disconnected_count, w.connected_count,
       w.channel, w.wifi_protocol, w.bssid, w.avg_signal_percentage, w.min_signal_percentage,
       w.max_signal_percentage, w.avg_rx_rate, w.avg_tx_rate, w.avg_cpu_usage, w.avg_ram_usage,
       w.ftp_file_path, w.test_start_time, w.test_end_time, w.created_at
FROM grk_wifi_analysis w
JOIN test_session ts ON ts._old_session_id = w.session_id;

-- 4) GRK speed → speed_test
INSERT INTO speed_test
    (session_id, test_name, node_name, total_measurements, avg_download_mbps, avg_upload_mbps,
     min_download_mbps, max_download_mbps, min_upload_mbps, max_upload_mbps,
     latency, jitter, server_name, ftp_file_path, created_at)
SELECT ts.session_id, 'GRK', ts.node_name, sp.total_measurements, sp.avg_download_mbps, sp.avg_upload_mbps,
       sp.min_download_mbps, sp.max_download_mbps, sp.min_upload_mbps, sp.max_upload_mbps,
       sp.latency, sp.jitter, sp.server_name, sp.ftp_file_path, sp.created_at
FROM grk_speed_test sp
JOIN test_session ts ON ts._old_session_id = sp.session_id;

-- 5) Geçici eşleme kolonunu kaldır
ALTER TABLE test_session DROP COLUMN _old_session_id;

COMMIT;
```
> ✅ **Beklenen:** GRK verisi kopyalandı, FULL verisi durmakta. Asıl kontrol: GRK
> sayısı kaynağıyla **EŞİT** olmalı.
> ```sql
> SELECT test_name, count(*) FROM test_session GROUP BY 1 ORDER BY 1;
> -- GRK satır sayısı = grk_test_session sayısı; FULL_SERVIS = değişmedi
> SELECT (SELECT count(*) FROM grk_test_session) AS grk_kaynak,
>        (SELECT count(*) FROM test_session WHERE test_name='GRK') AS yeni;  -- EŞİT olmalı
> SELECT (SELECT count(*) FROM grk_ping_test) AS grk_kaynak,
>        (SELECT count(*) FROM ping_test WHERE test_name='GRK') AS yeni;     -- EŞİT olmalı
> SELECT DISTINCT station_name FROM grk_test_session;  -- büyük ihtimalle NULL
> ```
> **NOT:** GRK setup'ı DB'ye yazmıyorsa (`station_name` NULL) GRK satırlarında `node_name`
> de NULL olur — bu NORMAL, veri kaybı değil. İleride GRK cutover'da (Prompt A) yeni
> testlerde `node_name` setup ile dolar; eski satırlar NULL kalır. FULL satırlarında
> `node_name` zaten makine adıyla doludur.
> `iperf_test`'e GRK verisi eklenmez (GRK'da iperf yok); FULL testleriyle dolar.
> Sorun görürsen `COMMIT` yerine `ROLLBACK`.

---

# 🤖 Prompt'lar

## Prompt B — FULL Servis kodu (Faz 4, ŞİMDİ)

```text
DB'de ortak sonuç tabloları kuruldu (copy_ staging tabloları final adlara yükseltildi).
FULL Servis artık bunlara yazacak. Şu değişiklikleri yap, başka bir şeyi değiştirme:

fullservice-backend/server/db_service.py — en üstteki tablo adı sabitleri:
   T_SESSION  = "test_session"
   T_PING     = "ping_test"
   T_SPEED    = "speed_test"
   T_WIFI     = "wifi_analysis"
   T_IPERF    = "iperf_test"
   T_FIRMWARE = "firmware"

FULL Servis TAMAMEN yeni yapıya alınıyor (canlı değil, tam geçiş yapılabilir):
 - common/firmware_db.py: get_brands/get_models/get_versions sorgularında
   "grk_firmware" -> "firmware".
 - server/auth_service.py: "grk_users" -> "users".

create_session'a has_iperf desteği ekle:
 - create_session(...) imzasına has_iperf parametresi + test_session INSERT'ine
   has_iperf_test kolonu.
 - orchestrator: oturumda iperf rolü varsa create_session'a has_iperf=True geçsin.

test_name zaten 'FULL_SERVIS', node_name zaten makine adı — değiştirme.
```
> ✅ **Beklenen (Faz 4):** Sunucu restart sonrası bir FULL testi koş → `test_session`'a
> `test_name='FULL_SERVIS'` yeni satır; `iperf_test`'e satır düşer.

## Prompt C — grk-test-platform kodu (Faz 5, ŞİMDİ)

```text
grk-test-platform artık cpeqadb'deki YENİ birleşik tablolardan okuyacak (aynı adlar:
test_session/ping_test/wifi_analysis/speed_test — artık view değil gerçek tablo).
Tablolar GRK + FULL verisini birlikte tutuyor; ayırt edici kolon test_name
('GRK'/'FULL_SERVIS'), makine/setup ise node_name. Sadece OKUMA; yazma yok.

1) Entity kolonları (backend/app/entities/):
   - test_session.py: station_name -> node_name DEĞİŞTİR; ayrıca ekle:
       test_name = Column(String(30)); has_iperf_test = Column(Boolean)
   - ping_test.py:      ekle: test_name, node_name
   - wifi_analysis.py:  ekle: test_name, node_name
   - speed_test.py:     ekle: test_name, node_name
   (__tablename__ AYNI kalıyor.)

2) İlgili DTO'ları (backend/app/dtos/) yeni alanları döndürecek şekilde güncelle
   (test_name, node_name, has_iperf_test).

3) YENİ test tipi: iperf. entity (iperf_test.py, __tablename__="iperf_test"), DTO ve
   results_controller'a GET /iperf-results ucu ekle (diğerleriyle aynı desen).
   Kolonlar: iperf_id (PK), session_id, test_name, node_name, server_node_name,
   server_ip, port, parallel, duration, sender_mbps, receiver_mbps, ftp_file_path,
   test_start_time, test_end_time, created_at.

4) grk_router_log tarafına DOKUNMA (grk_router_logs okumaya devam).

Sonra Docker image'ini yeniden kur ve sunucuda yeni image ile ayağa kaldır.
```
> ✅ **Beklenen (Faz 5):** Docker yeniden kalkınca panel yeni tablolardan okur;
> listede `test_name`/`node_name` kolonları görünür; GRK geçmişi + FULL verisi listelenir;
> iperf sekmesi/uç çalışır. Hata alırsan (ör. eksik kolon) bana yaz.

## Prompt A — GRK kodu (Faz 6, CUTOVER — SONRA)

```text
GRK'yı ortak tablolara geçir (firmware, users, test_session, ping_test, wifi_analysis,
speed_test). Davranışı başka türlü değiştirme:

1) Tablo adlarını güncelle: grk_firmware->firmware, grk_test_session->test_session,
   grk_ping_test->ping_test, grk_wifi_analysis->wifi_analysis, grk_speed_test->speed_test,
   grk_users->users.
2) Sonuç yazan tüm INSERT'lere test_name = 'GRK' ekle (default yok, hep açık yaz).
3) "station_name" olarak yazdığın setup değerini artık "node_name" kolonuna yaz
   (test_session.node_name ve ping/wifi/speed sonuç satırlarındaki node_name).
4) test_session INSERT'inde has_iperf_test = FALSE (GRK'da iperf yok) ya da hiç yazma.
5) median_time (ping) ve bssid (wifi) kolonlarını GRK hesaplamıyorsa NULL bırak.
6) Login artık "users" tablosundan.

Not: Sadece tablo/kolon adları değişir; iş mantığını ve testleri koru.
```

---

## 3. Faz 6 — Cutover detayları (şimdi değil, en son)

Staging (Faz 0–5) doğrulanınca GRK'yı da geçirirken:

1. **GRK kodu:** Prompt A ile geçir; Pazartesi test bilgisayarlarındaki exe'leri
   yeni build ile değiştir (GRK artık yeni tablolara yazar/okur).
2. **FK repoint:** `test_session.firmware_id` FK'sini `grk_firmware`'den `firmware`'e taşı
   (FULL Servis Faz 4'te zaten `firmware`/`users` okuyor; bu son bağ). Önce FK adını gör:
   `SELECT conname FROM pg_constraint WHERE conrelid='test_session'::regclass AND contype='f';`
3. **Interim delta:** GRK, staging boyunca `grk_*`'a yazdı. Kopyalama sonrası eklenen
   GRK kayıtlarını (`WHERE created_at > <SQL-3 zamanı>`) yeni tablolara aktar
   (SQL-3'teki eşleme yöntemiyle, yeni id vererek).
5. Her şey oturunca `grk_*`, `copy_*` (kalan) ve `yedek_*` arşivlenir/silinir.

> Faz 6'yı ayrı bir oturumda, hazır olduğunda yaparız — o zaman bu bölümü SQL'lerle
> detaylandırırım.
```
