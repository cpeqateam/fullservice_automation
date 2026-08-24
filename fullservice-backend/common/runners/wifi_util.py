# -*- coding: utf-8 -*-
"""
Wi-Fi izleme temel fonksiyon kütüphanesi — WLAN arayüzünden veri okur ve log dosyasına yazar.

Windows'ta netsh, macOS'ta CoreWLAN (wifi_util_mac) kullanarak sinyal gücü, kanal,
bant genişliği ve sistem kaynak bilgilerini toplar. WifiService tarafından periyodik
olarak çağrılır; ham veriler metin log dosyasına eklenir.

Orijinal yazar: samet (2023-03-03)

NOT (FULL Servis): Bu dosya GRK'daki functionBase_wifi.py'yi temel alır. CLI'a özel
initialIO()/pyfiglet çıkarıldı. TEK İŞLEVSEL FARK: GERÇEK BSSID desteği — GRK'da (ve
eski FULL Servis'te) BSSID hep 00:00:00:00:00:00 geliyordu çünkü netsh/system_profiler
onu gizliyor. Burada gerçek BSSID OS Wi-Fi API'sinden çekilir (get_wifi_bssid;
Windows WlanApi / macOS airport-wdutil). GRK koduna DOKUNULMADI (kullanıcı isteri).
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
        # macOS okuması wifi_util_mac'e devredilir: CoreWLAN ile TARAMASIZ okur
        # (system_profiler Wi-Fi taraması tetikliyordu, aynı karttaki iperf/YouTube
        # trafiğini yavaşlatıyordu). Geç import — wifi_util_mac bu modülü import ediyor.
        from common.runners import wifi_util_mac
        return wifi_util_mac.readWlan()
    else:
        cmd = "netsh wlan show interfaces"
        shellOutput = subprocess.run(cmd, capture_output=True, text=True, creationflags=NO_WINDOW).stdout
        return shellOutput.split("\n")


# ─────────────────────────────────────────────────────────────────────────────
# GERÇEK BSSID (FULL Servis eki — GRK'da yoktu, BSSID hep 00:00:.. geliyordu)
#
# Sorun: netsh (Windows 11 22H2+) ve system_profiler (macOS) bağlı AP'nin BSSID'ini
# gizlilik gereği GİZLİYOR/redakte ediyor. Bu yüzden metin çıktısından gerçek BSSID
# çıkmaz. Çözüm: işletim sisteminin Wi-Fi API'sini doğrudan sorgulamak.
#   • Windows: Native Wifi API (wlanapi.dll) → WLAN_CONNECTION_ATTRIBUTES.dot11Bssid
#   • macOS  : airport -I (varsa) → wdutil info (sudo gerekebilir)
# Hiçbiri gerçek değer veremezse "" döner ve çağıran eski (redakte) değeri korur.
#
# NOT: En yeni OS sürümlerinde bu API'ler de KONUM İZNİ ister. Gerçek BSSID için:
#   • Windows: Ayarlar → Gizlilik → Konum → açık + "Masaüstü uygulamaları erişebilsin"
#   • macOS  : Sistem Ayarları → Gizlilik/Konum → Terminal/uygulamaya izin
# ─────────────────────────────────────────────────────────────────────────────
_BSSID_RE = re.compile(r"^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$")


def _looks_like_bssid(val) -> bool:
    """Değer gerçek bir BSSID mi (6 hex çift, hepsi sıfır/broadcast DEĞİL)?"""
    if not val:
        return False
    v = str(val).strip().lower()
    if not _BSSID_RE.match(v):
        return False
    return v not in ("00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff")


def _bssid_from_netsh() -> str:
    """netsh çıktısındaki BSSID satırını okur (Konum kapalıysa redakte gelebilir)."""
    try:
        out = subprocess.run("netsh wlan show interfaces", capture_output=True,
                             text=True, creationflags=NO_WINDOW).stdout
        for line in out.split("\n"):
            if "BSSID" in line:
                val = ":".join(line.split(":")[1:]).strip()
                if _looks_like_bssid(val):
                    return val.lower()
    except Exception:
        pass
    return ""


def _bssid_windows() -> str:
    """Windows: önce Native Wifi API (wlanapi.dll) ile gerçek BSSID; olmazsa netsh.
    WlanApi, netsh'in redakte ettiği durumlarda çoğu sürümde gerçek BSSID'i verir."""
    try:
        import ctypes
        from ctypes import wintypes

        wlanapi = ctypes.windll.wlanapi

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                        ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

        class WLAN_INTERFACE_INFO(ctypes.Structure):
            _fields_ = [("InterfaceGuid", GUID),
                        ("strInterfaceDescription", wintypes.WCHAR * 256),
                        ("isState", wintypes.DWORD)]

        class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
            _fields_ = [("dwNumberOfItems", wintypes.DWORD),
                        ("dwIndex", wintypes.DWORD),
                        ("InterfaceInfo", WLAN_INTERFACE_INFO * 8)]

        class DOT11_SSID(ctypes.Structure):
            _fields_ = [("uSSIDLength", wintypes.ULONG), ("ucSSID", ctypes.c_ubyte * 32)]

        class WLAN_ASSOCIATION_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("dot11Ssid", DOT11_SSID),
                        ("dot11BssType", wintypes.DWORD),
                        ("dot11Bssid", ctypes.c_ubyte * 6),
                        ("dot11PhyType", wintypes.DWORD),
                        ("uDot11PhyIndex", wintypes.ULONG),
                        ("wlanSignalQuality", wintypes.ULONG),
                        ("ulRxRate", wintypes.ULONG),
                        ("ulTxRate", wintypes.ULONG)]

        class WLAN_SECURITY_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("bSecurityEnabled", wintypes.BOOL),
                        ("bOneXEnabled", wintypes.BOOL),
                        ("dot11AuthAlgorithm", wintypes.DWORD),
                        ("dot11CipherAlgorithm", wintypes.DWORD)]

        class WLAN_CONNECTION_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("isState", wintypes.DWORD),
                        ("wlanConnectionMode", wintypes.DWORD),
                        ("strProfileName", wintypes.WCHAR * 256),
                        ("wlanAssociationAttributes", WLAN_ASSOCIATION_ATTRIBUTES),
                        ("wlanSecurityAttributes", WLAN_SECURITY_ATTRIBUTES)]

        handle = wintypes.HANDLE()
        negotiated = wintypes.DWORD()
        if wlanapi.WlanOpenHandle(2, None, ctypes.byref(negotiated), ctypes.byref(handle)) != 0:
            return _bssid_from_netsh()
        try:
            p_list = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()
            if wlanapi.WlanEnumInterfaces(handle, None, ctypes.byref(p_list)) != 0:
                return _bssid_from_netsh()
            try:
                lst = p_list.contents
                for idx in range(lst.dwNumberOfItems):
                    guid = lst.InterfaceInfo[idx].InterfaceGuid
                    p_conn = ctypes.POINTER(WLAN_CONNECTION_ATTRIBUTES)()
                    size = wintypes.DWORD()
                    # 7 = wlan_intf_opcode_current_connection
                    ret = wlanapi.WlanQueryInterface(handle, ctypes.byref(guid), 7, None,
                                                     ctypes.byref(size),
                                                     ctypes.byref(p_conn), None)
                    if ret != 0 or not p_conn:
                        continue
                    try:
                        b = p_conn.contents.wlanAssociationAttributes.dot11Bssid
                        mac = ":".join("%02x" % x for x in b)
                        if _looks_like_bssid(mac):
                            return mac
                    finally:
                        wlanapi.WlanFreeMemory(p_conn)
            finally:
                wlanapi.WlanFreeMemory(p_list)
        finally:
            wlanapi.WlanCloseHandle(handle, None)
    except Exception as e:
        print(f"[WIFI] WlanApi BSSID alinamadi ({e}); netsh deneniyor.")

    return _bssid_from_netsh()


def _bssid_macos() -> str:
    """macOS: CoreWLAN'dan gerçek BSSID (tarama YAPMAZ, ~ms). Konum Servisleri izni
    yoksa macOS BSSID'i gizler → '' döner ve çağıran yer varsayılanı kullanır.

    Not: eski sürüm `airport -I` + `wdutil info` deniyordu; airport macOS 14.4'te
    kaldırıldı, wdutil sudo istiyor — ikisi de boşa süreç açıyordu."""
    try:
        from common.runners import wifi_util_mac
        iface = wifi_util_mac._WIFI_CLIENT.interface() if wifi_util_mac._WIFI_CLIENT else None
        val = iface.bssid() if iface else None
        if val and _looks_like_bssid(val):
            return val.lower()
    except Exception as e:
        print(f"[WIFI] CoreWLAN BSSID alinamadi: {e}")
    return ""


def get_wifi_bssid() -> str:
    """Bağlı Wi-Fi AP'sinin GERÇEK BSSID'ini döner (bulunamazsa '')."""
    try:
        return _bssid_macos() if sys.platform == "darwin" else _bssid_windows()
    except Exception as e:
        print(f"[WIFI] BSSID alinamadi: {e}")
        return ""


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

    # BSSID (her iki dilde de ayni). netsh/system_profiler bunu redakte ediyorsa
    # (00:00:.. ya da boş), gerçek BSSID'i OS Wi-Fi API'sinden çekeriz.
    bssid = ""
    for line in sheelOutput:
        if "BSSID" in line:
            bssid = ":".join(line.split(":")[1:]).strip()
            break
    if not _looks_like_bssid(bssid):
        real = get_wifi_bssid()
        if real:
            bssid = real
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
    bssid_hdr = ""
    for i in wlanInfo:
        if "BSSID" in i:
            bssid_hdr = ":".join(i.split(":")[1:]).strip()
            break
    if not _looks_like_bssid(bssid_hdr):
        bssid_hdr = get_wifi_bssid() or bssid_hdr
    log += bssid_hdr

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
