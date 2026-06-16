# FULL Servis — Gerçek Ortam Kurulumu (4 Fiziksel Makine)

Bu rehber, sistemi **gerçek sahaya** taşır: 3 fiziksel bilgisayar + 1 Linux sanal
makinesi. Amaç: her makinede ayarları **yalnızca BİR KEZ** yapmak; sonrasında
bilgisayarları açmak ve dashboard'da **Başlat**'a basmak dışında hiçbir şey
gerekmesin. Tüm servisler boot'ta otomatik kalkar, çökerse kendini yeniden başlatır.

> Bu doküman VM-lab rehberi [`KURULUM_TEST.md`](KURULUM_TEST.md)'nin yerine geçen
> **saha** sürümüdür. Lab'da tek Mac iki düğümü üstleniyordu; burada **her makine
> tek düğüm** çalıştırır, bu yüzden hepsi aynı **7531** portunu kullanır (port
> ayarıyla uğraşmak yok).

---

## ⚠️ ÖNCE BUNU OKU: Kendi ağ adresini belirle

Bu dokümandaki örnekler `192.168.1.x` ağına göre yazılmıştır. **Senin ağın farklı
olabilir.** Önce öğren: herhangi bir makinede modemin/gateway'in adresine bak
(Linux'ta `ip route | grep default` → "default via **192.168.X.1**" satırı).

- Modemin `192.168.1.1` ise → dokümandaki adresleri olduğu gibi kullan.
- Modemin **`192.168.88.1`** ise (bu kurulumda böyle) → dokümandaki **her** `192.168.1.x`
  yerine `192.168.88.x` oku. Yani:

| Düğüm | Bu kurulumdaki sabit IP'si |
|------|----------------------------|
| **server** (Linux VM) | **192.168.88.10** |
| **mac_cable** | **192.168.88.11** |
| **win_wifi** | **192.168.88.13** |
| **mac_wifi** | **192.168.88.14** |
| gateway (modem) | **192.168.88.1** |

> 💡 Bu "sabit IP"leri **sen seçiyorsun** (modem otomatik vermez). Linux şu an
> otomatik (DHCP) bir adres almış olabilir (örn. `192.168.88.41`) — onu kullanma,
> aşağıda `.10`'a sabitleyeceğiz. Bundan sonra dashboard adresin
> **http://192.168.88.10:8770** olacak.

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
UTM kurulumu ve Ubuntu adımları için [`KURULUM_TEST.md` → BÖLÜM 1](KURULUM_TEST.md)
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
```

Koymazsan sistem **çökmez**: Marka/Model/Firmware kutuları otomatik **serbest-metin**
girişine düşer, test yine başlatılır. Yalnızca **sunucuya** gerekir (agent'lara değil).

> Not: Linux dosya yolu ASCII olduğu için, Windows'ta yaşanan "Masaüstü" Türkçe-karakter
> sorunu burada olmaz; certleri koyman yeterli.

### 2.5 Sunucunun statik IP'sini ayarla (adım adım)

**Amaç:** Linux her açılışta aynı IP'yi (`192.168.88.10`) alsın. Şu an otomatik
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
"default via **192.168.88.1**" → gateway budur (bu kurulumda `192.168.88.1`).

**Adım 3 — config.json'u düzenle.** Önce `fullservice-backend` klasöründe ol:
```bash
cd ~/fullservice_automation/fullservice-backend
nano config.json
```
Açılan **nano** editöründe (fare yok, ok tuşlarıyla gez) `network` ve `server`
bölümlerini şöyle yap (IP'ler senin ağına, yani `192.168.88.x`):
```json
"network": {
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.88.1",
  "dns": ["8.8.8.8", "8.8.4.4"],
  "assignments": {
    "server":    { "ip": "192.168.88.10", "interface": "enp0s1" },
    "mac_cable": { "ip": "192.168.88.11", "interface": "Ethernet" },
    "win_wifi":  { "ip": "192.168.88.13", "interface": "Wi-Fi" },
    "mac_wifi":  { "ip": "192.168.88.14", "interface": "Wi-Fi" }
  }
},
"server": { "host": "0.0.0.0", "port": 8770, "lan_ip": "192.168.88.10" }
```
> 🔑 İki yeri karıştırma: `assignments.server.ip` = makineye atanacak sabit IP;
> `server.lan_ip` = "sunucu bu adreste" bilgisi. **İkisi de `192.168.88.10` olmalı.**

Kaydet ve çık: **Ctrl+O → Enter → Ctrl+X**.

**Adım 4 — Statik IP'yi uygula** (script config.json'u okuyup `nmcli` ile atar):
```bash
sudo bash provisioning/linux/set-static-ip.sh server
```
Şifre sorabilir. (Eğer SSH ile bağlıysan IP `.41`'den `.10`'a düşünce bağlantın
kopar — UTM penceresinden yazıyorsan sorun olmaz.)

**Adım 5 — Doğrula:**
```bash
ip addr show enp0s1      # satırlardan birinde "inet 192.168.88.10/24" görünmeli
```
Artık sunucunun IP'si sabit: **192.168.88.10** (her açılışta aynı).

> **Script yerine elle yapmak istersen:** Ayarlar → Ağ → ⚙️ → IPv4 → **Manual** →
> Adres `192.168.88.10`, Maske `255.255.255.0`, Gateway `192.168.88.1`, DNS `8.8.8.8`
> → Uygula, bağlantıyı kapat-aç. Bu durumda config'de yine `server.lan_ip` =
> `192.168.88.10` olmalı (agent'lar sunucuyu orada arar).

### 2.6 Sunucuyu boot'ta otomatik başlat (bir kez)
```bash
sudo bash provisioning/linux/install-server-systemd.sh
```
- Kontrol: `systemctl status fullservice-server`
- Log: `journalctl -u fullservice-server -f`
- Dashboard: VM'in Firefox'unda **http://localhost:8770** (veya ağdaki herhangi
  bir cihazdan **http://192.168.1.10:8770**).

✅ Sunucu artık VM her açıldığında kendiliğinden kalkar.

---

## 3. YENİ MACBOOK #1 → `mac_cable` (kablolu, iperf server)

Bu Mac'i modeme **Ethernet adaptörüyle kabloyla** bağla.

### 3.1 Araçlar + kod (bir kez)
```bash
brew install python git iperf3        # Homebrew yoksa: https://brew.sh
cd ~ && git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3.2 Statik IP (Ethernet)
```bash
networksetup -listallnetworkservices   # Ethernet adaptörünün adını gör
# config.json'da assignments.mac_cable.interface'i o ada eşitle (bir kez).
# config'i Adım 2.5'te push'ladıysan zaten doğru gelmiştir; sadece arayüz adını teyit et.
sudo bash provisioning/macos/set-static-ip.sh mac_cable
```

### 3.3 Agent'ı boot'ta otomatik başlat (bir kez)
> **Önemli:** launchd, kurulum anındaki `python3`'ü kaydeder. Doğru bağımlılıkların
> bulunması için **önce venv'i aktif et**, sonra kur:
```bash
source venv/bin/activate
bash provisioning/macos/install-agent-launchd.sh mac_cable http://192.168.1.10:8770 7531
```
- Kontrol: `launchctl list | grep fullservice`
- Log: `cat logs/agent-launchd.err.log`

✅ Bu Mac her açıldığında `mac_cable` agent'ı kalkar, sunucuya kaydolur.

---

## 4. YENİ MACBOOK #2 → `mac_wifi` (Wi-Fi, iperf client)

Bu Mac'i modemin **Wi-Fi**'sine bağla.

```bash
# 4.1 Araçlar + kod (bir kez) — Mac #1 ile aynı:
brew install python git iperf3
cd ~ && git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4.2 Statik IP (Wi-Fi):
networksetup -listallnetworkservices   # genelde "Wi-Fi"
sudo bash provisioning/macos/set-static-ip.sh mac_wifi

# 4.3 Agent'ı boot'ta başlat (venv aktifken!):
source venv/bin/activate
bash provisioning/macos/install-agent-launchd.sh mac_wifi http://192.168.1.10:8770 7531
```

✅ `mac_wifi` her açılışta kalkar; iperf client olarak `mac_cable`'a yük basar.

---

## 5. WINDOWS BİLGİSAYARI → `win_wifi` (Wi-Fi)

Windows'u modemin **Wi-Fi**'sine bağla. Aşağıdakileri **Yönetici PowerShell**'de yap.

### 5.1 Araçlar + kod (bir kez)
1. **Python** (python.org) — kurarken **"Add python.exe to PATH"** işaretle.
2. **iperf3** — Windows binary'sini indirip bir klasöre koy, PATH'e ekle.
3. **Git** (git-scm.com).
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
| Marka/Model **boş / serbest metin** | Sunucuda `certs/` (ca/client.crt+key) eksik veya DB'ye ağ yok. Beklenen geri-düşüş; test yine başlar. |
| **iperf** kutusu kırmızı | İlgili Mac'te `iperf3` yok (`brew install iperf3`) **veya** `mac_cable` (server) ayakta değil — client onu bekler, 5 kez yeniden dener. |
| Statik IP atanmadı (Linux) | Ubuntu'da NetworkManager (nmcli) gerekir; `ubuntu-desktop` kuruluysa vardır. Arayüz adını `ip -o link show` ile teyit et. |
| macOS Ethernet servis adı farklı | Adaptöre göre `USB 10/100/1000 LAN` vb. olabilir; `networksetup -listallnetworkservices` çıktısını config'e yaz. |
