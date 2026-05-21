"""
Agent'ı başlatan kısa yol (Mac/Windows client).

    python run_agent.py <node_id> [server_url]

Örnek:
    python run_agent.py mac_cable
    python run_agent.py win_wifi http://192.168.1.10:8770

node_id config.json'daki bir düğüm id'si olmalı (mac_cable / win_wifi / mac_wifi).
"""
import os
import sys

if len(sys.argv) < 2:
    print("Kullanim: python run_agent.py <node_id> [server_url]")
    print("  node_id: mac_cable | win_wifi | mac_wifi")
    sys.exit(1)

os.environ["FS_NODE_ID"] = sys.argv[1]
if len(sys.argv) >= 3:
    os.environ["FS_SERVER_URL"] = sys.argv[2]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from agent.main import app, AGENT_PORT, NODE_ID, SERVER_URL, LAN_IP

if __name__ == "__main__":
    print(f"[AGENT] node_id={NODE_ID} port={AGENT_PORT} server={SERVER_URL} lan_ip={LAN_IP}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
