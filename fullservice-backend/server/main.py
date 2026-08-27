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

from typing import List, Optional

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from common.config import load_config, DASHBOARD_DIR, LOGS_DIR
from common.protocol import RegisterRequest, ProgressUpdate, ResultReport
from common import firmware_db
from server import firmware_fetch_service


# ── app.log Tee: tüm print/stderr çıktısını logs/app.log'a da yaz ──────────────
# error_log (log_capture) test aralığını byte-offset ile bu dosyadan dilimler.
class _Tee:
    """stdout/stderr'i hem konsola hem de logs/app.log'a aynalayan sarmalayıcı
    (error_log, testin app.log dilimini byte-offset ile bu dosyadan alır)."""

    def __init__(self, stream, fh):
        """Asıl akışı (stream) ve app.log dosya tanıtıcısını (fh) sarar."""
        self._stream, self._fh = stream, fh
    def write(self, data):
        """Veriyi hem asıl akışa hem app.log'a yazar (hatayı yutar)."""
        try: self._stream.write(data)
        except Exception: pass
        try: self._fh.write(data); self._fh.flush()
        except Exception: pass
    def flush(self):
        """Asıl akışı boşaltır."""
        try: self._stream.flush()
        except Exception: pass
    def __getattr__(self, name):
        """Sarmalanmayan öznitelikleri asıl akışa devreder."""
        return getattr(self._stream, name)

try:
    _app_log_fh = open(os.path.join(LOGS_DIR, "app.log"), "a", encoding="utf-8", errors="replace")
    sys.stdout = _Tee(sys.stdout, _app_log_fh)
    sys.stderr = _Tee(sys.stderr, _app_log_fh)
except Exception as _e:
    print(f"[MAIN] app.log Tee kurulamadi: {_e}")
from server.orchestrator import Orchestrator
from server import log_collector
from server import auth_service
import time

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
    iperf_parallel: Optional[int] = None
    iperf_port: Optional[int] = None
    iperf_reverse: Optional[bool] = None
    # Kullanicinin arayuzden sectigi testler (None = hepsi). Secilmeyenler hic
    # baslatilmaz, panelde "ATLANDI" olarak gri durur.
    selected_tests: Optional[List[str]] = None
    # Cihaz bilgisi (Günlük Rutin Kontrol formundan) — log/dashboard için
    brand: Optional[str] = None
    model: Optional[str] = None
    firmware: Optional[str] = None
    # Bildirim mesajında gösterilecek kullanıcı (giriş yapan)
    user_name: Optional[str] = None
    user_surname: Optional[str] = None


@app.get("/health")
def health():
    """Sunucu ayakta mı — basit sağlık kontrolü."""
    return {"status": "ok"}


class LoginRequest(BaseModel):
    """Login isteği gövdesi: kullanıcı adı + şifre."""
    username: str
    password: str


@app.post("/api/login")
def login(req: LoginRequest):
    """Kullanıcı girişi. grk_users tablosundan doğrular; DB kapalı olsa bile
    varsayılan cpeteam/cpeteam hesabı her zaman geçerli."""
    user = auth_service.login(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı.")
    return {"token": f"token-{user['user_id']}-{int(time.time())}", "user": user}


@app.post("/api/register")
def register(req: RegisterRequest):
    """Agent kaydı/heartbeat — düğümü online işaretler."""
    orch.register(req.dict() if hasattr(req, "dict") else req.model_dump())
    return {"status": "registered", "node_id": req.node_id}


@app.post("/api/progress")
def progress(upd: ProgressUpdate):
    """Agent'tan gelen anlık test ilerlemesini orchestrator'a iletir."""
    orch.update_progress(upd.node_id, upd.task, upd.progress, upd.status, upd.message)
    return {"status": "ok"}


@app.post("/api/result")
def result_report(rep: ResultReport):
    """Agent'tan gelen nihai test özetini DB'ye (copy_ tablolar) yaz."""
    orch.record_result(rep.node_id, rep.kind, rep.stats, rep.ftp_file_path)
    return {"status": "ok"}


@app.post("/api/logs/upload")
def upload_log(node_id: str = Form(...), session_id: str = Form(...), file: UploadFile = File(...)):
    """Agent'ın yüklediği log dosyasını logs/ altına yazar ve arka planda FTP'ye iletir."""
    dest = log_collector.save_upload(node_id, session_id, file.filename, file.file)
    # Sunucuya inen log'u doğru FTP klasör yapısına (arka planda) yükle
    orch.upload_log_to_ftp(node_id, dest)
    return {"status": "saved", "path": os.path.basename(dest)}


@app.get("/api/state")
def state():
    """Dashboard'ın 1 sn'de bir çektiği birleşik durum (düğümler + oturum + ilerleme)."""
    return orch.get_state()


def _fmt_uptime(mins: int) -> str:
    """Dakikayı okunur süreye çevirir: 52 → '52 dakika', 75 → '1 sa 15 dk'."""
    if mins < 60:
        return f"{mins} dakika"
    return f"{mins // 60} sa {mins % 60} dk"


@app.post("/api/session/start")
def session_start(req: SessionStartRequest):
    """FULL Servis testini başlatır — override'ları alıp tüm düğümlere fan-out eder.
    ÖNCE uptime kontrolü: bir cihaz limitten uzun süredir açıksa (kırmızı) 409 döner,
    test başlatılmaz; kullanıcı o cihazı yeniden başlatmalı."""
    blocked = orch.check_uptime()
    if blocked:
        cihazlar = "; ".join(f"{b['label']} ({_fmt_uptime(b['minutes'])}dır açık)" for b in blocked)
        raise HTTPException(
            status_code=409,
            detail=(
                f"Test başlatılamaz. Şu cihaz(lar) {orch.uptime_limit_min} dakikadan uzun "
                f"süredir açık ve yeniden başlatılması gerekiyor: {cihazlar}. "
                f"İlgili cihaz(lar)ı kapatıp uygulamaya yeniden çift tıklayın; sağ paneldeki "
                f"tüm cihazlar yeşil olunca testi başlatabilirsiniz."
            ),
        )
    overrides = req.dict() if hasattr(req, "dict") else req.model_dump()
    overrides = {k: v for k, v in overrides.items() if v is not None}
    result = orch.start_session(overrides)
    return result


@app.post("/api/session/stop")
def session_stop():
    """Çalışan testleri durdurur (durdurma bildirimi tetiklemez)."""
    return orch.stop_session()


@app.post("/api/session/reset")
def session_reset():
    """Her şeyi başa al: testleri durdur, oturumu ve ilerlemeleri sıfırla."""
    return orch.reset_session()


# ── Health-Check (aktif bağlantı kontrolü) ──────────────────
@app.get("/api/health-check")
def health_check():
    """Tüm düğümlerin sunucuya/listener'a anlık erişilebilirliği (kırmızı/yeşil)."""
    return orch.health_check()


# ── Firmware DB (Marka / Model / Firmware combobox'ları) ─────
# DB erişilemezse 503 döner; frontend bunu serbest-metin girişine düşmek için kullanır.
#
# NOT (teşhis): SQLAlchemy'de create_engine() BAĞLANMAZ — bağlantı ilk sorguda
# kurulur. Yani bağlantı hataları açılışta değil, BURADA ortaya çıkar. Hatayı
# yalnızca 503 gövdesine koymak, konsolda/app.log'da hiç iz bırakmadığı için
# "combobox boş ama sebebi görünmüyor" körlüğüne yol açıyordu; bu yüzden asıl
# istisna ayrıca log'a da basılır (error_log'a da böylece girer).
def _firmware_503(e: Exception, ne: str) -> HTTPException:
    """Firmware DB hatasını log'a basar ve 503'e çevirir (tek yerden)."""
    print(f"[FIRMWARE_DB] {ne} alinamadi: {type(e).__name__}: {e}")
    return HTTPException(status_code=503, detail=f"Firmware DB erisilemiyor: {e}")


@app.get("/api/firmware/brands")
def firmware_brands():
    """Marka listesi (DB'den). DB yoksa 503 → frontend serbest-metne düşer."""
    try:
        return firmware_db.get_brands()
    except Exception as e:
        raise _firmware_503(e, "marka listesi")


@app.get("/api/firmware/models/{brand}")
def firmware_models(brand: str):
    """Markaya ait model listesi (DB'den). DB yoksa 503."""
    try:
        return firmware_db.get_models(brand)
    except Exception as e:
        raise _firmware_503(e, f"model listesi ({brand})")


@app.get("/api/firmware/versions/{brand}/{model}")
def firmware_versions(brand: str, model: str):
    """Marka+modele ait firmware sürüm listesi (DB'den). DB yoksa 503."""
    try:
        return firmware_db.get_versions(brand, model)
    except Exception as e:
        raise _firmware_503(e, f"firmware listesi ({brand}/{model})")


class FetchFirmwareRequest(BaseModel):
    """Firmware çekme isteği — marka, model ve modem IP'si."""
    brand: str
    model: str
    modem_ip: Optional[str] = "192.168.1.1"


@app.post("/api/firmware/fetch")
def firmware_fetch(req: FetchFirmwareRequest):
    """Modem arayüzünden firmware'i çeker; tarihi DB'de yoksa `firmware`
    tablosuna ekler. Dashboard'daki "Arayüzden Al" butonu bunu kullanır.

    Hatalar: 404 entegrasyon yok · 502 modeme bağlanılamadı · 503 tarayıcı ·
    500 beklenmedik (mesajlar frontend'de başlık/ikona çevrilir)."""
    return firmware_fetch_service.fetch(req.brand, req.model, req.modem_ip or "192.168.1.1")


# ── Dashboard (statik) ───────────────────────────────────────
# API rotaları yukarıda tanımlandı; en sona static mount eklenir ki "/" altındaki
# her şey dashboard'a düşsün ama /api ve /health gölgelenmesin.
if os.path.isdir(DASHBOARD_DIR):
    app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")
else:
    @app.get("/")
    def _no_dashboard():
        """dist/ derlenmemişse "/" için 404 döner (geliştirmede Vite ayrı portta çalışır)."""
        return JSONResponse({"detail": f"dashboard/ bulunamadi: {DASHBOARD_DIR}"}, status_code=404)


if __name__ == "__main__":
    host = CONFIG.get("server", {}).get("host", "0.0.0.0")
    port = int(CONFIG.get("server", {}).get("port", 8770))
    print(f"[SERVER] http://{orch.server_lan_ip}:{port}  (dashboard + API)")
    uvicorn.run(app, host=host, port=port)
