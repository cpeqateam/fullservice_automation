# FULL Servis — Geliştirme Günlüğü / Devam Notları

> Bu dosya, projenin **mevcut durumunu** ve **sıradaki adımları** özetler. Yeni bir
> oturuma (veya başka bir geliştiriciye) sıfırdan anlatmamak için kısa bir el kitabıdır.
>
> Son güncelleme: **2026-06-29**  ·  Branch: **aliimran**

---

## 1. Proje nedir

FULL Servis: **4 makineli dağıtık modem stres testi**. Hepsi aynı modeme bağlanır,
eş zamanlı yük basar (ping / youtube / iperf / torrent / wifi). Modem çökmeden
dayanırsa firmware başarılı sayılır.

| Düğüm | Rol |
|-------|-----|
| Linux Sunucu (orkestratör + dashboard, :8770) | ping, youtube |
| MAC Kablo (iperf **server**) | youtube, ping, iperf_server |
| WINDOWS Wi-Fi | youtube, ping, torrent, wifi_track |
| MAC Wi-Fi (iperf **client**) | youtube, ping, iperf, wifi_track |

Kod: `fullservice-backend/` (`server/`, `agent/`, `common/`, `common/runners/`) +
`fullservice-frontend/` (Vue 3 + Vuetify 3).
**GRK** (`grk-automation/`) = ayrı, canlı, **SALT-OKUNUR** referans. ASLA dokunma.

---

## 2. Veritabanı stratejisi (Senaryo 3 — staging aşamasında)

Hedef: GRK ile FULL Servis **aynı** tabloları paylaşacak.
- `grk_` önekleri kalkacak: `firmware`, `test_session`, `ping_test`, `speed_test`, `wifi_analysis`
- her sonuç tablosuna 2 yeni kolon: `test_name` (GRK / FULL_SERVIS) + `node_name`
  (FULL Serviste hangi makine: LINUX / MAC_ETH / MAC_WIFI / WIN_WIFI; GRK'da NULL)
- `test_session`'a `test_name` kolonu (`has_full_servis` yerine)
- yeni tablo: `iperf_test` (sadece FULL Servis)
- **torrent ve youtube DB'ye YAZILMAZ** (sadece yük basıcı; log/FTP'de kalır)
- `speed_test` FULL Serviste yok (GRK'ya özel)

**Güvenli yaklaşım (staging) — ŞU AN BURADAYIZ:** GRK'yı riske atmamak için
başında `copy_` olan kopya tablolar oluşturuldu; FULL Servis önce **bunlara** yazıyor.
Her şey doğrulanınca asıl birleştirme (rename + GRK güncelleme) yapılacak.

Oluşturulan staging tabloları (DB'de çalıştırıldı):
`copy_test_session`, `copy_ping_test`, `copy_speed_test`, `copy_wifi_analysis`, `copy_iperf_test`.
`firmware` için copy YOK — combobox hâlâ `grk_firmware`'i okur (GRK'ya dokunulmadı);
`copy_test_session` FK ile `grk_firmware`'e bağlanır.

> Tablo adları tek noktada: `server/db_service.py` en üstündeki sabitler
> (`T_SESSION="copy_test_session"` …). Birleştirmede sadece o sabitleri `copy_`'siz yap.

İlgili diyagramlar: `DB_YENI_SEMA.drawio` (hedef şema), `UML_CLASS_DIAGRAM.drawio`,
`UML_USECASE_DIAGRAM.drawio`.

---

## 3. Tamamlanan işler

### 3.1 DB yazma (copy_ tablolarına)
Akış: agent runner test biter → `ctx.result(kind, stats)` → `POST /api/result` →
`orchestrator.record_result` → `db_service.save_*` → `copy_` tablosu. Sunucu-yerel
testler (Linux) aynı `record_result`'ı doğrudan çağırır. DB yoksa sessizce atlanır,
testler yine çalışır. Her satırda `test_name='FULL_SERVIS'`, `node_name`=config'deki
`log_name`. İlgili: `server/db_service.py`, `common/protocol.py` (`ResultReport`),
`common/runners/base.py` (result callback) ve ping/iperf/wifi runner'ları (istatistik
hesaplar).

### 3.2 FTP yükleme
`server/ftp_service.py` (GRK FTP portu). Klasör yapısı:
`<MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<Bilgisayar>/`
TestTipi: Ping/Iperf/Wifi/Youtube/Torrent (log dosya adından çözülür).
Bilgisayar: LINUX/MAC_ETH/MAC_WIFI/WIN_WIFI. Klasörler ilk yüklemede otomatik açılır.
Arka planda (daemon thread) yükler. Sunucu `certs/ca.crt` kullanır.
Devre dışı: `FS_FTP_DISABLE=1`.

### 3.3 Log isimlendirme (GRK ile aynı)
`base.py`'ye `grk_style_filename` + `RunContext.grk_log_path` eklendi; tek fark
'grk' yerine **'FULL_Service'**. Örnekler:
`FULL_Service_ping_<brand>_<model>_<fw>_IPv4_8888_<ts>.txt`,
`FULL_Service_wifiAnaliz_<brand>_<model>_<fw>_54sn_<ts>.txt`,
`FULL_Service_iperf_<brand>_<model>_<fw>_<serverip>_<ts>.txt`.

### 3.4 Login ekranı
GRK ile **aynı** `grk_users` tablosundan doğrulanır. `server/auth_service.py` +
`POST /api/login`. **Varsayılan hesap DAİMA geçerli** (DB kapalı olsa bile):
`cpeteam` / `cpeteam`. Şifre formatları: bcrypt/md5/sha256/düz metin.
Frontend: `store/auth.js` (token localStorage), `components/Login.vue`,
`components/Welcome.vue` (GRK gibi karşılama ekranı). Hatalar kısa/Türkçe ve hep
"...sistem yöneticinize başvurun" der (`mapLoginError`).

### 3.5 Wi-Fi analiz scripti (GRK birebir)
`wifi_util.py` = GRK `functionBase_wifi.py`'nin **birebir aynısı** (sadece CLI
initialIO+pyfiglet çıkarıldı). `wifi_util_mac.py` = onun darwin kolu. `wifi_track_runner`
saniyede 1 örnek alır, satırı GRK `getPeriodicData` ile bayt bayt aynı yazar → bant
genişliği (RX/TX) sonuçlarda VAR. Takım liderinin koduna dokunulmadı.

### 3.6 Telegram + mail bildirimi (GRK ile aynı)
- `server/notify.py` = GRK notify.py portu (aynı bot + aynı grup CHAT_ID).
- `server/email_sender.py` = GRK `__sendEmail.py` portu (aynı Gmail SMTP).
- `server/notification_service.py` = test bitince Telegram'a tamamlanma mesajı + özet
  log dosyaları (50MB üstü gönderilmez); mail ise **yalnızca mesaj, dosya eki YOK**.
- **Tetikleme:** STOP butonuna değil, testin **bitmesine** bağlı. `update_progress`
  içinde kenar-yakalama: tüm testler terminal (completed/error/stopped) olunca
  `_on_session_complete` bir kez tetiklenir. Her yeni "Başlat" yeni session → her koşu
  yeniden bildirir (dedup yok).
- Devre dışı: `FS_NOTIFY_DISABLE=1`.

### 3.7 error_log → FTP (bildirim YOK)
`server/main.py` stdout/stderr'i `logs/app.log`'a Tee'ler. `orchestrator.start_session`
app.log offset'ini kaydeder; test bitince `server/log_capture.finalize_async`
app.log[offset:EOF] dilimini `FULL_Service_errorlog_<...>.log` olarak yazıp FTP'ye
`<MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/Errorlog/` altına yükler.
NOT: bu dilim **sunucu** taraf loglarıdır; agent hataları kendi konsolunda kalır.

### 3.8 Excel çıktısı
`server/excel_service.py` (başka bir oturumda eklendi) — Ping/Wifi için Excel üretir.
**Dokunma.**

---

## 4. ⚠️ SIRLAR (önemli)

Telegram token / SMTP şifresi **kodda DEĞİL**. `fullservice-backend/secrets.json`
(gitignore'lu) veya ortam değişkenlerinden okunur (`common.config.get_secret`):
`FS_TELEGRAM_BOT_TOKEN`, `FS_TELEGRAM_CHAT_ID`, `FS_SMTP_USER`, `FS_SMTP_PASS`, `FS_SMTP_FROM`.
Sunucuda bu dosyayı oluştur (`certs/` gibi repoya **gitmez**). Bir kez yanlışlıkla
GitHub'a gitti → commit sırsız yeniden yazılıp force-push edildi (geçmişten temizlendi).

---

## 5. Nasıl test edilir

1. `copy_` tabloları DB'de oluşturuldu mu? (oluşturuldu)
2. Sunucuda `fullservice-backend/certs/` (ca.crt, client.crt, client.key) var mı?
   `client.key` izni: `chmod 600` (Linux/mac). Yoksa DB/FTP bağlanmaz.
3. Bildirim için `fullservice-backend/secrets.json` var mı?
4. Sunucu: `cd fullservice-backend && python run_server.py`
5. Agent'lar: her makinede `python run_agent.py <node_id> http://<sunucu_ip>:8770`
6. Dashboard → giriş (cpeteam/cpeteam veya grk_users) → Marka/Model/Firmware → Başlat.
7. DB kontrol:
   ```sql
   SELECT * FROM copy_test_session ORDER BY session_id DESC LIMIT 5;
   SELECT * FROM copy_ping_test    ORDER BY ping_result_id DESC LIMIT 20;
   SELECT * FROM copy_iperf_test   ORDER BY iperf_id DESC LIMIT 5;
   SELECT * FROM copy_wifi_analysis ORDER BY wifi_summary_id DESC LIMIT 5;
   ```
   Beklenen: `test_name='FULL_SERVIS'`, `node_name` dolu, `firmware_id` doğru.

> Frontend değişince: `cd fullservice-frontend && npm run build`.
> Sunucu kod/route değişince: `run_server.py`'yi **yeniden başlat** (StaticFiles dist'i
> canlı okur ama rotalar süreç başında sabitlenir).

---

## 6. Sıradaki adımlar

- [ ] `copy_` tablolarına yazma **sahada** doğrulanacak (4 makine, gerçek MARKA/MODEL/FIRMWARE).
- [ ] FTP yüklemesi sahada doğrulanacak (gerçek MARKA/MODEL/FIRMWARE klasörleri).
- [ ] iperf otomasyondan düzgün başlamıyor olabilir — sahada doğrulanacak
      (`IPERF_REHBERI.md` kontrol listesi). iperf3 iki Mac'te de kurulu
      (kaynak koddan derlendi, `/usr/local/bin/iperf3`).
- [ ] Her şey çalışınca **BİRLEŞTİRME**:
  - DB: `grk_*` tablolarını rename + `test_name`/`node_name` ekle + `iperf_test`
  - GRK kodunu güncelle (`grk_firmware` → `firmware` vb.)
  - `db_service.py`'deki tablo adı sabitlerini `copy_`'siz yap
  - `copy_` tablolarını DROP et

---

## 7. Kurallar / notlar

- `grk-automation/` ASLA değiştirilmez (canlı, salt-okunur referans).
- `certs/` ve `secrets.json` gizli, repoya konmaz (gitignore). `client.key` chmod 600.
- Kullanıcı git push'u **kendi** yapar; sadece istenince commit'le.
- Kullanıcı Java'dan geliyor, Python'da yeni — kod açıklamalarını ona göre yap.
