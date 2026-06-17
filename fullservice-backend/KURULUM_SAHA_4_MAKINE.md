# FULL Servis — Gerçek Ortam Kurulumu (4 Fiziksel Makine)

Bu rehber, sistemi **gerçek sahaya** taşır: 3 fiziksel bilgisayar + 1 Linux sanal
makinesi. Amaç: her makinede ayarları **yalnızca BİR KEZ** yapmak; sonrasında
bilgisayarları açmak ve dashboard'da **Başlat**'a basmak dışında hiçbir şey
gerekmesin. Tüm servisler boot'ta otomatik kalkar, çökerse kendini yeniden başlatır.

> Bu doküman VM-lab rehberi [`KURULUM_VM_LAB_TEK_MAC.md`](KURULUM_VM_LAB_TEK_MAC.md)'nin
> yerine geçen **saha** sürümüdür. Lab'da tek Mac iki düğümü üstleniyordu; burada
> **her makine tek düğüm** çalıştırır, bu yüzden hepsi aynı **7531** portunu kullanır
> (port ayarıyla uğraşmak yok).

---

## ⚠️ ÖNCE BUNU OKU: Kendi ağ adresini belirle

**Bu kurulumdaki ağ `192.168.1.x` (modem/gateway `192.168.1.1`).** Plan budur:

| Düğüm | Sabit IP | Arayüz (interface) |
|------|----------|--------------------|
| **server** (Linux VM) | **192.168.1.10** | `enp0s1` |
| **mac_cable** | **192.168.1.11** | Ethernet adaptörü (ör. `AX88179A`) |
| **win_wifi** | **192.168.1.13** | `Wi-Fi` |
| **mac_wifi** | **192.168.1.14** | `Wi-Fi` |
| gateway (modem) | **192.168.1.1** | — |

> 💡 Bu "sabit IP"leri **sen seçiyorsun** (modem otomatik vermez). Bir makine şu an
> otomatik/DHCP bir adres almış olabilir (örn. `192.168.1.108`) — onu kullanma,
> aşağıda `.10/.11/.13/.14`'e sabitleyeceğiz. Dashboard adresin
> **http://192.168.1.10:8770** olacak.

> **Modemin farklıysa** (ör. gateway `192.168.0.1`): `ip route | grep default` ile
> öğren ve yukarıdaki **tüm** `192.168.1.x` adreslerini kendi ağına göre oku
> (sadece ilk üç hane değişir).
>
> ⚠️ **Yanlış Wi-Fi tuzağı:** Kurulum sırasında yanlışlıkla başka bir Wi-Fi'ye
> bağlanırsan ağ bambaşka görünür (ör. `192.168.88.x`). Statik IP'yi atamadan önce
> **test modemine** bağlı olduğundan emin ol; değilse tüm makineler aynı modemde
> olmaz ve birbirini göremez.

---

## 0. Kim ne çalıştıracak?

| Düğüm | Makine | Bağlantı | Rolleri | Listener portu |
|------|--------|----------|---------|------|
| **server** | Şahsi MacBook'ta **Linux VM** (UTM) | Kablo (modeme) | ping internet/modem, youtube, **orkestrasyon + dashboard** | 8770 (HTTP) |
| **mac_cable** | Yeni MacBook #1 | **Kablo** (Ethernet adaptörü) | youtube, ping, **iperf SERVER** | 7531 |
| **mac_wifi** | Yeni MacBook #2 | **Wi-Fi** | youtube, ping, **iperf CLIENT**, wifi_track | 7531 |
| **win_wifi** | Windows bilgisayarı | **Wi-Fi** | youtube, ping, torrent, wifi_track | 7531 |

**iperf akışı:** kablolu Mac (`mac_cable`) `iperf3 -s` ile dinler; wifi Mac
(`mac_wifi`) ona bağlanıp hattı doldurur → trafik iki Mac arasında **modem
üzerinden** akar, modeme yük biner. (Linux sunucu artık iperf server DEĞİL.)

**Donanım notu:** Yeni MacBook'larda Ethernet portu yoktur → `mac_cable` için bir
**USB‑C/Thunderbolt → Ethernet adaptörü** gerekir; o Mac'i modeme kabloyla bu
adaptörle bağlayacaksın.

---

## 1. IP planını anla (statik IP nasıl çalışır?)

### Önce kafa karışıklığını gidelim: sıra neden böyle?
Statik IP **keşfedilen** değil, **senin seçtiğin** bir adrestir. Yani "statik IP'leri
belirlemek" = "hangi makineye hangi IP" diye karar vermek = bu kararı bir yere yazmak.
Biz bu kararı `config.json`'a yazıyoruz. Statik-IP atama scripti de **IP'yi
config.json'dan okuyup** makineye uygular. Bu yüzden sıra şudur:

```
1) IP numaralarını seç (aşağıdaki tablo zaten hazır: .10/.11/.13/.14)
2) Makineye git, AĞ ARAYÜZÜNÜN ADINI öğren (tek "keşfedilen" şey bu)
3) IP + arayüz adını config.json'a yaz
4) Scripti çalıştır → config'i okur, IP'yi makineye uygular
```

> Elle (Ayarlar/GUI'den) IP yazmayı tercih edersen scripti hiç kullanmazsın; o
> zaman config'in `assignments` kısmı gerekmez. Sadece **sunucuda** `server.lan_ip`
> doğru olmalı (agent'lar sunucuyu orada arar). "Önce IP, sonra config" sıran bu
> yöntemde geçerlidir.

### 1.1 Modemin ağ şemasını öğren
Herhangi bir makineden modemin arayüz IP'sine (genelde Türk Telekom modemlerinde
`192.168.1.1`) bak. Modemin **gateway'i `192.168.1.1`** ise aşağıdaki plan olduğu
gibi kullanılır; farklıysa (örn. `192.168.0.1`) IP'lerin ilk üç hanesini ona göre
değiştir.

### 1.2 IP tablosu (önerilen plan)

| Düğüm | IP | Gateway | Maske |
|------|----|---------|-------|
| server | 192.168.1.10 | 192.168.1.1 | 255.255.255.0 |
| mac_cable | 192.168.1.11 | 192.168.1.1 | 255.255.255.0 |
| win_wifi | 192.168.1.13 | 192.168.1.1 | 255.255.255.0 |
| mac_wifi | 192.168.1.14 | 192.168.1.1 | 255.255.255.0 |

`config.json` zaten bu plana göre dolu gelir. Sende değiştmen gereken tek şey,
her makinede **arayüz adı** (interface). Onu da o makinedeyken öğreneceksin:
- **macOS:** `networksetup -listallnetworkservices` (ör. `Wi-Fi`, `Ethernet`, type-c adaptör `USB 10/100/1000 LAN` gibi)
- **Windows:** `Get-NetAdapter | Select Name` (ör. `Wi-Fi`)
- **Linux:** `ip -o link show` (UTM'de genelde `enp0s1`; Wi-Fi'de farklı olabilir)

> 🔑 **En kritik tek satır:** sunucu makinesinde `config.json` →
> `"server": { ..., "lan_ip": "192.168.1.10" }`. Tüm agent'lar ve dashboard
> sunucuyu bu adreste arar. Bunu bir kez doğru gir, gerisi buna bağlı.
>
> ℹ️ **Her makinede ayrı ayrı config düzenlemek zorunda değilsin.** Aslında bir
> agent makinesinde config'de önemli olan tek şey, statik-IP scriptini
> kullanacaksan kendi satırı (`assignments.<o_dugum>`). Sunucuyu nerede arayacağını
> ise boot-autostart komutuna doğrudan yazıyoruz (`http://192.168.1.10:8770`), config'den
> okumuyor. Yani agent'larda config'le fazla uğraşmana gerek yok.

---

## 2. ŞAHSİ MACBOOK → Linux VM (sunucu)

Sunucu, şahsi MacBook'ta bir UTM sanal makinesinde Ubuntu olarak çalışır.

### 2.1 Ubuntu VM'i kur (bir kez)
UTM kurulumu ve Ubuntu adımları için [`KURULUM_VM_LAB_TEK_MAC.md` → BÖLÜM 1](KURULUM_VM_LAB_TEK_MAC.md)
bölümünü izle (ISO indir → VM oluştur → Ubuntu kur → **ubuntu-desktop** kur →
**Network Mode = Bridged**). Bridged şart: VM gerçek LAN IP'si alır.

### 2.2 Kod + bağımlılıklar
```bash
sudo apt update
sudo apt install -y git python3-pip python3-venv iperf3 nodejs npm
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 Arayüzü derle (bir kez)
```bash
cd ../fullservice-frontend && npm install && npm run build && cd ../fullservice-backend
```
> Backend `fullservice-frontend/dist/`'i otomatik servis eder; bir daha derlemen
> gerekmez (arayüz kodunu değiştirmedikçe).

### 2.4 Firmware DB sertifikaları (Marka/Model/Firmware combobox'ları)

**`certs/` klasörü projede YOKTUR.** Gizli olduğu için `.gitignore`'da tutulur ve
git'e hiç girmez → `git clone` sonrası sunucuda bu klasör olmayacak. Onu sen
oluşturup içine **3 dosyayı** koyacaksın:

- `ca.crt`, `client.crt`, `client.key` — PostgreSQL'e (cpeqadb) SSL ile bağlanmak için.
- Bu 3 dosya **GRK projesinde mevcut** (`grk-automation/` klasörünün kökünde).
  Oradan kopyalayacaksın (USB bellek / `scp` / paylaşılan klasör ile Linux VM'e taşı).

```bash
# Linux VM'de, fullservice-backend klasörünün içindeyken:
mkdir -p certs
# Sonra ca.crt + client.crt + client.key dosyalarını GRK'dan alıp bu certs/ klasörüne kopyala.
ls certs    # üç dosyayı da görmelisin

# ⚠️ ZORUNLU: özel anahtarın izinlerini kısıtla (yoksa psycopg2 reddeder)
chmod 600 certs/client.key
chmod 644 certs/ca.crt certs/client.crt
```

> ⚠️ **`client.key` izinleri:** USB/scp ile kopyalayınca dosya "herkes okuyabilir"
> gelir; libpq/psycopg2 bunu güvenlik gereği reddeder ("private key file has group or
> world access"). Bu yüzden **`chmod 600 certs/client.key` şarttır.**

Koymazsan/izin yanlışsa sistem **çökmez**: Marka/Model/Firmware kutuları otomatik
**serbest-metin** girişine düşer, test yine başlatılır. Yalnızca **sunucuya** gerekir
(agent'lara değil).

> Not: Linux dosya yolu ASCII olduğu için, Windows'ta yaşanan "Masaüstü" Türkçe-karakter
> sorunu burada olmaz; certleri koyup `chmod 600` yapman yeterli.

### 2.5 Sunucunun statik IP'sini ayarla (adım adım)

**Amaç:** Linux her açılışta aynı IP'yi (`192.168.1.10`) alsın. Şu an otomatik
(DHCP) bir IP aldığı için her seferinde değişiyor; bunu sabitleyeceğiz.

**Adım 1 — Arayüz adını öğren** (zaten `enp0s1` olduğunu gördüysen atla):
```bash
ip -o link show
```
Çıktıda `enp0s1` gibi bir ad görürsün. (UTM VM'inde host'u Wi-Fi'den Ethernet'e
çevirsen bile bu ad **değişmez**, çünkü VM her zaman sanal `enp0s1` kartını görür.)

**Adım 2 — Gateway'i öğren:**
```bash
ip route | grep default
```
"default via **192.168.1.1**" → gateway budur (bu kurulumda `192.168.1.1`).

**Adım 3 — config.json'u düzenle.** Önce `fullservice-backend` klasöründe ol:
```bash
cd ~/fullservice_automation/fullservice-backend
nano config.json
```
Açılan **nano** editöründe (fare yok, ok tuşlarıyla gez) `network` ve `server`
bölümlerini şöyle yap:
```json
"network": {
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns": ["8.8.8.8", "8.8.4.4"],
  "assignments": {
    "server":    { "ip": "192.168.1.10", "interface": "enp0s1" },
    "mac_cable": { "ip": "192.168.1.11", "interface": "AX88179A" },
    "win_wifi":  { "ip": "192.168.1.13", "interface": "Wi-Fi" },
    "mac_wifi":  { "ip": "192.168.1.14", "interface": "Wi-Fi" }
  }
},
"server": { "host": "0.0.0.0", "port": 8770, "lan_ip": "192.168.1.10" }
```
> 🔑 İki yeri karıştırma: `assignments.server.ip` = makineye atanacak sabit IP;
> `server.lan_ip` = "sunucu bu adreste" bilgisi. **İkisi de `192.168.1.10` olmalı.**

Kaydet ve çık: **Ctrl+O → Enter → Ctrl+X**.

**Adım 4 — Statik IP'yi uygula** (script config.json'u okuyup `nmcli` ile atar):
```bash
sudo bash provisioning/linux/set-static-ip.sh server
```
Şifre sorabilir. (Eğer SSH ile bağlıysan IP değişince bağlantın kopar — UTM
penceresinden yazıyorsan sorun olmaz.)

**Adım 5 — Doğrula:**
```bash
ip addr show enp0s1      # satırlardan birinde "inet 192.168.1.10/24" görünmeli
ip route | grep default  # "default via 192.168.1.1" olmalı
ping -c 3 8.8.8.8        # internet gelmeli
```
Artık sunucunun IP'si sabit: **192.168.1.10** (her açılışta aynı).

> **Script yerine elle yapmak istersen:** Ayarlar → Ağ → ⚙️ → IPv4 → **Manual** →
> Adres `192.168.1.10`, Maske `255.255.255.0`, Gateway `192.168.1.1`, DNS `8.8.8.8`
> → Uygula, bağlantıyı kapat-aç. Bu durumda config'de yine `server.lan_ip` =
> `192.168.1.10` olmalı (agent'lar sunucuyu orada arar).
>
> 💡 **`git stash pop` çakışması yaşarsan** (config.json'da `<<<<<<<`, `=======`,
> `>>>>>>>` satırları belirirse): bunlar git çakışma işaretleridir, geçerli JSON
> değildir. nano ile aç, bu işaret satırlarını ve istemediğin kopyayı sil, doğru
> tek sürümü bırak; `python3 -m json.tool config.json` ile hatasız olduğunu doğrula.

### 2.6 Sunucuyu boot'ta otomatik başlat (bir kez)
```bash
sudo bash provisioning/linux/install-server-systemd.sh
```
- Kontrol: `systemctl status fullservice-server`
- Log: `journalctl -u fullservice-server -f`
- Dashboard: VM'in Firefox'unda **http://localhost:8770** (veya ağdaki herhangi
  bir cihazdan **http://192.168.1.10:8770**).

✅ Sunucu artık VM her açıldığında kendiliğinden kalkar.

### 2.7 Log klasör yapısı (bilgisayar başına)
Sunucu, her düğümden gelen logları **o bilgisayarın klasörü** altında toplar:
`logs/<BILGISAYAR>/<oturum_id>/`. Klasörler otomatik oluşur ama önceden kurmak istersen:
```bash
cd ~/fullservice_automation/fullservice-backend
mkdir -p logs/LINUX logs/MAC_ETH logs/MAC_WIFI logs/WIN_WIFI
```
Eşleme `config.json`'daki `log_name` alanlarından gelir:
server→**LINUX**, mac_cable→**MAC_ETH**, mac_wifi→**MAC_WIFI**, win_wifi→**WIN_WIFI**.

> Log akışı: (1) agent kendi makinesinin `logs/` klasörüne yazar → (2) HTTP ile
> sunucuya yüklenir (yukarıdaki bilgisayar klasörleri). (3) Genel FTP sunucusuna
> aktarım henüz eklenmedi (sonraki faz).

---

## 3. YENİ MACBOOK #1 → `mac_cable` (kablolu, iperf server)

Bu Mac'i modeme **Ethernet adaptörüyle kabloyla** bağla.

### ⚠️ 3.0 Önce macOS sürümüne bak — eski Mac'lerde brew ÇALIŞMAZ
 → **Bu Mac Hakkında** → macOS sürümü:
- **macOS 11 (Big Sur) ve üstü** → modern Homebrew çalışır. En kolayı:
  `brew install python git iperf3` (Homebrew yoksa https://brew.sh). Sonra 3.2'ye geç.
- **macOS 10.13 / 10.14 (High Sierra / Mojave) — bu kurulumdaki Mac'ler böyle** →
  **brew kurulmaz** ("Your version of macOS is too old to run Homebrew" hatası).
  Aşağıdaki **brew'siz** yolu izle. (Mümkünse Mac'i macOS 11+'a güncellemek her şeyi
  kolaylaştırır; güncelleyemiyorsan devam.)

### 3.1 Araçları brew olmadan kur (eski macOS)

**a) git + derleyici** (xcode komut satırı araçları — eski macOS'ta çalışır):
```bash
xcode-select --install
```

**b) Python 3.9** — sistemdeki Python 2.7'yi KULLANMA, en yeni 3.13/3.14'ü de kurma
(eski macOS'ta paketler kurulmaz). High Sierra'yı destekleyen sürüm **3.9.13**:
- Tarayıcı: https://www.python.org/downloads/release/python-3913/
- En altta **"macOS 64-bit Intel installer"** (universal2 değil, **Intel**) indir, kur.
- Doğrula: `python3.9 --version`

**c) iperf3** — brew yok, kaynaktan derle (xcode-select sonrası):
```bash
curl -L -o iperf3.tar.gz https://downloads.es.net/pub/iperf/iperf-3.17.1.tar.gz
tar xzf iperf3.tar.gz && cd iperf-3.17.1
./configure && make && sudo make install
iperf3 --version
cd ~
```
> Link hata verirse https://software.es.net/iperf/ adresinden güncel kaynağı indir.

### 3.2 Kod + venv (python3.9 ile)
```bash
cd ~ && git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3.9 -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Statik IP — Ethernet adaptörünü bul, sonra ELLE ata

**Önce adaptör adını bul.** Adaptörü modeme kabloyla takılıyken her adayı yokla;
hangisi `192.168.1.x` bir IP gösteriyorsa modeme bağlı olan **odur**:
```bash
networksetup -listallnetworkservices            # tüm arayüz adları
networksetup -getinfo "AX88179A"                # IP address: 192.168.1.x → bu!
networksetup -getinfo "USB 10/100/1000 LAN"     # değilse diğerlerini dene
```
(Bu kurulumda type-c adaptör **`AX88179A`** çıktı.)

**Sonra IP'yi ELLE ata.** ⚠️ macOS'un eski bash'i (3.2) `mapfile` içermediği için
`set-static-ip.sh` script'i eski Mac'lerde **çalışmaz** (`mapfile: command not found`).
O yüzden script yerine doğrudan `networksetup` kullan — script'in yaptığının aynısı:
```bash
sudo networksetup -setmanual "AX88179A" 192.168.1.11 255.255.255.0 192.168.1.1
sudo networksetup -setdnsservers "AX88179A" 8.8.8.8 8.8.4.4
networksetup -getinfo "AX88179A"                # IP address: 192.168.1.11 → tamam
```
> `"AX88179A"` yerine kendi adaptör adını yaz. (Script güncellendi; ileride `git pull`
> yapan yeni macOS Mac'lerde `set-static-ip.sh` de çalışır, ama eski Mac'te elle komut
> en garantisi.)

### 3.4 Agent'ı boot'ta otomatik başlat (bir kez)
> **Önemli:** launchd, kurulum anındaki python'u kaydeder. Bağımlılıkların bulunması
> için **önce venv'i aktif et**, sonra kur:
```bash
source venv/bin/activate
bash provisioning/macos/install-agent-launchd.sh mac_cable http://192.168.1.10:8770 7531
```
- Kontrol: `launchctl list | grep fullservice`
- Log: `cat logs/agent-launchd.err.log`

✅ Bu Mac her açıldığında `mac_cable` agent'ı kalkar, sunucuya kaydolur.

---

## 4. YENİ MACBOOK #2 → `mac_wifi` (Wi-Fi, iperf client)

Bu Mac'i modemin **Wi-Fi**'sine bağla. Adımlar Mac #1 ile **aynı**; tek farklar:
arayüz `Wi-Fi`, IP `192.168.1.14`, node id `mac_wifi`.

**4.1 Araçlar** — Bölüm 3.0 + 3.1'i aynen uygula (macOS eskiyse: xcode-select,
Python 3.9.13, iperf3 kaynaktan).

**4.2 Kod + venv** — Bölüm 3.2 ile aynı:
```bash
cd ~ && git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3.9 -m venv venv && source venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
```

**4.3 Statik IP (Wi-Fi) — elle ata** (Wi-Fi'nin adı genelde tam olarak `Wi-Fi`):
```bash
sudo networksetup -setmanual "Wi-Fi" 192.168.1.14 255.255.255.0 192.168.1.1
sudo networksetup -setdnsservers "Wi-Fi" 8.8.8.8 8.8.4.4
networksetup -getinfo "Wi-Fi"                   # IP address: 192.168.1.14 → tamam
```

**4.4 Agent'ı boot'ta başlat (venv aktifken!):**
```bash
source venv/bin/activate
bash provisioning/macos/install-agent-launchd.sh mac_wifi http://192.168.1.10:8770 7531
```

✅ `mac_wifi` her açılışta kalkar; iperf client olarak `mac_cable`'a yük basar.

---

## 5. WINDOWS BİLGİSAYARI → `win_wifi` (Wi-Fi)

Windows'u modemin **Wi-Fi**'sine bağla. Aşağıdakileri **Yönetici PowerShell**'de yap.

### 5.1 Araçlar + kod (bir kez)
1. **Python** (python.org) — kurarken **"Add python.exe to PATH"** işaretle.
2. **Git** (git-scm.com).
3. **Google Chrome** — YouTube'u en yüksek kaliteye zorlamak için (Selenium Chrome'u kullanır).
4. **qBittorrent** — torrent testi için. Kurduktan sonra **Araçlar → Seçenekler → Web
   Arayüzü**'nü aç: işaretle, port **8080**, kullanıcı **admin**, şifre **Admin123**.
   (Bunlar koddaki değerlerle aynı olmalı; `config.json → torrent_magnet` GTA5'tir.)

> ℹ️ **iperf3 GEREKMEZ:** `win_wifi`'nin rolleri `youtube, ping, torrent, wifi_track` —
> iperf yok (iperf yalnızca iki Mac arasında çalışır). Windows'a iperf3 kurmana gerek
> yok, bu adımı atla. (Yine de manuel iperf testi yapmak istersen: https://files.budman.pw/
> veya https://iperf.fr adresinden win64 zip indir → bir klasöre çıkar → o klasörü PATH'e
> ekle. iperf3.exe + cygwin1.dll birlikte dursun.)
```powershell
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation; git checkout aliimran
cd fullservice-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 5.2 Statik IP (Wi-Fi)
```powershell
Get-NetAdapter | Select Name        # Wi-Fi arayüz adını teyit et ("Wi-Fi")
.\provisioning\windows\set-static-ip.ps1 -NodeId win_wifi
```

### 5.3 Agent'ı boot'ta otomatik başlat (bir kez)
```powershell
.\provisioning\windows\install-agent-task.ps1 -NodeId win_wifi -ServerUrl http://192.168.1.10:8770 -Port 7531
Start-ScheduledTask -TaskName FullServiceAgent_win_wifi   # ilk seferde elle başlat (sonraki açılışlarda otomatik)
```
> Script venv python'unu otomatik bulur (`venv\Scripts\python.exe`). Görev
> "AtStartup" + SYSTEM hesabıyla çalışır; makine açılır açılmaz agent kalkar.

✅ `win_wifi` her açılışta otomatik kalkar.

---

## 6. DOĞRULAMA (bir kez)

1. **4 makineyi de yeniden başlat.** (Hepsi boot-otomatik kuruldu.)
2. Sunucu VM'in Firefox'unda **http://localhost:8770**'i aç (ya da herhangi bir
   cihazdan `http://192.168.1.10:8770`).
3. Sağ paneldeki **Health-Check**'e bas → 4 düğüm de **yeşil** yanmalı; her kartta
   işletim sistemi / IP / bağlantı durumu / yöntemi doğru görünmeli.
4. Sol formdan Marka/Model/Firmware + Süre seç → **FULL Servis Başlat**.
5. Tüm düğümlerde testler eşzamanlı akmalı; `mac_cable`'da **iperf (Server)**,
   `mac_wifi`'de **iperf (Client)** çalışmalı.

✅ Buraya kadar geldiyse kurulum bitti. Bundan sonra **tek yapman gereken:**
makineleri aç → dashboard'da **Başlat**.

---

## 7. "Bir daha ne zaman elle müdahale gerekir?"

Neredeyse hiç. Sadece şu durumlarda:
- **Modem/router değişir veya ağ şeması değişirse** → `config.json` IP planını bir
  kez güncelle, statik-IP scriptlerini tekrar çalıştır.
- **Kodu güncellersen** → her makinede `git pull` (+ sunucuda gerekirse
  `npm run build`), sonra servisi yeniden başlat (`systemctl restart
  fullservice-server` / `launchctl unload+load` / `Restart-ScheduledTask`).

Günlük kullanımda bunların hiçbiri gerekmez; servisler boot'ta kalkar, çökerse
otomatik yeniden başlar.

---

## Sorun giderme

| Belirti | Çözüm |
|--------|-------|
| Düğüm panelde **gri/offline** | O makine açık mı, agent servisi çalışıyor mu? `ping 192.168.1.10` sunucuyu görüyor mu? |
| Health-Check **kırmızı** | O düğümün listener'ı (7531) ayakta mı? Başka makineden `curl http://<dugum_ip>:7531/health` |
| macOS agent kalkmıyor | venv aktif **değilken** mi kurdun? `launchctl unload` edip venv aktifken tekrar kur. Log: `logs/agent-launchd.err.log` |
| Windows görevi çalışmıyor | `Get-ScheduledTask FullServiceAgent_win_wifi`; venv kuruluysa python doğru bulunur. Elle: `Start-ScheduledTask` |
| Marka/Model **boş / serbest metin** | Sunucuda `certs/` (ca/client.crt+key) eksik, **izin yanlış** veya DB'ye ağ yok. Beklenen geri-düşüş; test yine başlar. |
| **"private key file ... has group or world access"** | `client.key` izni gevşek → `chmod 600 certs/client.key`, sonra sunucuyu yeniden başlat. |
| **YouTube en yüksek kalitede açılmıyor** | O makinede **Chrome kurulu değil** veya `selenium` yok → basit tarayıcıya düşer. `pip install -r requirements.txt` + Chrome kur. (Çok eski macOS'ta Chrome desteklenmeyebilir.) |
| **Terminal pencereleri açılmıyor (ping/wifi)** | Agent/sunucu **boot servisinden** (systemd/SYSTEM görevi) çalışıyordur → masaüstü yok → pencere açılmaz. Görmek istiyorsan **elle, masaüstü oturumunda** çalıştır. |
| **torrent "Web UI'ye giriş yapılamadı"** | Windows'ta qBittorrent kapalı veya Web UI ayarı eksik. Web Arayüzü'nü aç (port 8080, admin/Admin123). |
| **iperf** kutusu kırmızı | İlgili Mac'te `iperf3` yok (eski macOS: 3.1c'deki kaynaktan derleme) **veya** `mac_cable` (server) ayakta değil — client onu bekler, 5 kez yeniden dener. |
| Statik IP atanmadı (Linux) | Ubuntu'da NetworkManager (nmcli) gerekir; `ubuntu-desktop` kuruluysa vardır. Arayüz adını `ip -o link show` ile teyit et. |
| macOS Ethernet servis adı farklı | Adaptöre göre `AX88179A` / `USB 10/100/1000 LAN` vb. olabilir; `networksetup -getinfo "<ad>"` ile `192.168.1.x` IP göstereni bul. |
| **brew kurulmuyor** ("macOS too old") | Mac eski (10.13/10.14). brew yok; Bölüm 3.1'deki brew'siz yolu kullan (xcode-select + Python 3.9.13 + iperf3 kaynaktan). Mümkünse macOS 11+'a güncelle. |
| **`mapfile: command not found`** | macOS bash 3.2 eski. `set-static-ip.sh` yerine elle `sudo networksetup -setmanual "<arayüz>" <ip> 255.255.255.0 192.168.1.1` kullan (Bölüm 3.3). |
| **pip install patlıyor** (eski Mac) | En yeni Python (3.13/3.14) kurmuşsundur; eski macOS'a wheel yok. **Python 3.9.13 Intel** kur, `python3.9 -m venv venv` ile baştan. |
| config.json'da `<<<<<<<` / `=======` | `git stash pop`/merge çakışması işaretleri — geçerli JSON değil. Sil, tek doğru sürümü bırak, `python3 -m json.tool config.json` ile doğrula. |
| `mv` "No such file or directory" | Hedef klasör yok ya da yolu yanlış (ör. `~/aliimran` yerine `~/Desktop/aliimran`). Önce `find ~ -type d -name fullservice_automation` ile yeri bul. |


---

## 8. ⚠️ Emanet Mac'leri iade ederken (eski haline döndür)

Test Mac'leri başkasından emanetse, geri vermeden önce yaptığın değişiklikleri geri al
ki "senden önceki gibi" olsun.

**1) Statik IP'yi otomatiğe (DHCP) çevir:**
```bash
# mac_cable (Ethernet adaptörü):
sudo networksetup -setdhcp "AX88179A"
# mac_wifi (Wi-Fi):
sudo networksetup -setdhcp "Wi-Fi"
```
(GUI ile: Ayarlar → Ağ → ilgili arayüz → IPv4 → **Using DHCP**.) Bu, internet/DNS dahil
her şeyi otomatiğe döndürür.

**2) Boot-otomatik (launchd) kurduysan kaldır:**
```bash
launchctl unload ~/Library/LaunchAgents/com.tt.fullservice.agent.*.plist 2>/dev/null
rm ~/Library/LaunchAgents/com.tt.fullservice.agent.*.plist 2>/dev/null
```

> Kurduğun araçlar (Python, iperf3, Chrome, repo klasörü) makinede kalabilir — zararsız;
> istersen klasörü ve araçları da silebilirsin.
