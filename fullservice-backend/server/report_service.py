"""
Oturum sonu rapor servisi (sunucu tarafı) — BİLGİSAYAR BAŞINA ping özet Excel'i.

Neden burada? Ping her makinede birden fazla log üretir (modem + internet, IPv4/IPv6).
Her log için ayrı Excel göndermek Telegram'ı gereksiz dosyaya boğuyordu. GRK'da olduğu
gibi (merge_parser.merge_ping_logs) tüm ping logları TEK bir özet Excel'de birleştirilir;
FULL Servis dağıtık olduğu için bu özet HER BİLGİSAYAR İÇİN AYRI üretilir ve dosya adında
bilgisayarın adı yer alır (LINUX / MAC_ETH / MAC_WIFI / WIN_WIFI).

Akış (test bitince, orchestrator._on_session_complete → build_ping_summaries):
  logs/<BILGISAYAR>/<session_id>/*ping*.txt
      → excel_service.ping_summary_excel(...)
      → aynı klasöre FULL_Service_ping_ozet_<BILGISAYAR>_<marka>_<model>_<fw>_<ts>.xlsx
      → FTP: <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/Ping/<BILGISAYAR>/

Böylece 4 ping makinesi (LINUX, MAC_ETH, WIN_WIFI, MAC_WIFI) için 4 özet Excel çıkar;
hangisinin hangi bilgisayara ait olduğu dosya adından bellidir.
"""
from __future__ import annotations

import os

from common.config import LOGS_DIR
from server import excel_service, ftp_service


def _session_dirs(session_id: str) -> list[tuple[str, str]]:
    """Bu oturuma ait (bilgisayar_adi, klasor_yolu) çiftlerini döner."""
    out = []
    if not os.path.isdir(LOGS_DIR):
        return out
    for node_folder in sorted(os.listdir(LOGS_DIR)):
        sdir = os.path.join(LOGS_DIR, node_folder, session_id or "adhoc")
        if os.path.isdir(sdir):
            out.append((node_folder, sdir))
    return out


def _ping_logs(directory: str) -> list[str]:
    """Klasördeki ping ham log .txt dosyalarını (adı sıralı) döner — özet .xlsx hariç."""
    return [
        os.path.join(directory, fn)
        for fn in sorted(os.listdir(directory))
        if fn.lower().endswith(".txt") and "ping" in fn.lower()
    ]


def build_ping_summaries(session_id: str, device: dict, start_time=None) -> list[str]:
    """Her bilgisayar için ping özet Excel'i üretip FTP'ye yükler; üretilen dosya
    yollarını döner (Telegram eki olarak da kullanılır). Hata olursa o bilgisayarı
    atlar — diğerlerinin raporu yine gider."""
    device = device or {}
    brand, model = device.get("brand"), device.get("model")
    firmware = device.get("firmware")

    produced: list[str] = []
    for node_name, sdir in _session_dirs(session_id):
        logs = _ping_logs(sdir)
        if not logs:
            continue
        try:
            xlsx = excel_service.ping_summary_excel(
                logs, node_name, brand, model, firmware,
                out_dir=sdir, test_start_time=start_time,
            )
        except Exception as e:
            print(f"[RAPOR] {node_name} ping ozeti uretilemedi: {e}")
            continue
        if not xlsx:
            continue
        produced.append(xlsx)
        try:
            ftp_service.upload_files_to_ftp(
                [xlsx],
                ftp_service.build_target_dir(brand, model, firmware, "Ping", node_name),
            )
        except Exception as e:
            print(f"[RAPOR] {node_name} ping ozeti FTP'ye gonderilemedi: {e}")
    print(f"[RAPOR] Ping ozet Excel sayisi: {len(produced)}")
    return produced
