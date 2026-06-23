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

**macOS — Arayüz adını öğren:**
```bash
networksetup -listallnetworkservices
# Çıktı örneği:
# Wi-Fi
# Ethernet
# USB 10/100/1000 LAN        ← adaptör varsa bu
# Thunderbolt Ethernet (opsiyonel)
```
Modeme kablolu/Wi-Fi ile bağlıyken `networksetup -getinfo "<adı>"` ile IP'yi doğrula:
```bash
networksetup -getinfo "Wi-Fi"
# IP Address: 192.168.1.x      ← modeme bağlıysa bu görünür
```

**Windows — Arayüz adını öğren:**
```powershell
Get-NetAdapter | Select Name, Status, MediaType
# Çıktı örneği:
# Name            Status  MediaType
# Wi-Fi          Up      Native 802.11
# Ethernet       Up      Ethernet
```

**Linux (UTM VM) — Arayüz adını öğren:**
> ⚠️ `ip -o link show` hata verirse, aşağıdaki alternatifleri dene:

```bash
# Yöntem 1 (en çok sisteme uyar):
ip link show
# Çıktı örneği:
# 1: lo: <LOOPBACK,UP...
# 2: enp0s1: <BROADCAST,MULTICAST...    ← bu arayüz, adı: enp0s1

# Yöntem 2 (NetworkManager varsa, daha kolay):
nmcli device show
# Bölüm: DEVICE, adını bul (enp0s1 vb.)

# Yöntem 3 (eski sistemler):
ifconfig
# eth0 / ens0 / enp0s1 gibi arayüz adları görünür

# Yöntem 4 (NAT/Bridged şüphesi varsa):
cat /etc/netplan/01-netcfg.yaml  # ya da /etc/network/interfaces
# Mevcut arayüz adı yazılı olabilir
```

**Beklenen sonuç:**
- **macOS:** `Wi-Fi`, `Ethernet`, `USB 10/100/1000 LAN`, `AX88179A` vb. (birden fazla varsa, modeme bağlı olana `networksetup -getinfo` ile testa yatır)
- **Windows:** `Wi-Fi`, `Ethernet`, `Wireless LAN adapter Wi-Fi` vb.
- **Linux VM:** `enp0s1` (Bridged mode) veya `eth0`, `ens0` (NAT mode)

> ⚠️ **"Bilmiyorum, hangi komut çalışır?" hatası:** Sırasıyla dene:
> 1. Linux: `ip link show` → başarısızsa `nmcli device show` → başarısızsa `ifconfig`
> 2. macOS: `networksetup -listallnetworkservices` (100% çalışır)
> 3. Windows: `Get-NetAdapter` (100% çalışır, PowerShell'de)
>
> **"VM bridged mi, NAT mi?" şüphesi:** UTM → Makine Ayarları → Ağ → Mode bak. Bridged ise real LAN IP alır (`192.168.1.x`); NAT ise sanal IP (`192.168.122.x`). Statik IP atamadan ÖNCE modu kesin test et: `ping 192.168.1.1` → yanıt varsa bridged, yoksa NAT.

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

## 1.3 ⚠️ KOMUT HATALARI VE ÇÖZÜMLER (Önceden oku!)

Kurulum sırasında bu hataları görebilirsin — çözümleri burada:

| Hata Mesajı | Komut | Sebep | Çözüm |
|-------------|-------|-------|-------|
| `command not found: ip` | `ip link show` | `ip` komutu yok (eski Linux) | `ifconfig` veya `cat /etc/network/interfaces` kullan |
| `command "-o" is unknown` | `ip -o link show` | Eski `ip` sürümü `-o` flag'ini desteklemiyor | `-o` flag'ini kaldır: `ip link show` |
| `command not found: nmcli` | `nmcli device show` | NetworkManager kurulmamış | `sudo apt install network-manager` veya `ip link show` kullan |
| `command not found: ifconfig` | `ifconfig` | eski sistem → komut yok | `ip addr show` kullan |
| `command not found: networksetup` | `networksetup -listallnetworkservices` | macOS değil / PATH yok | Mac'te çalıştırdığından emin ol; `/usr/sbin/networksetup` tam yolu kullan |
| `Get-NetAdapter : The term 'Get-NetAdapter' is not recognized` | `Get-NetAdapter` | PowerShell sürümü eski | `ipconfig /all` (cmd.exe) veya `wmic nic get name` (PowerShell) kullan |
| `sudo: command not found` (Windows) | `sudo ...` | Windows'ta sudo yok | Komutun öncesine `sudo` yazma; **Yönetici PowerShell**'de çalıştır |
| `Permission denied` | `chmod 600 certs/client.key` | Dosya sahibi değilsin | `sudo chmod 600 certs/client.key` |
| `cat: /etc/netplan/01-netcfg.yaml: No such file` | `cat /etc/netplan/...` | Dosya yok (DHCP config) | Normal — `ip link show` ile devam et |

**Genel kural:** Bir komut hata verirse:
1. **Hata mesajını oku** — `command not found` = komut yok, `Permission denied` = sudo gerek vb.
2. **Tablo yukarıda bak** — aynı hata varsa çözüm orada
3. **Alternative komutları dene** — tablonun sağ sütunu
4. **Sistem türünü doğrula** — `uname -a` (Linux), `sw_vers` (macOS), Windows (PowerShell) vb.

---

## 2. GERÇEK LINUX MAKİNESİ (Dell — Ubuntu 22.04.2 LTS, eth0)

Sunucu, gerçek fiziksel bir Dell bilgisayarda Ubuntu 22.04.2 LTS olarak çalışır.

### 2.1 ⚠️ VM KURULUMU GEREKMİYOR
**Zaten Linux var**, kurulum atlanabilir. Doğrudan 2.2'ye geç.

### 2.2 Kod + bağımlılıklar (adım adım, error handling ile)

```bash
# 1) Paket listesini güncelle
sudo apt update
# Beklenen: "Reading package lists... Done"
# Hata: "E: Could not open lock file" → başka kurulum çalışıyor, 1 dk bekle

# 2) Araçları kur
sudo apt install -y git python3-pip python3-venv iperf3 nodejs npm
# Beklenen: "Setting up git ...", "Setting up python3-pip ...", vb.
# Hata 1: "E: Unable to locate package nodejs" → older Ubuntu → kullan: sudo apt install -y nodejs npm
# Hata 2: "E: Unable to lock the administration directory" → yüksek derecede kalma ("sudo su") mı? Çık
# Hata 3: Internet yok → ping 8.8.8.8 ile test et, gateway doğru mu kontrol et (bölüm 2.5)

# 3) Kod deposunu klonla
git clone https://github.com/cpeqateam/fullservice_automation.git
# Beklenen: "Cloning into 'fullservice_automation'..." + "done."
# Hata 1: "fatal: unable to access ... Could not resolve host" → internet yok, netcheck et
# Hata 2: "fatal: repository not found" → repo URL yanlış (github.com adresini doğrula)
# Hata 3: "Cloning completed, but HEAD is a detached state" → normal, endişe etme

# 4) Branch'ı değiştir
cd fullservice_automation && git checkout aliimran
# Beklenen: "Switched to branch 'aliimran'"
# Hata: "error: pathspec 'aliimran' did not match any file(s)" → branch yoksa: git branch -a ile listele

# 5) Frontend-backend klasörüne git
cd fullservice-backend
# Doğrula: pwd sonrası ".../fullservice-backend" görünmelyi

# 6) Python venv'i kur (KRITIK)
python3 -m venv venv && source venv/bin/activate
# Beklenen: "(venv)" prompt'ta görünmeli, örn: "(venv) user@vm:~/fullservice-backend$"
# Hata 1: "command not found: python3" → "sudo apt install python3" çalıştır
# Hata 2: "Error: [Errno 13] Permission denied" → klasör sahibi değilsin, kopyayı başka yere al
# Hata 3: venv oluştu ama activate olmadı → "bash venv/bin/activate" dene
# Doğrulama: "which python" çalıştır, çıktı "/path/to/venv/bin/python" olmalı (sistem Python değil)

# 7) Python paketlerini kur
pip install -r requirements.txt
# Beklenen: "Successfully installed ..." satırları, son satırda "pip" sürümü
# Hata 1: "ERROR: Could not find a version..." → genel paket sorunu, şunu dene: pip install --upgrade pip
# Hata 2: "error: Microsoft Visual C++ 14.0 or greater is required" (Windows) → bölüm 5'te işlendi
# Hata 3: "Connection refused" → internet yok ya da pip cache sorun → "pip cache purge" dene
# Uyarı: "WARNING: Running pip as the 'root' user" → normal, sudo ile çalıştırdığın için

# Doğrulama (hepsini çalıştır):
python --version        # 3.x.x görünmeliy (3.10+ ise iyidir)
pip list                # fastapi, uvicorn, pydantic vb. görünmeliy
which python            # /path/to/venv/bin/python (sistem Python DEĞİL)
```

### 2.3 Arayüzü derle (bir kez)
```bash
cd ../fullservice-frontend && npm install && npm run build && cd ../fullservice-backend
```
> Backend `fullservice-frontend/dist/`'i otomatik servis eder; bir daha derlemen
> gerekmez (arayüz kodunu değiştirmedikçe).

### 2.4 Firmware DB + FTP sertifikaları (SSL)

**`certs/` klasörü projede YOKTUR.** Gizli olduğu için `.gitignore`'da tutulur ve
git'e hiç girmez → `git clone` sonrası sunucuda bu klasör olmayacak. Onu sen
oluşturup içine **3 dosyayı** koyacaksın:

- `ca.crt`, `client.crt`, `client.key` — **PostgreSQL'e (cpeqadb) VE FTP sunucusuna** SSL ile bağlanmak için.
- Bu 3 dosya **GRK projesinde mevcut** (`grk-automation/` klasörünün kökünde).
  Oradan kopyalayacaksın (USB bellek / `scp` / paylaşılan klasör ile Linux VM'e taşı).

```bash
# Linux VM'de, fullservice-backend klasörünün içindeyken:
mkdir -p certs
# Sonra ca.crt + client.crt + client.key dosyalarını GRK'dan alıp bu certs/ klasörüne kopyala.
ls certs    # üç dosyayı da görmelisin

# ⚠️ ZORUNLU: özel anahtarın izinlerini kısıtla (yoksa psycopg2/FTP reddeder)
chmod 600 certs/client.key
chmod 644 certs/ca.crt certs/client.crt
```

> ⚠️ **`client.key` izinleri:** USB/scp ile kopyalayınca dosya "herkes okuyabilir"
> gelir; libpq/psycopg2 bunu güvenlik gereği reddeder ("private key file has group or
> world access"). Bu yüzden **`chmod 600 certs/client.key` şarttır.**

**DB sertifikaları koymazsan** sistem **çökmez**: Marka/Model/Firmware kutuları otomatik
**serbest-metin** girişine düşer, test yine başlatılır. Yalnızca **sunucuya** gerekir
(agent'lara değil).

**FTP sertifikaları koymazsan** loglar FTP'ye **yuklenmez** (arka planda hata yutulur).
Bu durumda testler çalışır ama **loglar yalnızca sunucunun `logs/` klasöründe** kalır
(`logs/<BILGISAYAR>/<session>/`). Faz 5'te FTP entegrasyonu gerekiyorsa testler
başladıktan sonra `cat /tmp/fullservice-ftp.err` ile FTP hatalarını kontrol et.

### 2.5 Sunucunun statik IP'sini ayarla (adım adım)

**Amaç:** Linux her açılışta aynı IP'yi (`192.168.1.10`) alsın. Şu an otomatik
(DHCP) bir IP aldığı için her seferinde değişiyor; bunu sabitleyeceğiz.

**Adım 1 — Arayüz adını öğren**

✅ **Zaten buldun: `eth0`** (Dell fiziksel Ethernet portu)

Doğrulama (isteğe bağlı):
```bash
ip link show
# Çıktı örneği (eth0 seninkidir):
# 1: lo: <LOOPBACK,UP>...
# 2: eth0: <BROADCAST,MULTICAST,UP>...    ← bu arayüz, adı: eth0

# Ya da:
ifconfig eth0
# inet 192.168.1.x ile bağlı mı? Kontrol et
```

**Özet:** Arayüz adı = **`eth0`** (Dell fiziksel NIC)

**Adım 2 — Gateway'i öğren:**
```bash
ip route | grep default
```
"default via **192.168.1.1**" → gateway budur (bu kurulumda `192.168.1.1`).

**Adım 3 — config.json'u düzenle.**

```bash
# İlk olarak klasörde olduğundan emin ol:
cd ~/fullservice_automation/fullservice-backend
pwd
# Çıktı: .../fullservice-backend olmalı

# Dosyayı aç (nano editörü):
nano config.json
# nano açıldı mı? Dosya görünüyor mu?
# Hata: "nano: command not found" → "vim config.json" veya "cat config.json" dene
```

**nano editöründe (fare YOK, ok tuşları ile gez):**

Bulman gereken yerler:
1. `"network": {` satırını bul (Ctrl+W "network" yaz, Enter)
2. `"server": {` satırını bul (tekrar Ctrl+W, "server" yaz)

Değiştirmen gereken satırlar (arayüz adı `eth0`, Mac adaptörleri ve Windows isimleri zaten doğru):
```json
"network": {
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",          ← modem IP'si (192.168.1.1 değilse değiştir)
  "dns": ["8.8.8.8", "8.8.4.4"],
  "assignments": {
    "server":    { "ip": "192.168.1.10", "interface": "eth0" },        ← SENINKIDIR
    "mac_cable": { "ip": "192.168.1.11", "interface": "AX88179A" },    ← DOĞRU
    "win_wifi":  { "ip": "192.168.1.13", "interface": "Wi-Fi" },       ← DOĞRU
    "mac_wifi":  { "ip": "192.168.1.14", "interface": "Wi-Fi" }        ← DOĞRU
  }
},
"server": { "host": "0.0.0.0", "port": 8770, "lan_ip": "192.168.1.10" }
```

✅ **Senin durumunda tüm arayüz adları zaten doğru, eth0 bile zaten yazılı olabilir. Kontrol et:**
```bash
cat ~/fullservice_automation/fullservice-backend/config.json | grep -A 10 "assignments"
```
Çıktıda eth0, AX88179A, Wi-Fi, Wi-Fi görünüyorsa = **değiştirme, atla!**

> 🔑 **İki yeri karıştırma:**
> - `assignments.server.ip` = makineye atanacak sabit IP (192.168.1.10)
> - `server.lan_ip` = "sunucu bu adreste çalışıyor" (192.168.1.10)
> **İkisi de aynı olmalı.**

**nano'da kaydet ve çık:**
```
Ctrl+O  →  Enter  →  Ctrl+X
```

**Hata ayıklama:**
```bash
# Dosya kaydedildi mi? Doğrula:
python3 -m json.tool config.json > /dev/null
# Başarı: hiçbir çıktı yok
# Hata 1: "json.decoder.JSONDecodeError" → nano'da syntax hatası var (ör. missing comma)
#         Dosyayı tekrar aç: nano config.json, "network" kısmını kontrol et
# Hata 2: "No such file or directory" → config.json yok, pwd kontrol et
```

**Adım 4 — Statik IP'yi uygula** (script config.json'u okuyup NetworkManager ile atar):

```bash
# Script'i çalıştır:
sudo bash provisioning/linux/set-static-ip.sh server
# Password: (VM'in root şifresi)
```

**Beklenen çıktı:**
```
Setting static IP for server...
Using interface: enp0s1
Configuring: 192.168.1.10/24 with gateway 192.168.1.1
done.
```

**Hata ayıklama:**

| Çıktı | Sebep | Çözüm |
|-------|-------|-------|
| `command not found: nmcli` | NetworkManager yok | `sudo apt install network-manager`, sonra tekrar çalıştır |
| `Error: no such interface enp0s1` | config.json'daki arayüz adı yanlış | config.json'da `enp0s1`'i gerçek arayüz adıyla değiştir (Adım 1'de bul) |
| `sudo: command not found` | sudo kurulmamış (impossible ama olursa) | VM'i tekrar başlat |
| Şifre soruyor ama `Password:` yazılmıyor (SSH'de) | SSH ile bağlantı var, IP değişince kopar | Normal — Ctrl+C yap, UTM penceresinden yeniden bağlan |
| Script hata vermedi ama adresi kontrol etmek istiyor | Başarılı sayılır, Adım 5'e geç | |

**Adım 5 — IP'nin atanıp atanmadığını doğrula:**

```bash
# Adresi kontrol et:
ip addr show enp0s1
# Beklenen çıktı:
#   inet 192.168.1.10/24 brd 192.168.1.255 scope global enp0s1
# Hata: "inet 192.168.1.x" (x ≠ 10) → script başarısız, config.json kontrol et

# Gateway'i kontrol et:
ip route | grep default
# Beklenen: "default via 192.168.1.1 dev enp0s1"

# İnternet var mı? (DNS kontrol):
ping -c 3 8.8.8.8
# Beklenen: "3 packets transmitted, 3 received, 0% packet loss"
# Hata 1: "Network is unreachable" → gateway yanlış, config.json kontrol et
# Hata 2: "Temporary failure in name resolution" → DNS yapılandırması hatalı, aşağıyı dene:
#   cat /etc/resolv.conf  ← 8.8.8.8 yazılı mı?
#   Yoksa:  sudo nano /etc/netplan/01-netcfg.yaml → dns: [8.8.8.8] satırını ekle
```

**Nihai kontrol — bölüm 2.7'ye geçmeden önce:**
```bash
# Tüm bölümleri içinde tek bir komutla test et:
echo "=== IP ===" && ip addr show enp0s1 | grep "inet " && \
echo "=== GATEWAY ===" && ip route | grep default && \
echo "=== DNS ===" && ping -c 1 8.8.8.8 && echo "✓ BAŞARILI"
```

Başarılı? Artık sunucunun IP'si sabit: **192.168.1.10** (her açılışta aynı). 

Başarısız? config.json'u tekrar kontrol et (gateway, interface adı).

> **Script yerine elle yapmak istersen:** Ayarlar → Ağ → ⚙️ → IPv4 → **Manual** →
> Adres `192.168.1.10`, Maske `255.255.255.0`, Gateway `192.168.1.1`, DNS `8.8.8.8`
> → Uygula, bağlantıyı kapat-aç. Bu durumda config'de yine `server.lan_ip` =
> `192.168.1.10` olmalı (agent'lar sunucuyu orada arar).
>
> 💡 **`git stash pop` çakışması yaşarsan** (config.json'da `<<<<<<<`, `=======`,
> `>>>>>>>` satırları belirirse): bunlar git çakışma işaretleridir, geçerli JSON
> değildir. nano ile aç, bu işaret satırlarını ve istemediğin kopyayı sil, doğru
> tek sürümü bırak; `python3 -m json.tool config.json` ile hatasız olduğunu doğrula.

### 2.6 Sunucuyu boot'ta otomatik başlat (BU ADIM GÜNÜBİRLİK ATLA)

⚠️ **Bugün manuel test için:** bu bölümü ATLA. Sunucuyu elle başlatacaksın.

**Emanet ortamda boot-otomatik KURULMAYACAK**, çünkü sonradan kaldırmak gerekir.
Eğer kurulum/kaldırma testleri yapacaksan:
```bash
# Kurulum (emanet sonrası KALDıR):
sudo bash provisioning/linux/install-server-systemd.sh

# Kontrol:
systemctl status fullservice-server

# GERİ ALMA (emanet dönerken):
sudo systemctl disable fullservice-server
sudo systemctl stop fullservice-server
sudo rm /etc/systemd/system/fullservice-server.service
sudo systemctl daemon-reload
```

**Bugün manuel başlatma:**
```bash
cd ~/fullservice_automation/fullservice-backend
source venv/bin/activate
python3 run_server.py
# Dashboard: http://localhost:8770 (VM'de) veya http://192.168.1.10:8770 (ağdan)
```

### 2.7 Log klasör yapısı (bilgisayar başına)
Sunucu, her düğümden gelen logları **o bilgisayarın klasörü** altında toplar:
`logs/<BILGISAYAR>/<oturum_id>/`. Klasörler otomatik oluşur ama önceden kurmak istersen:
```bash
cd ~/fullservice_automation/fullservice-backend
mkdir -p logs/LINUX logs/MAC_ETH logs/MAC_WIFI logs/WIN_WIFI
```
Eşleme `config.json`'daki `log_name` alanlarından gelir:
server→**LINUX**, mac_cable→**MAC_ETH**, mac_wifi→**MAC_WIFI**, win_wifi→**WIN_WIFI**.

**Log akışı:**
1. Agent kendi makinesinin `logs/` klasörüne yazar
2. HTTP ile sunucuya yüklenir (`logs/<BILGISAYAR>/<oturum_id>/`)
3. **Yeni:** Sunucu, logları otomatik **FTP sunucusuna** aktarır — klasör yapısı:
   `<MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<BILGISAYAR>/`
   (Sertifikalar kuruluysa ve FTP erişebiliyorsa; yoksa loglar sunucuda kalır.)
4. **Yeni:** Test sonuçları PostgreSQL'in `copy_*` tablolarına yazılır (staging aşaması).

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
# Bir pencere açılmalı, "Install" butonuna bas, geçmesini bekle (~5 min)
# Doğrula:
xcode-select -p
# Beklenen: /Applications/Xcode.app/Contents/Developer (veya benzeri yol)
# Hata: "not installed" → tekrar çalıştır, kurulum ekranını tamamen takip et
```

**b) Python 3.9.13** — sistemdeki Python 2.7'yi KULLANMA, en yeni 3.13/3.14'ü de kurma (eski macOS'ta kurulmaz)

```
Tarayıcı: https://www.python.org/downloads/release/python-3913/
Sayfayı kaydır, en altta "Downloads" başlığı bulunur.
"macOS 64-bit Intel installer" (NOT "universal2", NOT "ARM64") indir
```

**Kurulum sonrası doğrula:**
```bash
python3.9 --version
# Beklenen: Python 3.9.13
# Hata 1: "command not found" → kurulum incomplete, kurucuyu tekrar çalıştır (.pkg dosyası)
# Hata 2: "Python 3.13.0" (farklı sürüm) → yanlış sürüm indirdim, 3.9.13 indir
```

**c) iperf3** — kaynaktan derle (xcode-select kurulduktan sonra):

```bash
# İndirme:
curl -L -o iperf3.tar.gz https://downloads.es.net/pub/iperf/iperf-3.17.1.tar.gz
# Hata: "curl: command not found" → xcode-select başarısız, tekrar çalıştır
# Hata: "Unable to resolve host" → internet yok, Wi-Fi kontrol et

# Çıkarma ve derleme:
tar xzf iperf3.tar.gz
cd iperf-3.17.1
./configure
# Beklenen çıktı: "config.status: executing libtool commands" gibi satırlar
# Hata: "command not found: ./configure" → tar başarısız, cd .. ve tekrar dene

make
# Beklenen: "iperf_client.o", "iperf_server.o" gibi satırlar (5-10 sec)
# Hata: "make: command not found" → xcode-select başarısız

sudo make install
# Password soruyor, Mac şifresi yaz
# Beklenen: "install -m 755 src/iperf3 /usr/local/bin/iperf3"

# Doğrula:
iperf3 --version
# Beklenen: "iperf 3.17.1"
# Hata: "command not found" → /usr/local/bin $PATH'te yok, şunu dene:
#   export PATH="/usr/local/bin:$PATH"
#   iperf3 --version

# Cleanup:
cd ~ && rm -rf iperf-3.17.1 iperf3.tar.gz
```

**Link hata verirse:**
```
https://software.es.net/iperf/ adresine git, "Download" bölümünde latest kaynağı bul
(3.17.x yerine yeni sürüm olabilir), curl'a yapıştır
```

### 3.2 Kod + venv (python3.9 ile)

```bash
# 1) Ev klasörüne git ve kodu klonla:
cd ~
git clone https://github.com/cpeqateam/fullservice_automation.git
# Hata 1: "command not found: git" → xcode-select --install tekrar çalıştır
# Hata 2: "fatal: unable to access ... Could not resolve host" → internet/Wi-Fi kontrol et

# 2) Branch'ı değiştir:
cd fullservice_automation && git checkout aliimran
# Beklenen: "Switched to branch 'aliimran'"
# Hata: "error: pathspec 'aliimran' did not match any file(s)" → git pull, branch'ları listele: git branch -a

# 3) Backend klasörüne git:
cd fullservice-backend
pwd
# Beklenen çıktı: ".../fullservice-backend" (kalıpması gerekir)

# 4) venv oluştur ve aktif et (KRITIK: python3.9 olmalı):
python3.9 -m venv venv
# Hata 1: "command not found: python3.9" → Python 3.9.13 kurulmuş mu? dene: which python3.9
# Hata 2: "Error: [Errno 13] Permission denied" → klasör sahibi değilsin, başka yere klonla
# Doğrula: ls -la venv/bin/python* (3.9 yazılı olmalı)

source venv/bin/activate
# Beklenen: prompt "(venv)" ile başlamalı, örn: "(venv) user@mac:~/fullservice_automation/fullservice-backend$"
# Hata: "command not found: source" → zsh shell'de: "source" yerine ". venv/bin/activate" dene
# Hata: "No such file or directory" → venv oluşturmada hata, aşağıyı dene:
#   rm -rf venv
#   python3.9 -m venv venv
#   source venv/bin/activate

# 5) pip'i güncelle:
pip install --upgrade pip
# Beklenen: "Successfully installed pip-x.y.z"
# Hata: "fatal error: 'Python.h' file not found" → python3.9 development headers yok
#   macOS'ta buramaz, Python 3.9.13 kurulucusunu tekrar çalıştır

# 6) Requirements'i kur:
pip install -r requirements.txt
# Beklenen: "Successfully installed fastapi-0.x.x uvicorn-0.x.x ..."
# Hata 1: "error: Microsoft Visual C++ 14.0" → macOS değil Windows (yanlış machine)
# Hata 2: "Could not find a version" → internet yok veya paket deprecated, şunu dene:
#   pip install --upgrade pip setuptools
#   pip install -r requirements.txt
# Hata 3: "fatal error: 'openssl/ssl.h'" → SSL headers yok, xcode-select tekrar çalıştır
# Doğrula:
python --version  # 3.9.x
pip list           # fastapi, uvicorn görünmeliydi
```

**Özet (venv kurulum doğrulaması):**
```bash
which python       # /path/to/venv/bin/python (sistem değil)
pip list | head -5 # fastapi, uvicorn, pydantic vb.
python -c "import fastapi; print(fastapi.__version__)"  # sürüm yazdırırsa ✓
```

### 3.3 Statik IP — Ethernet adaptörünü bul, sonra ELLE ata

**Adım 1: Adaptör adını bul**

Adaptörü modeme kabloyla takılıyken her adayı testlerle hangisinin modeme bağlı olduğunu anla:

```bash
# Tüm arayüz adlarını listele:
networksetup -listallnetworkservices
# Beklenen çıktı örneği:
# Wi-Fi
# Bluetooth PAN
# Ethernet
# USB 10/100/1000 LAN
# (ör. AX88179A gibi benzersiz ad olabilir)

# Her birini test et (modem IP'si görünüyorsa bağlı):
networksetup -getinfo "USB 10/100/1000 LAN"
# Beklenen (modem bağlı ise): "IP Address: 192.168.1.x"
# Değilse: "IP Address: (none)" → diğerini dene

# Tüm olasılıkları sıra sıra dene:
for service in "Ethernet" "USB 10/100/1000 LAN" "AX88179A" "Thunderbolt Ethernet"; do
  echo "=== $service ===" && networksetup -getinfo "$service" | grep "IP Address"
done
# 192.168.1.x görenin adını NOT AL (örn. AX88179A)
```

**Beklenen sonuç:** `AX88179A` ya da `USB 10/100/1000 LAN` ya da `Ethernet` (ortaya göre değişir)

**Hata:** Hiçbiri 192.168.1.x görmüyor:
- Adaptör modeme kabloyla bağlı mı? Kontrol et (LED yanıyor mu?)
- Adaptörün driver'ı kurulu mu? System Report → USB → adaptör görünüyor mu?
- Wi-Fi'ye bağlı değilmiş gibi yapma, SADECE kablolu test et

---

**Adım 2: IP'yi ELLE ata**

⚠️ macOS'un eski bash'i (3.2) `mapfile` içermediği için `set-static-ip.sh` **çalışmaz**.
Elle `networksetup` kullanacaksın:

```bash
# ADAPTÖR_ADI'nı Adım 1'de bulduğun adla değiştir (ör. AX88179A):
ARAYUZ="AX88179A"  # KENDI ADAPTÖR ADINI YAZ

# Sonra bu komutu çalıştır:
sudo networksetup -setmanual "$ARAYUZ" 192.168.1.11 255.255.255.0 192.168.1.1
# Soruyor: Password? (Mac şifresi)

sudo networksetup -setdnsservers "$ARAYUZ" 8.8.8.8 8.8.4.4

# Doğrula:
networksetup -getinfo "$ARAYUZ"
# Beklenen: "IPv4 Addresses: 192.168.1.11" ve "Subnet Mask: 255.255.255.0"

# Hata: "Unknown argument: -setmanual" → networksetup sürümü çok eski
#       Elle yap: Ayarlar → Ağ → $ARAYUZ → IPv4 → Manual → 192.168.1.11 / 255.255.255.0 / 192.168.1.1
```

**Kontrol (tüm adımlar bitince):**
```bash
networksetup -getinfo "AX88179A"  # IP 192.168.1.11 mi?
ping -c 3 192.168.1.1              # modeme ping atılıyor mu?
ping -c 3 8.8.8.8                  # internete ping atılıyor mu?
```

### 3.4 Agent'ı boot'ta otomatik başlat (BU ADIM GÜNÜBİRLİK ATLA)

⚠️ **Bugün manuel test için:** bu bölümü ATLA. Agent'ı elle başlatacaksın.

**Emanet ortamda boot-otomatik KURULMAYACAK**, çünkü sonradan kaldırmak gerekir.
Eğer test yapmak istersen:

```bash
# Kurulum (emanet sonrası KALDıR):
source venv/bin/activate
bash provisioning/macos/install-agent-launchd.sh mac_cable http://192.168.1.10:8770 7531

# Kontrol:
launchctl list | grep fullservice

# GERİ ALMA (emanet dönerken):
launchctl unload ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_cable.plist 2>/dev/null
rm ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_cable.plist 2>/dev/null
```

**Bugün manuel başlatma:**
```bash
cd ~/fullservice_automation/fullservice-backend
source venv/bin/activate
python3 -c "import os; os.environ['FS_NODE_ID']='mac_cable'; os.environ['FS_SERVER_URL']='http://192.168.1.10:8770'; exec(open('run_agent.py').read())"
# Veya:
FS_NODE_ID=mac_cable FS_SERVER_URL=http://192.168.1.10:8770 python3 run_agent.py
```

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

**4.4 Agent'ı boot'ta başlat (BU ADIM GÜNÜBİRLİK ATLA)**

⚠️ **Bugün manuel test için:** bu bölümü ATLA. Agent'ı elle başlatacaksın.

**Emanet ortamda boot-otomatik KURULMAYACAK**, çünkü sonradan kaldırmak gerekir.
Eğer test yapmak istersen:

```bash
# Kurulum (emanet sonrası KALDıR):
source venv/bin/activate
bash provisioning/macos/install-agent-launchd.sh mac_wifi http://192.168.1.10:8770 7531

# GERİ ALMA (emanet dönerken):
launchctl unload ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_wifi.plist 2>/dev/null
rm ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_wifi.plist 2>/dev/null
```

**Bugün manuel başlatma:**
```bash
cd ~/fullservice_automation/fullservice-backend
source venv/bin/activate
FS_NODE_ID=mac_wifi FS_SERVER_URL=http://192.168.1.10:8770 python3 run_agent.py
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

**Yönetici PowerShell'de** (başlık çubuğu "Administrator:" içerir):

```powershell
# 1) Ağ adaptörlerini listele:
Get-NetAdapter | Select Name, Status, InterfaceDescription
# Beklenen çıktı:
# Name            Status  InterfaceDescription
# Wi-Fi          Up      Qualcomm Atheros AR9485 Wireless Adapter
# Ethernet       Down    Realtek PCIe Ethernet Controller
# (Wi-Fi adı genelde "Wi-Fi" ama "Wireless Adapter 1" vb. olabilir)

# Hata: "Get-NetAdapter : The term 'Get-NetAdapter' is not recognized"
#   → Windows 7 / PowerShell çok eski; aşağıyı dene:
#   ipconfig /all  (komut satırında)

# 2) Modeme Wi-Fi ile bağlı olduğundan emin ol:
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"
# Beklenen: "IPv4Address: 192.168.1.x" görmeli
# Hata: IPv4 adı yok = Wi-Fi bağlı değil, bağlan

# 3) Statik IP script'ini çalıştır:
.\provisioning\windows\set-static-ip.ps1 -NodeId win_wifi
# Beklenen: "Setting static IP for win_wifi on Wi-Fi..." + başarı mesajı
# Hata 1: "File ...\set-static-ip.ps1 cannot be loaded because running scripts is disabled"
#   → Script izni: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   → Sonra tekrar çalıştır
# Hata 2: "Get-NetIPConfiguration : No such interface" → arayüz adı yanlış (Get-NetAdapter'da başka ad yok mu?)
# Hata 3: Network Manager ile çakışması → UAC (User Account Control) işaretlenmiş, devam et

# 4) Doğrula:
ipconfig /all
# Beklenen: "Wi-Fi" altında "IPv4 Address: 192.168.1.13" (DHCP ENABLED: NO olmalı)
# Hata: DHCP açık kalmışsa, elle kapatmanız gerek:
#   Ayarlar → Ağ → Wi-Fi → Özellikler → IPv4 → Manual → 192.168.1.13 / Maske 255.255.255.0 / Gateway 192.168.1.1
```

**Özet (doğrulama):**
```powershell
ipconfig /all | Select-String -Pattern "Wi-Fi" -A 15
# IPv4 Address: 192.168.1.13 görünmeliy
```

### 5.3 Agent'ı boot'ta otomatik başlat (BU ADIM GÜNÜBİRLİK ATLA)

⚠️ **Bugün manuel test için:** bu bölümü ATLA. Agent'ı elle başlatacaksın.

**Emanet ortamda boot-otomatik KURULMAYACAK**, çünkü sonradan kaldırmak gerekir.
Eğer test yapmak istersen:

```powershell
# Kurulum (emanet sonrası KALDıR):
.\provisioning\windows\install-agent-task.ps1 -NodeId win_wifi -ServerUrl http://192.168.1.10:8770 -Port 7531
Start-ScheduledTask -TaskName FullServiceAgent_win_wifi

# GERİ ALMA (emanet dönerken):
Unregister-ScheduledTask -TaskName FullServiceAgent_win_wifi -Confirm:$false -ErrorAction SilentlyContinue
```

**Bugün manuel başlatma:**
```powershell
cd fullservice_automation\fullservice-backend
.\venv\Scripts\activate
$env:FS_NODE_ID="win_wifi"
$env:FS_SERVER_URL="http://192.168.1.10:8770"
python run_agent.py
```

✅ `win_wifi` manuel olarak çalıştırıldı; çökmezse test başlayabilirsin.

---

## 2.8 ⚠️ YENİ: Veritabanı ve FTP entegrasyonu (2026-06-23 itibaren)

**Test sonuçları artık otomatik olarak PostgreSQL'e yazılıyor.** Bu aşamada **staging tablolarına** (copy_*) yazılır:
- `copy_test_session` — oturum bilgileri
- `copy_ping_test` — ping sonuçları
- `copy_iperf_test` — iperf (hız) sonuçları  
- `copy_wifi_analysis` — Wi-Fi örnekleri

**Önkoşullar:**
1. **DB sertifikaları** kuruldu (2.4 bölümü ✓)
2. **FS_FIRMWARE_DB_URL** ortam değişkeni doğru ayarlanmış (`postgresql://...cpeqadb`)
   - Varsayılan değer kod içinde; isterseniz `export FS_FIRMWARE_DB_URL="..."` ile override edin
3. **FTP sertifikaları** kuruldu (2.4) ve FTP sunucusu erişilebilir
   - FTP'yi devre dışı bırakmak istersen: `export FS_FTP_DISABLE=1`

**Test sırasında ne olur:**
- Her test bitince runner istatistik gönderiyor (`ctx.result(...)`)
- Sunucu bunu `copy_*` tablolarına yazıyor
- Loglar aynı anda FTP'ye aktarılıyor (arka planda, hata yutulur)

**Sorun giderme:**
- DB yazma başarısızsa testler **yine çalışır** (arka planda hata yutulur)
- FTP yazma başarısızsa loglar **sunucunun `logs/` klasöründe** kalır
- Hataları görmek için: `tail -f /tmp/fullservice-db.err` veya `tail -f /tmp/fullservice-ftp.err`

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

**Ek kontrol (DB + FTP yazması):**
```bash
# Terminal'de, test BITINCE:

# 1) DB'ye yazılmış mı? (PostgreSQL'e bağlanabiliyorsan):
psql -h <db_host> -U <user> cpeqadb -c "SELECT COUNT(*) FROM copy_test_session;"

# 2) FTP'ye yazılmış mı?
ls -la ~/fullservice_automation/fullservice-backend/logs/LINUX/<son_session_id>/
# Dosyalar varsa, arka planda FTP upload'u denendi.

# 3) Hata var mı?
cat /tmp/fullservice-db.err 2>/dev/null || echo "DB OK"
cat /tmp/fullservice-ftp.err 2>/dev/null || echo "FTP OK"
```

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
| **DB yazma başarısız (copy_test_session boş)** | Sertifikalar (`certs/`) eksik veya izin yanlış → `chmod 600 certs/client.key`. DB bağlantısı yoksa testler **yine çalışır**, yalnızca kayıt olmaz. Hata: `cat /tmp/fullservice-db.err`. |
| **FTP yazma başarısız (loglar FTP'de yok)** | Sertifikalar eksik, FTP sunucusu down veya `FS_FTP_DISABLE=1`. Testler **yine çalışır**, loglar sunucuda `logs/` kalır. Hata: `cat /tmp/fullservice-ftp.err`. |


---

## 8. ⚠️ EMANET ORTAMI İADE EDERKEN (Tüm değişiklikleri geri al)

**Geri alma işlemi — tek cümle:** Yaptığın 2 değişikliği geri al:
1. **Statik IP → DHCP** (otomatik IP'ye dön)
2. **Boot-otomatik servisleri sil** (eğer kurmuşsan)

---

### 8.1 LINUX SUNUCU (VM → Şahsi MacBook)

⚠️ **Sabık: Sadece statik IP değiştirildi, boot-otomatik KURULMADI.**

```bash
# Statik IP'yi DHCP'ye çevir:
sudo bash provisioning/linux/set-static-ip.sh server  # tekrar çalıştır
# Sorulduğunda DHCP seçeneğini seç (varsa)

# VEYA elle:
# Ayarlar → Ağ → IPv4 → Automatic (DHCP)

# Doğrula:
ip addr show enp0s1  # "inet" satırında DHCP adresi görmeliydi
```

---

### 8.2 MAC #1 (mac_cable) — Kablolu

**Geri alma: Statik IP + Kod deposu + Araçlar**

```bash
# 1) Statik IP'yi DHCP'ye çevir (adaptör adı doğrula):
networksetup -listallnetworkservices  # adaptör adını bul (ör. AX88179A)
sudo networksetup -setdhcp "AX88179A"
# Doğrula:
networksetup -getinfo "AX88179A"  # "Using DHCP" yazmalı

# 2) Boot-otomatik agent'ı sil (eğer kurmuşsan):
launchctl unload ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_cable.plist 2>/dev/null
rm ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_cable.plist 2>/dev/null

# 3) (Opsiyonel) Kod deposunu sil:
rm -rf ~/fullservice_automation

# 4) (Opsiyonel) Python + iperf3'ü sil:
# - Homebrew ile kurduysanız: brew uninstall python iperf3
# - Manuel kurduysanız: python3.9 kurulucusundan uninstall; iperf3 manuel silinir
```

---

### 8.3 MAC #2 (mac_wifi) — Wi-Fi

**Geri alma: Statik IP + Kod deposu + Araçlar**

```bash
# 1) Statik IP'yi DHCP'ye çevir:
sudo networksetup -setdhcp "Wi-Fi"
# Doğrula:
networksetup -getinfo "Wi-Fi"  # "Using DHCP" yazmalı

# 2) Boot-otomatik agent'ı sil (eğer kurmuşsan):
launchctl unload ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_wifi.plist 2>/dev/null
rm ~/Library/LaunchAgents/com.tt.fullservice.agent.mac_wifi.plist 2>/dev/null

# 3) (Opsiyonel) Kod deposunu sil:
rm -rf ~/fullservice_automation

# 4) (Opsiyonel) Araçları sil (2. Mac ile aynı).
```

---

### 8.4 WINDOWS (win_wifi)

**Geri alma: Statik IP + Görev Zamanlayıcı + Kod deposu**

```powershell
# Yönetici PowerShell'de çalıştır:

# 1) Statik IP'yi DHCP'ye çevir:
Get-NetAdapter | Select Name                # Wi-Fi arayüzünü doğrula
Set-NetIPInterface -InterfaceAlias "Wi-Fi" -DHCP Enabled
# Doğrula:
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"  # "DHCP" yazmalı

# 2) Boot-otomatik görev'i sil (eğer kurmuşsan):
Unregister-ScheduledTask -TaskName FullServiceAgent_win_wifi -Confirm:$false -ErrorAction SilentlyContinue

# 3) (Opsiyonel) Kod deposunu sil:
Remove-Item -Recurse -Force "$env:USERPROFILE\fullservice_automation"

# 4) (Opsiyonel) Araçları sil:
# - Python / Git / Chrome / qBittorrent: Denetim Paneli → Programlar → Kaldır
```

---

### 8.5 Kontrol Listesi (Teslim öncesi doğrula)

Emanet ortamı geri vermeden ÖNCE şunu kontrol et:

```bash
# Linux VM:
ip addr show enp0s1  # DHCP adresi mi? (192.168.1.10 OLMAMALI)

# Mac #1:
networksetup -getinfo "AX88179A"  # "Using DHCP" mi?

# Mac #2:
networksetup -getinfo "Wi-Fi"  # "Using DHCP" mi?

# Windows (PowerShell):
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"  # DHCP mi?
Get-ScheduledTask FullServiceAgent_win_wifi -ErrorAction SilentlyContinue  # SİLİNMİŞ mi?
```

✅ Hepsi "DHCP" / "silinmiş" / "doğru ağ" gösteriyorsa, emanet ortam eski haline dönmüştür.

---

### 8.6 Kalabilir (zorunlu değil):

- Kod deposu (`fullservice_automation/`)
- Python + venv
- iperf3, Chrome, Git, qBittorrent
- Sertifikalar (gizli `certs/` — zaten projede değil)

Bunlar başka makineye taşmaz, zararsızdır; ama isterseniz silebilirsiniz.
