"""
iperf3 client çalıştırıcı — wifi Mac düğümünde çalışır, kablolu Mac'teki
iperf3 server'a (iperf_server rolü) bağlanıp hattı doldurarak modeme yük
bindirir ("abanma"). Trafik iki Mac arasında modem üzerinden akar.

Komut:  iperf3 -c <iperf_server> -p <port> -t <duration> -P <parallel> [-R]
Çıktı log dosyasına yazılır; süre boyunca canlı ilerleme bildirilir; bitince
özet (toplam throughput) mesaja eklenir. iperf3 kurulu değilse anlaşılır hata verir.

Server ve client agent'ları PARALEL başlatıldığı için server (kablolu Mac) henüz
dinlemiyor olabilir; bu yüzden bağlantı birkaç kez yeniden denenir.

Kurulum:  Linux  → sudo apt install iperf3
          macOS  → brew install iperf3
"""
import re
import subprocess
import threading
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext, NO_WINDOW, open_log_viewer, close_terminal


def run(params: TestParams, ctx: RunContext) -> list[str]:
    """iperf3 client'ı çalıştırır (kablolu Mac'e yük basar), sonucu (sender/receiver Mbps)
    özetleyip görünür terminalde canlı gösterir; üretilen log dosyası yollarını döner."""
    server = (params.iperf_server or "").strip()
    # GRK ile aynı standart: FULL_Service_iperf_<brand>_<model>_<fw>_<server_ip>_<ts>.txt
    sanitized_server = server.replace(".", "").replace(":", "")
    log_file = ctx.grk_log_path("iperf", params.brand, params.model, params.firmware,
                                sanitized_server)

    if not server:
        ctx.progress(100.0, TestStatus.ERROR.value,
                     "iperf server adresi boş (kablolu Mac'in LAN IP'si gerekli).")
        return []

    duration = max(1, int(params.duration))
    cmd = ["iperf3", "-c", server, "-p", str(params.iperf_port),
           "-t", str(duration), "-P", str(params.iperf_parallel)]
    if params.iperf_reverse:
        cmd.append("-R")

    MAX_ATTEMPTS = 5      # server (kablolu Mac) henüz dinlemiyor olabilir → yeniden dene
    RETRY_WAIT = 2        # denemeler arası bekleme (sn)

    start_iso = datetime.now().isoformat(timespec="seconds")
    ctx.progress(0.0, TestStatus.RUNNING.value, f"iperf3 → {server}:{params.iperf_port}")

    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"FULL Servis iperf3 CLIENT — Node: {ctx.node_id}\n")
            f.write(f"Komut: {' '.join(cmd)}\nHedef: {server}:{params.iperf_port}\n")
            f.write(f"Baslangic: {datetime.now()}\n" + "-" * 30 + "\n")
            f.flush()

            viewer = open_log_viewer(log_file, f"iperf CLIENT → {server} [{ctx.node_id}]")
            proc = None
            for attempt in range(1, MAX_ATTEMPTS + 1):
                if ctx.stop.is_set():
                    close_terminal(viewer)
                    ctx.progress(0.0, TestStatus.STOPPED.value, "iperf durduruldu")
                    return [log_file]
                try:
                    proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                                            text=True, creationflags=NO_WINDOW)
                except FileNotFoundError:
                    msg = "iperf3 bulunamadı. Kurulum: apt install iperf3 / brew install iperf3"
                    f.write(msg + "\n")
                    close_terminal(viewer)
                    ctx.progress(100.0, TestStatus.ERROR.value, msg)
                    return [log_file]

                # Süre boyunca canlı ilerleme
                ran_full = True
                for i in range(duration):
                    if ctx.stop.is_set():
                        proc.terminate()
                        close_terminal(viewer)
                        ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "iperf durduruldu")
                        return [log_file]
                    if proc.poll() is not None:
                        ran_full = False     # süreden önce bitti → muhtemelen bağlantı hatası
                        break
                    time.sleep(1)
                    ctx.progress(((i + 1) / duration) * 100, TestStatus.RUNNING.value,
                                 f"iperf yük basıyor {i + 1}/{duration}s → {server}")

                try:
                    proc.wait(timeout=20)
                except Exception:
                    pass

                # Başarılı (returncode 0) ya da süreyi tamamladıysa döngüden çık
                if proc.returncode == 0:
                    break
                # Bağlantı erken koptu ve hâlâ deneme hakkı varsa: server'ın
                # ayağa kalkmasını bekleyip yeniden bağlan.
                if not ran_full and attempt < MAX_ATTEMPTS and not ctx.stop.is_set():
                    f.write(f"\n[Deneme {attempt} basarisiz — server hazir degil, {RETRY_WAIT}s sonra yeniden]\n")
                    f.flush()
                    ctx.progress(0.0, TestStatus.RUNNING.value,
                                 f"server bekleniyor… (deneme {attempt + 1}/{MAX_ATTEMPTS})")
                    time.sleep(RETRY_WAIT)
                    continue
                break

            f.write("\n" + "-" * 30 + f"\nBitis: {datetime.now()}\n")

        close_terminal(viewer)
        summary = _parse_summary(log_file)
        rc = proc.returncode if proc else 1
        status = TestStatus.COMPLETED.value if rc == 0 else TestStatus.ERROR.value
        ctx.progress(100.0, status, summary or ("iperf tamamlandı" if status == "completed" else "iperf hatası — server'a bağlanılamadı"))
        if ctx.result:
            snd, rcv = _parse_rates(log_file)
            ctx.result("iperf", {
                "server_ip": server,
                "port": params.iperf_port,
                "parallel": params.iperf_parallel,
                "duration": duration,
                "sender_mbps": snd,
                "receiver_mbps": rcv,
                "test_start_time": start_iso,
                "test_end_time": datetime.now().isoformat(timespec="seconds"),
            })
        return [log_file]

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"iperf hatası: {e}")
        return [log_file]


def _parse_summary(log_file: str) -> str:
    """Log'un sonundan özet throughput satırını (sender/receiver) yakalamaya çalışır."""
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        # "... 0.00-60.00 sec  6.50 GBytes   930 Mbits/sec   ... sender"
        matches = re.findall(r"([\d.]+\s*[KMG]bits/sec).*?(sender|receiver)", text)
        if matches:
            parts = {role: rate for rate, role in matches}
            snd = parts.get("sender", "?")
            rcv = parts.get("receiver", "?")
            return f"iperf bitti — gönderen {snd}, alıcı {rcv}"
    except Exception:
        pass
    return ""


def _to_mbps(value: float, unit: str) -> float:
    """K/M/G bits/sec değerini Mbit/sn'ye normalize eder."""
    u = unit.upper()
    if u.startswith("G"):
        return round(value * 1000, 2)
    if u.startswith("K"):
        return round(value / 1000, 2)
    return round(value, 2)  # Mbits


def _parse_rates(log_file: str):
    """Log sonundaki sender/receiver throughput'unu SAYISAL Mbit/sn olarak döner.
    Bulunamazsa (None, None)."""
    snd = rcv = None
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        for value, unit, role in re.findall(
                r"([\d.]+)\s*([KMG])bits/sec.*?(sender|receiver)", text):
            mbps = _to_mbps(float(value), unit)
            if role == "sender":
                snd = mbps
            else:
                rcv = mbps
    except Exception as e:
        print(f"[IPERF] rate parse hatasi: {e}")
    return snd, rcv
