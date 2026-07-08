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
