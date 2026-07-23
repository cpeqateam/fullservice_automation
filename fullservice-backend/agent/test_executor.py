"""
Agent test yürütücüsü — sunucudan gelen StartCommand'i alır, bu düğüme atanan
testleri paralel thread'lerde yerelde koşar, ilerlemeyi sunucuya iter ve biten
testin loglarını sunucuya yükler.

Tek bir ortak durdurma bayrağı (Event) tüm testleri kapsar; sunucudan /stop
gelince hepsi temiz çıkar. Sunucuya erişilemese bile testler yerelde çalışmaya
devam eder (push/upload best-effort'tür, hata yutulur).
"""
from __future__ import annotations

import os
import threading

import requests

from common.config import LOGS_DIR, node_log_folder
from common.protocol import StartCommand, TestParams, TestStatus
from common.runners.base import RunContext
from common.runners.registry import get_runner


class TestExecutor:
    """Bu agent'ta testleri ayrı thread'lerde koşan yürütücü. Her testin ilerlemesini
    (`/api/progress`), nihai özetini (`/api/result`) ve log dosyalarını (`/api/logs/upload`)
    sunucuya iletir."""

    def __init__(self, node_id: str, server_url: str):
        """node_id ve sunucu adresiyle yürütücüyü kurar (durdurma bayrağı + thread listesi)."""
        self.node_id = node_id
        # Log dosya adına girecek client adı (MAC_ETH / MAC_WIFI / WIN_WIFI)
        self.node_name = node_log_folder(node_id)
        self.server_url = server_url.rstrip("/")
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self.session_id: str | None = None

    # ── sunucudan komut ──────────────────────────────────────
    def start(self, cmd: StartCommand):
        """Atanan testleri başlatır (zaten çalışıyorsa önce durdurur)."""
        self.stop()
        self._stop = threading.Event()
        self.session_id = cmd.session_id
        self._threads = []

        for test in cmd.tests:
            runner = get_runner(test)
            if runner is None:
                self._push(test, 100.0, TestStatus.ERROR.value, "Bilinmeyen test tipi")
                continue
            t = threading.Thread(target=self._run_one, args=(test, runner, cmd.params), daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        """Çalışan tüm testlere durma sinyali gönderir."""
        self._stop.set()

    # ── tek bir testin yaşam döngüsü ─────────────────────────
    def _run_one(self, test: str, runner, params: TestParams):
        """Tek bir testi koşar: RunContext'i kurar (progress/stop/result geri çağrıları),
        runner'ı çalıştırır, hata olursa error bildirir, bitince logları sunucuya yükler."""
        session_dir = os.path.join(LOGS_DIR, self.session_id or "adhoc")
        ctx = RunContext(
            node_id=self.node_id,
            session_id=self.session_id or "adhoc",
            log_dir=session_dir,
            progress=lambda p, s, m: self._push(test, p, s, m),
            stop=self._stop,
            result=lambda kind, stats, _t=test: self._report_result(_t, kind, stats),
            node_name=self.node_name,
        )
        logs: list[str] = []
        try:
            logs = runner(params, ctx) or []
        except Exception as e:
            self._push(test, 100.0, TestStatus.ERROR.value, f"Çalıştırıcı hatası: {e}")
        # Test bitince üretilen logları sunucuya yükle
        for fp in logs:
            self._upload(fp)

    # ── sunucuya bildirim ────────────────────────────────────
    def _push(self, task: str, progress: float, status: str, message: str):
        """Bir testin anlık ilerleme/durumunu sunucuya (`/api/progress`) iletir (best-effort)."""
        payload = {
            "node_id": self.node_id,
            "session_id": self.session_id or "",
            "task": task,
            "progress": round(float(progress), 1),
            "status": status,
            "message": message,
        }
        try:
            requests.post(f"{self.server_url}/api/progress", json=payload, timeout=3)
        except Exception:
            pass  # sunucuya ulaşılamasa da test devam etsin

    def _report_result(self, task: str, kind: str, stats: dict):
        """Test bitince nihai özeti sunucuya iletir (sunucu DB'ye yazar)."""
        payload = {
            "node_id": self.node_id,
            "session_id": self.session_id or "",
            "task": task,
            "kind": kind,
            "stats": stats,
        }
        try:
            requests.post(f"{self.server_url}/api/result", json=payload, timeout=5)
        except Exception:
            pass  # sunucuya ulaşılamasa da test devam etsin

    def _upload(self, file_path: str):
        """Üretilen bir log dosyasını sunucuya (`/api/logs/upload`, multipart) yükler."""
        if not file_path or not os.path.exists(file_path):
            return
        try:
            with open(file_path, "rb") as f:
                requests.post(
                    f"{self.server_url}/api/logs/upload",
                    data={"node_id": self.node_id, "session_id": self.session_id or ""},
                    files={"file": (os.path.basename(file_path), f)},
                    timeout=30,
                )
        except Exception as e:
            print(f"[AGENT] Log yükleme hatası ({file_path}): {e}")
