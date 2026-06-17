"""
Wi-Fi izleme temel fonksiyonları (Windows / netsh) + ortak yardımcılar.

GRK `utils/wifi/functionBase_wifi.py` portudur. WLAN arayüzünden sinyal/kanal/
rx-tx/radyo bilgisini ve sistem kaynaklarını (CPU/RAM/pil) okur, log dosyasına
satır satır yazar. wifi_track_runner her saniye `sample_once()` çağırır.

macOS için readWlan ayrı dosyadadır: [wifi_util_mac.py]. getSignalInfo / sample_once
gibi parse/yazma yardımcıları platform-bağımsızdır; her iki platform da bunları kullanır.
"""
import platform
import re
import subprocess
import sys
from time import asctime

NO_WINDOW = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
SPACER = "\t|\t"


def readWlan():
    """Windows: `netsh wlan show interfaces` çıktısını satır listesi olarak döner."""
    out = subprocess.run("netsh wlan show interfaces", capture_output=True,
                         text=True, creationflags=NO_WINDOW).stdout
    return out.split("\n")


def getSignalInfo(shellOutput):
    """WLAN çıktısından [BSSID, State, Signal, RX, TX, Channel, Radio] çıkarır.

    netsh çıktısı sistem diline göre lokalizedir (TR Windows'ta Durum/Sinyal/Kanal);
    her metrik için İngilizce + Türkçe anahtar kelimeleri denenir.
    """
    def _find(keywords):
        for line in shellOutput:
            low = line.lower()
            for kw in keywords:
                if kw.lower() in low:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        return ":".join(parts[1:]).strip() if kw == "BSSID" else parts[-1].strip()
        return ""

    theList = []

    bssid = ""
    for line in shellOutput:
        if "BSSID" in line:
            bssid = ":".join(line.split(":")[1:]).strip()
            break
    theList.append(bssid)

    theList.append(_find(["State", "Durum"]))

    sig_val = ""
    for line in shellOutput:
        s = line.strip().lower()
        if s.startswith("signal") or s.startswith("sinyal"):
            sig_val = line.split(":")[-1].strip()
            break
    theList.append(sig_val)

    theList.append(_find(["Receive rate", "Alma hızı", "Alma hizi"]))
    theList.append(_find(["Transmit rate", "İletim hızı", "Iletim hizi"]))
    theList.append(_find(["Channel", "Kanal"]))
    theList.append(_find(["Radio type", "Radyo türü", "Radyo turu", "Telsiz türü", "Telsiz turu"]))
    return theList


def getSystemInfo():
    """[CPU%, RAM%, AC takılı mı, pil%] döner. psutil yoksa makul placeholder döner."""
    try:
        import psutil
        mem = psutil.virtual_memory()[2]
        cpu = psutil.cpu_percent(0)
        battery = psutil.sensors_battery()
        if battery is None:
            plugged, percent = True, 100
        else:
            plugged, percent = battery.power_plugged, battery.percent
        return [str(cpu), str(mem), plugged, percent]
    except Exception:
        return ["0", "0", True, 100]


def writeLogsToFile(log, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.writelines(log)


def createFileName(inputs):
    """[brand, model, firmware, duration, timestamp] → benzersiz log dosyası adı."""
    return ("full_wifiAnaliz_" + str(inputs[0]) + "_" + str(inputs[1]) + "_" +
            str(inputs[2]) + "_" + str(inputs[3]) + "sn_" + str(inputs[4]) + ".txt")


def getOneTimeInfo(wlanInfo, filename):
    """Test başında bir kez: istemci/cihaz bilgisi log başlığı."""
    log = "************************ Turk Telekom Wi-Fi State Tracker Logs *****************************\n\n"
    log += "\t\t\t\t\t\t************ Client Info *****************\n"
    log += "\t\t\t\t\t\tInterface: "
    for i in wlanInfo:
        if "Name" in i:
            log += i.split(":")[-1].strip() + "\n"
            break
    log += "\t\t\t\t\t\tWi-Fi Card: "
    for i in wlanInfo:
        if "Description" in i:
            log += i.split(":")[-1].strip() + "\n"
            break
    log += "\t\t\t\t\t\tHWADDR(MAC): "
    for i in wlanInfo:
        if "Physical address" in i:
            log += ":".join(i.split(":")[1:])
            break
    log += "\n\n\t\t\t\t\t\t************ DUT Info ********************\n"
    log += "\t\t\t\t\t\tSSID: "
    for i in wlanInfo:
        if "SSID" in i:
            log += i.split(":")[-1].strip() + "\n"
            break
    log += "\t\t\t\t\t\tBSSID: "
    for i in wlanInfo:
        if "BSSID" in i:
            log += ":".join(i.split(":")[1:])
            break
    log += "\n\n\t\t\t\t\t\t******************************************\n"
    log += "\n\n****************************** Periyodik Data Blogu ***************************************\n\n"
    log += ("----- Time | State, BSSID, Signal Level, Receive Rate, Transmit Rate, "
            "Channel, 802.11x | CPU Usage, RAM Usage, Power State, Battery Percentage\n\n")
    writeLogsToFile(log, filename)


def sample_once(read_wlan, filename):
    """Tek bir periyodik örnek satırı: anlık sinyal + sistem bilgisini log'a yazar
    ve satırı (string) döner. read_wlan: platforma uygun WLAN okuma fonksiyonu."""
    logString = "----- " + asctime() + SPACER

    try:
        signal = getSignalInfo(read_wlan())
    except Exception as e:
        print(f"[WIFI] readWlan/getSignalInfo hatasi: {e}")
        signal = []

    if signal and any(str(s).strip() for s in signal):
        logString += ", ".join(str(s) for s in signal)
    else:
        logString += "00:00:00:00:00:00, disconnected, 0%, 0, 0, 0, N/A"
    logString += SPACER

    try:
        systemInfo = getSystemInfo()
    except Exception as e:
        print(f"[WIFI] getSystemInfo hatasi: {e}")
        systemInfo = ["0", "0", True, 0]

    parts = []
    for s in systemInfo:
        parts.append(str(s) if isinstance(s, bool) else f"{s}%")
    logString += ", ".join(parts) + "\n"

    try:
        writeLogsToFile(logString, filename)
    except Exception as e:
        print(f"[WIFI] writeLogsToFile hatasi: {e}")
    return logString
