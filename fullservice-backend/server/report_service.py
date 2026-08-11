"""
Oturum sonu rapor servisi (sunucu tarafı) — özet Excel'leri üretir, TÜM oturum
dosyalarını FTP'ye yükler ve DB'deki ftp_file_path'leri gerçek dosya yoluyla
günceller.

Neden tek yerde? Test biterken yazılan DB satırı, dosya henüz FTP'ye gitmediği
için yalnızca hedef KLASÖRü işaret ediyordu; test platformundaki "indir" butonu
ise tam DOSYA yolu beklediğinden hata veriyordu. Yükleme ve DB güncellemesi
artık burada, oturum sonunda, sırayla yapılır.

Akış (test bitince, notification_service._worker → finalize_session):
  1) Özet Excel'ler üretilir (bilgisayar başına):
       ping  logları → fullServis_pingOzet_<BILGISAYAR>_..._.xlsx
       iperf logları → fullServis_iperfOzet_<BILGISAYAR>_..._.xlsx
     (wifi Excel'i ham log yüklenirken zaten üretilmiştir)
  2) Oturumun TÜM dosyaları (ham .txt + .xlsx) FTP'ye, test tipine göre
     ayrılmış klasörlere yüklenir — zip DEĞİL, tek tek dosya olarak; böylece
     test platformundan tek tek indirilebilir:
       <MARKA>/<MODEL>/<FIRMWARE>/FULLSERVIS/<TestTipi>/<BILGISAYAR>/<dosya>
  3) DB'deki ping/iperf/wifi satırlarının ftp_file_path'i, o bilgisayarın
     ÖZET Excel'inin tam FTP yoluyla güncellenir.
  4) Telegram'a gidecek Excel listesi döner (zip'i notification_service yapar).
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


def upload_session_to_ftp(session_id: str, device: dict) -> dict[str, str]:
    """Oturumun TÜM dosyalarını (ham .txt + .xlsx) FTP'ye, test tipine göre
    ayrılmış klasörlere yükler. {yerel_yol: tam_ftp_yolu} döner.

    Aynı klasöre gidecek dosyalar tek bağlantıda toplu gönderilir (her dosya için
    yeniden bağlanmamak adına)."""
    device = device or {}
    brand, model, fw = device.get("brand"), device.get("model"), device.get("firmware")

    groups: dict[str, list[str]] = {}          # hedef klasör → yerel dosyalar
    mapping: dict[str, str] = {}               # yerel dosya → tam FTP yolu
    for node_name, sdir in _session_dirs(session_id):
        for fn in sorted(os.listdir(sdir)):
            local = os.path.join(sdir, fn)
            if not os.path.isfile(local):
                continue
            test_type = ftp_service.test_type_from_filename(fn)
            target = ftp_service.build_target_dir(brand, model, fw, test_type, node_name)
            groups.setdefault(target, []).append(local)
            mapping[local] = f"{target}/{fn}"

    total = 0
    for target, files in sorted(groups.items()):
        try:
            ftp_service.upload_files_to_ftp(files, target)
            total += len(files)
        except Exception as e:
            print(f"[RAPOR] FTP yukleme hatasi ({target}): {e}")
    print(f"[RAPOR] FTP'ye yuklenen dosya sayisi: {total}")
    return mapping


def finalize_session(session_id: str, device: dict, start_time=None,
                     db_session_id=None, server_node_name: str | None = None) -> list[str]:
    """Oturum sonu tüm rapor işini yapar; Telegram'a gidecek Excel yollarını döner.

    Sıra önemlidir: önce özet Excel'ler üretilir (ki FTP taramasına dahil olsunlar),
    sonra her şey FTP'ye yüklenir, en sonda DB'deki ftp_file_path'ler yüklenen
    ÖZET dosyanın tam yoluyla güncellenir."""
    ping_x = build_ping_summaries(session_id, device, start_time)
    iperf_x = build_iperf_summaries(session_id, device, server_node_name)

    uploaded = upload_session_to_ftp(session_id, device)

    # DB satırlarını, o bilgisayarın özet dosyasının TAM FTP yoluyla güncelle.
    # wifi'de ayrı bir "özet" yok — ham logdan üretilen .xlsx'in kendisi rapordur.
    # Tip tespiti yüklemeyle AYNI fonksiyonla yapılır; aksi halde (ör. adında
    # "macWifi" geçen ping özeti) yanlış dosya wifi satırına yazılabilirdi.
    wifi_x: dict[str, str] = {}
    for node_name, sdir in _session_dirs(session_id):
        for fn in sorted(os.listdir(sdir)):
            if fn.lower().endswith(".xlsx") and ftp_service.test_type_from_filename(fn) == "Wifi":
                wifi_x[node_name] = os.path.join(sdir, fn)

    if db_session_id:
        for kind, produced in (("ping", ping_x), ("iperf", iperf_x), ("wifi", wifi_x)):
            for node_name, local in produced.items():
                remote = uploaded.get(local)
                if remote:
                    db_service.update_ftp_file_path(db_session_id, kind, node_name, remote)

    # Telegram eki: yalnızca Excel'ler (ham .txt'ler FTP'de ve sunucuda duruyor)
    return sorted({*ping_x.values(), *iperf_x.values(), *wifi_x.values()})
