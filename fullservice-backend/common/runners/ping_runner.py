"""
Ping testi çalıştırıcı — modeme veya internete cross-platform ping atar.

GRK ping_service'ten uyarlanmıştır. Kullanıcı isteri: ping atılırken komut satırı
çıktısı CANLI görünsün. Bu yüzden:
  • Arka planda bir ping çalışır → log dosyasına yazar (özet + kayıt + durdurma kontrolü).
  • Ayrıca GÖRÜNÜR bir terminal penceresinde aynı ping çalışır → kullanıcı canlı izler.
Görünür pencere yalnızca masaüstü oturumunda açılır; açılamazsa test arka planda
normal devam eder. ping_internet ve ping_modem aynı motoru farklı hedefle kullanır.
"""
import re
import statistics
import subprocess
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import (
    RunContext, NO_WINDOW, is_windows, is_mac, open_terminal_running, close_terminal,
)


def _compute_ping_stats(log_file: str, target: str, count: int,
                        start_iso: str, end_iso: str) -> dict:
    """Ping log dosyasından özet istatistik çıkarır. Yanıt sürelerini (time=/süre=)
    platform/dil bağımsız regex ile toplayıp min/max/avg/median/std hesaplar.
    Başarılı = yanıt süresi bulunan paket sayısı; gerisi kayıp sayılır."""
    times: list[float] = []
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        # "time=12.3 ms" (EN), "süre=12 ms"/"zaman=12ms" (TR Windows), "time<1ms"
        for m in re.findall(r"(?:time|s[üu]re|zaman)[=<]\s*([\d.,]+)", text, re.IGNORECASE):
            try:
                times.append(float(m.replace(",", ".")))
            except ValueError:
                pass
    except Exception as e:
        print(f"[PING] stat hesaplanamadi: {e}")

    total = max(count, len(times))
    success = len(times)
    failed = max(0, total - success)
    return {
        "target_ip": target,
        "ip_version": "IPv6" if ":" in (target or "") else "IPv4",
        "total_pings": total,
        "successful_pings": success,
        "failed_pings": failed,
        "success_rate": round(success / total * 100, 2) if total else 0.0,
        "packet_loss_percent": round(failed / total * 100, 2) if total else 100.0,
        "min_time": min(times) if times else None,
        "max_time": max(times) if times else None,
        "avg_time": statistics.mean(times) if times else None,
        "median_time": statistics.median(times) if times else None,
        "std_dev_time": statistics.pstdev(times) if len(times) > 1 else 0.0,
        "test_start_time": start_iso,
        "test_end_time": end_iso,
    }


def _run_ping(target: str, label: str, params: TestParams, ctx: RunContext) -> list[str]:
    if not target:
        ctx.progress(100.0, TestStatus.ERROR.value, f"{label}: hedef IP boş.")
        return []

    count = max(1, int(params.duration))
    if is_windows():
        cmd = ["ping", "-n", str(count), "-w", "1000", target]
    elif is_mac():
        # macOS'ta -W MİLİSANİYE'dir; "-W 1" (1ms) tüm yanıtları zaman aşımına
        # uğratıp satır satır çıktıyı bozuyordu. Varsayılan beklemeyle bırak →
        # her yanıt satır satır görünür (özet zaten en sonda gelir).
        cmd = ["ping", "-c", str(count), target]
    else:
        # Linux: -c paket sayısı, -W yanıt bekleme (saniye)
        cmd = ["ping", "-c", str(count), "-W", "1", target]

    log_file = ctx.log_path(f"ping_{label}_{target}")
    start_iso = datetime.now().isoformat(timespec="seconds")
    ctx.progress(0.0, TestStatus.RUNNING.value, f"{label} başlıyor → {target}")

    # Canlı izleme için görünür terminal (best-effort, masaüstü oturumu gerekir)
    viewer = open_terminal_running(cmd, f"PING {label} → {target} [{ctx.node_id}]")

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
                    close_terminal(viewer)
                    f.write(f"\n-- Kullanici durdurdu: {datetime.now()} --\n")
                    ctx.progress((i / count) * 100, TestStatus.STOPPED.value, f"{label} durduruldu")
                    f.flush()
                    if ctx.result:
                        end_iso = datetime.now().isoformat(timespec="seconds")
                        ctx.result("ping", _compute_ping_stats(log_file, target, i, start_iso, end_iso))
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
        if ctx.result:
            end_iso = datetime.now().isoformat(timespec="seconds")
            ctx.result("ping", _compute_ping_stats(log_file, target, count, start_iso, end_iso))
        return [log_file]

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"{label} hatası: {e}")
        return [log_file]
    finally:
        close_terminal(viewer)


def run_internet(params: TestParams, ctx: RunContext) -> list[str]:
    return _run_ping(params.internet_ip, "Internet", params, ctx)


def run_modem(params: TestParams, ctx: RunContext) -> list[str]:
    return _run_ping(params.modem_ip, "Modem", params, ctx)
