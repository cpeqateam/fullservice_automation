"""
FULL Servis — Veritabanı yazma servisi (sunucu tarafı).

Test sonuçlarını PostgreSQL'e (cpeqadb) yazar. Sonuçlar GRK ile ORTAK birleşik
tablolara (test_session/ping_test/wifi_analysis/speed_test/iperf_test) yazılır;
her satır test_name ('FULL_SERVIS') ile GRK satırlarından ayrışır. Tablo adları
aşağıdaki TABLO ADLARI sabitlerinde tutulur (tek değişim noktası).

GRK'daki app/services/db_service.py mantığının dağıtık (çok-düğümlü) karşılığıdır:
  • Her satıra test_name='FULL_SERVIS' yazılır (GRK satırlarından ayırt etmek için).
  • Her sonuç satırında node_name vardır (hangi makine: LINUX/MAC_ETH/...).

Bağlantı yoksa (firmware_db.SessionLocal=None) tüm fonksiyonlar sessizce atlar;
testler DB olmadan da çalışmaya devam eder.

Bağlantı/sertifika yapılandırması firmware_db.py'de yapılır; buradaki yazma
işlemleri o modülün hazırladığı SessionLocal'ı (aynı SSL bağlantısı) kullanır.
"""
from __future__ import annotations

from common import firmware_db

# ── TABLO ADLARI ────────────────────────────────────────────────────────
# Ortak sonuç tabloları (copy_ staging'den final adlara yükseltildi).
T_FIRMWARE = "firmware"            # combobox + FK kaynağı
T_SESSION  = "test_session"
T_PING     = "ping_test"
T_SPEED    = "speed_test"
T_WIFI     = "wifi_analysis"
T_IPERF    = "iperf_test"

TEST_NAME = "FULL_SERVIS"          # bu projenin tüm satırlarına yazılır


# ── Tip dönüştürme yardımcıları (None-güvenli) ──────────────────────────
def _f(val, decimals: int = 3):
    """float'a çevirir; çevrilemezse None döner (DB'de NULL)."""
    if val is None:
        return None
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return None


def _i(val):
    """int'e çevirir; çevrilemezse None döner."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _s(val):
    """str'e çevirir; None ise None bırakır."""
    return None if val is None else str(val)


def db_available() -> bool:
    """DB bağlantısı (SessionLocal) hazır mı? Değilse tüm yazma fonksiyonları sessizce atlar."""
    return firmware_db.SessionLocal is not None


def _get_firmware_id(db, brand, model, firmware):
    """Marka/model/firmware'den firmware_id bulur (LOWER/TRIM ile esnek eşleşme).
    Bulamazsa None döner — oturum yine NULL firmware_id ile oluşturulur."""
    if not (brand and model and firmware):
        return None
    from sqlalchemy import text
    try:
        row = db.execute(text(
            f"SELECT firmware_id FROM {T_FIRMWARE} "
            "WHERE LOWER(TRIM(brand)) = LOWER(TRIM(:b)) "
            "AND LOWER(TRIM(model)) = LOWER(TRIM(:m)) "
            "AND LOWER(TRIM(firmware_version)) = LOWER(TRIM(:f)) LIMIT 1"
        ), {"b": brand, "m": model, "f": firmware}).fetchone()
        if row:
            return row[0]
        print(f"[DB] Firmware eslesmedi: {brand!r}/{model!r}/{firmware!r} (firmware_id=NULL)")
    except Exception as e:
        print(f"[DB] Firmware sorgusu hatasi: {e}")
    return None


# ── OTURUM ──────────────────────────────────────────────────────────────
def create_session(brand, model, firmware, start_time,
                   has_ping=False, has_speedtest=False, has_wifi=False,
                   has_iperf=False):
    """test_session'a yeni satır ekler, oluşan session_id'yi döner.
    DB yoksa veya hata olursa None döner (test yine çalışır)."""
    if not db_available():
        print("[DB] Baglanti yok — test_session olusturulamadi (test devam eder).")
        return None

    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        firmware_id = _get_firmware_id(db, brand, model, firmware)
        row = db.execute(text(
            f"INSERT INTO {T_SESSION} "
            "(firmware_id, test_name, session_start_time, "
            " has_ping_test, has_speedtest, has_wifi_analysis, has_iperf_test) "
            "VALUES (:fid, :tn, :st, :hp, :hs, :hw, :hi) RETURNING session_id"
        ), {
            "fid": firmware_id, "tn": TEST_NAME, "st": start_time,
            "hp": has_ping, "hs": has_speedtest, "hw": has_wifi, "hi": has_iperf,
        }).fetchone()
        db.commit()
        session_id = row[0]
        print(f"[DB] test_session olusturuldu: session_id={session_id} (firmware_id={firmware_id})")
        return session_id
    except Exception as e:
        db.rollback()
        print(f"[DB] test_session olusturulamadi: {e}")
        return None
    finally:
        db.close()


def update_session_end(session_id, end_time, test_duration,
                       ftp_file_path=None, error_log_ftp_path=None):
    """Oturumun bitiş zamanı/süresi/FTP yollarını günceller."""
    if not db_available() or not session_id:
        return
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        db.execute(text(
            f"UPDATE {T_SESSION} SET session_end_time=:et, test_duration=:dur, "
            "ftp_file_path=:ftp, error_log_ftp_path=:err WHERE session_id=:sid"
        ), {
            "sid": session_id, "et": end_time, "dur": _i(test_duration),
            "ftp": ftp_file_path, "err": error_log_ftp_path,
        })
        db.commit()
        print(f"[DB] test_session guncellendi (bitis): session_id={session_id}")
    except Exception as e:
        db.rollback()
        print(f"[DB] test_session guncellenemedi: {e}")
    finally:
        db.close()


# ── PING ────────────────────────────────────────────────────────────────
def save_ping(session_id, node_name, stats: dict, ftp_file_path=None):
    """ping_test'e bir ping özeti satırı yazar."""
    if not db_available() or not session_id:
        return
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        db.execute(text(
            f"INSERT INTO {T_PING} "
            "(session_id, test_name, node_name, target_ip, ip_version, "
            " total_pings, successful_pings, failed_pings, success_rate, "
            " packet_loss_percent, min_time, max_time, avg_time, median_time, "
            " std_dev_time, ftp_file_path, test_start_time, test_end_time) "
            "VALUES (:sid, :tn, :nn, :tip, :ipv, :tot, :suc, :fail, :sr, "
            " :loss, :mn, :mx, :avg, :med, :std, :ftp, :ts, :te)"
        ), {
            "sid": session_id, "tn": TEST_NAME, "nn": node_name,
            "tip": _s(stats.get("target_ip")), "ipv": _s(stats.get("ip_version", "IPv4")),
            "tot": _i(stats.get("total_pings")), "suc": _i(stats.get("successful_pings")),
            "fail": _i(stats.get("failed_pings")), "sr": _f(stats.get("success_rate"), 2),
            "loss": _f(stats.get("packet_loss_percent"), 2),
            "mn": _f(stats.get("min_time")), "mx": _f(stats.get("max_time")),
            "avg": _f(stats.get("avg_time")), "med": _f(stats.get("median_time")),
            "std": _f(stats.get("std_dev_time")), "ftp": ftp_file_path,
            "ts": stats.get("test_start_time"), "te": stats.get("test_end_time"),
        })
        db.commit()
        print(f"[DB] ping_test yazildi: node={node_name} target={stats.get('target_ip')}")
    except Exception as e:
        db.rollback()
        print(f"[DB] ping_test yazilamadi: {e}")
    finally:
        db.close()


# ── FTP YOLU GÜNCELLEME (oturum sonu) ───────────────────────────────────
# Sonuç satırları test biterken yazılır; o an dosya henüz FTP'ye gitmemiştir,
# bu yüzden ftp_file_path yalnızca hedef KLASÖRü gösterir. Oturum sonunda
# dosyalar yüklendikten sonra burası satırları gerçek DOSYA yoluyla günceller —
# test platformundaki "indir" butonu bu tam yolu kullanır.
_FTP_UPDATE_TABLES = {"ping": T_PING, "iperf": T_IPERF, "wifi": T_WIFI, "speed": T_SPEED}


def update_session_error_log(session_id, error_log_ftp_path: str) -> bool:
    """test_session.error_log_ftp_path'i, FTP'ye yüklenen error_log dosyasının TAM
    yoluyla günceller — test platformundaki "Error Log İndir" butonu bunu kullanır."""
    if not db_available() or not session_id or not error_log_ftp_path:
        return False
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        db.execute(text(
            f"UPDATE {T_SESSION} SET error_log_ftp_path = :err WHERE session_id = :sid"
        ), {"err": error_log_ftp_path, "sid": session_id})
        db.commit()
        print(f"[DB] test_session.error_log_ftp_path guncellendi: {error_log_ftp_path}")
        return True
    except Exception as e:
        db.rollback()
        print(f"[DB] error_log_ftp_path guncellenemedi: {e}")
        return False
    finally:
        db.close()


def update_ftp_file_path(session_id, kind: str, node_name: str, ftp_file_path: str) -> int:
    """Bir oturumdaki (kind, node_name) satırlarının ftp_file_path'ini tam dosya
    yoluyla günceller. Güncellenen satır sayısını döner (DB yoksa 0)."""
    table = _FTP_UPDATE_TABLES.get(kind)
    if not db_available() or not session_id or not table or not ftp_file_path:
        return 0
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        res = db.execute(text(
            f"UPDATE {table} SET ftp_file_path = :ftp "
            "WHERE session_id = :sid AND node_name = :nn AND test_name = :tn"
        ), {"ftp": ftp_file_path, "sid": session_id, "nn": node_name, "tn": TEST_NAME})
        db.commit()
        n = res.rowcount or 0
        print(f"[DB] {table} ftp_file_path guncellendi: node={node_name} satir={n}")
        return n
    except Exception as e:
        db.rollback()
        print(f"[DB] {table} ftp_file_path guncellenemedi ({node_name}): {e}")
        return 0
    finally:
        db.close()


# ── IPERF ───────────────────────────────────────────────────────────────
def save_iperf(session_id, node_name, server_node_name, stats: dict, ftp_file_path=None):
    """iperf_test'e bir iperf özeti satırı yazar."""
    if not db_available() or not session_id:
        return
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        db.execute(text(
            f"INSERT INTO {T_IPERF} "
            "(session_id, test_name, node_name, server_node_name, server_ip, "
            " port, parallel, duration, sender_mbps, receiver_mbps, "
            " ftp_file_path, test_start_time, test_end_time) "
            "VALUES (:sid, :tn, :nn, :snn, :sip, :port, :par, :dur, "
            " :snd, :rcv, :ftp, :ts, :te)"
        ), {
            "sid": session_id, "tn": TEST_NAME, "nn": node_name,
            "snn": server_node_name, "sip": _s(stats.get("server_ip")),
            "port": _i(stats.get("port")), "par": _i(stats.get("parallel")),
            "dur": _i(stats.get("duration")), "snd": _f(stats.get("sender_mbps"), 2),
            "rcv": _f(stats.get("receiver_mbps"), 2), "ftp": ftp_file_path,
            "ts": stats.get("test_start_time"), "te": stats.get("test_end_time"),
        })
        db.commit()
        print(f"[DB] iperf_test yazildi: node={node_name} -> server={server_node_name}")
    except Exception as e:
        db.rollback()
        print(f"[DB] iperf_test yazilamadi: {e}")
    finally:
        db.close()


# ── WIFI ────────────────────────────────────────────────────────────────
def save_wifi(session_id, node_name, stats: dict, ftp_file_path=None):
    """wifi_analysis'e bir wifi özeti satırı yazar."""
    if not db_available() or not session_id:
        return
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        db.execute(text(
            f"INSERT INTO {T_WIFI} "
            "(session_id, test_name, node_name, total_samples, disconnected_count, "
            " connected_count, channel, wifi_protocol, bssid, "
            " avg_signal_percentage, min_signal_percentage, max_signal_percentage, "
            " avg_rx_rate, avg_tx_rate, avg_cpu_usage, avg_ram_usage, "
            " ftp_file_path, test_start_time, test_end_time) "
            "VALUES (:sid, :tn, :nn, :ts_, :dc, :cc, :ch, :wp, :bs, "
            " :asig, :msig, :xsig, :arx, :atx, :acpu, :aram, :ftp, :ts, :te)"
        ), {
            "sid": session_id, "tn": TEST_NAME, "nn": node_name,
            "ts_": _i(stats.get("total_samples")), "dc": _i(stats.get("disconnected_count")),
            "cc": _i(stats.get("connected_count")), "ch": _s(stats.get("channel")),
            "wp": _s(stats.get("wifi_protocol")), "bs": _s(stats.get("bssid")),
            "asig": _f(stats.get("avg_signal_percentage"), 2),
            "msig": _f(stats.get("min_signal_percentage"), 2),
            "xsig": _f(stats.get("max_signal_percentage"), 2),
            "arx": _f(stats.get("avg_rx_rate"), 2), "atx": _f(stats.get("avg_tx_rate"), 2),
            "acpu": _f(stats.get("avg_cpu_usage"), 2), "aram": _f(stats.get("avg_ram_usage"), 2),
            "ftp": ftp_file_path,
            "ts": stats.get("test_start_time"), "te": stats.get("test_end_time"),
        })
        db.commit()
        print(f"[DB] wifi_analysis yazildi: node={node_name}")
    except Exception as e:
        db.rollback()
        print(f"[DB] wifi_analysis yazilamadi: {e}")
    finally:
        db.close()


# ── SPEED (FULL Serviste kullanılmıyor; bütünlük için) ──────────────────
def save_speed(session_id, node_name, stats: dict, ftp_file_path=None):
    """speed_test'e satır yazar. FULL Serviste speedtest rolü yok; ileride
    bir otomasyon eklerse diye hazır durur."""
    if not db_available() or not session_id:
        return
    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        db.execute(text(
            f"INSERT INTO {T_SPEED} "
            "(session_id, test_name, node_name, total_measurements, "
            " avg_download_mbps, avg_upload_mbps, min_download_mbps, max_download_mbps, "
            " min_upload_mbps, max_upload_mbps, latency, jitter, server_name, ftp_file_path) "
            "VALUES (:sid, :tn, :nn, :tm, :ad, :au, :mnd, :mxd, :mnu, :mxu, "
            " :lat, :jit, :srv, :ftp)"
        ), {
            "sid": session_id, "tn": TEST_NAME, "nn": node_name,
            "tm": _i(stats.get("total_measurements")),
            "ad": _f(stats.get("avg_download_mbps")), "au": _f(stats.get("avg_upload_mbps")),
            "mnd": _f(stats.get("min_download_mbps")), "mxd": _f(stats.get("max_download_mbps")),
            "mnu": _f(stats.get("min_upload_mbps")), "mxu": _f(stats.get("max_upload_mbps")),
            "lat": _f(stats.get("latency")), "jit": _f(stats.get("jitter")),
            "srv": _s(stats.get("server_name")), "ftp": ftp_file_path,
        })
        db.commit()
        print(f"[DB] speed_test yazildi: node={node_name}")
    except Exception as e:
        db.rollback()
        print(f"[DB] speed_test yazilamadi: {e}")
    finally:
        db.close()
