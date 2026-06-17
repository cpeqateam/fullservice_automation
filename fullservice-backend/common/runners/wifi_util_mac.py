"""
Wi-Fi izleme — macOS WLAN okuma (system_profiler).

GRK functionBase_wifi'nin macOS koluna dayanır. `system_profiler SPAirPortDataType`
çıktısını parse edip netsh benzeri satırlara çevirir; böylece [wifi_util.py]'deki
ortak parse/yazma yardımcıları (getSignalInfo, sample_once, getOneTimeInfo) macOS'ta
da aynen çalışır.

NOT: Mac'te wifi_track ölçümü biraz farklı olabiliyor; takım liderinden gelecek
gerçek mac koduyla bu dosyayı (özellikle readWlan) değiştir. Şimdilik GRK'daki
çalışan macOS yaklaşımının portudur.
"""
import re
import subprocess


def readWlan():
    """macOS: system_profiler çıktısını netsh-benzeri satır listesine çevirir.

    NOT: `system_profiler SPAirPortDataType` macOS'ta bazen çok yavaştır / asılı
    kalır (kullanıcı gözleminde örnekleme 32/33'te takıldı). Bu yüzden timeout ile
    çağrılır; süre aşarsa boş çıktıyla devam edilir (o örnek "disconnected" yazılır,
    döngü takılmaz)."""
    try:
        out = subprocess.run("system_profiler SPAirPortDataType", shell=True,
                             capture_output=True, text=True, timeout=8).stdout
    except Exception as e:
        print(f"[WIFI-MAC] system_profiler okunamadi/timeout: {e}")
        out = ""

    bssid = "00:00:00:00:00:00"
    ssid = "Unknown"
    state = "disconnected"
    signal = "0%"
    rx_rate = "0"
    tx_rate = "0"
    channel = "1"
    radio = "802.11"
    mac_address = "00:00:00:00:00:00"
    is_connected = False

    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("Status: Connected"):
            state = "connected"
            is_connected = True
        elif line.startswith("MAC Address:") and mac_address == "00:00:00:00:00:00":
            mac_address = line.split(":", 1)[1].strip()
        elif is_connected and line.startswith("Channel:"):
            m = re.search(r"Channel:\s*(\d+)", line)
            if m:
                channel = m.group(1)
        elif is_connected and line.startswith("Signal / Noise:"):
            m = re.search(r"Signal / Noise:\s*([-\d]+)", line)
            if m:
                rssi = int(m.group(1))
                pct = max(0, min(100, 2 * (rssi + 100)))
                signal = f"{pct}%"
        elif is_connected and line.startswith("Transmit Rate:"):
            tx_rate = line.split(":", 1)[1].strip()
            rx_rate = tx_rate
        elif is_connected and line.startswith("PHY Mode:"):
            radio = line.split(":", 1)[1].strip()

    sim = [
        "    Name                   : Wi-Fi",
        "    Description            : AirPort",
        f"    State                  : {state}",
        f"    Physical address       : {mac_address}",
    ]
    if state == "connected":
        sim += [
            f"    SSID                   : {ssid}",
            f"    BSSID                  : {bssid}",
            "    Network type           : Infrastructure",
            f"    Radio type             : {radio}",
            f"    Channel                : {channel}",
            f"    Receive rate (Mbps)    : {rx_rate}",
            f"    Transmit rate (Mbps)   : {tx_rate}",
            f"    Signal                 : {signal}",
        ]
    return sim
