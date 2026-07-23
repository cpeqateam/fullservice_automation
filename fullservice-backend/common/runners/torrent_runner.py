"""
Torrent çalıştırıcı — qBittorrent Web API ile sürekli indirme döngüsü (modeme yük).

GRK pc_control_service._torrent_loop_worker mantığının portudur: qBittorrent'i
başlatır, Web UI'ye (admin / Admin123 @ :8080) giriş yapar, magnet'i ekler,
indirme ilerlemesini dashboard'a yansıtır, tamamlanınca dosyaları silip yeniden
ekler — durdurulana kadar. Magnet, config.json defaults.torrent_magnet'ten gelir.

Yalnızca Windows düğümünde (win_wifi) çalışır. qBittorrent kurulu ve Web UI açık
(admin/Admin123, port 8080) olmalıdır.

Torrent yalnızca YÜK BASICIDIR; ölçüm/rapor üretmez. Bu yüzden LOG DOSYASI ÜRETMEZ
(kullanıcı isteri) — ilerleme yalnızca konsola yazılır ve boş liste döner, dolayısıyla
FTP/Telegram/DB'ye hiçbir şey gitmez.
"""
import time
from datetime import datetime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext
from common.runners import torrent_util

QB_URL = "http://127.0.0.1:8080"
QB_USER = "admin"
QB_PASS = "Admin123"


def run(params: TestParams, ctx: RunContext) -> list[str]:
    """qBittorrent ile magnet (GTA5) indirme döngüsünü koşturur (gerçek yük). torrent_recycle_gb
    kadar inince siler/yeniden başlar (0 = sadece %100'de siler). Log üretmez; boş liste döner."""
    magnet = (params.torrent_magnet or "").strip()

    if not magnet:
        ctx.progress(100.0, TestStatus.ERROR.value,
                     "Magnet link boş (config.json → defaults.torrent_magnet).")
        return []

    def log(line: str):
        """İlerlemeyi konsola yazar (dosya üretilmez — kullanıcı isteri)."""
        print(f"[TORRENT:{ctx.node_id}] [{datetime.now():%H:%M:%S}] {line}")

    log(f"Baslangic. Magnet: {magnet[:80]}...")

    try:
        ctx.progress(0.0, TestStatus.RUNNING.value, "qBittorrent başlatılıyor...")
        ok = torrent_util.ensure_qbittorrent_running()
        if not ok:
            msg = "qBittorrent başlatılamadı veya Web UI port 8080'de açılmadı. qBittorrent'i elle aç → Tools→Options→Web UI: aktif, port 8080."
            log(msg)
            ctx.progress(100.0, TestStatus.ERROR.value, msg)
            return []

        session = torrent_util.login_qbittorrent(QB_URL, QB_USER, QB_PASS)
        if not session:
            msg = (
                "qBittorrent Web UI'ye giriş yapılamadı. "
                "Kontrol: 1) qBittorrent açık mı?  "
                "2) Tools→Options→Web UI: aktif, port 8080, kullanıcı 'admin', şifre 'Admin123'  "
                "3) 'Bypass authentication for localhost' KAPALI olmalı"
            )
            ctx.progress(100.0, TestStatus.ERROR.value, msg)
            log(f"Web UI giris basarisiz. {msg}")
            return []

        # Bu kadar bayt inince hepsini silip yeniden başla (disk dolmasın + sürekli yük).
        # 0 ise: yalnızca %100 tamamlanınca sil.
        recycle_bytes = max(0.0, float(params.torrent_recycle_gb)) * 1_000_000_000

        iteration = 0
        while not ctx.stop.is_set():
            iteration += 1
            ctx.progress(5.0, TestStatus.RUNNING.value, f"#{iteration} — Torrent ekleniyor...")
            torrent_util.add_torrent(session, QB_URL, magnet)
            log(f"#{iteration} torrent eklendi")
            ctx.progress(10.0, TestStatus.RUNNING.value, f"#{iteration} — İndirme izleniyor...")

            recycle = False
            # İndirme tamamlanana VEYA boyut sınırına gelene kadar ilerlemeyi yansıt
            while not ctx.stop.is_set():
                torrents = torrent_util.list_torrents(session, QB_URL)
                if torrents:
                    avg = sum(t["progress"] for t in torrents) / len(torrents)
                    downloaded = sum(t.get("completed", 0) for t in torrents)  # diskteki bayt
                    gb = downloaded / 1_000_000_000
                    pct = 10.0 + avg * 85.0
                    ctx.progress(pct, TestStatus.RUNNING.value,
                                 f"#{iteration} — İndiriliyor %{avg * 100:.0f} ({gb:.1f} GB)")
                    if all(t["progress"] == 1.0 for t in torrents):
                        break
                    if recycle_bytes and downloaded >= recycle_bytes:
                        recycle = True
                        break
                time.sleep(3)

            if ctx.stop.is_set():
                break

            # Tamamlandı ya da sınıra gelindi → HEPSİNİ diskten sil, döngü yeniden
            reason = f"{params.torrent_recycle_gb} GB sınırı" if recycle else "tamamlandı"
            ctx.progress(97.0, TestStatus.RUNNING.value, f"#{iteration} — {reason}, siliniyor...")
            torrent_util.remove_all_torrents(session, QB_URL)
            log(f"#{iteration} {reason}, dosyalar silindi, dongu yeniden")
            time.sleep(2)

        # Çıkarken yarım kalan indirmeyi de diskten temizle
        torrent_util.remove_all_torrents(session, QB_URL)
        ctx.progress(100.0, TestStatus.STOPPED.value, "Torrent durduruldu (dosyalar silindi)")
        log("Durduruldu, dosyalar silindi.")
        return []

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"Torrent hatası: {e}")
        log(f"HATA: {e}")
        return []
