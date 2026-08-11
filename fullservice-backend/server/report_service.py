"""
Oturum sonu rapor servisi (sunucu tarafı) — BİLGİSAYAR BAŞINA ping ve iperf özet
Excel'i üretir, FTP'ye yükler ve DB'deki ftp_file_path'i gerçek dosya yoluyla
günceller.

Neden özet? Ping her makinede birden fazla log üretir (modem + internet, IPv4/IPv6).
Her log için ayrı Excel göndermek Telegram'ı gereksiz dosyaya boğuyordu. GRK'da olduğu
gibi (merge_parser.merge_ping_logs) tüm ping logları TEK bir özet Excel'de birleştirilir;
FULL Servis dağıtık olduğu için bu özet HER BİLGİSAYAR İÇİN AYRI üretilir ve dosya adında
bilgisayarın adı yer alır (LINUX / MAC_ETH / MAC_WIFI / WIN_WIFI). iperf için de aynı
desende bir özet Excel (Grafik + DataLog) üretilir.

Neden ftp_file_path burada güncelleniyor? Test biterken yazılan DB satırı, dosya
henüz FTP'ye gitmediği için yalnızca hedef KLASÖRü işaret ediyordu; test
platformundaki "indir" butonu ise tam DOSYA yolu bekliyor (GRK da öyle yazıyor).

Akış (test bitince, notification_service._worker → finalize_session):
  logs/<BILGISAYAR>/<session_id>/*ping*.txt  → fullServis_pingOzet_<BILGISAYAR>_...xlsx
  logs/<BILGISAYAR>/<session_id>/*iperf*.txt → fullServis_iperfOzet_<BILGISAYAR>_...xlsx
      → FTP: <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<BILGISAYAR>/
      → DB : ilgili satırların ftp_file_path'i bu tam yolla güncellenir

NOT: Ham loglar (ve wifi Excel'i) FTP'ye burada değil, test SIRASINDA log geldikçe
yüklenir — bkz. orchestrator.upload_log_to_ftp.
"""
from __future__ import annotations

import os

from common.config import LOGS_DIR
from server import db_service, excel_service, ftp_service


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


def _txt_logs(directory: str, keyword: str) -> list[str]:
    """Klasördeki, adında `keyword` geçen ham .txt loglarını (adı sıralı) döner."""
    return [
        os.path.join(directory, fn)
        for fn in sorted(os.listdir(directory))
        if fn.lower().endswith(".txt") and keyword in fn.lower()
    ]


def _iperf_logs(directory: str) -> list[str]:
    """iperf ham loglarını döner. Özet için CLIENT logları tercih edilir; bir
    bilgisayarda yalnızca server logu varsa (iperf_server rolü) o kullanılır."""
    logs = _txt_logs(directory, "iperf")
    client = [p for p in logs if "iperfserver" not in os.path.basename(p).lower()]
    return client or logs


def build_ping_summaries(session_id: str, device: dict, start_time=None) -> dict[str, str]:
    """Her bilgisayar için ping özet Excel'i üretir. {bilgisayar: xlsx_yolu} döner.
    Hata olursa o bilgisayarı atlar — diğerlerinin raporu yine üretilir."""
    device = device or {}
    produced: dict[str, str] = {}
    for node_name, sdir in _session_dirs(session_id):
        logs = _txt_logs(sdir, "ping")
        if not logs:
            continue
        try:
            xlsx = excel_service.ping_summary_excel(
                logs, node_name, device.get("brand"), device.get("model"),
                device.get("firmware"), out_dir=sdir, test_start_time=start_time,
            )
        except Exception as e:
            print(f"[RAPOR] {node_name} ping ozeti uretilemedi: {e}")
            continue
        if xlsx:
            produced[node_name] = xlsx
    print(f"[RAPOR] Ping ozet Excel sayisi: {len(produced)}")
    return produced


def build_iperf_summaries(session_id: str, device: dict,
                          server_node_name: str | None = None) -> dict[str, str]:
    """Her bilgisayar için iperf özet Excel'i (Grafik + DataLog) üretir.
    {bilgisayar: xlsx_yolu} döner."""
    device = device or {}
    produced: dict[str, str] = {}
    for node_name, sdir in _session_dirs(session_id):
        logs = _iperf_logs(sdir)
        if not logs:
            continue
        try:
            xlsx = excel_service.iperf_summary_excel(
                logs, node_name, server_node_name=server_node_name,
                brand=device.get("brand"), model=device.get("model"),
                firmware=device.get("firmware"), out_dir=sdir,
            )
        except Exception as e:
            print(f"[RAPOR] {node_name} iperf ozeti uretilemedi: {e}")
            continue
        if xlsx:
            produced[node_name] = xlsx
    print(f"[RAPOR] Iperf ozet Excel sayisi: {len(produced)}")
    return produced


def _upload_summary(local: str, device: dict, test_type: str, node_name: str) -> str | None:
    """Bir özet Excel'ini FTP'ye yükler; başarılıysa TAM FTP yolunu döner.
    (DB'deki ftp_file_path bu tam yolla güncellenir — indirme butonu bunu kullanır.)"""
    device = device or {}
    target = ftp_service.build_target_dir(
        device.get("brand"), device.get("model"), device.get("firmware"),
        test_type, node_name)
    try:
        ftp_service.upload_files_to_ftp([local], target)
        return f"{target}/{os.path.basename(local)}"
    except Exception as e:
        print(f"[RAPOR] {node_name} {test_type} ozeti FTP'ye gonderilemedi: {e}")
        return None


def finalize_session(session_id: str, device: dict, start_time=None,
                     db_session_id=None, server_node_name: str | None = None) -> list[str]:
    """Oturum sonu rapor işini yapar; Telegram'a gidecek Excel yollarını döner.

    Ham loglar (ve wifi Excel'i) FTP'ye zaten test sırasında, log geldikçe
    yüklenir (orchestrator.upload_log_to_ftp). Burada yalnızca oturum sonunda
    ÜRETİLEN özet Excel'ler yüklenir ve DB'deki ftp_file_path'ler bu dosyaların
    TAM yoluyla güncellenir."""
    ping_x = build_ping_summaries(session_id, device, start_time)
    iperf_x = build_iperf_summaries(session_id, device, server_node_name)

    # Özet Excel'leri FTP'ye yükle + DB satırlarını tam dosya yoluyla güncelle.
    for kind, test_type, produced in (("ping", "Ping", ping_x),
                                      ("iperf", "Iperf", iperf_x)):
        for node_name, local in produced.items():
            remote = _upload_summary(local, device, test_type, node_name)
            if remote and db_session_id:
                db_service.update_ftp_file_path(db_session_id, kind, node_name, remote)

    # wifi'de ayrı bir "özet" yok — ham logdan üretilen .xlsx'in kendisi rapordur ve
    # FTP'ye test sırasında zaten yüklendi; burada yalnızca DB yolu yazılır.
    # Tip tespiti yüklemeyle AYNI fonksiyonla yapılır; aksi halde (ör. adında
    # "macWifi" geçen ping özeti) yanlış dosya wifi satırına yazılabilirdi.
    wifi_x: dict[str, str] = {}
    for node_name, sdir in _session_dirs(session_id):
        for fn in sorted(os.listdir(sdir)):
            if fn.lower().endswith(".xlsx") and ftp_service.test_type_from_filename(fn) == "Wifi":
                local = os.path.join(sdir, fn)
                wifi_x[node_name] = local
                if db_session_id:
                    target = ftp_service.build_target_dir(
                        (device or {}).get("brand"), (device or {}).get("model"),
                        (device or {}).get("firmware"), "Wifi", node_name)
                    db_service.update_ftp_file_path(
                        db_session_id, "wifi", node_name, f"{target}/{fn}")

    # Telegram eki: yalnızca Excel'ler (ham .txt'ler FTP'de ve sunucuda duruyor)
    return sorted({*ping_x.values(), *iperf_x.values(), *wifi_x.values()})
