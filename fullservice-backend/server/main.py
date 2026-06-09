"""
FULL Servis Sunucu — Linux orkestratör + dashboard host.

Endpoint'ler:
  GET  /health                  Sağlık kontrolü
  POST /api/register            Agent kaydı / heartbeat
  POST /api/progress            Agent ilerleme bildirimi
  POST /api/logs/upload         Agent log dosyası yükleme (multipart)
  GET  /api/state               Tüm düğümlerin birleşik durumu (dashboard polling)
  POST /api/session/start       FULL Servis testini başlat (tüm düğümlere fan-out)
  POST /api/session/stop        Testi durdur
  GET  /                        Dashboard (statik, build gerektirmez)

Çalıştırma (proje kökünden):  python -m server.main   veya   python run_server.py
"""
import os
import sys

# UTF-8 olmayan konsollarda (özellikle Windows) print()'in çökmemesi için — GRK ile aynı
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Proje kökünü import yoluna ekle (common'a erişim için)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from common.config import load_config, DASHBOARD_DIR
from common.protocol import RegisterRequest, ProgressUpdate
from server.orchestrator import Orchestrator
from server import log_collector

CONFIG = load_config()
orch = Orchestrator(CONFIG)

app = FastAPI(title="FULL Servis Sunucu", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


class SessionStartRequest(BaseModel):
    """Dashboard'dan opsiyonel override'lar (boş bırakılırsa config.json varsayılanları)."""
    modem_ip: Optional[str] = None
    internet_ip: Optional[str] = None
    youtube_link: Optional[str] = None
    duration: Optional[int] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/register")
def register(req: RegisterRequest):
    orch.register(req.dict() if hasattr(req, "dict") else req.model_dump())
    return {"status": "registered", "node_id": req.node_id}


@app.post("/api/progress")
def progress(upd: ProgressUpdate):
    orch.update_progress(upd.node_id, upd.task, upd.progress, upd.status, upd.message)
    return {"status": "ok"}


@app.post("/api/logs/upload")
def upload_log(node_id: str = Form(...), session_id: str = Form(...), file: UploadFile = File(...)):
    dest = log_collector.save_upload(node_id, session_id, file.filename, file.file)
    return {"status": "saved", "path": os.path.basename(dest)}


@app.get("/api/state")
def state():
    return orch.get_state()


@app.post("/api/session/start")
def session_start(req: SessionStartRequest):
    overrides = req.dict() if hasattr(req, "dict") else req.model_dump()
    overrides = {k: v for k, v in overrides.items() if v is not None}
    result = orch.start_session(overrides)
    return result


@app.post("/api/session/stop")
def session_stop():
    return orch.stop_session()


# ── Dashboard (statik) ───────────────────────────────────────
# API rotaları yukarıda tanımlandı; en sona static mount eklenir ki "/" altındaki
# her şey dashboard'a düşsün ama /api ve /health gölgelenmesin.
if os.path.isdir(DASHBOARD_DIR):
    app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")
else:
    @app.get("/")
    def _no_dashboard():
        return JSONResponse({"detail": f"dashboard/ bulunamadi: {DASHBOARD_DIR}"}, status_code=404)


if __name__ == "__main__":
    host = CONFIG.get("server", {}).get("host", "0.0.0.0")
    port = int(CONFIG.get("server", {}).get("port", 8770))
    print(f"[SERVER] http://{orch.server_lan_ip}:{port}  (dashboard + API)")
    uvicorn.run(app, host=host, port=port)
