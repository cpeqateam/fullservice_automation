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
        result = youtube_util.force_play_max(link)
        if result.get("quality_set"):
            ctx.progress(100.0, TestStatus.COMPLETED.value, "▶ YouTube EN YÜKSEK kalitede oynatılıyor")
        else:
            ctx.progress(100.0, TestStatus.COMPLETED.value, "▶ YouTube oynatılıyor (kalite menüsü ayarlanamadı)")
        return [log_file]
    except Exception as e:
        print(f"[YOUTUBE] Selenium ile acilamadi ({e}); tarayiciya fallback.")
        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"Selenium fallback sebebi: {e}\n")

    # 2) Fallback: varsayılan tarayıcıda aç (kalite yalnızca URL ipucu)
    try:
        webbrowser.open(quality_link)
    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"YouTube açılamadı: {e}")
        return [log_file]

    ctx.progress(100.0, TestStatus.COMPLETED.value, "▶ YouTube oynatılıyor (Selenium yok — kalite ipucu)")
    return [log_file]
