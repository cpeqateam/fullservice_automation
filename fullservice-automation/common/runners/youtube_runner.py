"""
YouTube çalıştırıcı — varsayılan tarayıcıda videoyu açar ve test süresince
"oynuyor" kabul edip ilerleme bildirir.

GRK pc_control_service.start_youtube mantığı (1080p zorlama) + süre/durdurma
takibi eklenmiştir. Tarayıcı sekmesini programatik kapatmak platformlar arası
güvenilir olmadığından, süre dolunca testi tamamlandı olarak işaretler (sekme
açık kalır; stres sırasında oynaması istenen davranıştır).
"""
import time
import webbrowser
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext


def run(params: TestParams, ctx: RunContext) -> list[str]:
    link = (params.youtube_link or "").strip()
    log_file = ctx.log_path("youtube")

    if not link:
        ctx.progress(100.0, TestStatus.ERROR.value, "YouTube linki boş.")
        return []

    # 1080p zorlama (GRK ile aynı): &vq=hd1080 / ?vq=hd1080
    quality_link = link
    if "youtu" in quality_link:
        sep = "&" if "?" in quality_link else "?"
        quality_link = f"{quality_link}{sep}vq=hd1080"

    with open(log_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"FULL Servis YouTube — Node: {ctx.node_id}\n")
        f.write(f"Link: {quality_link}\nAcilis: {datetime.now()}\n")

    ctx.progress(0.0, TestStatus.RUNNING.value, "YouTube açılıyor...")
    try:
        webbrowser.open(quality_link)
    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"YouTube açılamadı: {e}")
        return [log_file]

    duration = max(1, int(params.duration))
    for i in range(duration):
        if ctx.stop.is_set():
            ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "YouTube durduruldu")
            return [log_file]
        time.sleep(1)
        ctx.progress(((i + 1) / duration) * 100, TestStatus.RUNNING.value,
                     f"YouTube oynatılıyor {i + 1}/{duration}s")

    ctx.progress(100.0, TestStatus.COMPLETED.value, "YouTube tamamlandı")
    return [log_file]
