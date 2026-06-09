"""
Sunucuyu başlatan kısa yol (Linux orkestratör).

    python run_server.py

Dashboard + API config.json'daki server.port üzerinden yayınlanır.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from server.main import app, CONFIG, orch

if __name__ == "__main__":
    host = CONFIG.get("server", {}).get("host", "0.0.0.0")
    port = int(CONFIG.get("server", {}).get("port", 8770))
    print(f"[SERVER] Dashboard + API → http://{orch.server_lan_ip}:{port}")
    uvicorn.run(app, host=host, port=port)
