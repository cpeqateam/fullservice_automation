"""
Torrent çalıştırıcı — ŞİMDİLİK SİMÜLASYON (Faz 4'te gerçek qBittorrent'e bağlanacak).

Hedef gerçek hali: GRK'daki utils/pc_control/gbtorrent.py mantığı — qBittorrent
Web API ile sonsuz indirme döngüsü (ekle → indir → sil → tekrar) → modeme yük.
Şu an pipeline'ı uçtan uca görebilmek için süre boyunca sahte ilerleme üretir ve
bir yer-tutucu log yazar.

TODO(Faz 4): qBittorrent Web UI (http://127.0.0.1:8080) entegrasyonu, magnet link
parametresi (params.extra["magnet_link"]), hız limiti, döngü.
"""
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext


def run(params: TestParams, ctx: RunContext) -> list[str]:
    log_file = ctx.log_path("torrent")
    duration = max(1, int(params.duration))

    with open(log_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"FULL Servis Torrent (SIMULASYON) — Node: {ctx.node_id}\n")
        f.write(f"Baslangic: {datetime.now()}\n")

        ctx.progress(0.0, TestStatus.RUNNING.value, "Torrent (simülasyon) başlıyor...")
        for i in range(duration):
            if ctx.stop.is_set():
                ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "Torrent durduruldu")
                return [log_file]
            time.sleep(1)
            pct = ((i + 1) / duration) * 100
            f.write(f"[{datetime.now():%H:%M:%S}] simulasyon indirme %{pct:.0f}\n")
            ctx.progress(pct, TestStatus.RUNNING.value, f"Torrent (sim) %{pct:.0f}")

    ctx.progress(100.0, TestStatus.COMPLETED.value, "Torrent (simülasyon) tamamlandı")
    return [log_file]
