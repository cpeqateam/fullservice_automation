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
from __future__ import annotations

import os
import threading
from datetime import datetime

import requests

from common.config import LOGS_DIR, detect_lan_ip, node_log_folder
from common.protocol import TestParams, TestStatus, TEST_LABELS
from common.runners.base import RunContext
from common.runners.registry import get_runner
from server import db_service
from server import ftp_service


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
                        "started_at": None, "ended_at": None, "params": {},
                        "db_session_id": None,
                        "device": {"brand": None, "model": None, "firmware": None}}

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

    def _iperf_server_ip(self) -> str:
        """
        iperf client'ın (wifi Mac) bağlanacağı adres = "iperf_server" rolündeki
        (kablolu) Mac'in LAN IP'si. Önce agent kaydından gelen canlı IP kullanılır;
        agent henüz kayıt olmadıysa config.json'daki statik atamaya (network.
        assignments) düşülür. Hiçbiri yoksa boş döner (client anlaşılır hata verir).
        """
        server_node = next(
            (n for n in self.nodes.values() if "iperf_server" in n.get("roles", [])),
            None,
        )
        if not server_node:
            return ""
        if server_node.get("ip"):
            return server_node["ip"]
        assignments = self.config.get("network", {}).get("assignments", {})
        return assignments.get(server_node["node_id"], {}).get("ip", "") or ""

    # ── Oturum başlat / durdur ───────────────────────────────
    def start_session(self, overrides: dict | None = None) -> dict:
        overrides = overrides or {}
        with self._lock:
            session_id = datetime.now().strftime("FS_%Y%m%d_%H%M%S")
            params = TestParams(
                modem_ip=overrides.get("modem_ip") or self.defaults.get("modem_ip", "192.168.1.1"),
                internet_ip=overrides.get("internet_ip") or self.defaults.get("internet_ip", "8.8.8.8"),
                youtube_link=overrides.get("youtube_link") or self.defaults.get("youtube_link", ""),
                # iperf server artık kablolu Mac'te (iperf_server rolü) koşuyor;
                # client (wifi Mac) bu adrese bağlanır.
                iperf_server=self._iperf_server_ip(),
                iperf_port=int(self.defaults.get("iperf_port", 5201)),
                iperf_parallel=int(self.defaults.get("iperf_parallel", 4)),
                torrent_magnet=overrides.get("torrent_magnet") or self.defaults.get("torrent_magnet", ""),
                torrent_recycle_gb=float(self.defaults.get("torrent_recycle_gb", 5)),
                duration=int(overrides.get("duration") or self.defaults.get("duration", 60)),
            )
            self.session = {
                "session_id": session_id,
                "running": True,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "ended_at": None,
                "params": params.dict() if hasattr(params, "dict") else params.model_dump(),
                "db_session_id": None,
                "device": {
                    "brand":    overrides.get("brand"),
                    "model":    overrides.get("model"),
                    "firmware": overrides.get("firmware"),
                },
            }
            # Tüm test durumlarını sıfırla
            for node in self.nodes.values():
                for r in node["roles"]:
                    node["tests"][r] = self._blank_test()

            online_nodes = [self._node_view(n) for n in self.nodes.values()]
            started_at = self.session["started_at"]
            device = dict(self.session["device"])

        # DB: oturum satırını (copy_test_session) oluştur — lock dışında (ağ/DB I/O).
        # Hangi test tipleri var? (has_* bayrakları için tüm düğümlerin rollerinin birleşimi)
        roles_all = {r for n in self.config.get("nodes", []) for r in n.get("roles", [])}
        db_session_id = db_service.create_session(
            device.get("brand"), device.get("model"), device.get("firmware"),
            started_at,
            has_ping=any(r in roles_all for r in ("ping_internet", "ping_modem")),
            has_speedtest="speedtest" in roles_all,
            has_wifi="wifi_track" in roles_all,
        )
        with self._lock:
            self.session["db_session_id"] = db_session_id

        # iperf server'ı artık Linux sunucu değil, "iperf_server" rolündeki kablolu
        # Mac kendi agent'ında koşturur (fan-out ile başlatılır). Sunucu tarafında
        # ayrıca bir iperf3 -s ayağa kaldırmaya gerek yok.

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

    def _iperf_server_node_name(self) -> str | None:
        """iperf server rolündeki düğümün log adını (MAC_ETH gibi) döner — iperf
        satırına 'server tarafı hangi makineydi' bilgisini yazmak için."""
        node = next(
            (n for n in self.nodes.values() if "iperf_server" in n.get("roles", [])),
            None,
        )
        return node_log_folder(node["node_id"], self.config) if node else None

    def record_result(self, node_id: str, kind: str, stats: dict, ftp_file_path: str | None = None):
        """Bir testin nihai özetini ilgili copy_ tablosuna yazar. Hem agent'lardan
        (/api/result) hem sunucu-yerel testlerden çağrılır. DB yoksa sessizce atlar.
        ftp_file_path verilmezse sunucu, FTP hedef klasörünü kendisi hesaplar (DB'de
        'bu testin logları FTP'de nerede' işaretçisi olur)."""
        db_sid = self.session.get("db_session_id")
        if not db_sid:
            return
        node_name = node_log_folder(node_id, self.config)
        if not ftp_file_path:
            dev = self.session.get("device", {})
            ftp_file_path = ftp_service.build_target_dir(
                dev.get("brand"), dev.get("model"), dev.get("firmware"),
                ftp_service.test_type_from_kind(kind), node_name,
            )
        try:
            if kind == "ping":
                db_service.save_ping(db_sid, node_name, stats, ftp_file_path)
            elif kind == "iperf":
                db_service.save_iperf(db_sid, node_name, self._iperf_server_node_name(),
                                      stats, ftp_file_path)
            elif kind == "wifi":
                db_service.save_wifi(db_sid, node_name, stats, ftp_file_path)
            else:
                print(f"[ORCH] Bilinmeyen sonuc tipi: {kind}")
        except Exception as e:
            print(f"[ORCH] record_result hatasi ({kind}): {e}")

    def upload_log_to_ftp(self, node_id: str, file_path: str):
        """Bir log dosyasını FTP'ye, doğru klasör yapısına (arka planda) yükler:
        <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<Bilgisayar>/
        Test tipi dosya adından, bilgisayar node'un log adından çözülür."""
        if not file_path:
            return
        dev = self.session.get("device", {})
        node_name = node_log_folder(node_id, self.config)
        test_type = ftp_service.test_type_from_filename(os.path.basename(file_path))
        target = ftp_service.build_target_dir(
            dev.get("brand"), dev.get("model"), dev.get("firmware"), test_type, node_name)
        ftp_service.upload_async([file_path], target)

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
        # Sunucunun kendi logları da bilgisayar klasörü altına (logs/LINUX/<session>)
        log_dir = os.path.join(LOGS_DIR, node_log_folder("server", self.config), session_id)
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
                    result=lambda kind, stats: self.record_result("server", kind, stats),
                )
                try:
                    logs = fn(params, ctx) or []
                    # Sunucunun kendi testlerinin loglarını da FTP'ye yükle
                    for lp in logs:
                        self.upload_log_to_ftp("server", lp)
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
            db_sid = self.session.get("db_session_id")
            started_at = self.session.get("started_at")
            ended_at = self.session["ended_at"]

        # DB: oturumun bitiş zamanını/süresini güncelle (copy_test_session)
        if db_sid:
            duration = None
            try:
                if started_at:
                    duration = int((datetime.fromisoformat(ended_at)
                                    - datetime.fromisoformat(started_at)).total_seconds())
            except Exception:
                duration = None
            db_service.update_session_end(db_sid, ended_at, duration)

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

    def reset_session(self) -> dict:
        """
        Her şeyi programın ilk açıldığı hale döndürür: çalışan testleri durdurur,
        oturum bilgisini ve tüm düğümlerin test ilerlemelerini sıfırlar. (Bağlantı
        ışıkları/health-check durumu frontend'de tutulur; o da orada sıfırlanır.)
        """
        # Önce çalışanları durdur (agent'lara /stop + sunucu-yerel)
        try:
            self.stop_session()
        except Exception as e:
            print(f"[ORCH] reset sirasinda stop hatasi: {e}")

        with self._lock:
            self.session = {"session_id": None, "running": False,
                            "started_at": None, "ended_at": None, "params": {},
                            "db_session_id": None,
                            "device": {"brand": None, "model": None, "firmware": None}}
            for node in self.nodes.values():
                for r in node["roles"]:
                    node["tests"][r] = self._blank_test()
        return {"status": "reset"}

    # ── Aktif bağlantı kontrolü (health-check) ───────────────
    def health_check(self) -> dict:
        """
        Her düğümün sunucuya/listener'a anlık erişilebilirliğini AKTİF olarak ölçer.
        Heartbeat tabanlı `online`dan bağımsızdır: dashboard'daki "Health-Check"
        butonu bunu aşamalı aralıklarla çağırır (kırmızı/yeşil ışıklar).

        Sunucu düğümü daima reachable (yerel). Diğer düğümler için son bilinen
        ip:agent_port'a paralel GET /health atılır.
        """
        with self._lock:
            nodes = [self._node_view(n) for n in self.nodes.values()]

        results: dict[str, dict] = {}
        threads: list[threading.Thread] = []

        def _probe(nv):
            if nv["is_server"]:
                results[nv["node_id"]] = {"reachable": True, "latency_ms": 0}
                return
            ip, port = nv.get("ip"), nv.get("agent_port")
            if not ip or not port:
                results[nv["node_id"]] = {"reachable": False, "latency_ms": None}
                return
            t0 = datetime.now()
            try:
                r = requests.get(f"http://{ip}:{port}/health", timeout=1.5)
                ok = r.status_code == 200
            except Exception:
                ok = False
            latency = int((datetime.now() - t0).total_seconds() * 1000) if ok else None
            results[nv["node_id"]] = {"reachable": ok, "latency_ms": latency}

        for nv in nodes:
            th = threading.Thread(target=_probe, args=(nv,), daemon=True)
            th.start()
            threads.append(th)
        for th in threads:
            th.join(timeout=2)

        return {
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "results": results,
        }
