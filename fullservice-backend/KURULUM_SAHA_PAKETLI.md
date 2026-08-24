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

## A.1.1 — WINDOWS: derleme bitti, şimdi ne yapmalısın (adım adım kontrol)

Bu makine kendi GitHub klonundan kendi uygulamasını üretiyor (Linux'takiyle
aynı mantık — bkz. A.3.1). Sırayla, PowerShell'de:

**0) Çıktı gerçekten oluşmuş mu?**
```powershell
dir launchers\build\cikti\FULLSERVIS-WINDOWS-WIFI
# olması gerekenler: FULLSERVIS-WINDOWS-WIFI.exe, ayarlar\config.json
```

**1) Gömülen config doğru mu?**
```powershell
type launchers\build\cikti\FULLSERVIS-WINDOWS-WIFI\ayarlar\config.json | findstr win_wifi
# beklenen: "win_wifi": { "ip": "192.168.1.13", "interface": "Wi-Fi" }
```

**2) Statik IP — şimdi doğrula (Yönetici PowerShell):**
```powershell
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"
# beklenen: IPv4Address 192.168.1.13
```
- `192.168.1.13` yoksa/farklıysa:
  ```powershell
  provisioning\windows\set-static-ip.ps1 -NodeId win_wifi
  ```
  sonra `Get-NetIPConfiguration` ile tekrar doğrula.
- ⚠️ **Arayüz adı gerçekten "Wi-Fi" mi?** `Get-NetAdapter` ile listele — bazı
  makinelerde "Wi-Fi 2", "Kablosuz Ağ Bağlantısı" gibi farklı görünür. Farklıysa
  ya adaptörü Windows ayarlarından "Wi-Fi" diye yeniden adlandır, ya da
  `config.json`'daki `win_wifi.interface` değerini gerçek ada göre değiştirip
  **yeniden derle**.
- Reboot sonrası (AŞAMA C, 45 dk kuralı) bu kontrolü bir daha yap.

**3) secrets.json / certs/** — bu makinede **yok/gerekmiyor** (sadece Linux
sunucuda, bkz. B.3). Atla.

**4) `cikti\FULLSERVIS-WINDOWS-WIFI\` klasörünü repo'nun yanına taşı**
(repo kökünden — klonladığın klasörün içinden):
```powershell
move launchers\build\cikti\FULLSERVIS-WINDOWS-WIFI ..\FULLSERVIS-WINDOWS-WIFI
```
Sonuç: `FULL SERVIS OTOMASYON\FULLSERVIS-WINDOWS-WIFI\` — repo'nun kardeşi.
```powershell
dir ..\FULLSERVIS-WINDOWS-WIFI
dir ..\FULLSERVIS-WINDOWS-WIFI\ayarlar
```
`.exe` ve `ayarlar\config.json` görmelisin.

**5) Taşıma doğrulandıysa klonladığın kaynak kod klasörünü sil** (bkz. A.4) —
sadece 4. adım gerçekten başarılıysa.

**6) İlk çalıştırma güveni** — `.exe`'ye çift tıkla → **Windows Defender
SmartScreen** uyarısı çıkarsa **"Daha fazla bilgi" → "Yine de çalıştır"**
(bir kerelik). Ayrıca **Windows Firewall'da agent portuna (7531,
`config.json → agent_port`) inbound izin ver** — vermezsen kayıt (agent→sunucu,
8770) çalışsa bile panelde **kırmızı** kalır, çünkü Health-Check sunucudan
agent'a **ters yönde** (7531'e) bağlanmayı dener:
```powershell
New-NetFirewallRule -DisplayName "FULL Servis Agent" -Direction Inbound -Protocol TCP -LocalPort 7531 -Action Allow
```

**7) Gerçek deneme** — `.exe`'ye çift tıkla → konsol penceresi açık kalmalı
(kapatma). Bu bir **agent** uygulaması, kendi paneli yok — doğrulamayı
**Linux sunucunun panelinden** yap: bir tarayıcıda `http://192.168.1.10:8770`
aç → giriş `cpeteam`/`cpeteam` → Health-Check'te **win_wifi yeşil** olmalı.
Hâlâ kırmızıysa Linux'tan doğrudan test et:
```bash
curl http://<windows-ip>:7531/health
# beklenen: {"status":"ok","node_id":"win_wifi"}
```

> ⚠️ Bu denemeden sonra makine 45 dakikayı geçmeden test başlatabilirsin, ama
> gerçek test günü öncesi son bir kez daha reboot et (uptime kilidi).

### A.2 — Mac uygulamaları (her Mac kendi klonundan kendi uygulamasını üretir)
```bash
chmod +x launchers/build/derle-mac.sh
./launchers/build/derle-mac.sh
```
Çıktı: **her iki** `cikti/FULLSERVIS-MAC-WIFI/` ve `cikti/FULLSERVIS-MAC-KABLO/`
(script ikisini de üretir, sen sadece o makineye ait olanı kullanacaksın).

> Not: Artık her Mac GitHub'dan kendi klonunu çekip kendi üstünde derliyor
> (Linux'takiyle aynı mantık) — bu yüzden eski "bir Mac'te üret, USB ile
> diğerine taşı" kısıtı (aynı işlemci ailesi şartı) **geçerli değil**; her Mac
> kendi native binary'sini üretir.

## A.2.1 — MAC (Kablo veya Wi-Fi): derleme bitti, şimdi ne yapmalısın

Hangi Mac'tesen ona ait `<UYGULAMA>` adını kullan: Kablo Mac'te
`FULLSERVIS-MAC-KABLO`, Wi-Fi Mac'te `FULLSERVIS-MAC-WIFI`. Terminalde,
sırayla:

**0) Çıktı gerçekten oluşmuş mu?**
```bash
ls launchers/build/cikti/<UYGULAMA>/
# olması gerekenler: <UYGULAMA> (calistirilabilir), ayarlar/config.json,
# BASLAT-<UYGULAMA>.command
```

**1) Gömülen config doğru mu?**
```bash
grep -A1 '"mac_cable"\|"mac_wifi"' launchers/build/cikti/<UYGULAMA>/ayarlar/config.json
# mac_cable icin beklenen interface: "AX88179A"  (ip 192.168.1.11)
# mac_wifi  icin beklenen interface: "Wi-Fi"     (ip 192.168.1.14)
```

**2) Statik IP — şimdi doğrula:**
```bash
networksetup -getinfo "AX88179A"   # mac_cable icin
networksetup -getinfo "Wi-Fi"      # mac_wifi icin
# beklenen: IP address: 192.168.1.11 (kablo) / 192.168.1.14 (wifi)
```
- Yanlışsa/yoksa:
  ```bash
  sudo provisioning/macos/set-static-ip.sh mac_cable   # ya da mac_wifi
  ```
  sonra `networksetup -getinfo ...` ile tekrar doğrula.
- ⚠️ **Servis adı gerçekten "AX88179A" mı?** USB-Ethernet adaptörler
  sürücüye göre farklı isimle görünebilir. Kontrol:
  ```bash
  networksetup -listallnetworkservices
  ```
  Listede `AX88179A` yoksa gerçek adı `config.json`'daki
  `mac_cable.interface` değerine yaz ve **yeniden derle**.
- Reboot sonrası (AŞAMA C, 45 dk kuralı) bu kontrolü bir daha yap.

**3) secrets.json / certs/** — bu makinede **yok/gerekmiyor** (sadece Linux
sunucuda, bkz. B.3). Atla.

**4) `cikti/<UYGULAMA>/` klasörünü repo'nun yanına taşı** (repo kökünden):
```bash
mv launchers/build/cikti/<UYGULAMA> ../<UYGULAMA>
```
Sonuç: `FULL SERVIS OTOMASYON/<UYGULAMA>/` — repo'nun kardeşi.
```bash
ls ../<UYGULAMA>/
ls ../<UYGULAMA>/ayarlar/
```
Binary, `BASLAT-*.command` ve `ayarlar/config.json` görmelisin.

**5) Taşıma doğrulandıysa klonladığın kaynak kod klasörünü sil** (bkz. A.4) —
sadece 4. adım gerçekten başarılıysa. (Kullanmadığın diğer `<UYGULAMA>`
zaten bu klasörle birlikte gider, ayrıca taşımana gerek yok.)

**6) İlk çalıştırma güveni** — macOS "geliştirici doğrulanamadı" derse:
`BASLAT-*.command`'a **sağ tık → Aç → Aç** (bir kerelik). Hâlâ açılmıyorsa:
```bash
xattr -dr com.apple.quarantine ../<UYGULAMA>
```

**7) Gerçek deneme** — `BASLAT-<UYGULAMA>.command`'a çift tıkla → Terminal
açılıp uygulama başlamalı. Bu bir **agent** uygulaması, kendi paneli yok —
doğrulamayı **Linux sunucunun panelinden** yap: bir tarayıcıda
`http://192.168.1.10:8770` aç → giriş `cpeteam`/`cpeteam` → Health-Check'te
bu makine (**mac_cable** ya da **mac_wifi**) **yeşil** olmalı.

> ⚠️ Bu denemeden sonra makine 45 dakikayı geçmeden test başlatabilirsin, ama
> gerçek test günü öncesi son bir kez daha reboot et (uptime kilidi).

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

## A.3.1 — LINUX: derleme bitti, şimdi ne yapmalısın (adım adım kontrol)

`derle-linux.sh` bitince o makinede aşağıdakileri **sırayla** yap; her adımdan
sonraki komutla doğrula, atlama.

**0) Neredesin, çıktı gerçekten oluşmuş mu?**
```bash
pwd                                            # repo kökünde olmalısın (klonladığın klasör)
ls launchers/build/cikti/FULLSERVIS-SUNUCU/    # şunlar olmalı:
#   FULLSERVIS-SUNUCU                (calistirilabilir dosya)
#   ayarlar/config.json
#   ayarlar/certs/                   (henuz bos, B.3'te dolacak)
#   FULL-Servis-Sunucu.desktop
```
Bu dosyalar yoksa derleme başarısız demektir — `derle-linux.sh` çıktısındaki
son hata satırına bak, buraya geçme.

**1) Gömülen config gerçekten doğru mu?**
```bash
grep interface launchers/build/cikti/FULLSERVIS-SUNUCU/ayarlar/config.json
# beklenen: "server": { "ip": "192.168.1.10", "interface": "eth0" }
```
`enp0s1` görürsen: repo güncel değil demektir — `git pull` çekip
`derle-linux.sh`'ı tekrar çalıştır.

**2) Statik IP — DAHA ÖNCE ayarladıysan bile şimdi tekrar doğrula**
(reboot, DHCP yenileme, elle ayarlama gibi nedenlerle değişmiş olabilir).
Bazı makinelerde `ip` komutu kurulu değil/çalışmıyor — o durumda `ifconfig`
kullan (ikisi de aynı bilgiyi verir):
```bash
ip addr show eth0 | grep inet          # ip calismiyorsa:
ifconfig eth0 | grep "inet "           # bunu kullan
# beklenen (ikisinde de): inet 192.168.1.10 ...
```
- `192.168.1.10` **yoksa veya farklıysa** (ör. DHCP'den gelen `192.168.1.102`
  gibi bir adres görüyorsan statik IP hiç uygulanmamış demektir) → script'i
  (yeniden) çalıştır:
  ```bash
  sudo fullservice-backend/provisioning/linux/set-static-ip.sh server
  ```
  sonra yukarıdaki komutu (`ip addr` ya da `ifconfig`, hangisi çalışıyorsa)
  **tekrar** çalıştırıp gerçekten `192.168.1.10` göründüğünü teyit et.
- Doğruysa bile not al: **AŞAMA C'de makineyi yeniden başlatacaksın** (45 dk
  kuralı) — reboot'tan sonra bu kontrolü bir kez daha yap, statik IP
  NetworkManager profilinde kalıcı olsa da gözle görmeden güvenme.

**3) secrets.json + certs/ (Telegram/mail/DB için — testin ÇALIŞMASI için ZORUNLU DEĞİL)**
Şu an elinde yoksa sorun değil, testler yine çalışır (giriş `cpeteam`/`cpeteam`,
Marka/Model/Firmware serbest metin olur, Telegram/mail/DB kaydı gitmez). Elde
ettiğinde (USB ile) şu tam konuma koy:
```
launchers/build/cikti/FULLSERVIS-SUNUCU/ayarlar/secrets.json
launchers/build/cikti/FULLSERVIS-SUNUCU/ayarlar/certs/ca.crt
launchers/build/cikti/FULLSERVIS-SUNUCU/ayarlar/certs/client.crt
launchers/build/cikti/FULLSERVIS-SUNUCU/ayarlar/certs/client.key
```
(`secrets.json` içeriği için bkz. B.3 aşağıda.) Daha sonra eklersen yeniden
derlemene gerek yok — bu klasördeki `ayarlar/` her zaman canlı okunur.

**4) `cikti/FULLSERVIS-SUNUCU/` klasörünü repo'nun yanına taşı**
(2. ve 3. adımı bitirdikten sonra — sırası önemli değil ama taşımadan
kaynak klasörü SİLME). Repo kökünden (klonladığın `fullservice_automation/`
klasörünün içinden) çalıştır — `FULL SERVIS OTOMASYON/` klasörüne, repo'nun
**kardeşi** olarak taşınır:
```bash
mv launchers/build/cikti/FULLSERVIS-SUNUCU ../FULLSERVIS-SUNUCU
```
(Bkz. B.2 — aynı mantık tüm makineler için orada da anlatılıyor.)

**5) Taşınan klasörde her şey hâlâ yerinde mi?**
```bash
ls "$(xdg-user-dir DESKTOP)/FULLSERVIS-SUNUCU/"
ls "$(xdg-user-dir DESKTOP)/FULLSERVIS-SUNUCU/ayarlar/"
```
`FULLSERVIS-SUNUCU`, `FULL-Servis-Sunucu.desktop`, `ayarlar/config.json`
görmelisin (3. adımı yaptıysan `secrets.json` ve `certs/*` de).

**6) Şimdi (ve ancak şimdi) klonladığın kaynak kod klasörünü sil** (bkz. A.4).

**7) İlk çalıştırma güveni** — `.desktop` dosyasına sağ tık →
**"Çalıştırmaya izin ver"** (bir kerelik, B.4).
> Bazı GNOME/Nautilus kurulumlarında `.desktop` dosyası "güvenilir" işaretlenmeden
> çift tıklanınca **metin dosyası gibi açılır**, program başlamaz. Bu durumda
> `.desktop`'ın **yanındaki asıl çalıştırılabilir dosyaya** (`FULLSERVIS-SUNUCU`,
> uzantısız) çift tıkla — sonuç birebir aynıdır, `.desktop` sadece kolaylık
> kısayolu. Hangisi çalışıyorsa onu kullanmaya devam edebilirsin.

**8) Gerçek deneme** — `.desktop`'a (ya da yukarıdaki not geçerliyse doğrudan
`FULLSERVIS-SUNUCU`'ya) çift tıkla → terminal penceresi açılmalı → tarayıcıda
`http://192.168.1.10:8770` otomatik açılmalı (açılmazsa elle yaz).
Giriş `cpeteam`/`cpeteam` ile çalışmalı. Diğer 3 makine henüz kurulmadığı için
panelde şu an sadece Linux düğümü **yeşil**, diğer 3'ü **kırmızı/gri** görünür
— bu normal, hata değil.

> ⚠️ Bu denemeyi yaptıktan sonra makine 45 dakikayı geçmeden test
> **başlatabilirsin**, ama gerçek test günü öncesi son bir kez daha reboot et
> (uptime kilidi — bkz. AŞAMA C).

---

### A.4 — Derleme bitince: kaynak kodu sil, sadece çıktıyı bırak

Her makine GitHub'dan kod çekip (git clone + `git checkout aliimran`) kendi
uygulamasını kendi üstünde derliyor. Derleme bitince o makinede **artık git
deposuna ihtiyaç yok** — uygulama PyInstaller "onefile" ile tek dosyada:
Python + kod + tüm bağımlılıklar (Linux'ta ayrıca derlenmiş panel/Vue de)
doğrudan çalıştırılabilirin içine gömülü.

**KALACAK** — sadece Masaüstündeki `cikti/<UYGULAMA>/` klasörü (bkz. B.2):

| Makine | Klasörde ne var |
|---|---|
| Linux | `FULLSERVIS-SUNUCU` + `ayarlar/{config.json, secrets.json, certs/}` + `.desktop` kısayolu |
| Mac (Kablo / Wi-Fi) | `FULLSERVIS-MAC-*` + `ayarlar/config.json` + `BASLAT-*.command` |
| Windows | `FULLSERVIS-WINDOWS-WIFI.exe` + `ayarlar\config.json` |

**SİLİNEBİLİR** — git ile çekilen `fullservice_automation/` klasörünün tamamı:
kaynak kod, `venv/` (veya Python), `node_modules/`, `build/` ve `dist/`
(PyInstaller'ın ara klasörleri — Masaüstüne kopyaladığın `cikti/` ile
karıştırma), `.git/` — hepsi silinebilir, uygulamanın çalışması için hiçbiri
gerekmiyor.

⚠️ Sırayla yap:
1. `cikti/<UYGULAMA>/` klasörünü önce **Masaüstüne kopyala** (B.2).
2. Aynı makinede birden fazla uygulama üretiyorsan (ör. Mac'te iki `cikti/`
   klasörü, ya da diğer Mac'e USB ile taşıyacaksan) **hepsini çıkardıktan
   sonra** sil.
3. Kopyaladığından emin olduktan sonra klonladığın `fullservice_automation/`
   klasörünü (git deposu dahil) sil.

Kod ileride değişirse: yine `git clone` + `git checkout aliimran` ile baştan
çek, yeniden derle, çıkan `cikti/` klasörünü Masaüstündeki eskisinin üzerine
kopyala (bkz. aşağıdaki "Sonradan değişiklik" tablosu) — bu yüzden silmekten
çekinme, her şey GitHub'da duruyor.

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

Her makinede Masaüstünde bir **"FULL SERVIS OTOMASYON"** klasörü açıp repoyu
onun **içine** klonladığını varsayıyoruz (`FULL SERVIS OTOMASYON/fullservice_automation/`).
`cikti/<UYGULAMA>/` klasörünü, **içindeki `ayarlar/` ile birlikte**, repo'nun
**yanına** (bir üst dizine — yani `FULL SERVIS OTOMASYON/` içine, `fullservice_automation/`
klasörünün kardeşi olarak) taşı. Komutu **repo kökünden** (klonladığın klasörün
içinden) çalıştır:

| Makine | Komut (repo kökünden) |
|---|---|
| Linux | `mv launchers/build/cikti/FULLSERVIS-SUNUCU ../FULLSERVIS-SUNUCU` |
| Mac (kablo) | `mv launchers/build/cikti/FULLSERVIS-MAC-KABLO ../FULLSERVIS-MAC-KABLO` |
| Mac (wifi) | `mv launchers/build/cikti/FULLSERVIS-MAC-WIFI ../FULLSERVIS-MAC-WIFI` |
| Windows (cmd) | `move launchers\build\cikti\FULLSERVIS-WINDOWS-WIFI ..\FULLSERVIS-WINDOWS-WIFI` |

Taşıma bitince o klasörün yapısı şöyle olmalı:
```
FULL SERVIS OTOMASYON/
├── fullservice_automation/     ← klon (B.2'den sonra, A.4'e göre silinecek)
└── FULLSERVIS-SUNUCU/          ← (ya da makineye göre diğer isim) — KALICI, çift tıklanan bu
```
> Mac'te `derle-mac.sh` **her iki** uygulamayı da üretir (`cikti/`'de ikisi de
> vardır) — o makineye ait **olmayanı** taşımana/tutmana gerek yok, repo
> silinince zaten gider.

> ⚠️ **Uygulamanın adını değiştirme** — hangi makine olduğunu **dosya adından**
> çözüyor (FULLSERVIS-WINDOWS-WIFI → win_wifi). Ad değişirse kimliğini bulamaz.

## B.3 — Sırlar ve sertifikalar (SADECE Linux sunucuda)

Linux'taki `FULLSERVIS-SUNUCU/ayarlar/` klasörüne şunları koy (repoda YOK, USB ile):
- `secrets.json` → Telegram + mail bildirimi için
- `certs/` (`ca.crt`, `client.crt`, `client.key`) → FTP + DB yazımı için

`secrets.json` içeriği (`FS_FIRMWARE_DB_URL` DB bağlantısı için ZORUNLU —
Marka/Model/Firmware combobox'larını o besler):
```json
{
  "FS_FIRMWARE_DB_URL": "postgresql://...",
  "FS_TELEGRAM_BOT_TOKEN": "...",
  "FS_TELEGRAM_CHAT_ID": -4802883729,
  "FS_SMTP_USER": "cpetestteam",
  "FS_SMTP_PASS": "...",
  "FS_SMTP_FROM": "cpetestteam@gmail.com"
}
```

**Kopyaladıktan sonra sertifika izinlerini düzelt** (USB/dosya yöneticisiyle
kopyalama izinleri 777 yapar; libpq dünyaya açık özel anahtarla bağlanmayı
reddeder → combobox'lar boş gelir):
```bash
chmod 600 ayarlar/certs/client.key
chmod 644 ayarlar/certs/ca.crt ayarlar/certs/client.crt
ls -la ayarlar/certs        # client.key -rw------- olmali
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
| Kodda bir şey (yeni özellik / düzeltme) | Aşağıdaki **"Kod güncellemesi"** akışını uygula. |

## Kod güncellemesi — makineleri yeni sürüme çekme

Kaynak kodu sildiysen (A.4) elde yalnızca çalıştırılabilir uygulama var; kod
değişince o uygulamanın **yeniden derilmesi** gerekir. Yani: kodu tekrar çek →
derle → yeni klasörü eskisinin üzerine koy.

**Hangi makineleri güncellemeliyim?** Değişiklik nerede olduğuna bakılır — ama
pratikte ayırt etmek zor olduğu için **4 makineyi de güncellemek en güvenlisidir**
(hepsi aynı `fullservice-backend` kodunu paylaşıyor).

### Her makinede, sırayla

**1) Uygulamayı kapat** (siyah konsol penceresi açıksa kapat) — çalışan dosyanın
üzerine yazılamaz (özellikle Windows'ta "dosya kullanımda" hatası verir).

**2) `ayarlar/` klasörünü yedekle** — içinde `config.json` (+ Linux'ta
`secrets.json`, `certs/`) var; bunlar repoda YOK, kaybedersen tekrar üretemezsin:
```bash
cp -r ~/Desktop/"FULL SERVIS OTOMASYON"/FULLSERVIS-SUNUCU/ayarlar /tmp/ayarlar_yedek
```
(Windows: `ayarlar` klasörünü Masaüstüne kopyala.)

**3) Kodu tekrar çek** — "FULL SERVIS OTOMASYON" klasörünün içine:
```bash
cd ~/Desktop/"FULL SERVIS OTOMASYON"
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
```
> Kaynak klasörü silmediysen `git clone` yerine, o klasörün içinde
> `git checkout aliimran && git pull` yeterlidir.

**3.5) SADECE mac_wifi'de — CoreWLAN kur.** Wi-Fi Analiz testi buna mecburdur ve
**derlemeden ÖNCE** kurulmalıdır, yoksa uygulamanın içine girmez:
```bash
python3 -m pip install pyobjc-framework-CoreWLAN
python3 -c "import CoreWLAN; print('OK')"
```
Hata verirse: `python3 -m pip install 'pyobjc-framework-CoreWLAN<11'`
(mac_cable ve Windows'ta gerekmez — orada `wifi_track` rolü yok.)

**4) Derle** — makineye göre (AŞAMA A ile aynı):

| Makine | Komut |
|---|---|
| Linux | `chmod +x launchers/build/derle-linux.sh && ./launchers/build/derle-linux.sh` |
| Mac | `chmod +x launchers/build/derle-mac.sh && ./launchers/build/derle-mac.sh` |
| Windows | `launchers\build\derle-windows.bat` dosyasına çift tıkla |

**5) Yeni klasörü eskisinin yerine koy** — eskiyi sil, yenisini taşı:
```bash
rm -rf ../FULLSERVIS-SUNUCU                                    # eski (ayarlar yedekte)
mv launchers/build/cikti/FULLSERVIS-SUNUCU ../FULLSERVIS-SUNUCU
```
(Mac/Windows'ta `FULLSERVIS-SUNUCU` yerine o makinenin uygulama adını yaz.)

**6) `ayarlar/` klasörünü geri koy** — derleme yeni bir `ayarlar/` üretir ama
içinde yalnızca repodaki varsayılan `config.json` olur; **senin** ayarların
(özellikle Linux'ta `secrets.json` + `certs/`) 2. adımdaki yedekte:
```bash
cp -r /tmp/ayarlar_yedek/. ../FULLSERVIS-SUNUCU/ayarlar/
# ⚠️ SERTIFIKA IZINLERI — kopyalama sonrasi HER ZAMAN calistir (asagidaki nota bak)
chmod 600 ../FULLSERVIS-SUNUCU/ayarlar/certs/client.key
chmod 644 ../FULLSERVIS-SUNUCU/ayarlar/certs/ca.crt ../FULLSERVIS-SUNUCU/ayarlar/certs/client.crt
ls -la ../FULLSERVIS-SUNUCU/ayarlar ../FULLSERVIS-SUNUCU/ayarlar/certs
```
⚠️ Bu adımı atlarsan Linux'ta Telegram/mail/DB/FTP sessizce çalışmaz.

> **`client.key` izni neden önemli?** PostgreSQL istemcisi (libpq), özel anahtar
> dosyası grup/dünya tarafından okunabiliyorsa bağlantıyı **reddeder**. Dosya
> yöneticisiyle kopyala-yapıştır (özellikle USB/Windows disk üzerinden) izinleri
> `-rwxrwxrwx` (777) yapar ve DB bağlantısı sessizce kurulamaz. Belirtisi:
> **Marka/Model/Firmware combobox'ları boş gelir** (arayüz serbest-metne düşer)
> ve sunucu konsolunda açılışta şu satır olur:
> `[FIRMWARE_DB] Veritabani baglantisi yapilandirilamadi: ...`
> Bağlantı yalnızca **açılışta bir kez** kurulur — izni düzelttikten sonra
> uygulamayı **kapatıp yeniden aç**, yoksa düzelme etkili olmaz.

**7) Kaynak kodu tekrar sil** (A.4) ve **8) uygulamayı bir kez çalıştırıp**
panelde o makinenin **yeşil** olduğunu doğrula.

> **Windows'ta firewall kuralı:** bir kez eklediysen kalıcıdır, yeniden derlemede
> tekrar eklemene gerek yoktur (bkz. A.1.1 madde 6).

> **Sürüm doğrulama:** güncellemenin gerçekten geçtiğinden emin olmak için,
> derlemeden önce repo klasöründe `git log --oneline -1` çalıştır ve son commit'in
> GitHub'daki `aliimran` dalıyla aynı olduğunu gör.

---

# Sorun giderme

| Belirti | Çözüm |
|---|---|
| Bir makine **kırmızı** | Uygulaması açık mı? `ping 192.168.1.10` gidiyor mu? Ya da **45 dk kuralı** — makineyi yeniden başlat. |
| Terminalde **"Sunucuya ulasilamadi (http://192.168.1.10:8770)"** tekrar tekrar yazıyor | Agent, sunucuya `POST /api/register` atamıyor demektir. Sırayla kontrol et: **1)** O makinede `ping 192.168.1.10` gidiyor mu? Gitmiyorsa **Wi-Fi yanlış ağa bağlı olabilir** — makine, gateway'i 192.168.1.1 olan **CPE'nin kendi Wi-Fi/LAN'ına** bağlı olmalı, başka bir ağa (ev/ofis Wi-Fi'si) değil. **2)** `ipconfig` (Win) / `ifconfig` (Mac) ile o adaptörün IP'sinin gerçekten 192.168.1.13/14 (ve doğru subnet'te) olduğunu doğrula. **3)** Konsolun en üstündeki `[AGENT] node_id=... server=... lan_ip=...` satırına bak — `lan_ip=` beklenenden farklıysa (ör. başka bir ağın IP'si) makine internete/8.8.8.8'e o **yanlış** arayüzden çıkıyor demektir (bkz. `detect_lan_ip()`), aynı kök nedene işaret eder. **4)** Linux'ta sunucu penceresi hâlâ açık mı (kapatılmamış mı)? |
| "Bu uygulamanın hangi bilgisayara ait olduğu anlaşılamadı" | Uygulama adı değişmiş → eski adına çevir; ya da yanına `ayarlar/agent.json` koy: `{"node_id":"win_wifi","server_url":"http://192.168.1.10:8770"}` |
| Windows/Mac **kayıt oldu** (konsolda "Sunucuya kayit olundu" / uptime görünüyor) ama panelde **hâlâ kırmızı** | Health-Check, sunucudan agent'a **ters yönde** bağlanır (agent'ın 7531 portuna). Windows Firewall'da bu porta inbound izin ver (bkz. A.1.1 madde 6); Mac'te genelde sorun olmaz. Doğrulama: Linux'tan `curl http://<agent-ip>:7531/health`. |
| Panel tarayıcıda açılmadı | Elle yaz: `http://192.168.1.10:8770` |
| **iperf** kırmızı/hatalı | mac_cable açık mı? iki Mac'te de iperf3 kurulu mu? |
| **torrent** hatası | Windows'ta qBittorrent açık mı? Web UI 8080 / admin / Admin123, "Bypass auth" kapalı mı? |
| **Marka/Model/Firmware combobox'ları boş** | DB bağlantısı açılışta kurulamamış. Sunucu konsolunun ilk satırlarında `[FIRMWARE_DB] Veritabani baglantisi yapilandirilamadi: ...` var mı, bak — asıl sebebi orası yazar. Sık sebepler: **1)** `ayarlar/certs/client.key` izni 777 (kopyala-yapıştır sonrası) → `chmod 600 ayarlar/certs/client.key`, **2)** `ayarlar/secrets.json` yok ya da `FS_FIRMWARE_DB_URL` boş, **3)** `ayarlar/ayarlar/...` gibi iç içe klasör oluşmuş, **4)** DB'de `too many clients already`. Düzelttikten sonra **uygulamayı kapatıp yeniden aç** — bağlantı yalnızca açılışta kurulur. (Sistem yine çalışır, alanları elle yazabilirsin.) |
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
