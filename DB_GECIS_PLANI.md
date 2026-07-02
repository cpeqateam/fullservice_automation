# DB Geçiş Planı — GRK + FULL Servis Ortak Yapı (Senaryo 3)

> FULL Servis'in şu anki **`copy_` staging** tablolarından, GRK ile **ortak tek tablo
> setine** geçişi. Canlı GRK verisi olduğu için bu bir **migration**'dır (sıfırdan
> kurulum değil). Sıra: **önce yedek → sonra şema (rename+kolon) → sonra kod (prompt'larla)**.
>
> Hedef şema görseli: [`DB_YENI_SEMA.drawio`](DB_YENI_SEMA.drawio)
> SQL komutları ve GRK/FULL kod güncelleme prompt'ları **en altta**.

---

## 1. Nerede olduğumuz / nereye gittiğimiz

- **Şu an:** FULL Servis `copy_*` tablolarına, GRK `grk_*` canlı tablolarına yazıyor.
- **Hedef:** İki sistem **aynı** tabloları paylaşır. `grk_` öneki kalkar. Her satır
  **`test_name`** ile kime ait olduğunu söyler; **`node_name`** hangi kurulum/makine:
  - FULL Servis → `LINUX / MAC_ETH / MAC_WIFI / WIN_WIFI`
  - GRK → **seçilen setup adı** (ör. `GRK-1 - 2.4 GHz`), test başlatma sekmesindeki combobox'tan
- `grk_users` → **`users`** olarak yeniden adlandırılır (isim GRK'ya özgü olmasın).

---

## 2. Hedef yapı (özet)

| Tablo (yeni ad) | Eski ad | Eklenen kolonlar |
|-----------------|---------|------------------|
| `firmware` | grk_firmware | — |
| `files` | files | — (değişmez) |
| `test_session` | grk_test_session | `test_name`, **`has_iperf_test`**, (`station_name`→`node_name`) |
| `ping_test` | grk_ping_test | `test_name`, `node_name`, `median_time` |
| `wifi_analysis` | grk_wifi_analysis | `test_name`, `node_name`, `bssid` |
| `speed_test` | grk_speed_test | `test_name`, `node_name` (GRK'ya özel) |
| `iperf_test` | **YENİ** | (tüm tablo; sadece FULL) |
| `users` | grk_users | — (yalnız ad değişir) |

> **Not:** SQL'deki her kolon senin diyagramından gelir; diyagramda olmayan hiçbir
> kolon eklenmedi. Tek istisna, senin K8'de açıkça istediğin `has_iperf_test`.

### Gerçek şemadan çıkan farklar (canlı DB çıktısına göre)

- **`median_time` (ping) ve `bssid` (wifi) GRK tablolarında ZATEN VAR** → eklenmez.
  (`ping_test.median_time numeric(10,3)`, `wifi_analysis.bssid varchar(20)`.)
- **`test_session`'daki `station_name varchar(50)`** → **`node_name` olarak yeniden
  adlandırılıyor.** Mevcut setup değerleri otomatik korunur (kolon aynı, sadece adı değişir);
  ayrı `station_name` kalmaz. GRK kodundaki `station_name` referansları `node_name` olacak.
- **`iperf_test` sıfırdan kurulmuyor**; `copy_iperf_test` (yapısı zaten doğru) → `iperf_test`
  olarak **yeniden adlandırılıyor**.
- Eklenecek kolonlar: `test_name` (test_session, ping_test, wifi_analysis, speed_test) +
  `node_name` (ping_test, wifi_analysis, speed_test — test_session'ınki station_name'den geliyor) +
  `has_iperf_test` (test_session).
- Tipler gerçek şemayla eşitlendi: `test_name varchar(30)`, `node_name varchar(50)`.

---

## 3. Kararlar (senin cevaplarınla KESİNLEŞTİ)

| # | Konu | Karar |
|---|------|-------|
| K1 | Yaklaşım | **Yeniden adlandırma** (grk_ kalkar). GRK kodunu sen kendi Claude Code'unla güncelleyeceksin (Prompt aşağıda). |
| K2 | GRK kodunu kim güncelleyecek | Sen — Claude Code prompt'u ile (aşağıda). |
| K3 | `test_name` | **Varsayılan YOK.** Her INSERT değeri açıkça yazar (GRK→'GRK', FULL→'FULL_SERVIS'). Eski satırlar tek seferlik 'GRK' ile doldurulur. |
| K4 | GRK'da `node_name` | **NULL değil** → seçilen **setup adı** yazılır (combobox). GRK prompt'unda anlatıldı. Eski GRK satırları NULL kalır. |
| K5 | `median_time` | ping tablosunda kalır. GRK yazmaz (NULL), FULL yazar. GRK'ya dokunulmaz. |
| K6 | `bssid` tipi | Teknik detay: `VARCHAR(32)` (MAC adresi sığar), boş olabilir. |
| K7 | `created_at` | Senin tablolarında zaten var → **dokunulmuyor**, yeni bir şey eklenmiyor. (Yalnız yeni `iperf_test` tablosunda tanımlı.) |
| K8 | `has_iperf_test` | **test_session'a eklenir** (iperf var mı yok mu görünsün). `iperf_test`'te `session_id` FK olarak var. |
| K9 | Kolon adları | Senin/takım liderinin verdiği adlar **aynen** korunur (`parallel` vb. değişmez). |
| K10 | Zamanlama | SQL'i pgAdmin'den **sen** çalıştıracaksın; rename anında GRK yazmıyor olsun yeter. |
| K11 | `copy_*` silme | Silme SQL'i aşağıda (bölüm C). Doğrulamadan sonra çalıştır. |
| K12 | Yedek | Güncellemeden **önce** DB içinde `yedek_*` tabloları oluşturulur (bölüm A). |

---

## 4. Adım adım geçiş (senin sıraladığın düzen)

> Hepsini **sen** yapacaksın: SQL'ler pgAdmin'den, kod güncellemeleri Claude Code prompt'larıyla.

### Faz 0 — Yedekleme (SQL bölüm A)
- [ ] `yedek_*` tablolarını oluştur (mevcut veriyi kopyalar). → **Bölüm A**

### Faz 1 — Şema güncelleme (SQL bölüm B)
- [ ] Tabloları yeniden adlandır (`grk_*` → yeni ad, `grk_users`→`users`).
- [ ] Yeni kolonları ekle (`test_name`, `node_name`, `median_time`, `bssid`, `has_iperf_test`).
- [ ] Eski satırları `test_name='GRK'` ile doldur.
- [ ] `iperf_test` tablosunu oluştur. → **Bölüm B**

### Faz 2 — FULL Servis kodu (Prompt B)
- [ ] Kendi Claude Code'unla FULL Servis kodunu güncelle. → **Prompt B**
- [ ] FULL Servis sunucusunu yeniden başlat.

### Faz 3 — GRK kodu (Prompt A)
- [ ] GRK'yı yönettiğin Claude Code'a Prompt A'yı ver. → **Prompt A**
- [ ] GRK'yı yeniden başlat.

### Faz 4 — Doğrulama
- [ ] GRK bir test koşar → `test_name='GRK'`, `node_name`=setup adı.
- [ ] FULL Servis bir test koşar → `test_name='FULL_SERVIS'`, `node_name`=makine, `iperf_test` dolu.
- [ ] Combobox (marka/model/firmware) çalışıyor; login (`users`) çalışıyor.

### Faz 5 — Temizlik (SQL bölüm C)
- [ ] Birkaç gün sorunsuz çalıştıktan sonra `copy_*` tablolarını sil. → **Bölüm C**
- [ ] (İstersen) `yedek_*` tablolarını da sonra sil.

---

## 5. Doğrulama sorguları (Faz 4)

```sql
SELECT test_name, node_name, COUNT(*) FROM ping_test GROUP BY 1,2 ORDER BY 1,2;
SELECT * FROM test_session ORDER BY session_id DESC LIMIT 5;
SELECT * FROM iperf_test ORDER BY iperf_id DESC LIMIT 5;
SELECT node_name, bssid, wifi_protocol FROM wifi_analysis
  WHERE test_name='FULL_SERVIS' ORDER BY wifi_summary_id DESC LIMIT 5;
SELECT username FROM users LIMIT 3;   -- rename doğrulama
```

---

## 6. Geri alma (rollback)

- Şema adımında sorun → transaction içinde `ROLLBACK` (bölüm B tek transaction).
- Sonradan sorun → tabloları eski `grk_*` adlarına geri `RENAME` et; veri `yedek_*`
  tablolarında zaten duruyor. Son çare: `yedek_*`'ten geri yükle.

---

# 📜 SQL Komutları

> pgAdmin'de **sırayla** çalıştır. Kolon tipleri teknik seçimdir; DB'ndeki mevcut
> tiplerle çelişirse (ör. `avg_time` `NUMERIC` ise) ona göre uyarlarsın.

## Bölüm A — Yedekleme (ÖNCE bunu çalıştır)

```sql
-- Mevcut veriyi aynen kopyalar (yalnız veri; kısıtlar/PK kopyalanmaz — snapshot amaçlı).
CREATE TABLE yedek_grk_firmware      AS SELECT * FROM grk_firmware;
CREATE TABLE yedek_grk_test_session  AS SELECT * FROM grk_test_session;
CREATE TABLE yedek_grk_ping_test     AS SELECT * FROM grk_ping_test;
CREATE TABLE yedek_grk_wifi_analysis AS SELECT * FROM grk_wifi_analysis;
CREATE TABLE yedek_grk_speed_test    AS SELECT * FROM grk_speed_test;
CREATE TABLE yedek_grk_users         AS SELECT * FROM grk_users;
```

## Bölüm B — Şema güncelleme (tek transaction)

```sql
BEGIN;

-- 1) Tablo adlarından grk_ önekini kaldır (files ve firmware ilişkisi otomatik korunur)
ALTER TABLE IF EXISTS grk_firmware      RENAME TO firmware;
ALTER TABLE IF EXISTS grk_test_session  RENAME TO test_session;
ALTER TABLE IF EXISTS grk_ping_test     RENAME TO ping_test;
ALTER TABLE IF EXISTS grk_wifi_analysis RENAME TO wifi_analysis;
ALTER TABLE IF EXISTS grk_speed_test    RENAME TO speed_test;
ALTER TABLE IF EXISTS grk_users         RENAME TO users;

-- 2) test_session: station_name -> node_name (mevcut setup verisi korunur) +
--    test_name (default YOK) + has_iperf_test
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name = 'test_session' AND column_name = 'station_name') THEN
    ALTER TABLE test_session RENAME COLUMN station_name TO node_name;
  END IF;
END $$;
ALTER TABLE test_session ADD COLUMN IF NOT EXISTS test_name      VARCHAR(30);
ALTER TABLE test_session ADD COLUMN IF NOT EXISTS has_iperf_test BOOLEAN DEFAULT FALSE;
UPDATE test_session SET test_name = 'GRK' WHERE test_name IS NULL;

-- 3) ping_test: test_name + node_name  (median_time ZATEN VAR → eklenmez)
ALTER TABLE ping_test ADD COLUMN IF NOT EXISTS test_name VARCHAR(30);
ALTER TABLE ping_test ADD COLUMN IF NOT EXISTS node_name VARCHAR(50);
UPDATE ping_test SET test_name = 'GRK' WHERE test_name IS NULL;

-- 4) wifi_analysis: test_name + node_name  (bssid ZATEN VAR → eklenmez)
ALTER TABLE wifi_analysis ADD COLUMN IF NOT EXISTS test_name VARCHAR(30);
ALTER TABLE wifi_analysis ADD COLUMN IF NOT EXISTS node_name VARCHAR(50);
UPDATE wifi_analysis SET test_name = 'GRK' WHERE test_name IS NULL;

-- 5) speed_test: test_name + node_name (GRK'ya özel; FULL yazmaz)
ALTER TABLE speed_test ADD COLUMN IF NOT EXISTS test_name VARCHAR(30);
ALTER TABLE speed_test ADD COLUMN IF NOT EXISTS node_name VARCHAR(50);
UPDATE speed_test SET test_name = 'GRK' WHERE test_name IS NULL;

-- 6) iperf_test: copy_iperf_test'i yeniden adlandır (yapısı zaten FULL koduyla birebir)
ALTER TABLE IF EXISTS copy_iperf_test RENAME TO iperf_test;
--   (İsteğe bağlı) staging sırasında birikmiş test satırlarını temizle:
-- TRUNCATE iperf_test;
--   (İsteğe bağlı) session_id için foreign key ekle:
-- ALTER TABLE iperf_test
--   ADD CONSTRAINT iperf_test_session_fk
--   FOREIGN KEY (session_id) REFERENCES test_session(session_id);

COMMIT;
```

> Sorun görürsen `COMMIT;` yerine `ROLLBACK;` yaz → hiçbir değişiklik kalıcı olmaz.

## Bölüm C — Temizlik (Faz 4 doğrulamasından SONRA)

```sql
-- FULL Servis artık ortak tablolara yazdığı için kalan copy_ tabloları gereksiz.
-- DİKKAT: copy_iperf_test YOK — o "iperf_test" olarak yeniden adlandırıldı (Bölüm B/6).
DROP TABLE IF EXISTS copy_ping_test;
DROP TABLE IF EXISTS copy_wifi_analysis;
DROP TABLE IF EXISTS copy_speed_test;
DROP TABLE IF EXISTS copy_test_session;
-- İstersen yedekleri de sonra sil:
-- DROP TABLE IF EXISTS yedek_grk_firmware, yedek_grk_test_session, yedek_grk_ping_test,
--                      yedek_grk_wifi_analysis, yedek_grk_speed_test, yedek_grk_users;
```

---

# 🤖 Prompt'lar (kod güncellemeleri için)

> Bunları ilgili Claude Code oturumuna **olduğu gibi** yapıştır.

## Prompt A — GRK kodunu güncelle (GRK'yı yönettiğin makinede)

```text
cpeqadb veritabanında tablo adları değişti (grk_ öneki kaldırıldı) ve yeni kolonlar eklendi.
Aşağıdaki değişiklikleri GRK kod tabanına uygula, davranışı başka türlü değiştirme:

1) Tüm SQL referanslarında tablo adlarını güncelle:
   grk_firmware      -> firmware
   grk_test_session  -> test_session
   grk_ping_test     -> ping_test
   grk_wifi_analysis -> wifi_analysis
   grk_speed_test    -> speed_test
   grk_users         -> users

2) Sonuç yazan tüm INSERT'lere test_name = 'GRK' ekle (test_session, ping_test,
   wifi_analysis, speed_test). Bu kolonun DEFAULT'u YOK; her zaman açıkça yazılmalı.

3) node_name: test_session'daki "station_name" kolonu "node_name" olarak yeniden
   adlandırıldı. GRK kodunda geçen TÜM "station_name" referanslarını "node_name" yap.
   Ayrıca kullanıcının seçtiği SETUP adını (ör. "GRK-1 - 2.4 GHz") ping_test,
   wifi_analysis, speed_test sonuç INSERT'lerine de node_name olarak yaz. (Bu değer zaten
   SessionInitRequest.server / setup seçiminde mevcut; onu kullan.)

4) test_session INSERT'inde has_iperf_test alanını FALSE ver (GRK'da iperf yok) ya da hiç
   yazma (kolonun default'u FALSE).

5) median_time (ping) ve bssid (wifi) kolonları tabloda ZATEN VAR ama GRK hesaplamıyor;
   bunları YAZMA (NULL kalsınlar). Şema değişikliği gerektirmez.

6) Login/kullanıcı sorguları artık "users" tablosunu kullanmalı (eski grk_users).

Not: Sadece tablo adları + yukarıdaki kolonlar değişiyor; iş mantığını, testleri ve
diğer davranışları aynen koru.
```

## Prompt B — FULL Servis kodunu güncelle (bu repo)

```text
DB birleştirmesi yapıldı: copy_ staging tabloları yerine ortak tablolara yazacağız ve
grk_ önekli tablolar yeniden adlandırıldı. Şu değişiklikleri uygula:

1) fullservice-backend/server/db_service.py — en üstteki tablo adı sabitlerini güncelle:
   T_SESSION = "test_session"
   T_PING    = "ping_test"
   T_SPEED   = "speed_test"
   T_WIFI    = "wifi_analysis"
   T_IPERF   = "iperf_test"
   T_FIRMWARE = "firmware"

2) fullservice-backend/common/firmware_db.py — get_brands/get_models/get_versions
   sorgularında "grk_firmware" -> "firmware".

3) fullservice-backend/server/auth_service.py — "grk_users" -> "users".

4) has_iperf_test desteği ekle:
   - db_service.create_session(...) imzasına has_iperf parametresi ekle ve
     test_session INSERT'ine has_iperf_test kolonunu ekle.
   - orchestrator, oturumda iperf rolü varsa create_session'a has_iperf=True geçsin
     (has_ping/has_wifi ile aynı mantık).

5) test_name zaten 'FULL_SERVIS', node_name zaten makine adı (log_name) olarak
   yazılıyor — bunları değiştirme.

Sadece bu değişiklikler; başka davranış değişmesin. Sırlar/certs mantığına dokunma.
```

---

> **Sıradaki adım:** Bölüm A'yı (yedek) çalıştır, sonra Bölüm B (şema). Ardından Prompt B
> ile FULL Servis'i, Prompt A ile GRK'yı güncelle. Doğrulama geçince Bölüm C ile temizle.
