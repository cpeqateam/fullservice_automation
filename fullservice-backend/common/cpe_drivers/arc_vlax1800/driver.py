"""
ARC-VLAX1800 driver adapter.

Connect: OPENINTERFACE + LOGINPANEL + SKIP_PASSWORD_CHANGE
Modem IP kaynak kodda 192.168.1.1 hardcoded; burada frontend'den gelen
`modem_ip` kullanılır.

Desteklenmeyen FRONTEND_KEYS (kaynak kod zaten "N/A" döner; biz de driver
seviyesinde aynı şekilde "N/A" dönüyoruz):
    - ram, cpu              (system_page.get_ram / get_cpu)
    - download, upload      (traffic_page)
    - ipv4_voice_*          (wan_page sadece Internet & IPTV ayrıştırıyor)
    - ipv6_*                (wan_page IPv6 satırını ayırmıyor)
    - dhcp_count            (page var ama Bağlı Cihazlar menüsü modele göre
                             değişebilir — desteği page sayesinde aktif)
"""
import time
from . import scraper

BRAND = "Arcadyan"
MODEL = "ARC-VLAX1800"


def connect(driver, modem_ip: str) -> None:
    # Orijinal akış: LOGOUT → OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE
    # OPENINTERFACE/LOGOUT hardcoded 192.168.1.1'e gidiyor; biz modem_ip ile
    # önce manuel yönlendirelim, sonra zinciri çalıştıralım.
    driver.get(f"http://{modem_ip}/")
    time.sleep(3)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # ---- Uptime ----
    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    # ---- WAN grubu ----
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }
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

    # ---- RAM / CPU (model desteklemiyor — page "N/A" döner) ----
    if "ram" in secilen: result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen: result["cpu"] = scraper._get_cpu(driver)

    # ---- Wi-Fi 2.4 ----
    if {"ssid_24", "ch_24", "bw_24"} & secilen:
        ssid, ch, bw = scraper._get_wifi_24(driver)
        if "ssid_24" in secilen: result["ssid_24"] = ssid
        if "ch_24"   in secilen: result["ch_24"]   = ch
        if "bw_24"   in secilen: result["bw_24"]   = bw

    # ---- Wi-Fi 5 ----
    if {"ssid_5", "ch_5", "bw_5"} & secilen:
        ssid, ch, bw = scraper._get_wifi_5(driver)
        if "ssid_5" in secilen: result["ssid_5"] = ssid
        if "ch_5"   in secilen: result["ch_5"]   = ch
        if "bw_5"   in secilen: result["bw_5"]   = bw

    # ---- Trafik (model desteklemiyor — page "N/A" döner) ----
    if {"download", "upload"} & secilen:
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    # ---- DHCP client sayısı ----
    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
