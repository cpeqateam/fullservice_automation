"""
Orkestratör — FULL Servis'in beyni (sunucuda tek örnek).

Sorumlulukları:
  • Düğüm kaydı (registry): agent'lar kendini buraya tanıtır, heartbeat ile
    online/offline takip edilir.
  • Merkezi ilerleme (aggregator): GRK'daki tek-makinelik progress_manager'ın
    çok-düğümlü hali — her düğümün her testinin anlık durumu burada toplanır.
  • Komut dağıtımı (fan-out): "başlat/durdur" komutunu tüm online agent'lara
    HTTP ile gönderir; sunucunun kendi rollerini ise yerelde (in-process) koşar.
  • Durum sunumu: dashboard'ın 1 sn'de bir çektiği birleşik state'i üretir.

Tüm state bellekte tutulur ve _lock ile korunur (4 düğüm × ~6 test, düşük hacim).
"""
import os
import threading
from datetime import datetime

import requests

from common.config import LOGS_DIR, detect_lan_ip
from common.protocol import TestParams, TestStatus, TEST_LABELS
from common.runners.base import RunContext
from common.runners.registry import get_runner
from server import iperf_server


class Orchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.defaults = config.get("defaults", {})
        self.server_lan_ip = config.get("server", {}).get("lan_ip") or detect_lan_ip()
        self._lock = threading.RLock()

        # node_id -> runtime durum
        self.nodes: dict[str, dict] = {}
        for n in config.get("nodes", []):
            is_server = bool(n.get("is_server"))
            self.nodes[n["id"]] = {
                "node_id": n["id"],
                "label": n.get("label", n["id"]),
                "conn": n.get("conn", ""),
                "is_server": is_server,
                "roles": list(n.get("roles", [])),
                "ip": self.server_lan_ip if is_server else None,
                "agent_port": None,
                "platform": "Linux" if is_server else None,
                "online": is_server,           # sunucu kendisi her zaman "online"
                "last_seen": None,
                "tests": {r: self._blank_test() for r in n.get("roles", [])},
            }

        self.session = {"session_id": None, "running": False,
                        "started_at": None, "ended_at": None, "params": {}}

        # Sunucu-yerel testler için durdurma bayrağı + thread'ler
        self._server_stop = threading.Event()
        self._server_threads: list[threading.Thread] = []

    @staticmethod
    def _blank_test() -> dict:
        return {"progress": 0.0, "status": TestStatus.IDLE.value, "message": "", "updated": None}

    # ── Kayıt / heartbeat ────────────────────────────────────
    def register(self, req: dict):
        """Agent kaydı/heartbeat. Bilinmeyen node_id gelirse dinamik olarak eklenir."""
        with self._lock:
            nid = req.get("node_id")
            node = self.nodes.get(nid)
            if node is None:
                # config'de tanımsız bir agent — yine de kabul et, rolsüz ekle
                node = {
                    "node_id": nid, "label": nid, "conn": "", "is_server": False,
                    "roles": [], "tests": {}, "online": True,
                }
                self.nodes[nid] = node
            node["ip"] = req.get("ip")
            node["agent_port"] = req.get("agent_port")
            node["platform"] = req.get("platform")
            node["online"] = True
            node["last_seen"] = datetime.now().isoformat(timespec="seconds")

    # ── İlerleme güncelleme (agent push + sunucu-yerel) ──────
    def update_progress(self, node_id: str, task: str, progress: float,
                        status: str, message: str = ""):
        with self._lock:
            node = self.nodes.get(node_id)
            if not node:
                return
            if task not in node["tests"]:
                node["tests"][task] = self._blank_test()
            t = node["tests"][task]
            t["progress"] = round(float(progress), 1)
            t["status"] = status
            t["message"] = message
            t["updated"] = datetime.now().isoformat(timespec="seconds")

    # ── Dashboard durum çıktısı ──────────────────────────────
    def get_state(self) -> dict:
        with self._lock:
            return {
                "session": dict(self.session),
                "test_labels": TEST_LABELS,
                "server_lan_ip": self.server_lan_ip,
                "nodes": [self._node_view(n) for n in self.nodes.values()],
            }

    def _node_view(self, node: dict) -> dict:
        # Heartbeat 30 sn'den eskiyse offline say (sunucu hariç)
        online = node.get("online", False)
        if not node.get("is_server") and node.get("last_seen"):
            try:
                age = (datetime.now() - datetime.fromisoformat(node["last_seen"])).total_seconds()
                online = age < 30
            except Exception:
                pass
        return {
            "node_id": node["node_id"],
            "label": node["label"],
            "conn": node["conn"],
            "is_server": node.get("is_server", False),
            "platform": node.get("platform"),
            "ip": node.get("ip"),
            "agent_port": node.get("agent_port"),
            "online": online,
            "last_seen": node.get("last_seen"),
            "roles": node.get("roles", []),
            "tests": node.get("tests", {}),
        }

    # ── Oturum başlat / durdur ───────────────────────────────
    def start_session(self, overrides: dict | None = None) -> dict:
        overrides = overrides or {}
        with self._lock:
            session_id = datetime.now().strftime("FS_%Y%m%d_%H%M%S")
            params = TestParams(
                modem_ip=overrides.get("modem_ip") or self.defaults.get("modem_ip", "192.168.1.1"),
                internet_ip=overrides.get("internet_ip") or self.defaults.get("internet_ip", "8.8.8.8"),
                youtube_link=overrides.get("youtube_link") or self.defaults.get("youtube_link", ""),
                iperf_server=self.server_lan_ip,
                iperf_port=int(self.defaults.get("iperf_port", 5201)),
                iperf_parallel=int(self.defaults.get("iperf_parallel", 4)),
                duration=int(overrides.get("duration") or self.defaults.get("duration", 60)),
            )
            self.session = {
                "session_id": session_id,
                "running": True,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "ended_at": None,
                "params": params.dict() if hasattr(params, "dict") else params.model_dump(),
            }
            # Tüm test durumlarını sıfırla
            for node in self.nodes.values():
                for r in node["roles"]:
                    node["tests"][r] = self._blank_test()

            # iperf rolü olan düğüm var mı? Varsa server'ı kaldır
            needs_iperf = any("iperf" in n["roles"] for n in self.nodes.values())
            online_nodes = [self._node_view(n) for n in self.nodes.values()]

        if needs_iperf:
            iperf_server.ensure_running(params.iperf_port)

        # Fan-out (lock dışında — ağ çağrıları bloke etmesin). Agent'lara komut
        # PARALEL gönderilir; kapalı bir client diğerlerini bekletmesin.
        dispatched, skipped = [], []
        self._server_stop = threading.Event()
        self._server_threads = []
        agent_threads: list[threading.Thread] = []
        results: dict[str, bool] = {}

        for nv in online_nodes:
            roles = nv["roles"]
            if not roles:
                continue
            if nv["is_server"]:
                self._run_server_local(session_id, roles, params)
                dispatched.append(nv["node_id"])
            elif nv["online"] and nv["ip"] and nv["agent_port"]:
                def _dispatch(n=nv):
                    results[n["node_id"]] = self._send_start(n, session_id, n["roles"], params)
                th = threading.Thread(target=_dispatch, daemon=True)
                th.start()
                agent_threads.append(th)
            else:
                skipped.append(nv["node_id"])

        for th in agent_threads:
            th.join(timeout=6)
        for nid, ok in results.items():
            (dispatched if ok else skipped).append(nid)

        return {"session_id": session_id, "dispatched": dispatched, "skipped": skipped}

    def _send_start(self, nv: dict, session_id: str, roles: list, params: TestParams) -> bool:
        url = f"http://{nv['ip']}:{nv['agent_port']}/start"
        payload = {
            "session_id": session_id,
            "tests": roles,
            "params": params.dict() if hasattr(params, "dict") else params.model_dump(),
        }
        # Yalnızca ağ çağrısını try içine al — print/log hatası dispatch'i bozmasın.
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[ORCH] {nv['node_id']} agent'ina ulasilamadi: {e}")
            self.update_progress(nv["node_id"], roles[0] if roles else "?", 0.0,
                                 TestStatus.ERROR.value, "Agent'a ulasilamadi")
            return False
        print(f"[ORCH] START gonderildi -> {nv['node_id']} ({url})")
        return True

    def _run_server_local(self, session_id: str, roles: list, params: TestParams):
        """Sunucunun kendi rollerini in-process thread'lerde koşar."""
        log_dir = os.path.join(LOGS_DIR, session_id, "server")
        for test in roles:
            runner = get_runner(test)
            if runner is None:
                self.update_progress("server", test, 100.0, TestStatus.ERROR.value, "Bilinmeyen test")
                continue

            def _worker(t=test, fn=runner):
                ctx = RunContext(
                    node_id="server", session_id=session_id, log_dir=log_dir,
                    progress=lambda p, s, m, _t=t: self.update_progress("server", _t, p, s, m),
                    stop=self._server_stop,
                )
                try:
                    fn(params, ctx)
                except Exception as e:
                    self.update_progress("server", t, 100.0, TestStatus.ERROR.value, f"Hata: {e}")

            th = threading.Thread(target=_worker, daemon=True)
            th.start()
            self._server_threads.append(th)

    def stop_session(self) -> dict:
        with self._lock:
            self.session["running"] = False
            self.session["ended_at"] = datetime.now().isoformat(timespec="seconds")
            targets = [self._node_view(n) for n in self.nodes.values() if not n.get("is_server")]

        # Sunucu-yerel testleri durdur
        self._server_stop.set()
        # Agent'lara /stop gönder
        for nv in targets:
            if nv["online"] and nv["ip"] and nv["agent_port"]:
                try:
                    requests.post(f"http://{nv['ip']}:{nv['agent_port']}/stop", timeout=5)
                except Exception:
                    pass
        return {"status": "stopped"}
