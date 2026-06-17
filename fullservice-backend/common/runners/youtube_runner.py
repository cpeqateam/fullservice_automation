"""
YouTube çalıştırıcı — varsayılan tarayıcıda videoyu açar.

Kullanıcı isteri: YouTube'un ilerlemesini saniye saniye izlemeye gerek yok. Video
bir kez açılır ve o makinedeki kişi sekmeyi kapatana kadar açık/oynuyor kalır.
Bu yüzden runner sadece videoyu açar ve tek bir "oynatılıyor" bildirimi verir
(geri sayım/ilerleme çubuğu doldurma yok). İlerleme çubuğu %100 dolu görünür.

GRK pc_control_service.start_youtube mantığı (1080p zorlama) korunmuştur.
"""
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

    # Tek bildirim — kapatana kadar açık kalır, ayrıca takip etmiyoruz.
    ctx.progress(100.0, TestStatus.COMPLETED.value, "▶ YouTube oynatılıyor (kapatana kadar açık)")
    return [log_file]
