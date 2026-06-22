"""
Agent'ı başlatan kısa yol (Mac/Windows client).

    python run_agent.py <node_id> [server_url] [port]

Örnek:
    python run_agent.py mac_cable
    python run_agent.py win_wifi http://192.168.1.10:8770
    # Tek makinede iki agent — farklı portlar:
    python run_agent.py mac_cable http://127.0.0.1:8770 8771
    python run_agent.py mac_wifi  http://127.0.0.1:8770 8772

node_id config.json'daki bir düğüm id'si olmalı (mac_cable / win_wifi / mac_wifi).
[port] verilmezse config.json'daki agent_port (varsayılan 8771) kullanılır.
Aynı makinede birden fazla agent çalıştıracaksan her birine FARKLI port ver.
"""
import os
import sys

if len(sys.argv) < 2: # node_id gerekli
    print("Kullanim: python run_agent.py <node_id> [server_url] [port]")
    print("  node_id: mac_cable | win_wifi | mac_wifi")
    sys.exit(1)

os.environ["FS_NODE_ID"] = sys.argv[1] # node_id'yi ortam değişkeni olarak ayarla
if len(sys.argv) >= 3:
    os.environ["FS_SERVER_URL"] = sys.argv[2] # server_url verilmişse ortam değişkeni olarak ayarla (örn. http://
if len(sys.argv) >= 4:
    os.environ["FS_AGENT_PORT"] = sys.argv[3] # port verilmişse ortam değişkeni olarak ayarla (örn. 8771)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # agent klasöründeki modülleri bulabilmesi için çalışma dizinini sys.path'e ekle

import uvicorn
from agent.main import app, AGENT_PORT, NODE_ID, SERVER_URL, LAN_IP

if __name__ == "__main__":
    print(f"[AGENT] node_id={NODE_ID} port={AGENT_PORT} server={SERVER_URL} lan_ip={LAN_IP}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
