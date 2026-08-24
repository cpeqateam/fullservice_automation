Her makinede önce:


cd fullservice_automation && git pull
Linux (server, eth0):


cd fullservice-backend && source venv/bin/activate
pip install -r requirements.txt
ifconfig eth0   # 192.168.1.10 değilse:
sudo bash provisioning/linux/set-static-ip.sh server
python3 run_server.py
Mac Cable (mac_cable, AX88179A):


cd fullservice-backend && source venv/bin/activate
pip install -r requirements.txt
networksetup -getinfo "AX88179A"   # 192.168.1.11 değilse:
sudo networksetup -setmanual "AX88179A" 192.168.1.11 255.255.255.0 192.168.1.1
python run_agent.py mac_cable http://192.168.1.10:8770
Mac WiFi (mac_wifi, Wi-Fi):


cd fullservice-backend && source venv/bin/activate
pip install -r requirements.txt
networksetup -getinfo "Wi-Fi"   # 192.168.1.14 değilse:
sudo networksetup -setmanual "Wi-Fi" 192.168.1.14 255.255.255.0 192.168.1.1
python run_agent.py mac_wifi http://192.168.1.10:8770
Windows (win_wifi, Wi-Fi):


cd fullservice-backend; venv\Scripts\activate
pip install -r requirements.txt
Get-NetIPConfiguration -InterfaceAlias "Wi-Fi"   # 192.168.1.13 değilse:
.\provisioning\windows\set-static-ip.ps1 -NodeId win_wifi
$env:FS_NODE_ID="win_wifi"; $env:FS_SERVER_URL="http://192.168.1.10:8770"
python run_agent.py
Sonra: http://192.168.1.10:8770 → giriş (cpeteam/cpeteam) → Health Check 4 yeşil → Test Ekranına Gir.