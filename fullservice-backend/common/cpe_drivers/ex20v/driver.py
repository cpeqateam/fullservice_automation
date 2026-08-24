"""
EX20V driver adapter.

Bu dosya scraper.py'daki orijinal koda dokunmadan üstüne
standart driver sözleşmesini geçirir. Scraper.py her zaman kaynak
altındaki orijinaliyle 1:1 eşleştirilebilir.

Sözleşme: app/cpe_drivers/base.py
"""
import time
from . import scraper

BRAND = "TP-Link"
MODEL = "EX20V"


def connect(driver, modem_ip: str) -> None:
    """Modem arayüzünü aç, login ol, şifre değiştirme ekranını geç."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    """(yazilim, donanim, seri) döner."""
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    """
    Frontend'in granular anahtarlarına göre seçili alanları kazır ve
    {anahtar: değer} olarak döndür. secilen'de olmayan anahtarları üretmez.
    """
    result: dict = {}

    # WAN tablosundan gelen tüm IPv4/IPv6 alanları aynı sayfada okunur,
    # bu yüzden ihtiyaç varsa tek seferde alıp parçala.
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
        groups = [
            ("ipv4_internet_", "ipv4_internet"),
            ("ipv4_voice_",    "ipv4_voice"),
            ("ipv4_iptv_",     "ipv4_iptv"),
            ("ipv6_",          "ipv6_internet"),
        ]
        for prefix, group_key in groups:
            ip, status, uptime = wan.get(group_key, ("N/A", "N/A", "N/A"))
            for fkey, val in (
                (f"{prefix}ip",     ip),
                (f"{prefix}status", status),
                (f"{prefix}uptime", uptime),
            ):
                if fkey in secilen:
                    result[fkey] = val

    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)
    if "ram" in secilen:
        result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen:
        result["cpu"] = scraper._get_cpu(driver)

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
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
