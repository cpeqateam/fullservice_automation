"""
G5B2 driver adapter.

Connect: OPENINTERFACE + SIMACCEPT + LOGINPANEL + GIZLILIK + SKIP_PASSWORD_CHANGE
Modem IP default 192.168.0.1 (kaynak kodda 0.x ağı kullanılıyor) — yine
parametrik geçilir, frontend'den ne gelirse o kullanılır.
DHCP_count desteklenmiyor.
"""
import time
from . import scraper

BRAND = "Telli"
MODEL = "G5B2"


def connect(driver, modem_ip: str) -> None:
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.SIMACCEPT(driver)
    scraper.LOGINPANEL(driver)
    scraper.GIZLILIK(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # Orijinal akışta her tur başında ana sayfaya gidiliyor (uptime/trafik orada)
    # Modem IP'sini bilmiyoruz; ancak driver.current_url'den çıkarabiliriz.
    try:
        current = driver.current_url
        # http://192.168.0.1/... formatından ana sayfayı çıkar
        from urllib.parse import urlparse
        host = urlparse(current).hostname
        if host:
            driver.get(f"http://{host}/index.html")
            time.sleep(3)
    except Exception:
        pass

    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    if "uptime" in secilen: result["uptime"] = scraper._get_uptime(driver)

    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
        for prefix, group_key in (
            ("ipv4_internet_", "ipv4_internet"),
            ("ipv4_voice_",    "ipv4_voice"),
            ("ipv4_iptv_",     "ipv4_iptv"),
            ("ipv6_",          "ipv6_internet"),
        ):
            ip, status, uptime = wan.get(group_key, ("N/A", "N/A", "N/A"))
            for fkey, val in (
                (f"{prefix}ip",     ip),
                (f"{prefix}status", status),
                (f"{prefix}uptime", uptime),
            ):
                if fkey in secilen:
                    result[fkey] = val

    if "ram" in secilen: result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen: result["cpu"] = scraper._get_cpu(driver)

    if {"ssid_24", "ch_24", "bw_24"} & secilen:
        ssid, ch, bw = scraper._get_wifi_24(driver)
        if "ssid_24" in secilen: result["ssid_24"] = ssid
        if "ch_24"   in secilen: result["ch_24"]   = ch
        if "bw_24"   in secilen: result["bw_24"]   = bw

    if {"ssid_5", "ch_5", "bw_5"} & secilen:
        ssid, ch, bw = scraper._get_wifi_5(driver)
        if "ssid_5" in secilen: result["ssid_5"] = ssid
        if "ch_5"   in secilen: result["ch_5"]   = ch
        if "bw_5"   in secilen: result["bw_5"]   = bw

    if {"download", "upload"} & secilen:
        # Trafik için ana sayfaya tekrar dön (orijinal akışta da yapılıyor)
        try:
            from urllib.parse import urlparse
            host = urlparse(driver.current_url).hostname
            if host:
                driver.get(f"http://{host}/index.html")
                time.sleep(3)
        except Exception:
            pass
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    # G5B2 DHCP_count desteklemiyor — seçildiyse "N/A" döner
    if "dhcp_count" in secilen:
        result["dhcp_count"] = "N/A"

    return result
