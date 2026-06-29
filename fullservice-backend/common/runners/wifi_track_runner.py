"""
Wi-Fi Track çalıştırıcı — WLAN sinyal/kanal/rx-tx + sistem kaynaklarını periyodik
okuyup log'a yazar.

Ölçüm ve satır formatı GRK functionBase_wifi.py ile BİREBİR AYNIDIR:
  • Windows → [wifi_util.py] (netsh)        ← GRK scriptinin aynısı
  • macOS   → [wifi_util_mac.py] (system_profiler) ← GRK scriptinin macOS kolu
Her saniye bir örnek alınır; satır GRK'nın getPeriodicData satırıyla bayt bayt
aynı biçimde yazılır. Ayrıca özet (DB için) hesaplanır. FULL Servis'e özgü olan
tek şey döngü kontrolüdür (durdurma/ilerleme/canlı pencere/DB) — ölçüm değerleri
ve çıktı formatı GRK'nın koduna aittir, değiştirilmemiştir.
"""
import re
import statistics
import time
from datetime import datetime
from time import asctime

from common.protocol import TestParams, TestStatus
from common.runners.base import RunContext, is_mac, open_log_viewer, close_terminal
from common.runners import wifi_util
from common.runners.wifi_util import SPACER


def _grk_line(signal, systemInfo) -> str:
    """GRK getPeriodicData'nın tek-iterasyon satırının BİREBİR AYNISI."""
    logString = "----- "
    logString += (asctime() + SPACER)
    if signal and any(str(s).strip() for s in signal):
        for s in signal:
            logString += (str(s) + ", ")
        logString = logString[:-2]
    else:
        logString += "00:00:00:00:00:00, disconnected, 0%, 0, 0, 0, N/A"
    logString += SPACER
    for s in systemInfo:
        if isinstance(s, bool):
            logString += str(s) + ", "
        else:
            logString += str(s) + "%, "
    logString = logString[:-2]
    logString += "\n"
    return logString


def _num(val):
    """Bir metinden ilk sayıyı (float) çıkarır: '85%'→85, '866.7 Mbps'→866.7. Yoksa None."""
    if val is None:
        return None
    m = re.search(r"[-\d.]+", str(val).replace(",", "."))
    return float(m.group()) if m else None


def _aggregate(samples: list, start_iso: str, end_iso: str) -> dict:
    """Toplanan örneklerden wifi özeti (DB için) üretir.
    Her örnek: (signal_list, system_list)
      signal_list = [bssid, state, signal%, rx, tx, channel, radio]  (getSignalInfo)
      system_list = [cpu, ram, plugged(bool), battery]               (getSystemInfo)"""
    sig_vals, rx_vals, tx_vals, cpu_vals, ram_vals = [], [], [], [], []
    connected = 0
    channel = protocol = bssid = None

    for signal, system in samples:
        state = (signal[1] if len(signal) > 1 else "") or ""
        sig = _num(signal[2]) if len(signal) > 2 else None
        is_conn = ("disconnected" not in state.lower()) and bool(sig)
        if is_conn:
            connected += 1
            if sig is not None:
                sig_vals.append(sig)
            if len(signal) > 3 and _num(signal[3]) is not None:
                rx_vals.append(_num(signal[3]))
            if len(signal) > 4 and _num(signal[4]) is not None:
                tx_vals.append(_num(signal[4]))
            if len(signal) > 5 and str(signal[5]).strip():
                channel = str(signal[5]).strip()
            if len(signal) > 6 and str(signal[6]).strip():
                protocol = str(signal[6]).strip()
            if len(signal) > 0 and str(signal[0]).strip():
                bssid = str(signal[0]).strip()
        if len(system) > 0 and _num(system[0]) is not None:
            cpu_vals.append(_num(system[0]))
        if len(system) > 1 and _num(system[1]) is not None:
            ram_vals.append(_num(system[1]))

    total = len(samples)

    def _avg(xs):
        return round(statistics.mean(xs), 2) if xs else None

    return {
        "total_samples": total,
        "connected_count": connected,
        "disconnected_count": total - connected,
        "channel": channel,
        "wifi_protocol": protocol,
        "bssid": bssid,
        "avg_signal_percentage": _avg(sig_vals),
        "min_signal_percentage": min(sig_vals) if sig_vals else None,
        "max_signal_percentage": max(sig_vals) if sig_vals else None,
        "avg_rx_rate": _avg(rx_vals),
        "avg_tx_rate": _avg(tx_vals),
        "avg_cpu_usage": _avg(cpu_vals),
        "avg_ram_usage": _avg(ram_vals),
        "test_start_time": start_iso,
        "test_end_time": end_iso,
    }


def run(params: TestParams, ctx: RunContext) -> list[str]:
    duration = max(1, int(params.duration))
    # GRK ile aynı standart: FULL_Service_wifiAnaliz_<brand>_<model>_<fw>_<sn>sn_<ts>.txt
    log_file = ctx.grk_log_path("wifiAnaliz", params.brand, params.model, params.firmware,
                                f"{duration}sn")

    # Platforma uygun WLAN okuyucu (her ikisi de GRK'nın scriptinin aynısı)
    if is_mac():
        from common.runners import wifi_util_mac as wu
    else:
        wu = wifi_util

    ctx.progress(0.0, TestStatus.RUNNING.value, "Wi-Fi analizi başlıyor...")

    # Başlık (istemci/cihaz bilgisi) — GRK getOneTimeInfo
    try:
        wifi_util.getOneTimeInfo(wu.readWlan(), log_file)
    except Exception as e:
        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[uyari] baslik bilgisi alinamadi: {e}\n")

    # Canlı izleme penceresi (best-effort; masaüstü oturumu gerekir)
    viewer = open_log_viewer(log_file, f"Wi-Fi Track [{ctx.node_id}]")

    start_iso = datetime.now().isoformat(timespec="seconds")
    samples: list = []   # (signal, system) — DB özeti için biriktirilir

    def _emit():
        if ctx.result:
            end_iso = datetime.now().isoformat(timespec="seconds")
            ctx.result("wifi", _aggregate(samples, start_iso, end_iso))

    try:
        for i in range(duration):
            if ctx.stop.is_set():
                close_terminal(viewer)
                ctx.progress((i / duration) * 100, TestStatus.STOPPED.value, "Wi-Fi track durduruldu")
                _emit()
                return [log_file]
            start_t = time.time()

            # Tek WLAN okuması (mac'te system_profiler yavaş — çift okuma yok):
            # GRK'nın getSignalInfo/getSystemInfo'su ile ölç, GRK satır formatıyla yaz.
            try:
                signal = wifi_util.getSignalInfo(wu.readWlan())
            except Exception as e:
                print(f"[WIFI] okuma hatasi: {e}")
                signal = []
            try:
                system = wifi_util.getSystemInfo()
            except Exception:
                system = ["0", "0", True, 0]
            wifi_util.writeLogsToFile(_grk_line(signal, system), log_file)
            samples.append((signal, system))

            ctx.progress(((i + 1) / duration) * 100, TestStatus.RUNNING.value,
                         f"Wi-Fi analizi {i + 1}/{duration} sn")
            elapsed = time.time() - start_t
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

        with open(log_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\nBitis: {datetime.now()}\n")
        ctx.progress(100.0, TestStatus.COMPLETED.value, "Wi-Fi analizi tamamlandı")
        _emit()
        return [log_file]

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"Wi-Fi track hatası: {e}")
        return [log_file]
    finally:
        close_terminal(viewer)
