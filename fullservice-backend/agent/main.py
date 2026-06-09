"""
FULL Servis Agent — Mac/Windows client makinelerinde çalışan hafif uygulama.

Görevi:
  • Açılışta sunucuya kayıt olur ve periyodik heartbeat gönderir.
  • Sunucudan /start komutu alınca bu düğüme atanan testleri yerelde koşar.
  • /stop ile testleri durdurur.
  • İlerlemeyi ve logları sunucuya iletir (TestExecutor üzerinden).

Çalıştırma (proje kökünden):
  FS_NODE_ID=mac_cable FS_SERVER_URL=http://192.168.1.10:8770 python -m agent.main
  veya: python run_agent.py mac_cable
"""
import os
import sys
import platform
import socket
import threading
import time

# UTF-8 olmayan konsollarda (özellikle Windows agent) print()'in çökmemesi için — GRK ile aynı
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Proje kökünü import yoluna ekle (common'a erişim için)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
import requests
from fastapi import FastAPI

from common.config import load_config, detect_lan_ip
from common.protocol import StartCommand
from agent.test_executor import TestExecutor

CONFIG = load_config()
_srv = CONFIG.get("server", {})

NODE_ID    = os.environ.get("FS_NODE_ID", "mac_cable")
SERVER_URL = os.environ.get("FS_SERVER_URL", f"http://{_srv.get('lan_ip', '127.0.0.1')}:{_srv.get('port', 8770)}")
AGENT_PORT = int(os.environ.get("FS_AGENT_PORT", CONFIG.get("agent_port", 8771)))
LAN_IP     = detect_lan_ip()

executor = TestExecutor(NODE_ID, SERVER_URL)
app = FastAPI(title=f"FULL Servis Agent [{NODE_ID}]", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "node_id": NODE_ID}


@app.post("/start")
def start(cmd: StartCommand):
    """Sunucudan gelen başlatma komutu — atanan testleri başlatır."""
    print(f"[AGENT:{NODE_ID}] START session={cmd.session_id} tests={cmd.tests}")
    executor.start(cmd)
    return {"status": "started", "node_id": NODE_ID, "tests": cmd.tests}


@app.post("/stop")
def stop():
    """Çalışan testleri durdurur."""
    print(f"[AGENT:{NODE_ID}] STOP")
    executor.stop()
    return {"status": "stopped", "node_id": NODE_ID}


def _register_loop():
    """Sunucuya kayıt + heartbeat (10 sn'de bir). Sunucu erişilemezse sessizce yeniden dener."""
    payload = {
        "node_id": NODE_ID,
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "ip": LAN_IP,
        "agent_port": AGENT_PORT,
    }
    first = True
    while True:
        try:
            requests.post(f"{SERVER_URL}/api/register", json=payload, timeout=3)
            if first:
                print(f"[AGENT:{NODE_ID}] Sunucuya kayit olundu → {SERVER_URL}")
                first = False
        except Exception:
            if first:
                print(f"[AGENT:{NODE_ID}] Sunucuya ulasilamadi ({SERVER_URL}), tekrar denenecek...")
        time.sleep(10)


@app.on_event("startup")
def _on_startup():
    threading.Thread(target=_register_loop, daemon=True).start()


if __name__ == "__main__":
    print(f"[AGENT] node_id={NODE_ID}  port={AGENT_PORT}  server={SERVER_URL}  lan_ip={LAN_IP}")
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
