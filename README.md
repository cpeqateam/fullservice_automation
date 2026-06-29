# fullservice_automation

> **Türk Telekom — CPE QA Ekibi** için geliştirilen **dağıtık modem stres testi**
> sistemi. Tek bir modeme 4 farklı cihazdan eş zamanlı yük bindirerek
> **"abandırır"** (stres uygular). Modem fail vermeden dayanıyorsa firmware
> başarılı sayılır.

> **GRK** (Günlük Rutin Kontrol) tek-makineli rutin testtir; bu proje (**FULL
> Servis**) onun **çok-makineli, eş zamanlı stres** versiyonudur.

---

## Depo Yapısı

```
fullservice_automation/
├── fullservice-backend/      # FastAPI sunucu (orkestratör) + agent (Mac/Win/Linux)
│   ├── common/  agent/  server/  config.json  run_server.py  run_agent.py
│   ├── common/firmware_db.py            # Marka/Model/Firmware DB erişimi (cpeqadb)
│   ├── provisioning/                    # Statik IP + boot listener kurulum script'leri
│   └── README.md                        # backend dokümantasyonu (API, kurulum, runner'lar)
│
├── fullservice-frontend/     # Vue 3 + Vuetify 3 dashboard (Türk Telekom temalı)
│   ├── src/  package.json  vite.config.js
│   └── README.md                        # frontend dokümantasyonu (dev/build, bileşenler)
│
├── KOD_HAKIMIYETI.md                    # Java'dan gelen biri için kod gezisi (dosya dosya)
├── GELISTIRME_GUNLUGU.md                # mevcut durum + sıradaki adımlar (geliştirme günlüğü)
├── IPERF_REHBERI.md                     # iperf kurulum + sorun giderme rehberi
├── DB_YENI_SEMA.drawio                  # hedef birleşik DB şeması (Senaryo 3)
├── UML_CLASS_DIAGRAM.drawio             # backend sınıf/modül diyagramı
├── UML_USECASE_DIAGRAM.drawio           # use-case diyagramı
└── README.md                            # (bu dosya)

Kurulum rehberleri (fullservice-backend/ altında):
- KURULUM_SAHA_4_MAKINE.md   → gerçek saha: 4 ayrı fiziksel makine
- KURULUM_VM_LAB_TEK_MAC.md  → tek Mac üzerinde VM lab (hızlı deneme)
```

---

## Sistemin Topolojisi

```
                    Modem (Türk Telekom CPE — test altındaki cihaz)
                              │ (kablo + Wi-Fi linkleri aynı modeme)
   ┌──────────────────────────┼───────────────────────────┐
   │                          │                            │
┌──┴────────┐   ┌─────────────────┐   ┌────────────────────┐   ┌───────────────┐
│ LINUX SUN.│   │ MAC (kablo)     │   │ WINDOWS (Wi-Fi)    │   │ MAC (Wi-Fi)   │
│ orkestr.  │   │ listener:7531   │   │ listener:7531      │   │ listener:7531 │
│ ping/yt   │   │ ping/yt/        │   │ ping/yt/torrent/wt │   │ ping/yt/wt/   │
│ dashboard │   │ iperf3 -s (SRV) │◄──│                    │   │ iperf -c (CLI)│
└───────────┘   └─────────────────┘   └────────────────────┘   └──────┬────────┘
       │  HTTP (/api/register, /progress, /logs/upload,            iperf │ (Wi-Fi Mac
       │        /session/start, /session/reset, /health-check)           │  → kablolu
       │  (4 düğüm hep birlikte koşar → modeme stres)                    │  Mac'e yük)
       └─ Dashboard (Vue 3) tarayıcıdan açılır → 4 düğümü canlı izler
          + sağ panelde aşamalı Health-Check + üstte "Sıfırla" butonu
```

> **iperf topolojisi:** Linux sunucu artık iperf server DEĞİL. **Kablolu Mac**
> `iperf3 -s` (server), **Wi-Fi Mac** client olur; trafik iki Mac arasında modem
> üzerinden akar.

**Statik IP & listener:** Her makineye yerel statik IP atanır ve listener (agent)
boot'ta otomatik başlar. Bunun için `fullservice-backend/provisioning/` altındaki
script'ler kullanılır (config'in `network` bölümünü okur).

---

## Hızlı Başlangıç

### Backend (her makinede)
```bash
cd fullservice-backend
python3 -m venv venv && source venv/bin/activate    # Win: venv\Scripts\activate
pip install -r requirements.txt
```

**Sunucu (Linux)**:
```bash
python run_server.py                # http://<lan_ip>:8770
```

**Agent / listener (her client)** — varsayılan port **7531**:
```bash
python run_agent.py mac_cable http://<lan_ip>:8770
FS_AGENT_PORT=7532 python run_agent.py mac_wifi http://<lan_ip>:8770   # aynı host'ta 2. agent
python run_agent.py win_wifi http://<lan_ip>:8770
```

### Frontend (geliştirme)
```bash
cd fullservice-frontend
npm install
npm run dev                         # http://localhost:5173 (API'yi 8770'e proxy'ler)
```

### Frontend (üretim)
```bash
cd fullservice-frontend
npm run build                       # → dist/
# Backend dist'i otomatik servis eder; doğrudan http://<lan_ip>:8770'e bağlan.
```

Kurulum rehberleri (**statik IP**, **boot listener**, ön koşullar):
- Saha (4 fiziksel makine): [`fullservice-backend/KURULUM_SAHA_4_MAKINE.md`](fullservice-backend/KURULUM_SAHA_4_MAKINE.md)
- Tek Mac VM lab: [`fullservice-backend/KURULUM_VM_LAB_TEK_MAC.md`](fullservice-backend/KURULUM_VM_LAB_TEK_MAC.md)
- Provisioning scriptleri: [`fullservice-backend/provisioning/README.md`](fullservice-backend/provisioning/README.md)

---

## Arayüz (sunucu dashboard)

GRK'nın **Günlük Rutin Kontrol** sekmesi örnek alınarak:

- **Giriş ekranı:** GRK ile aynı `grk_users` tablosundan doğrulanır; DB'ye erişim
  yoksa bile `cpeteam / cpeteam` varsayılan hesabı **her zaman** geçerlidir. Giriş
  sonrası karşılama ekranı (logo + "Hoş Geldiniz \<kullanıcı\>" + "Test Ekranına Gir").
  Sol üstteki logoya tıklayınca karşılama ekranına döner.
- **Cihaz ve Test Bilgileri** kartı: **Marka / Model / Firmware** combobox'ları
  (DB'den — `cpeqadb`/`grk_firmware`; bağlantı yoksa serbest-metin girişine düşer),
  **Süre (sn)** girişi, **FULL Servis Başlat** butonu. Başlat → online listener'lara
  fan-out → her cihaz kendi executer'larını (runner'lar) ayağa kaldırır.
- **Sağ panel — Health-Check:** Bir kez basılınca aşamalı bağlantı kontrolü başlar:
  `1sn×3 → 3sn×3 → 5sn×3 → 15sn×1 → 30sn×1 → sürekli 60sn` (program kapanana dek).
  Her düğüm için kırmızı/yeşil ışık + gecikme (ms).
- **Canlı test ilerlemesi:** Her düğümün her testinin ilerleme yüzdesi 1 sn'de bir
  güncellenir; düğüm kartları orta sütunda **2×2** dizilir, sol kartta **oturum &
  ilerleme özeti** görünür.
- **Sıfırla butonu (üst bar):** Onay sorduktan sonra her şeyi başa alır — testleri
  durdurur, ilerleme/oturum ve Health-Check'i sıfırlar (`POST /api/session/reset`).
- **Tema:** Türk Telekom mavisi; sol açılır menüde Panel / Ayarlar / Profil (son ikisi
  şimdilik yer tutucu).

---

## Test Türleri (4 düğüme dağıtılmış)

| Test            | Ne yapar                                                                 | Hangi düğümler   |
|-----------------|--------------------------------------------------------------------------|------------------|
| `ping_modem`    | Modeme ping — **görünür terminalde canlı**                               | hepsi            |
| `ping_internet` | 8.8.8.8'e ping — **görünür terminalde canlı**                            | hepsi            |
| `youtube`       | Tarayıcıda **en yüksek kalitede** video (Selenium/Chrome zorlar)         | sunucu + 3 client|
| `iperf_server`  | `iperf3 -s` dinler (kablolu Mac)                                          | mac_cable        |
| `iperf`         | `iperf3 -c` ile kablolu Mac'e yük basar                                   | mac_wifi         |
| `torrent`       | **qBittorrent** ile GTA5 magnet indirme döngüsü (gerçek)                  | Windows          |
| `wifi_track`    | Wi-Fi sinyal/kanal/rx-tx + sistem kaynağı takibi — **canlı terminal**    | 2 kablosuz       |

---

## Faz / Durum

| Faz | İçerik                                                                  | Durum |
|-----|-------------------------------------------------------------------------|-------|
| 1–3 | İskelet + protokol + agent + sunucu + dashboard                         | ✅    |
| —   | Marka/Model/Firmware DB combobox + aşamalı Health-Check paneli          | ✅    |
| —   | Statik IP + boot listener paketleme (`provisioning/`)                   | ✅    |
| —   | Mavi tema, sol menü, 2×2 kart, Sıfırla butonu, oturum/ilerleme özeti    | ✅    |
| 4   | torrent (qBittorrent) + wifi_track **gerçek**; ping/wifi **canlı terminal**; YouTube en yüksek kalite | ✅ |
| —   | Login ekranı (GRK `grk_users`; `cpeteam/cpeteam` her zaman geçerli) + karşılama ekranı | ✅ |
| 5   | Loglar **bilgisayar klasörlerine** (LINUX/MAC_ETH/MAC_WIFI/WIN_WIFI) ✅; **FTPS** yükleme ✅; **PostgreSQL** yazma (`copy_` staging) ✅; **mail/Telegram** bildirim ✅; **error_log** → FTP ✅ | ✅ |
| —   | iperf topoloji (kablolu Mac server / Wi-Fi Mac client) — sahada doğrulama sürüyor | 🟡 |
| —   | DB: `copy_` staging → asıl tablolara **birleştirme** (Senaryo 3)        | ⏳    |
| 6   | Tek-tıklık installer paketleme                                          | ⏳    |

---

## Güvenlik / Gizlilik

Bu repo **hiçbir** üretim kimliği içermez:
- DB şifresi, FTP parolası ❌
- SSL sertifikaları (`ca.crt`, `client.crt`, `client.key`) ❌
- Mail / Telegram token'ları ❌

**Sırlar nereden okunur:** Tüm sırlar önce **ortam değişkeni**, yoksa gitignore'lu
`fullservice-backend/secrets.json` dosyasından okunur (`common.config.get_secret`).
Bildirim için gerekli anahtarlar: `FS_TELEGRAM_BOT_TOKEN`, `FS_TELEGRAM_CHAT_ID`,
`FS_SMTP_USER`, `FS_SMTP_PASS`, `FS_SMTP_FROM`. SSL sertifikaları
`fullservice-backend/certs/` altında aranır. Bu dosyaların hiçbiri repoda yoktur;
sunucuya elle konur. Repo içine **asla** sır yazılmaz.

---

## Lisans / İletişim

İç kullanım (Türk Telekom CPE QA). Geliştirici notları, mevcut durum ve karar
gerekçeleri [`GELISTIRME_GUNLUGU.md`](GELISTIRME_GUNLUGU.md) içinde; kod gezisi için
[`KOD_HAKIMIYETI.md`](KOD_HAKIMIYETI.md).
