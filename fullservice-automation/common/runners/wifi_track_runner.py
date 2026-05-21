"""
Wi-Fi Track çalıştırıcı — ŞİMDİLİK SİMÜLASYON (Faz 4'te gerçek ölçüme bağlanacak).

Hedef gerçek hali: GRK'daki wifi_service + utils/wifi/functionBase_wifi.py mantığı —
her saniye WLAN adaptöründen sinyal/kanal/rx-tx oranı okuyup log'a yazma; sonunda
Excel + grafik. Windows'ta `netsh wlan show interfaces`, macOS'ta
`system_profiler SPAirPortDataType` kullanılır (GRK main.py'de örneği var).

Şu an pipeline bütünlüğü için süre boyunca sahte ilerleme üretir.

TODO(Faz 4): platforma özgü WLAN okuma + saniyelik örnekleme + Excel raporu.
"""
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext


def run(params: TestParams, ctx: RunContext) -> list[str]:
    log_file = ctx.log_path("wifitrack")
    duration = max(1, int(params.duration))

    with open(log_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"FULL Servis Wi-Fi Track (SIMULASYON) — Node: {ctx.node_id}\n")
        f.write(f"Baslangic: {datetime.now()}\n")

        ctx.progress(0.0, TestStatus.RUNNING.value, "Wi-Fi track (simülasyon) başlıyor...")
        for i in range(duration):
            if ctx.stop.is_set():
                ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "Wi-Fi track durduruldu")
                return [log_file]
            time.sleep(1)
            pct = ((i + 1) / duration) * 100
            f.write(f"[{datetime.now():%H:%M:%S}] ornek #{i+1} sinyal=-- kanal=-- rx=-- tx=--\n")
            ctx.progress(pct, TestStatus.RUNNING.value, f"Wi-Fi track (sim) {i+1}/{duration}s")

    ctx.progress(100.0, TestStatus.COMPLETED.value, "Wi-Fi track (simülasyon) tamamlandı")
    return [log_file]
