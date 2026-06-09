"""
iperf3 client çalıştırıcı — Mac düğümlerinde çalışır, Linux sunucudaki
iperf3 server'a bağlanıp hattı doldurarak modeme yük bindirir ("abanma").

Komut:  iperf3 -c <iperf_server> -p <port> -t <duration> -P <parallel>
Çıktı log dosyasına yazılır; süre boyunca canlı ilerleme bildirilir; bitince
özet (toplam throughput) mesaja eklenir. iperf3 kurulu değilse anlaşılır hata verir.

Kurulum:  Linux  → sudo apt install iperf3
          macOS  → brew install iperf3
"""
import re
import subprocess
import threading
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext, NO_WINDOW


def run(params: TestParams, ctx: RunContext) -> list[str]:
    server = (params.iperf_server or "").strip()
    log_file = ctx.log_path("iperf")

    if not server:
        ctx.progress(100.0, TestStatus.ERROR.value,
                     "iperf server adresi boş (Linux sunucu LAN IP'si gerekli).")
        return []

    duration = max(1, int(params.duration))
    cmd = ["iperf3", "-c", server, "-p", str(params.iperf_port),
           "-t", str(duration), "-P", str(params.iperf_parallel)]

    ctx.progress(0.0, TestStatus.RUNNING.value, f"iperf3 → {server}:{params.iperf_port}")

    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"FULL Servis iperf3 — Node: {ctx.node_id}\n")
            f.write(f"Komut: {' '.join(cmd)}\nBaslangic: {datetime.now()}\n" + "-" * 30 + "\n")
            f.flush()
            try:
                proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                                        text=True, creationflags=NO_WINDOW)
            except FileNotFoundError:
                msg = "iperf3 bulunamadı. Kurulum: apt install iperf3 / brew install iperf3"
                f.write(msg + "\n")
                ctx.progress(100.0, TestStatus.ERROR.value, msg)
                return [log_file]

            for i in range(duration):
                if ctx.stop.is_set():
                    proc.terminate()
                    ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "iperf durduruldu")
                    return [log_file]
                if proc.poll() is not None:
                    break
                time.sleep(1)
                ctx.progress(((i + 1) / duration) * 100, TestStatus.RUNNING.value,
                             f"iperf yük basıyor {i + 1}/{duration}s → {server}")

            proc.wait(timeout=20)
            f.write("\n" + "-" * 30 + f"\nBitis: {datetime.now()}\n")

        summary = _parse_summary(log_file)
        status = TestStatus.COMPLETED.value if proc.returncode == 0 else TestStatus.ERROR.value
        ctx.progress(100.0, status, summary or ("iperf tamamlandı" if status == "completed" else "iperf hatası"))
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
