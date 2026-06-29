# FULL Servis — Saha Kurulum Rehberi (4 Fiziksel Makine)

## Ağ planı

| Düğüm | IP | Arayüz | Makine |
|-------|----|--------|--------|
| server | 192.168.1.10 | eth0 | Dell Linux (Ubuntu 22.04) |
| mac_cable | 192.168.1.11 | AX88179A | MacBook — Ethernet adaptörü |
| win_wifi | 192.168.1.13 | Wi-Fi | Windows |
| mac_wifi | 192.168.1.14 | Wi-Fi | MacBook — Wi-Fi |
| gateway | 192.168.1.1 | — | Modem |

Dashboard: **http://192.168.1.10:8770**

---

## 1. Linux Sunucu (Dell, Ubuntu 22.04, eth0)

### Kurulum (bir kez)
```bash
# Node.js 20 kur (apt install nodejs eski sürüm verir)
curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt-get install -y nodejs

# Bağımlılıklar
sudo apt update
sudo apt install -y git python3-pip python3-venv iperf3

# Kod
cd ~/Desktop/aliimran
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend

# Python ortamı
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Frontend derle (bir kez)
cd ../fullservice-frontend && npm install && npm run build && cd ../fullservice-backend

# Sertifikalar (Mac'ten scp ile kopyala)
# Mac terminalinde:
# scp -r /Users/aliimranatabey/vscode-workspace/fullservice_automation/fullservice-backend/certs/ telekom@192.168.1.100:~/Desktop/aliimran/fullservice_automation/fullservice-backend/
chmod 600 certs/client.key
```

> **Sırlar (Telegram + mail bildirimi için) — sadece sunucuda gerekli:**
> `fullservice-backend/secrets.json` dosyasını **elle** oluştur (repoda YOK, gitignore'lu).
> İçeriği:
> ```json
> {
>   "FS_TELEGRAM_BOT_TOKEN": "...",
>   "FS_TELEGRAM_CHAT_ID": -4802883729,
>   "FS_SMTP_USER": "cpetestteam",
>   "FS_SMTP_PASS": "...",
>   "FS_SMTP_FROM": "cpetestteam@gmail.com"
> }
> ```
> Bu dosya yoksa testler yine çalışır, sadece bildirim gitmez. Aynı değerleri ortam
> değişkeni olarak da verebilirsin (`FS_TELEGRAM_BOT_TOKEN=...` vb.).
> FTP/DB yazımı ise `certs/` ile çalışır (yukarıda kopyalandı); `certs` yoksa sessizce atlanır.

### Statik IP
```bash
# config.json'u doğrula (eth0 yazılı olmalı)
cat config.json | grep -A 10 "assignments"

# IP ata
sudo bash provisioning/linux/set-static-ip.sh server

# Doğrula
ifconfig eth0   # inet 192.168.1.10 görünmeli
ping -c 3 8.8.8.8
```

### Sunucuyu başlat
```bash
cd ~/Desktop/aliimran/fullservice_automation/fullservice-backend
source venv/bin/activate
python3 run_server.py
```

---

## 2. Mac Cable (mac_cable — Ethernet, iperf server)

### Kurulum (bir kez)
```bash
# Python 3.9.13 kur: python.org/downloads/release/python-3913/
# "macOS 64-bit Intel installer" indir, kur.

# iperf3 (eski macOS'ta brew çalışmaz, kaynaktan derle)
curl -L -o iperf3.tar.gz https://downloads.es.net/pub/iperf/iperf-3.17.1.tar.gz
tar xzf iperf3.tar.gz && cd iperf-3.17.1
./configure && make && sudo make install
cd ~ && rm -rf iperf-3.17.1 iperf3.tar.gz

# Kod
cd ~
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3.9 -m venv venv && source venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
```

### Statik IP
```bash
sudo networksetup -setmanual "AX88179A" 192.168.1.11 255.255.255.0 192.168.1.1
sudo networksetup -setdnsservers "AX88179A" 8.8.8.8 8.8.4.4
networksetup -getinfo "AX88179A"   # IPv4 Addresses: 192.168.1.11 görünmeli
```

### Agent'ı başlat
```bash
cd ~/fullservice_automation/fullservice-backend
source venv/bin/activate
python run_agent.py mac_cable http://192.168.1.10:8770
```

---

## 3. Mac WiFi (mac_wifi — Wi-Fi, iperf client)

### Kurulum (bir kez)
Mac Cable ile aynı (Python 3.9.13 + iperf3 + git clone):
```bash
cd ~
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation && git checkout aliimran
cd fullservice-backend
python3.9 -m venv venv && source venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
```

### Statik IP
```bash
sudo networksetup -setmanual "Wi-Fi" 192.168.1.14 255.255.255.0 192.168.1.1
sudo networksetup -setdnsservers "Wi-Fi" 8.8.8.8 8.8.4.4
networksetup -getinfo "Wi-Fi"   # IPv4 Addresses: 192.168.1.14 görünmeli
```

### Agent'ı başlat
```bash
cd ~/fullservice_automation/fullservice-backend
source venv/bin/activate
python run_agent.py mac_wifi http://192.168.1.10:8770
```

---

## 4. Windows (win_wifi — Wi-Fi)

### Kurulum (bir kez)
1. Python 3.11 kur (python.org) — "Add python.exe to PATH" işaretle
2. Git kur (git-scm.com)
3. Chrome kur
4. qBittorrent kur → **Araçlar → Seçenekler → Web Arayüzü**: aktif, port **8080**, kullanıcı **admin**, şifre **Admin123**

```powershell
# Yönetici PowerShell'de:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

cd Desktop\aliimran
git clone https://github.com/cpeqateam/fullservice_automation.git
cd fullservice_automation; git checkout aliimran
cd fullservice-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Statik IP
```powershell
.\provisioning\windows\set-static-ip.ps1 -NodeId win_wifi
# Doğrula:
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"   # 192.168.1.13 görünmeli
```

### Agent'ı başlat
```powershell
cd Desktop\aliimran\fullservice_automation\fullservice-backend
venv\Scripts\activate
$env:FS_NODE_ID="win_wifi"
$env:FS_SERVER_URL="http://192.168.1.10:8770"
python run_agent.py
```

---

## 5. Test Başlatma

1. Linux'ta `run_server.py` çalışıyor olmalı
2. 3 makinede `run_agent.py` çalışıyor olmalı
3. **http://192.168.1.10:8770** → giriş yap (`cpeteam` / `cpeteam`, ya da `grk_users`'taki
   bir hesap) → karşılama ekranında **Test Ekranına Gir**
4. Health Check → 4 düğüm yeşil
5. Marka/Model/Firmware seç → FULL Servis Başlat
6. Test bitince: loglar FTP'ye, sonuçlar `copy_` tablolarına yazılır; Telegram + mail
   bildirimi gider (secrets.json varsa)

---

## 6. Güncelleme (git pull)

Her makinede:
```bash
git pull
# Sonra agent/sunucuyu yeniden başlat
```

---

## 7. Emanet İade — Statik IP Kaldır

### Linux
```bash
sudo systemctl stop fullservice-server 2>/dev/null
sudo systemctl disable fullservice-server 2>/dev/null
sudo rm -f /etc/systemd/system/fullservice-server.service
sudo systemctl daemon-reload

sudo nmcli con show   # bağlantı adını bul
sudo nmcli con mod "Wired connection 1" ipv4.method auto ipv4.addresses "" ipv4.gateway "" ipv4.dns ""
sudo nmcli con up "Wired connection 1"
# Doğrula: ifconfig eth0  → DHCP adresi (192.168.1.10 OLMAMALI)
```

### Mac Cable
```bash
sudo networksetup -setdhcp "AX88179A"
networksetup -getinfo "AX88179A"   # "Using DHCP" yazmalı
```

### Mac WiFi
```bash
sudo networksetup -setdhcp "Wi-Fi"
networksetup -getinfo "Wi-Fi"   # "Using DHCP" yazmalı
```

### Windows (Yönetici PowerShell)
```powershell
Set-NetIPInterface -InterfaceAlias "Wi-Fi" -Dhcp Enabled
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ResetServerAddresses
Restart-NetAdapter -Name "Wi-Fi"
Unregister-ScheduledTask -TaskName FullServiceAgent_win_wifi -Confirm:$false -ErrorAction SilentlyContinue
# Doğrula: Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"  → DHCP
```

---

## Hızlı sorun giderme

| Belirti | Çözüm |
|---------|-------|
| Düğüm offline | O makinede agent çalışıyor mu? `ping 192.168.1.10` gidiyor mu? |
| iperf kırmızı | mac_cable'da agent çalışıyor mu? iperf3 kurulu mu? |
| torrent hatası | qBittorrent açık mı? Web UI: port 8080, admin/Admin123. qBittorrent 5.x: "Bypass auth" kapalı olmalı |
| Marka/Model boş | `certs/` eksik veya `chmod 600 certs/client.key` yapılmamış |
| Mac terminal açılmıyor | Normal — boot servisi varsa masaüstü yok. Elle başlatınca açılır |
| Windows PS script hatası | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Giriş yapılamıyor | DB kapalıysa bile `cpeteam`/`cpeteam` her zaman çalışır; rota 405 verirse `run_server.py`'yi yeniden başlat |
| Telegram/mail gelmiyor | Sunucuda `secrets.json` var mı? `FS_NOTIFY_DISABLE=1` ayarlı olmasın |
| FTP'ye yüklenmiyor | `certs/` var mı? `FS_FTP_DISABLE=1` ayarlı olmasın |
