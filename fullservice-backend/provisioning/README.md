# Provisioning — Statik IP + Boot Listener Kurulumu

Bu klasör, FULL Servis düğümlerini saha/lab kurulumuna hazırlayan script'leri içerir:

1. **Statik IP atama** — MAC (kablo), MAC (Wi-Fi), Windows (Wi-Fi) ve Linux sunucu.
2. **Listener'ı boot'ta başlatma** — agent (listener) makine açılır açılmaz kalkar;
   sunucudan gelen "Başlat" komutuyla testleri (executer/runner) ayağa kaldırır.

> Tüm IP/arayüz değerleri `fullservice-backend/config.json` içindeki **`network`**
> bölümünden okunur. Önce orayı kendi LAN şemanıza göre düzenleyin:
>
> ```json
> "network": {
>   "subnet_mask": "255.255.255.0",
>   "gateway": "192.168.1.1",
>   "dns": ["8.8.8.8", "8.8.4.4"],
>   "assignments": {
>     "server":    { "ip": "192.168.1.10", "interface": "eth0" },
>     "mac_cable": { "ip": "192.168.1.11", "interface": "Ethernet" },
>     "win_wifi":  { "ip": "192.168.1.13", "interface": "Wi-Fi" },
>     "mac_wifi":  { "ip": "192.168.1.14", "interface": "Wi-Fi" }
>   }
> }
> ```
>
> `interface` her platformda o makinedeki ağ arayüzü/servis adıdır:
> - **macOS**: `networksetup -listallnetworkservices` (or. `Ethernet`, `Wi-Fi`)
> - **Windows**: `Get-NetAdapter | Select Name` (or. `Wi-Fi`, `Ethernet`)
> - **Linux**: `ip link` (or. `eth0`, `ens33`)

---

## 1) Statik IP

| Platform | Komut |
|----------|-------|
| macOS    | `sudo provisioning/macos/set-static-ip.sh mac_cable` |
| Windows  | `provisioning\windows\set-static-ip.ps1 -NodeId win_wifi` (Yönetici PS) |
| Linux    | `sudo provisioning/linux/set-static-ip.sh server` |

---

## 2) Listener'ı boot'ta otomatik başlatma

Listener = mevcut **agent** (FastAPI). Varsayılan port **7531** (`config.json:agent_port`).

### macOS (launchd)
```bash
provisioning/macos/install-agent-launchd.sh mac_cable http://192.168.1.10:8770 7531
```
> Tek Mac'te iki düğüm (mac_cable + mac_wifi) koşacaksa **farklı port** verip
> script'i iki kez çalıştırın (or. mac_cable→7531, mac_wifi→7532).

### Windows (Görev Zamanlayıcı)
```powershell
# Yönetici PowerShell
.\provisioning\windows\install-agent-task.ps1 -NodeId win_wifi -ServerUrl http://192.168.1.10:8770 -Port 7531
```

### Linux sunucu (systemd)
```bash
sudo provisioning/linux/install-server-systemd.sh
```

---

## Doğrulama
- Statik IP: `ping <atanan_ip>` başka makineden çalışmalı.
- Listener: makineyi yeniden başlatın → sunucu dashboard'ında düğüm **online**
  görünmeli ve sağ paneldeki **Health-Check** o düğüm için **yeşil** yanmalı.
