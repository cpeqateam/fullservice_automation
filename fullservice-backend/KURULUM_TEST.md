# FULL Servis — Test Lab Kurulumu (Linux + Mac + Windows)

Bu rehber, M4 MacBook (16 GB) üzerinde **3 makineli** test ortamını sıfırdan kurar.
Hiç sanal makine kurmamış biri için ekran ekran yazılmıştır.

---

## 0. Genel bakış — kim nerede, ne kadar RAM?

16 GB RAM'e sığsın diye plan: **sadece 2 VM** (Linux + Windows). Mac'in kendisi
iki "Mac düğümü"nü üstlenir (gerçek Mac olduğu için temsili doğru).

| Düğüm | Nerede çalışır | RAM | Disk | Port |
|------|----------------|-----|------|------|
| **Linux sunucu** (arayüzlü) | UTM'de **VM** | 4 GB | 25 GB | 8770 |
| **mac_cable** | **Mac'in kendisi** (VM yok) | — | — | 8771 |
| **mac_wifi** | **Mac'in kendisi** (VM yok) | — | — | 8772 |
| **win_wifi** | UTM'de **VM** (Windows 11 ARM) | 5 GB | 64 GB | 8771 |

> ⚠️ 16 GB'da **3 VM'i (Linux+Windows+macOS) aynı anda açamazsın.** O yüzden iki Mac
> düğümünü ayrı macOS VM'leri yerine doğrudan Mac host'ta çalıştırıyoruz. En sonda
> gerçek stres testi zaten 4 **fiziksel** makinede yapılacak; VM lab sadece
> yazılımın doğru çalıştığını kanıtlamak içindir.

> 💡 **Windows VM en zahmetli kısım.** İlk testte onu atlayıp `win_wifi` agent'ını da
> geçici olarak Mac'te çalıştırabilirsin (aşağıda "Hızlı ön-deneme"). Sistem çalışınca
> Windows VM'i eklersin.

---

## ⚡ Hızlı ön-deneme (hiç VM yok, sadece Mac) — 5 dk

VM'lerle uğraşmadan önce sistemin çalıştığını gör. Mac'te:

```bash
brew install python iperf3
cd <fullservice-backend klasörü>
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4 terminal aç (her terminalde önce: source venv/bin/activate):
python run_server.py                                              # Terminal 1
python run_agent.py mac_cable http://127.0.0.1:8770              # Terminal 2 (port 8771)
FS_AGENT_PORT=8772 python run_agent.py mac_wifi http://127.0.0.1:8770   # Terminal 3
FS_AGENT_PORT=8773 python run_agent.py win_wifi http://127.0.0.1:8770   # Terminal 4
```

Tarayıcı: **http://127.0.0.1:8770** → **FULL Servis Başlat**. 4 kutu yeşil yanıyorsa
sistem sağlam. Şimdi gerçek VM lab'a geçebilirsin.

---

# BÖLÜM 1 — Linux Sunucu (UTM'de VM)

## 1.0 Ubuntu ISO'sunu indir
1. Safari → **https://ubuntu.com/download/server/arm**
2. **Download Ubuntu Server (ARM)** → `...arm64.iso` (~2-3 GB) iner.

## 1.1 UTM'de VM oluştur (ekran ekran)
1. UTM → **Create a New Virtual Machine** → **Virtualize** → **Linux**.
2. **"Use Apple Virtualization"** işaretsiz bırak. **Boot from ISO image** → **Browse** → indirdiğin .iso → **Continue**.
3. **Memory: 4096**, **CPU Cores: 2** → **Continue**.
4. **Storage: 25** (GB) → **Continue**.
5. **Shared Directory:** boş geç → **Continue**.
6. **Name:** `linux-sunucu` → **Save**.

## 1.2 Ubuntu'yu kur
1. `linux-sunucu`'yu seç → **▶ Play**.
2. Sırayla: Dil **English** → Klavye seç → **Ubuntu Server** (varsayılan) → Network/Proxy/Mirror'a dokunma → Disk **Use entire disk** → Done → Continue.
3. **Profile:** ad / server name (`linuxsunucu`) / username / password belirle — **NOT AL.**
4. **Install OpenSSH server** ✅ (Space ile).
5. Kurulum bitince **Reboot Now**. Tekrar kurulum açılırsa: VM'i kapat → UTM → VM → **Edit** → CD/ISO sürücüsünü **Clear/Delete** → tekrar başlat.

## 1.3 Masaüstü (arayüz) kur
Server arayüzsüz gelir; paneli sunucunun kendi Firefox'unda açmak için:
```bash
sudo apt update
sudo apt install ubuntu-desktop -y     # büyük indirme, 20-40 dk
sudo reboot
```
Açılınca grafik giriş ekranı → şifrenle gir → Ubuntu masaüstü + Firefox hazır.
(Yavaşsa: `sudo apt install xubuntu-desktop -y`)

## 1.4 Ağı Bridged yap (gerçek IP için — ZORUNLU)
1. `sudo poweroff` ile kapat.
2. UTM → `linux-sunucu` → **Edit** → **Network → Network Mode → Bridged (Advanced)** → **Save**.
3. Tekrar başlat, giriş yap.

## 1.5 git + python + venv + iperf3 + kod
```bash
sudo apt update
sudo apt install -y git python3-pip python3-venv iperf3

# Kodu çek (aliimran branch'inde):
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation
git checkout aliimran
cd fullservice-backend

# Sanal ortam + bağımlılıklar (yeni Ubuntu için venv ŞART):
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Bu VM'in IP'sini öğren (örn. 192.168.1.50):
hostname -I
```
Çıkan `192.168.x.x` adresini **not al** → buna **LINUX_IP** diyeceğiz. = 192.168.88.11

## 1.55 Frontend'i derle (dashboard için — bir kez)

Backend, kardeş `fullservice-frontend/dist/` klasörünü statik servis eder.
Bu klasör build sonrası oluşur. Linux VM'de:

```bash
# Node.js + npm (bir kez):
sudo apt install -y nodejs npm

# fullservice-frontend dizini klasörde zaten var (repo'dan geldi)
cd ../fullservice-frontend
npm install
npm run build
cd ../fullservice-backend
```

`fullservice-frontend/dist/` oluşur; backend tekrar başlatılınca otomatik
servis eder. Frontend kodunu değiştirip canlı görmek istersen `npm run dev`
(http://localhost:5173) — backend yine 8770'te çalışır, Vite `/api/*`'yi
proxy'ler.

## 1.6 config.json'da lan_ip'i ayarla
```bash
nano config.json
```
`"server"` satırındaki `lan_ip`'i LINUX_IP yap:
```json
"server": { "host": "0.0.0.0", "port": 8770, "lan_ip": "LINUX_IP" }
```
Kaydet: **Ctrl+O → Enter → Ctrl+X**.

## 1.7 Sunucuyu başlat
```bash
source venv/bin/activate     # zaten aktifse atla
python run_server.py
```
Bu terminali açık bırak. Panel: Linux'un Firefox'unda **http://localhost:8770**.

---

# BÖLÜM 2 — Mac (host, VM YOK) = mac_cable + mac_wifi

Mac'in kendisi iki düğümü üstlenir. Mac'te yeni bir terminal aç:

## 2.1 Gerekli araçlar (bir kez)
```bash
brew install python iperf3 git
```
(Homebrew yoksa: https://brew.sh adresindeki tek satırı çalıştır.)

## 2.2 Kodu çek + venv
```bash
cd ~
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 2.3 İki agent'ı başlat (LINUX_IP = sunucunun IP'si)
İki ayrı terminal aç, **her ikisinde önce** `cd ...fullservice-automation && source venv/bin/activate`:
```bash
# Terminal A:
python run_agent.py mac_cable http://LINUX_IP:8770          # port 8771 = 192.168.88.11

# Terminal B:
FS_AGENT_PORT=8772 python run_agent.py mac_wifi http://LINUX_IP:8770
```
Açılınca panelde mac_cable ve mac_wifi yeşil yanar.

---

# BÖLÜM 3 — Windows 11 ARM (UTM'de VM) = win_wifi

> En zahmetli kısım. Acelen yoksa önce Bölüm 1+2 ile sistemi çalıştır,
> bunu sonra ekle. (O zamana kadar win_wifi'yi Mac'te koşabilirsin:
> `FS_AGENT_PORT=8773 python run_agent.py win_wifi http://LINUX_IP:8770`)

## 3.1 Windows 11 ARM ISO indir
- En kolayı **CrystalFetch** uygulaması (Mac App Store, ücretsiz): aç → Windows 11 →
  **arm64** + dil seç → **Download**. Resmi Microsoft ISO'sunu indirir.

## 3.2 UTM'de VM oluştur
1. UTM → **Create** → **Virtualize** → **Windows**.
2. **Boot from ISO image** → indirdiğin Windows ARM ISO'yu seç. (UTM "guest tools"
   sürücülerini otomatik ekler — bırak.)
3. **Memory: 5120**, **CPU Cores: 2** → **Storage: 64 GB** → Name `windows-wifi` → **Save**.

## 3.3 Windows'u kur
1. Başlat, kurulumu izle. Ürün anahtarı: **"I don't have a product key"** → **Windows 11 Pro**.
2. Microsoft hesabı/internet zorlarsa: **Shift+F10** ile cmd aç → `start ms-cxh:localonly`
   (eski sürümlerde `oobe\bypassnro`) → yerel hesap oluştur.
3. Masaüstü gelince UTM'in taktığı **guest tools / SPICE** ISO'sundan sürücüleri kur
   (ağ ve ekran için gerekir), yeniden başlat.

## 3.4 Ağı Bridged yap
UTM → `windows-wifi` → **Edit** → **Network → Bridged (Advanced)** → Save → başlat.

## 3.5 Python + iperf3 + kod (Windows içinde)
1. **Python:** python.org → Windows **ARM64** installer → kurarken **"Add to PATH"** işaretle.
2. **iperf3:** Windows iperf3 binary'sini indir, bir klasöre koy, PATH'e ekle (veya o klasörde çalıştır).
3. **Git:** git-scm.com'dan kur. PowerShell aç:
```powershell
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation; git checkout aliimran
cd fullservice-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_agent.py win_wifi http://LINUX_IP:8770
```
(Windows tek agent çalıştırdığı için port 8771 varsayılanı yeterli, env gerekmez.)

---

# BÖLÜM 4 — Testi başlat

Linux'un Firefox'unda → **http://localhost:8770** (veya herhangi bir cihazdan
`http://LINUX_IP:8770`) → **FULL Servis Başlat**.

Panelde 4 düğüm yeşil yanıp testler eşzamanlı koşmalı. ✅

---

## Sorun giderme
- **`pip: command not found`** → `sudo apt install -y python3-pip python3-venv`, sonra venv kullan.
- **`externally-managed-environment` hatası** → sistem geneline pip yasak; mutlaka `python3 -m venv venv && source venv/bin/activate` içinden kur.
- **Panelde düğüm gri/offline** → o agent'ın terminali açık mı? IP doğru mu? Ağ **Bridged** mi? Mac↔Linux birbirini görüyor mu (`ping LINUX_IP`)?
- **İki Mac agent'ı çakışıyor** → ikisine farklı port ver (`FS_AGENT_PORT=8772 ...`).
- **`iperf` kutusu kırmızı** → o makinede iperf3 yok (mac: `brew install iperf3`, linux: `sudo apt install iperf3`).
- **`youtube` tarayıcı açıyor** → normal; istemezsen `config.json`'da `youtube_link`'i boş bırak.
- **`git checkout aliimran` "branch yok" derse** → `git fetch origin` sonra tekrar dene.
