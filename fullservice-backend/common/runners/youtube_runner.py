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
    """YouTube videosunu tarayıcıda (Selenium/Chrome) en yüksek kalitede oynatır — yük basıcı.
    Üretilen log dosyası yollarını döner."""
    link = (params.youtube_link or "").strip()
    # GRK ile aynı standart: FULL_Service_youtube_<brand>_<model>_<fw>_<ts>.txt
    log_file = ctx.grk_log_path("youtube", params.brand, params.model, params.firmware)

    if not link:
        ctx.progress(100.0, TestStatus.ERROR.value, "YouTube linki boş.")
        return []

    # URL ipucu (Selenium başarısız olursa fallback için): vq=hd2160 + hd=1
    quality_link = link
    if "youtu" in quality_link:
        sep = "&" if "?" in quality_link else "?"
        quality_link = f"{quality_link}{sep}vq=hd2160&hd=1"

    with open(log_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"FULL Servis YouTube — Node: {ctx.node_id}\n")
        f.write(f"Link: {link}\nAcilis: {datetime.now()}\n")

    ctx.progress(0.0, TestStatus.RUNNING.value, "YouTube açılıyor (en yüksek kalite)...")

    # 1) Selenium ile EN YÜKSEK kaliteye zorla (Chrome + selenium gerekir)
    try:
        from common.runners import youtube_util
        youtube_util.force_play_max(link)
        ctx.progress(100.0, TestStatus.COMPLETED.value, "▶ YouTube oynatılıyor")
        return [log_file]
    except Exception as e:
        print(f"[YOUTUBE] Selenium ile acilamadi ({e}); tarayiciya fallback.")
        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"Selenium fallback sebebi: {e}\n")

    # 2) Fallback: varsayılan tarayıcıda aç
    try:
        webbrowser.open(quality_link)
    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"YouTube açılamadı: {e}")
        return [log_file]

    ctx.progress(100.0, TestStatus.COMPLETED.value, "▶ YouTube oynatılıyor")
    return [log_file]
