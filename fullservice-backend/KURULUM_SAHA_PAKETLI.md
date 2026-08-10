# FULL Servis — Saha Kurulumu (Çift-Tık / Paketlenmiş Uygulamalar)

> Bu rehber, FULL Servis'i odadaki 4 makineye **çift tıklanan uygulamalar** olarak
> kurmak içindir. Son kullanıcıda Python / git / terminal **gerekmez**.
> (Terminal ile çalışan eski manuel yöntem: `KURULUM_SAHA_4_MAKINE.md`.)

## Ağ planı (config.json ile aynı olmalı)

| Düğüm | IP | Arayüz (config'deki `interface`) | Makine |
|-------|----|--------|--------|
| server | 192.168.1.10 | **`ip link` çıktısına göre** (or. enp0s1 / eth0) | Dell Linux (Ubuntu) |
| mac_cable | 192.168.1.11 | AX88179A (USB-Ethernet) | MacBook — Ethernet |
| win_wifi | 192.168.1.13 | Wi-Fi | Windows |
| mac_wifi | 192.168.1.14 | Wi-Fi | MacBook — Wi-Fi |
| gateway | 192.168.1.1 | — | Modem (test edilen CPE) |

**Panel:** http://192.168.1.10:8770 &nbsp;•&nbsp; **Giriş:** `cpeteam` / `cpeteam`

> ⚠️ **Linux arayüz adı:** config.json'da `enp0s1` yazıyor. Gerçek makinede
> `ip link` ile bak; farklıysa **config.json'daki `network.assignments.server.interface`
> değerini gerçek ada çevir** (statik-IP script'i bu değeri okur).

---

## Genel akış (3 fazda)

1. **AŞAMA A — Uygulamaları üret** (her işletim sisteminde bir kez, repo+Python olan makinede).
2. **AŞAMA B — Her makineye kur** (statik IP + ön koşullar + klasörü kopyala).
3. **AŞAMA C — Çalıştır** (taze reboot → sırayla çift tık → panelde başlat).

---

# AŞAMA A — Uygulamaları üret (derleme)

Paketlenmiş uygulama **kendi işletim sisteminde** üretilir (Windows'ta Windows,
Mac'te Mac, Linux'ta Linux — çapraz derleme yok). Bu adımı sadece **derleyen
makinede** yaparsın; oda makinelerine sadece çıktı klasörünü kopyalarsın.

Derleme yapılan makinede önce kodu çek:
```bash
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
```

### A.1 — Windows uygulaması  ✅ (bugün üretildi)
`launchers\build\derle-windows.bat` dosyasına **çift tıkla**.
Çıktı: `launchers\build\cikti\FULLSERVIS-WINDOWS-WIFI\` (`.exe` + `ayarlar\config.json`).

### A.2 — Mac uygulamaları (bir Mac'te, ikisini birden üretir)
```bash
chmod +x launchers/build/derle-mac.sh
./launchers/build/derle-mac.sh
```
Çıktı: `cikti/FULLSERVIS-MAC-WIFI/` ve `cikti/FULLSERVIS-MAC-KABLO/`.
Bir Mac'te üretip diğerine USB ile götür — **koşul:** iki Mac de aynı işlemci ailesi
(ikisi de Apple Silicon **ya da** ikisi de Intel).

### A.3 — Linux sunucu uygulaması (Dell'de)
```bash
# Node.js 20 (panel derlemesi için)
curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh && sudo apt-get install -y nodejs
sudo apt install -y git python3-pip python3-venv

chmod +x launchers/build/derle-linux.sh
./launchers/build/derle-linux.sh
```
Bu script önce paneli (Vue) derler, sonra paneli exe'nin içine gömer.
Çıktı: `cikti/FULLSERVIS-SUNUCU/` (uygulama + `.desktop` kısayolu + `ayarlar/`).

> Derleme yapmadan önce, gerekiyorsa `fullservice-backend/config.json`'daki IP'leri
> ve `network.interface` değerlerini odanın gerçek LAN'ına göre düzenle — böylece
> exe'nin **içine gömülen** yedek config de doğru olur. (Yine de dışarıdaki
> `ayarlar/config.json` her zaman öncelikli; sonradan yeniden derlemeden değiştirebilirsin.)

---

# AŞAMA B — Her makineye kurulum (bir kez)

## B.0 — Ön koşul programlar (uygulamanın içine giremezler, elle kurulur)

| Program | Hangi makine | Not |
|---|---|---|
| **Google Chrome** | 4 makine de | YouTube testi için |
| **iperf3** | mac_cable + mac_wifi | Mac'te: `brew install iperf3` (eski macOS'ta kaynaktan derle) |
| **qBittorrent** | sadece Windows | Web UI: **aktif, port 8080, kullanıcı `admin`, şifre `Admin123`** |

> qBittorrent 5.x'te **"Bypass authentication for localhost" KAPALI** olmalı;
> aksi halde giriş 8080/admin/Admin123 ile başarısız olur.

## B.1 — Statik IP

Önce config.json'daki `network` bölümünün doğru olduğundan emin ol, sonra:

| Makine | Komut |
|---|---|
| Linux | `sudo provisioning/linux/set-static-ip.sh server` |
| Windows (Yönetici PS) | `provisioning\windows\set-static-ip.ps1 -NodeId win_wifi` |
| Mac (kablo) | `sudo provisioning/macos/set-static-ip.sh mac_cable` |
| Mac (wifi) | `sudo provisioning/macos/set-static-ip.sh mac_wifi` |

**Doğrulama:** başka bir makineden `ping <atanan_ip>` çalışmalı.
- Linux: `ip addr show <arayüz>` → `inet 192.168.1.10`
- Windows: `Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"` → 192.168.1.13
- Mac: `networksetup -getinfo "Wi-Fi"` → IPv4: 192.168.1.14

> Statik-IP script'lerini çalıştırmak için o makinede kodun (repo) bir kopyası
> gerekir. Alternatif olarak IP'yi işletim sisteminin ağ ayarlarından elle de
> verebilirsin (aynı IP/mask/gateway/DNS).

## B.2 — Uygulama klasörünü kopyala

`cikti/<UYGULAMA>/` klasörünü, **içindeki `ayarlar/` ile birlikte**, o makinenin
**Masaüstüne** kopyala:

| Klasör | Makine |
|---|---|
| `FULLSERVIS-SUNUCU/` | Linux |
| `FULLSERVIS-MAC-KABLO/` | Mac (kablo) |
| `FULLSERVIS-MAC-WIFI/` | Mac (wifi) |
| `FULLSERVIS-WINDOWS-WIFI/` | Windows |

> ⚠️ **Uygulamanın adını değiştirme** — hangi makine olduğunu **dosya adından**
> çözüyor (FULLSERVIS-WINDOWS-WIFI → win_wifi). Ad değişirse kimliğini bulamaz.

## B.3 — Sırlar ve sertifikalar (SADECE Linux sunucuda)

Linux'taki `FULLSERVIS-SUNUCU/ayarlar/` klasörüne şunları koy (repoda YOK, USB ile):
- `secrets.json` → Telegram + mail bildirimi için
- `certs/` (`ca.crt`, `client.crt`, `client.key`) → FTP + DB yazımı için

`secrets.json` içeriği:
```json
{
  "FS_TELEGRAM_BOT_TOKEN": "...",
  "FS_TELEGRAM_CHAT_ID": -4802883729,
  "FS_SMTP_USER": "cpetestteam",
  "FS_SMTP_PASS": "...",
  "FS_SMTP_FROM": "cpetestteam@gmail.com"
}
```
> Bunlar olmadan **testler yine çalışır**, sadece Telegram/mail bildirimi ve DB
> kaydı yapılmaz. Marka/Model/Firmware listeleri de DB'den gelir; DB'ye ulaşılamazsa
> alanları elle (serbest metin) girersin.

## B.4 — İlk açılışta işletim sistemi uyarıları (bir kerelik)

- **Mac:** "geliştirici doğrulanamadı" → uygulamaya **sağ tık → Aç → Aç** (bir kez).
- **Windows:** Defender uyarısı → **"Yine de çalıştır"**.
- **Linux:** `.desktop` dosyasına sağ tık → **"Çalıştırmaya izin ver"**.

---

# AŞAMA C — Çalıştırma (test günü)

### ⚠️ ÖNEMLİ — Uptime kilidi (yeni)
Bir makine **45 dakikadan** uzun süredir açıksa panelde **KIRMIZI** görünür ve
**test başlatılamaz** (uyarı verir). Bu yüzden test öncesi **tüm makineleri yeniden
başlat**; taze açılışta hepsi yeşil olur. (Eşik: `config.json → uptime_limit_minutes`.)

### Sıra
1. **Tüm makineleri yeniden başlat** (uptime < 45 dk olsun).
2. **Linux** → `FULLSERVIS-SUNUCU`'ya (ya da `.desktop` kısayoluna) çift tıkla.
   → Siyah pencere açılır, panel tarayıcıda `http://192.168.1.10:8770` adresinde açılır.
3. **Mac (Kablo)** → `FULLSERVIS-MAC-KABLO` → panelde **yeşil**.
4. **Mac (Wi-Fi)** → `FULLSERVIS-MAC-WIFI` → **yeşil**.
5. **Windows** → `FULLSERVIS-WINDOWS-WIFI` → **yeşil**.
6. Panelde: **giriş** (`cpeteam`/`cpeteam`) → **Test Ekranına Gir** →
   sağ panelde **Health-Check** → 4 düğüm yeşil →
   **Marka / Model / Firmware** seç + **süre** gir → **FULL Servis Başlat**.

> Açılan pencereleri **KAPATMA** — kapatırsan o makine panelden düşer.
> Yanlışlıkla iki kez tıklarsan sorun olmaz; uygulama eskisini kendi kapatır.

**Test bitince:** loglar bilgisayar-bazlı klasörlere (LINUX / MAC_ETH / MAC_WIFI /
WIN_WIFI) toplanır → FTP'ye yüklenir → sonuçlar DB'ye (`copy_` tablolar) yazılır →
Telegram (tek ZIP) + mail bildirimi gider.

---

# Sonradan değişiklik

| Ne değişti? | Ne yapmalısın |
|---|---|
| IP, süre, hangi makine hangi testi koşacak | O makinedeki `ayarlar/config.json`'u düzenle. **Yeniden derleme yok.** |
| Telegram/mail/DB şifresi | Linux'taki `ayarlar/secrets.json`'u düzenle. |
| Kodda bir şey (yeni özellik / düzeltme) | O işletim sisteminde derleme scriptini tekrar çalıştır, yeni klasörü eskisinin üzerine kopyala. |

---

# Sorun giderme

| Belirti | Çözüm |
|---|---|
| Bir makine **kırmızı** | Uygulaması açık mı? `ping 192.168.1.10` gidiyor mu? Ya da **45 dk kuralı** — makineyi yeniden başlat. |
| "Bu uygulamanın hangi bilgisayara ait olduğu anlaşılamadı" | Uygulama adı değişmiş → eski adına çevir; ya da yanına `ayarlar/agent.json` koy: `{"node_id":"win_wifi","server_url":"http://192.168.1.10:8770"}` |
| Panel tarayıcıda açılmadı | Elle yaz: `http://192.168.1.10:8770` |
| **iperf** kırmızı/hatalı | mac_cable açık mı? iki Mac'te de iperf3 kurulu mu? |
| **torrent** hatası | Windows'ta qBittorrent açık mı? Web UI 8080 / admin / Admin123, "Bypass auth" kapalı mı? |
| **Marka/Model boş** | Linux `ayarlar/certs/` ve `secrets.json` var mı? (Sistem yine çalışır, alanları elle yaz.) |
| **Telegram/mail gelmiyor** | Linux `ayarlar/secrets.json` dolu mu? `FS_NOTIFY_DISABLE=1` ayarlı olmasın. |
| **FTP'ye yüklenmiyor** | Linux `ayarlar/certs/` var mı? `FS_FTP_DISABLE=1` ayarlı olmasın. |
| Giriş yapılamıyor | DB kapalı olsa bile `cpeteam`/`cpeteam` her zaman çalışır. |

---

# Emanet iade — statik IP kaldırma

| Makine | Komut |
|---|---|
| Linux | `sudo nmcli con mod "<baglanti>" ipv4.method auto ipv4.addresses "" ipv4.gateway "" ipv4.dns ""` → `sudo nmcli con up "<baglanti>"` |
| Mac (kablo) | `sudo networksetup -setdhcp "AX88179A"` |
| Mac (wifi) | `sudo networksetup -setdhcp "Wi-Fi"` |
| Windows (Yön. PS) | `Set-NetIPInterface -InterfaceAlias "Wi-Fi" -Dhcp Enabled; Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ResetServerAddresses; Restart-NetAdapter -Name "Wi-Fi"` |

> Boot listener (otomatik başlatma) kurduysan onu da kaldır:
> Linux `sudo systemctl disable --now fullservice-server`;
> Windows `Unregister-ScheduledTask -TaskName FullServiceAgent_win_wifi -Confirm:$false`;
> Mac `launchctl unload ~/Library/LaunchAgents/com.tt.fullservice.agent.plist`.
