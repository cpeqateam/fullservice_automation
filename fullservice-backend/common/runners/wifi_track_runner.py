"""
Wi-Fi Track çalıştırıcı — WLAN sinyal/kanal/rx-tx + sistem kaynaklarını periyodik
okuyup log'a yazar (GRK wifi analiz portu).

GRK `wifi_service` + `functionBase_wifi` mantığının dağıtık portudur:
  • Windows → [wifi_util.py] (netsh)
  • macOS   → [wifi_util_mac.py] (system_profiler) — geçici, takım liderinden
              gelecek kodla değiştirilecek
Her saniye bir örnek alınır; satır log'a yazılır. Kullanıcı isteri: bu test için
ayrı bir terminal penceresi açılıp örneklerin canlı aktığı görülsün.
"""
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext, is_mac, open_log_viewer, close_terminal
from common.runners import wifi_util


def run(params: TestParams, ctx: RunContext) -> list[str]:
    log_file = ctx.log_path("wifitrack")
    duration = max(1, int(params.duration))

    # Platforma uygun WLAN okuyucu
    if is_mac():
        from common.runners import wifi_util_mac
        read_wlan = wifi_util_mac.readWlan
    else:
        read_wlan = wifi_util.readWlan

    ctx.progress(0.0, TestStatus.RUNNING.value, "Wi-Fi analizi başlıyor...")

    # Başlık (istemci/cihaz bilgisi)
    try:
        wifi_util.getOneTimeInfo(read_wlan(), log_file)
    except Exception as e:
        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[uyari] baslik bilgisi alinamadi: {e}\n")

    # Canlı izleme penceresi (best-effort; masaüstü oturumu gerekir)
    viewer = open_log_viewer(log_file, f"Wi-Fi Track [{ctx.node_id}]")

    try:
        for i in range(duration):
            if ctx.stop.is_set():
                close_terminal(viewer)
                ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "Wi-Fi track durduruldu")
                return [log_file]
            start_t = time.time()
            wifi_util.sample_once(read_wlan, log_file)   # bir örnek satırı yaz
            ctx.progress(((i + 1) / duration) * 100, TestStatus.RUNNING.value,
                         f"Wi-Fi analizi {i + 1}/{duration} sn")
            elapsed = time.time() - start_t
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\nBitis: {datetime.now()}\n")
        ctx.progress(100.0, TestStatus.COMPLETED.value, "Wi-Fi analizi tamamlandı")
        return [log_file]

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"Wi-Fi track hatası: {e}")
        return [log_file]
    finally:
        close_terminal(viewer)
