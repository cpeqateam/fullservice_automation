"""
Ping testi çalıştırıcı — modeme veya internete cross-platform ping atar.

GRK ping_service'ten uyarlanmıştır; tek hedef + canlı ilerleme + temiz durdurma
ekler. ping_internet ve ping_modem aynı motoru farklı hedefle kullanır.
"""
import subprocess
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext, NO_WINDOW, is_windows


def _run_ping(target: str, label: str, params: TestParams, ctx: RunContext) -> list[str]:
    if not target:
        ctx.progress(100.0, TestStatus.ERROR.value, f"{label}: hedef IP boş.")
        return []

    count = max(1, int(params.duration))
    if is_windows():
        cmd = ["ping", "-n", str(count), "-w", "1000", target]
    else:
        # Linux/macOS: -c paket sayısı, -W yanıt bekleme (sn)
        cmd = ["ping", "-c", str(count), "-W", "1", target]

    log_file = ctx.log_path(f"ping_{label}_{target}")
    ctx.progress(0.0, TestStatus.RUNNING.value, f"{label} başlıyor → {target}")

    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"FULL Servis Ping — {label}\n")
            f.write(f"Node: {ctx.node_id}  Hedef: {target}\n")
            f.write(f"Baslangic: {datetime.now()}\n" + "-" * 30 + "\n")
            f.flush()

            proc = subprocess.Popen(
                cmd, stdout=f, stderr=subprocess.STDOUT, text=True, creationflags=NO_WINDOW
            )

            # Süre boyunca saniyede bir ilerleme bildir; durdurma sinyali gelirse pingi kes
            for i in range(count):
                if ctx.stop.is_set():
                    proc.terminate()
                    f.write(f"\n-- Kullanici durdurdu: {datetime.now()} --\n")
                    ctx.progress((i / count) * 100, TestStatus.STOPPED.value, f"{label} durduruldu")
                    return [log_file]
                if proc.poll() is not None:
                    break
                time.sleep(1)
                ctx.progress(((i + 1) / count) * 100, TestStatus.RUNNING.value,
                             f"{label} {i + 1}/{count}s → {target}")

            proc.wait(timeout=15)
            f.write("\n" + "-" * 30 + f"\nBitis: {datetime.now()}\n")

        status = TestStatus.COMPLETED.value if proc.returncode == 0 else TestStatus.ERROR.value
        msg = f"{label} tamamlandı" if proc.returncode == 0 else f"{label}: yanıt yok / hata"
        ctx.progress(100.0, status, msg)
        return [log_file]

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"{label} hatası: {e}")
        return [log_file]


def run_internet(params: TestParams, ctx: RunContext) -> list[str]:
    return _run_ping(params.internet_ip, "Internet", params, ctx)


def run_modem(params: TestParams, ctx: RunContext) -> list[str]:
    return _run_ping(params.modem_ip, "Modem", params, ctx)
