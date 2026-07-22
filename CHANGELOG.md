# Değişiklik Günlüğü (CHANGELOG)

Bu dosya FULL Servis'in sürüm sürüm değişikliklerini kaydeder.
Biçim [Keep a Changelog](https://keepachangelog.com/tr/), sürümleme
[Semantic Versioning](https://semver.org/lang/tr/) mantığına dayanır.

> Kurulum/kullanım için `README.md`, kod gezisi için `KOD_HAKIMIYETI.md`,
> DB geçişi için `DB_GECIS_PLANI.md`.

---

## [Yayınlanmamış]

### Eklendi
- Formal `CHANGELOG.md` (eski `GELISTIRME_GUNLUGU.md` bunun yerine geçti).
- Backend genelinde eksik **docstring**'ler tamamlandı (modül/sınıf/fonksiyon).
- **Tek-tık paketleme (PyInstaller)**: son kullanıcı artık Python/venv/kaynak kod
  olmadan çift tıklayarak çalıştırıyor.
  - `launchers/build/`: `server_app.py`, `agent_app.py` giriş noktaları; `*.spec`
    tarifleri; `derle-linux.sh` / `derle-mac.sh` / `derle-windows.bat`.
  - Uygulama adları: `FULLSERVIS-SUNUCU`, `FULLSERVIS-MAC-WIFI`,
    `FULLSERVIS-MAC-KABLO`, `FULLSERVIS-WINDOWS-WIFI`.
  - `common/app_boot.py`: eski örneği kapatma (`free_port`), panelin varsayılan
    tarayıcıda otomatik açılması (`open_browser_later`, `FS_NO_BROWSER` ile kapatılır),
    hata olunca pencerenin açık kalması.
  - `common/config.py`: **agent kimliği uygulamanın dosya adından** çözülüyor
    (`resolve_node_id`) — `python run_agent.py mac_wifi <url>` yazmaya gerek yok;
    `ayarlar/agent.json` ve `FS_NODE_ID` ile ezilebilir.
  - Tek rehber: `launchers/KURULUM.md` (derleme + odaya kurulum + günlük kullanım).

### Kaldırıldı
- Eski venv tabanlı başlatıcılar (`launchers/baslat-*.bat|sh|command`) ve dağınık
  paketleme belgeleri — yerlerini derlenen uygulamalar + tek `KURULUM.md` aldı.

### Değişti
- `common/config.py` **donmuş (frozen) modu** destekliyor: kod ve panel exe'nin içinde,
  `config.json` / `secrets.json` / `certs/` / `logs/` ise exe'nin yanındaki
  `ayarlar/` + `logs/` klasörlerinde → IP/süre değişikliği için yeniden derleme gerekmez,
  sırlar exe'ye gömülmez.

### Yapılacak / sürüyor
- DB birleştirme **cutover**: GRK exe'lerinin 8 setup'a taşınması; `test_session.firmware_id`
  FK'sinin `firmware`'e alınması; interim `grk_*` delta aktarımı.
- `wifi_analysis`'e roaming / band-steering özet kolonları (planlanan).

---

## [1.4.0] - 2026-07-07 — DB Birleştirme (Senaryo 3)

### Eklendi
- GRK + FULL Servis **ortak DB yapısı**: `test_session`, `ping_test`, `wifi_analysis`,
  `speed_test`, `iperf_test` + `firmware`, `users`. Satırlar `test_name` ('GRK'/'FULL_SERVIS')
  ile ayrışır; `node_name` makine/setup bilgisini tutar.
- `iperf_test` tablosu (FULL Servis'e özel).
- DB geçişini adım adım anlatan `DB_GECIS_PLANI.md` (SQL + prompt'lar + beklenen sonuçlar).

### Değişti
- FULL Servis kodu artık ortak tablolara yazıyor (`db_service` tablo sabitleri;
  `firmware_db` → `firmware`; `auth_service` → `users`; `create_session`'a `has_iperf`).
- GRK kodu ortak tablolara geçti (`grk_*` önekleri kalktı; `station_name` → `node_name`;
  login `users`'tan).
- grk-test-platform (okuma paneli) ortak tablolardan okuyacak şekilde güncellendi.

### Kaldırıldı
- `grk_*` → öneksiz geçiş **view**'ları; yerlerine gerçek tablolar geldi.
- Kullanılmayan `ping`, `speedtest`, `test_run`, `wifianaliz` tabloları.

### Güvenlik
- `firmware_db.py`'deki gömülü `DB_URL` koddan çıkarıldı → `secrets.json` / ortam
  değişkeni (`get_secret("FS_FIRMWARE_DB_URL")`).

---

## [1.3.0] - 2026-06-29 — Bildirim + Login

### Eklendi
- **Telegram + mail bildirimi**: test tamamlanınca (GRK ile aynı format, grup ve adresler);
  Telegram'a özet log dosyaları da gider.
- **Login ekranı**: GRK ile aynı `grk_users` tablosundan; DB kapalıyken bile geçerli
  varsayılan hesap `cpeteam / cpeteam`. Karşılama (Welcome) ekranı.
- **error_log → FTP**: sunucu log dilimi ayrı dosya olarak FTP'ye (bildirim yok).

### Değişti
- Bildirim tetiği: **ölçüm testleri** (ping/iperf/wifi_track) bitince — torrent/youtube
  (sonsuz yük) beklenmez.
- Wi-Fi analiz scripti GRK `functionBase_wifi.py` ile **birebir** (bant genişliği/RX-TX).
- Sağ üstteki "HAZIR" chip'i yerine giriş yapan kullanıcı adı.

### Güvenlik
- Telegram token'ı + SMTP şifresi koddan çıkarıldı → gitignore'lu `secrets.json`
  (`get_secret`). Sızan token temizlendi.

---

## [1.2.0] - 2026-06-23 — DB Yazma + FTP

### Eklendi
- Sonuçların **DB'ye yazılması** (`copy_` staging tabloları): ping / iperf / wifi.
- **FTP yükleme**: `<MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<Bilgisayar>/`.
- GRK ile **aynı log dosya isimlendirmesi** ('grk' yerine 'FULL_Service').

---

## [1.1.0] - 2026-06-19 — Faz 4: Gerçek testler

### Eklendi
- **torrent** (qBittorrent Web API) ve **wifi_track** gerçek (simülasyon değil).
- **iperf topolojisi**: kablolu Mac server / Wi-Fi Mac client (Linux artık server değil).
- **YouTube** en yüksek kaliteyi zorlar (Selenium/Chrome).
- UML sınıf/use-case ve DB şema draw.io diyagramları.

### Değişti
- ping ve wifi_track görünür terminalde canlı akar.

---

## [1.0.0] - 2026-06-17 — Faz 1–3: İskelet

### Eklendi
- **Dağıtık mimari**: Linux orkestratör (:8770) + 3 agent (:7531), HTTP/JSON protokol.
- **Vue 3 + Vuetify 3 dashboard**: 4 düğüm canlı izleme, 2×2 kart, mavi tema, Sıfırla butonu.
- **Marka/Model/Firmware combobox** (cpeqadb, SSL; bağlantı yoksa serbest metin).
- **Aşamalı Health-Check** paneli (kırmızı/yeşil, artan periyot).
- **Statik IP + boot listener** paketleme (`provisioning/`: launchd / Task Scheduler / systemd).
