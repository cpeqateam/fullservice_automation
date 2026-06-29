# -*- coding: utf-8 -*-
"""
Wi-Fi izleme temel fonksiyon kütüphanesi — WLAN arayüzünden veri okur ve log dosyasına yazar.

Windows'ta netsh, macOS'ta system_profiler komutunu kullanarak sinyal gücü, kanal,
bant genişliği ve sistem kaynak bilgilerini toplar. WifiService tarafından periyodik
olarak çağrılır; ham veriler metin log dosyasına eklenir.

Orijinal yazar: samet (2023-03-03)

NOT (FULL Servis): Bu dosya GRK'daki functionBase_wifi.py'nin BİREBİR AYNISIDIR.
Yalnızca CLI'a özel initialIO() ve onun pyfiglet bağımlılığı çıkarıldı; ölçüm/parse/
yazma fonksiyonları (readWlan, getSignalInfo, getSystemInfo, getOneTimeInfo,
getPeriodicData, createFileName) hiç değiştirilmeden korundu.
"""

# %%
from time import sleep, asctime
import subprocess
import platform

NO_WINDOW = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
import psutil

SPACER = "\t|\t"

import sys
import re

def readWlan():
    """Aktif WLAN arayüzünün bilgilerini işletim sistemine göre okur ve satır listesi döner."""
    if sys.platform == "darwin":
        # macOS implementation using system_profiler
        cmd = "system_profiler SPAirPortDataType"
        shellOutput = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=NO_WINDOW).stdout

        # Parse macOS output to simulate netsh output
        simulated_netsh = []

        # Defaults
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

        for line in shellOutput.split("\n"):
            line = line.strip()
            if line.startswith("Status: Connected"):
                state = "connected"
                is_connected = True
            elif line.startswith("MAC Address:") and mac_address == "00:00:00:00:00:00":
                mac_address = line.split(":", 1)[1].strip()
            elif is_connected and line.startswith("Channel:"):
                # Channel: 36 (5GHz, 160MHz) -> 36
                ch_match = re.search(r'Channel:\s*(\d+)', line)
                if ch_match: channel = ch_match.group(1)
            elif is_connected and line.startswith("Signal / Noise:"):
                # Signal / Noise: -73 dBm / -91 dBm
                sig_match = re.search(r'Signal / Noise:\s*([-\d]+)', line)
                if sig_match:
                    rssi = int(sig_match.group(1))
                    # rough conversion from RSSI to %:
                    # -50 or better = 100%, -100 = 0%
                    pct = max(0, min(100, 2 * (rssi + 100)))
                    signal = f"{pct}%"
            elif is_connected and line.startswith("Transmit Rate:"):
                tx_rate = line.split(":", 1)[1].strip()
                rx_rate = tx_rate # Approximation since macOS doesn't split it usually
            elif is_connected and line.startswith("PHY Mode:"):
                radio = line.split(":", 1)[1].strip()

        # Build fake netsh output
        simulated_netsh.append(f"    Name                   : Wi-Fi")
        simulated_netsh.append(f"    Description            : AirPort")
        simulated_netsh.append(f"    State                  : {state}")
        simulated_netsh.append(f"    Physical address       : {mac_address}")

        if state == "connected":
            simulated_netsh.append(f"    SSID                   : {ssid}")
            simulated_netsh.append(f"    BSSID                  : {bssid}")
            simulated_netsh.append(f"    Network type           : Infrastructure")
            simulated_netsh.append(f"    Radio type             : {radio}")
            simulated_netsh.append(f"    Channel                : {channel}")
            simulated_netsh.append(f"    Receive rate (Mbps)    : {rx_rate}")
            simulated_netsh.append(f"    Transmit rate (Mbps)   : {tx_rate}")
            simulated_netsh.append(f"    Signal                 : {signal}")

        return simulated_netsh
    else:
        cmd = "netsh wlan show interfaces"
        shellOutput = subprocess.run(cmd, capture_output=True, text=True, creationflags=NO_WINDOW).stdout
        return shellOutput.split("\n")

def getSignalInfo(sheelOutput):
    """WLAN çıktı satırlarından BSSID, durum, sinyal, RX/TX hızı, kanal ve radyo tipini çıkarır.

    netsh wlan show interfaces ciktisi sistem diline gore lokalizedir. Turkce
    Windows'ta "State" -> "Durum", "Signal" -> "Sinyal" gibi karsiliklar gelir.
    Bu yuzden her metrik icin Ingilizce + Turkce alternatif anahtar kelimeleri
    kontrol ediyoruz; ilk eslesen satirin ":" sonrasi degerini aliyoruz.
    """

    def _find(keywords):
        """Verilen anahtar kelimelerden herhangi birini iceren ilk satiri bul."""
        # Daha spesifik ifadeler once denenmeli (ornegin "Receive rate" "rate"den once)
        for line in sheelOutput:
            low = line.lower()
            for kw in keywords:
                if kw.lower() in low:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        return ":".join(parts[1:]).strip() if kw == "BSSID" else parts[-1].strip()
            # devam et
        return ""

    theList = []

    # BSSID (her iki dilde de ayni)
    bssid = ""
    for line in sheelOutput:
        if "BSSID" in line:
            bssid = ":".join(line.split(":")[1:]).strip()
            break
    theList.append(bssid)

    # State / Durum
    theList.append(_find(["State", "Durum"]))

    # Signal / Sinyal — "Signal" eslesmesi "Profile"de geciyor olabilir mi diye
    # case-insensitive ve tam kelime olarak ariyoruz
    sig_val = ""
    for line in sheelOutput:
        s = line.strip().lower()
        # "signal" tek basina basta gelmeli, "signal " veya "sinyal " gibi
        if s.startswith("signal") or s.startswith("sinyal"):
            sig_val = line.split(":")[-1].strip()
            break
    theList.append(sig_val)

    # Receive rate (Mbps) / Alma hızı (Mb/sn)
    theList.append(_find(["Receive rate", "Alma hızı", "Alma hizi"]))

    # Transmit rate (Mbps) / İletim hızı (Mb/sn)
    theList.append(_find(["Transmit rate", "İletim hızı", "Iletim hizi"]))

    # Channel / Kanal
    theList.append(_find(["Channel", "Kanal"]))

    # Radio type / Radyo türü / Telsiz türü
    theList.append(_find(["Radio type", "Radyo türü", "Radyo turu", "Telsiz türü", "Telsiz turu"]))

    return theList


def getSystemInfo():
    """CPU kullanımı, RAM kullanımı, priz durumu ve pil yüzdesini liste olarak döner.

    Pil sensörü bulunmayan masaüstü PC'lerde psutil.sensors_battery() None döner.
    Bu durumda makinenin AC ile çalıştığını varsayıyoruz (plugged=True, percent=100).
    """
    memoryUsage = psutil.virtual_memory()[2]
    cpuUsage = psutil.cpu_percent(0)
    battery = psutil.sensors_battery()
    if battery is None:
        # Masaüstü PC: pil sensörü yok, sürekli AC bağlı kabul ediyoruz
        plugged = True
        percent = 100
    else:
        plugged = battery.power_plugged
        percent = battery.percent

    return [str(cpuUsage), str(memoryUsage), plugged, percent]


def writeLogsToFile(log, filename):
    """Verilen log metnini belirtilen dosyaya UTF-8 olarak ekler (append modu)."""
    # filename burada mutlak yol olarak gelir (WifiService tarafından)
    with open(filename, "a", encoding="utf-8") as f:
        f.writelines(log)


def getOneTimeInfo(wlanInfo, filename):
    """Test başında bir kez çalışır; istemci ve cihaz bilgilerini log başlığı olarak yazar."""

    log = "************************ Türk Telekom Wi-Fi State Tracker Logs *****************************\n\n"


    log += "\t\t\t\t\t\t************ Client Info *****************\n"
    log += ("\t\t\t\t\t\tInterface: ")

    for i in wlanInfo:
        if "Name" in i:
            log += (i.split(":")[-1].strip() + "\n")
            break

    log += ("\t\t\t\t\t\tWi-Fi Card: ")
    for i in wlanInfo:
        if "Description" in i:
            log += (i.split(":")[-1].strip() + "\n")
            break

    log += ("\t\t\t\t\t\tHWADDR(MAC): ")
    for i in wlanInfo:
        if "Physical address" in i:
            log += ":".join(i.split(":")[1:])
            break

    log += "\n\n\t\t\t\t\t\t************ DUT Info ********************\n"

    log += ("\t\t\t\t\t\tSSID: ")
    for i in wlanInfo:
        if "SSID" in i:
            log += (i.split(":")[-1].strip() + "\n")
            break

    log += ("\t\t\t\t\t\tBSSID: ")
    for i in wlanInfo:
        if "BSSID" in i:
            log += ":".join(i.split(":")[1:])
            break

    log += "\n\n\t\t\t\t\t\t******************************************\n"


    log += "\n\n****************************** Periyodik Data Blogu ***************************************\n\n"

    log += "----- Time | State, BSSID, Signal Level, Receive Rate, Transmit Rate, Channel, 802.11x | CPU Usage, RAM Usage, Power State, Battery Percentage\n\n"

    writeLogsToFile(log, filename)
    print(log)


def createFileName(inputs):
    """Marka, model, firmware, süre ve zaman damgasından benzersiz log dosyası adı üretir."""
    # Son parametre olarak gelen tarih ve saati ekliyoruz
    return "grk_wifiAnaliz_" + inputs[0] + "_" + inputs[1] + "_" + inputs[2] + "_" + str(inputs[3]) + "sn_" + str(inputs[4]) + ".txt"

def getPeriodicData(duration, filename):
    """Her iterasyonda anlık sinyal ve sistem bilgisini okuyup log satırı olarak dosyaya ekler.

    Sinyal veya sistem bilgisi alınamazsa hata yutulur ve placeholder satır yazılır.
    Bu sayede tek bir hatalı okuma tüm Wi-Fi analizini kırıp Excel'i bomboş bırakmaz.
    """

    logString = "----- "

    for _i in range(duration):
        currentTime = asctime()
        logString += (currentTime + SPACER)

        # ----- Sinyal bilgisi -----
        try:
            signal = getSignalInfo(readWlan())
        except Exception as e:
            print(f"[WIFI] readWlan/getSignalInfo hatasi: {e}")
            signal = []

        # getSignalInfo her zaman 7-elemanli liste dondurur (bos olsa bile).
        # Tum elemanlar bos/bosluksa netsh veri dondurmemis demektir — placeholder kullan.
        if signal and any(str(s).strip() for s in signal):
            for s in signal:
                logString += (str(s) + ", ")
            logString = logString[:-2]
        else:
            # Wi-Fi karti yok / baglantisiz: parse.py 7 alan bekliyor
            # (BSSID, State, Signal%, RX, TX, Channel, Radio)
            logString += "00:00:00:00:00:00, disconnected, 0%, 0, 0, 0, N/A"
        logString += SPACER

        # ----- Sistem bilgisi -----
        try:
            systemInfo = getSystemInfo()
        except Exception as e:
            print(f"[WIFI] getSystemInfo hatasi: {e}")
            systemInfo = ["0", "0", True, 0]

        for s in systemInfo:
            # Bool degerlere yuzde isareti ekleme
            if isinstance(s, bool):
                logString += str(s) + ", "
            else:
                logString += str(s) + "%, "
        logString = logString[:-2]
        logString += "\n"

        print(logString)
        try:
            writeLogsToFile(logString, filename)
        except Exception as e:
            print(f"[WIFI] writeLogsToFile hatasi: {e}")

        # sleep(1)

        logString = "----- "
