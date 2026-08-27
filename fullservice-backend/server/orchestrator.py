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
from server import notification_service
from server import log_capture
from server import excel_service


class Orchestrator:
    """FULL Servis'in beyni (sunucuda tek örnek): düğüm kaydı, merkezi ilerleme toplama,
    başlat/durdur/sıfırla komutlarının tüm agent'lara fan-out'u, sunucu-yerel testlerin
    koşumu, DB/FTP/bildirim tetikleme ve health-check. Tüm durum bellekte, _lock ile korunur."""

    def __init__(self, config: dict):
        """config'ten düğüm topolojisini kurar, her düğüm için boş test durumları oluşturur."""
        self.config = config
        self.defaults = config.get("defaults", {})
        self.server_lan_ip = config.get("server", {}).get("lan_ip") or detect_lan_ip()
        # Uptime limiti (dakika): bir cihaz bu süreden uzundur açıksa "kırmızı" sayılır
        # ve test BAŞLATILAMAZ (yeniden başlatılmalı). config.json'dan okunur.
        self.uptime_limit_min = int(config.get("uptime_limit_minutes", 45))
        self._lock = threading.RLock()

        try:
            import psutil as _psutil
            _boot_iso = datetime.fromtimestamp(_psutil.boot_time()).isoformat(timespec="seconds")
        except Exception:
            _boot_iso = datetime.now().isoformat(timespec="seconds")
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
                "online": is_server,
                "last_seen": None,
                # server node'u kendi başlangıç zamanını bilir; agent node'ları
                # ilk heartbeat gelince first_seen_at alır (agent restart gerekmez)
                "agent_started_at": _boot_iso if is_server else None,
                "first_seen_at": _boot_iso if is_server else None,
                "tests": {r: self._blank_test() for r in n.get("roles", [])},
            }

        self.session = {"session_id": None, "running": False,
                        "started_at": None, "ended_at": None, "params": {},
                        "db_session_id": None,
                        "selected_tests": None,   # None = henüz oturum yok
                        "device": {"brand": None, "model": None, "firmware": None}}

        # Sunucu-yerel testler için durdurma bayrağı + thread'ler
        self._server_stop = threading.Event()
        self._server_threads: list[threading.Thread] = []

    @staticmethod
    def _blank_test() -> dict:
        """Bir test için başlangıç (idle) durum sözlüğü döner."""
        return {"progress": 0.0, "status": TestStatus.IDLE.value, "message": "", "updated": None}

    @staticmethod
    def _skipped_test() -> dict:
        """Kullanıcının seçmediği test için durum sözlüğü — hiç başlatılmaz."""
        return {"progress": 0.0, "status": TestStatus.SKIPPED.value,
                "message": "Bu oturumda seçilmedi", "updated": None}

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
            # agent_started_at: yeni agent kodu gönderirse kullan; yoksa first_seen_at fallback
            if req.get("agent_started_at"):
                node["agent_started_at"] = req["agent_started_at"]
            if not node.get("first_seen_at"):
                node["first_seen_at"] = datetime.now().isoformat(timespec="seconds")

    _TERMINAL = {"completed", "error", "stopped", "skipped"}

    # Bildirimi/tamamlanmayı belirleyen "ölçüm" testleri. Torrent ve youtube sonsuz
    # yük basıcıdır (ancak Durdur'a basınca biter), iperf_server yalnızca dinleyicidir —
    # bunlar bitişi belirlemez; aksi halde torrent hiç bitmediği için bildirim
    # hiçbir zaman tetiklenmezdi.
    _COMPLETION_ROLES = {"ping_internet", "ping_modem", "iperf", "wifi_track"}

    def _all_tests_terminal(self) -> bool:
        """Ölçüm testleri (ping/iperf/wifi_track) bitiş durumunda mı (completed/error/stopped)?
        Sonsuz yük (torrent/youtube) ve dinleyici (iperf_server) dikkate ALINMAZ."""
        has_any = False
        for node in self.nodes.values():
            for r in node.get("roles", []):
                if r not in self._COMPLETION_ROLES:
                    continue
                st = node["tests"].get(r, {}).get("status")
                # Seçilmeyen test ne bekletir ne de "bitti" saydırır; yok sayılır.
                # (Aksi halde tüm ölçüm testleri kapatıldığında oturum daha
                #  başlar başlamaz "bitti" sayılıp bildirim giderdi.)
                if st == TestStatus.SKIPPED.value:
                    continue
                has_any = True
                if st not in self._TERMINAL:
                    return False
        return has_any

    # ── İlerleme güncelleme (agent push + sunucu-yerel) ──────
    def update_progress(self, node_id: str, task: str, progress: float,
                        status: str, message: str = ""):
        """Bir düğüm-testinin ilerleme/durumunu günceller; ölçüm testleri (ping/iperf/wifi)
        hep birlikte terminal olduğu ilk anda (kenar yakalama) bir kez tamamlanma tetikler."""
        fire = None
        with self._lock:
            node = self.nodes.get(node_id)
            if not node:
                return
            # Bu güncellemeden ÖNCE ve SONRA "hepsi bitti mi" — kenar (transition)
            # yakala: yalnızca son testi bitiren güncellemede bir kez tetiklensin.
            before = self._all_tests_terminal()
            if task not in node["tests"]:
                node["tests"][task] = self._blank_test()
            t = node["tests"][task]
            t["progress"] = round(float(progress), 1)
            t["status"] = status
            t["message"] = message
            t["updated"] = datetime.now().isoformat(timespec="seconds")
            after = self._all_tests_terminal()

            # Ölçüm testleri (ping/iperf/wifi_track) bitince — kenar yakalama ile bir kez.
            # Torrent/youtube (sonsuz yük) beklenmez; onlar Durdur'a kadar sürebilir.
            # session_id varsa (gerçek bir koşu) tetikle; yeni "Başlat" yeni
            # session_id → her koşu yeniden bildirir.
            if self.session.get("session_id") and not before and after:
                fire = {
                    "device":     dict(self.session.get("device", {})),
                    "session_id": self.session.get("session_id"),
                    "started_at": self.session.get("started_at"),
                    "log_offset": self.session.get("log_offset", 0),
                    "db_session_id": self.session.get("db_session_id"),
                }

        if fire:
            self._on_session_complete(fire)

    def _on_session_complete(self, info: dict):
        """Test bitince (lock dışında): Telegram+mail bildirimi VE error_log'u FTP'ye."""
        # 1) Özet Excel'ler + Telegram (mesaj + tek zip) + mail (sadece mesaj)
        try:
            notification_service.send_completion(
                info["device"], info["session_id"], info["started_at"],
                info.get("db_session_id"), self._iperf_server_node_name())
        except Exception as e:
            print(f"[ORCH] Bildirim baslatilamadi: {e}")
        # 2) error_log dilimini FTP'ye yükle + DB'ye yolunu yaz (bildirim YOK —
        #    sadece hata görünürlüğü / "Error Log İndir" butonu için)
        try:
            log_capture.finalize_async(
                info["device"], info["session_id"], info["started_at"],
                info["log_offset"], info.get("db_session_id"))
        except Exception as e:
            print(f"[ORCH] error_log gonderilemedi: {e}")

    # ── Dashboard durum çıktısı ──────────────────────────────
    def get_state(self) -> dict:
        """Dashboard'ın çektiği birleşik durum: oturum + test etiketleri + sunucu IP + düğümler."""
        with self._lock:
            return {
                "session": dict(self.session),
                "test_labels": TEST_LABELS,
                "server_lan_ip": self.server_lan_ip,
                "uptime_limit_min": self.uptime_limit_min,
                "nodes": [self._node_view(n) for n in self.nodes.values()],
            }

    def check_uptime(self) -> list[dict]:
        """Uptime limitini AŞAN online düğümleri döner: [{'label','node_id','minutes'}].
        Boş liste → tüm cihazlar limit altında (yeşil), test başlatılabilir. Bir cihaz
        limit üstündeyse (kırmızı) test başlatılmamalı — çağıran engeller."""
        now = datetime.now()
        blocked = []
        with self._lock:
            for node in self.nodes.values():
                view = self._node_view(node)
                if not view["online"]:
                    continue                       # kapalı/erişilemez cihaz uptime'la engellemez
                started = view.get("agent_started_at")
                if not started:
                    continue
                try:
                    mins = int((now - datetime.fromisoformat(started)).total_seconds() // 60)
                except Exception:
                    continue
                if mins >= self.uptime_limit_min:
                    blocked.append({"label": view["label"], "node_id": view["node_id"],
                                    "minutes": mins})
        return blocked

    def _node_view(self, node: dict) -> dict:
        """Bir düğümün dashboard için sunulan görünümünü üretir (heartbeat 30 sn'den eskiyse offline)."""
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
            "agent_started_at": node.get("agent_started_at") or node.get("first_seen_at"),
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
        """Yeni bir test oturumu başlatır: TestParams'ı kurar, DB'de oturum satırı açar,
        sunucu-yerel rolleri koşar ve online agent'lara `/start` fan-out'u yapar."""
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
                iperf_port=int(overrides.get("iperf_port") or self.defaults.get("iperf_port", 5201)),
                iperf_parallel=int(overrides.get("iperf_parallel") or self.defaults.get("iperf_parallel", 10)),
                iperf_reverse=bool(overrides.get("iperf_reverse", False)),
                torrent_magnet=overrides.get("torrent_magnet") or self.defaults.get("torrent_magnet", ""),
                torrent_recycle_gb=float(self.defaults.get("torrent_recycle_gb", 5)),
                duration=int(overrides.get("duration") or self.defaults.get("duration", 60)),
                # Cihaz bilgisi — log dosyası adlandırması GRK standardında olsun diye
                brand=overrides.get("brand") or "Unknown",
                model=overrides.get("model") or "Unknown",
                firmware=overrides.get("firmware") or "Unknown",
            )
            # Kullanıcının seçtiği testler. None/boş gelirse HEPSİ seçili sayılır
            # (eski davranış korunur — arayüzü güncellenmemiş bir istemci de çalışır).
            _all_roles = {r for n in self.config.get("nodes", []) for r in n.get("roles", [])}
            _sel = overrides.get("selected_tests")
            # DİKKAT: boş liste ile hiç gönderilmemiş olmak FARKLI şeydir.
            #   None  → istemci seçim göndermedi  → hepsi koşar (eski davranış)
            #   []    → kullanıcı hepsini kapattı → hiçbiri koşmaz
            selected = set(_all_roles) if _sel is None else set(_sel)

            self.session = {
                "session_id": session_id,
                "running": True,
                # Panelin hangi testlerin atlandığını bilmesi + seçim panelini
                # test sürerken kilitlemesi için durumla birlikte sunulur.
                "selected_tests": sorted(selected),
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "ended_at": None,
                "params": params.dict() if hasattr(params, "dict") else params.model_dump(),
                "db_session_id": None,
                "device": {
                    "brand":    overrides.get("brand"),
                    "model":    overrides.get("model"),
                    "firmware": overrides.get("firmware"),
                    # Bildirim (Telegram/mail) mesajında kullanılan ek bilgiler
                    "user_name":    overrides.get("user_name", ""),
                    "user_surname": overrides.get("user_surname", ""),
                    "server":       "FULL Servis",
                    "duration":     params.duration,
                },
                # error_log için: app.log'un bu oturum başındaki byte konumu
                "log_offset": log_capture.current_size(),
            }
            # Tüm test durumlarını sıfırla — seçilmeyenler ATLANDI olarak işaretlenir
            for node in self.nodes.values():
                for r in node["roles"]:
                    node["tests"][r] = (self._blank_test() if r in selected
                                        else self._skipped_test())

            online_nodes = [self._node_view(n) for n in self.nodes.values()]
            started_at = self.session["started_at"]
            device = dict(self.session["device"])

        # DB: oturum satırını (test_session) oluştur — lock dışında (ağ/DB I/O).
        # has_* bayrakları GERÇEKTEN KOŞULACAK testlere göre kurulur: kullanıcı bir
        # testin tikini kaldırdıysa DB'de "bu oturumda vardı" demek yanlış olur.
        roles_all = {r for n in self.config.get("nodes", []) for r in n.get("roles", [])} & selected
        db_session_id = db_service.create_session(
            device.get("brand"), device.get("model"), device.get("firmware"),
            started_at,
            has_ping=any(r in roles_all for r in ("ping_internet", "ping_modem")),
            has_speedtest="speedtest" in roles_all,
            has_wifi="wifi_track" in roles_all,
            has_iperf="iperf" in roles_all,
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
            # SEÇİM FİLTRESİ: kullanıcının tikini kaldırdığı testler agent'a hiç
            # gönderilmez. Düğümün tüm rolleri kapatılmışsa o düğüme komut gitmez.
            roles = [r for r in nv["roles"] if r in selected]
            if not roles:
                continue
            if nv["is_server"]:
                self._run_server_local(session_id, roles, params)
                dispatched.append(nv["node_id"])
            elif nv["online"] and nv["ip"] and nv["agent_port"]:
                def _dispatch(n=nv, _roles=roles):
                    """Bir agent'a start komutunu gönderip sonucu results'a yazar (thread hedefi)."""
                    results[n["node_id"]] = self._send_start(n, session_id, _roles, params)
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
        """Bir testin nihai özetini ilgili sonuç tablosuna yazar. Hem agent'lardan
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

        FTP'ye HER ŞEY gider (kullanıcı isteri): ham .txt loglar ve üretilen
        Excel'ler, test tipine göre ayrılmış klasörlere TEK TEK dosya olarak
        (zip değil) — böylece test platformundan tek tek indirilebilir.
          • WIFI  → ham .txt VE ondan üretilen GRK formatındaki Excel
                    (Veriler+Özet+10 grafik) birlikte gider.
          • Diğer → dosya olduğu gibi gider.

        Yükleme log geldikçe (teste yayılı) yapılır; oturum sonunu beklemez.
        Excel üretimi + yükleme arka plan thread'inde yapılır (matplotlib yavaş
        olabilir; HTTP yanıtını bloke etmesin).

        Oturum sonunda üretilen ÖZET Excel'leri (ping/iperf) report_service
        kendi yükler."""
        if not file_path:
            return
        dev = self.session.get("device", {})
        node_name = node_log_folder(node_id, self.config)
        test_type = ftp_service.test_type_from_filename(os.path.basename(file_path))
        target = ftp_service.build_target_dir(
            dev.get("brand"), dev.get("model"), dev.get("firmware"), test_type, node_name)

        def _work():
            """Ham logu (wifi ise ayrıca ondan üretilen Excel'i) FTP'ye yükler (thread hedefi)."""
            files = [file_path]
            if test_type == "Wifi":
                try:
                    xlsx = excel_service.wifi_log_to_excel(file_path)
                    if xlsx:
                        files.append(xlsx)
                except Exception as e:
                    print(f"[ORCH] Wifi Excel uretilemedi: {e}")
            ftp_service.upload_files_to_ftp(files, target)

        threading.Thread(target=_work, daemon=True).start()

    def _send_start(self, nv: dict, session_id: str, roles: list, params: TestParams) -> bool:
        """Tek bir agent'a `/start` komutunu (rolleri + parametreleri) HTTP ile gönderir."""
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
        server_name = node_log_folder("server", self.config)
        log_dir = os.path.join(LOGS_DIR, server_name, session_id)
        for test in roles:
            runner = get_runner(test)
            if runner is None:
                self.update_progress("server", test, 100.0, TestStatus.ERROR.value, "Bilinmeyen test")
                continue

            def _worker(t=test, fn=runner):
                """Sunucu-yerel tek bir testi koşar (RunContext ile progress/result) — thread hedefi."""
                ctx = RunContext(
                    node_id="server", session_id=session_id, log_dir=log_dir,
                    progress=lambda p, s, m, _t=t: self.update_progress("server", _t, p, s, m),
                    stop=self._server_stop,
                    result=lambda kind, stats: self.record_result("server", kind, stats),
                    node_name=server_name,
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
        """Çalışan tüm testleri durdurur: sunucu-yerel thread'lere ve tüm online agent'lara
        durma sinyali/`/stop` gönderir (bildirim tetiklemez)."""
        with self._lock:
            self.session["running"] = False
            self.session["ended_at"] = datetime.now().isoformat(timespec="seconds")
            targets = [self._node_view(n) for n in self.nodes.values() if not n.get("is_server")]
            db_sid = self.session.get("db_session_id")
            started_at = self.session.get("started_at")
            ended_at = self.session["ended_at"]

        # DB: oturumun bitiş zamanını/süresini güncelle (test_session)
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
        # NOT: Bildirim burada GÖNDERİLMEZ. Test "bittiğinde" (tüm testler terminal)
        # update_progress içinden _on_session_complete tetiklenir.
        return {"status": "stopped"}

    def reset_session(self) -> dict:
        """
        Her şeyi programın ilk açıldığı hale döndürür: çalışan testleri durdurur,
        oturum bilgisini ve tüm düğümlerin test ilerlemelerini sıfırlar. (Bağlantı
        ışıkları/health-check durumu frontend'de tutulur; o da orada sıfırlanır.)
        """
        # Önce çalışanları durdur (agent'lara /stop + sunucu-yerel).
        try:
            self.stop_session()
        except Exception as e:
            print(f"[ORCH] reset sirasinda stop hatasi: {e}")

        with self._lock:
            self.session = {"session_id": None, "running": False,
                            "started_at": None, "ended_at": None, "params": {},
                            "db_session_id": None,
                            "selected_tests": None,
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
            """Bir düğümün /health'ine bakıp erişilebilirlik + gecikme (ms) döner (thread hedefi)."""
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
