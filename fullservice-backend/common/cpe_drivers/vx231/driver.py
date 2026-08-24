"""
VX231 driver adapter.

Kaynak koddaki VX231/main2.py tek dosyada login + scrape yapıyordu.
XPath/CSS selektör/login akışı AYNEN korunarak modüler hale getirildi.

Login akışı:
    driver.get(http://modem_ip/) -> LOGINPANEL (admin/turktelekom) -> HANDLE_ALERTS
    -> ADVANCED_SECTION (gelişmiş menü)

Desteklenen alanlar (kaynak koddaki GET_SYSTEM / GET_WIFI_24/5 / GET_NETWORK):
    uptime, ram, cpu,
    ipv4_internet_ip,
    ssid_24, ch_24, bw_24, ssid_5, ch_5, bw_5,
    download, upload

Desteklenmeyen:
    dhcp_count, ipv4_voice_*, ipv4_iptv_*, ipv6_*
"""
import time
from . import scraper

BRAND = "ZTE"
MODEL = "VX231"


def connect(driver, modem_ip: str) -> None:
    driver.get(f"http://{modem_ip}/")
    time.sleep(3)
    scraper.LOGINPANEL(driver)
    scraper.HANDLE_ALERTS(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # Orijinal akışta main_loop'ta her turda önce ADVANCED_SECTION açılıyor
    # (uptime/wifi orada okunuyor). Her collect çağrısında aynısını yap.
    try:
        driver.refresh()
        time.sleep(3)
        scraper.HANDLE_ALERTS(driver)
        scraper.ADVANCED_SECTION(driver)
    except Exception:
        pass

    # System (uptime + ram + cpu) tek seferde
    sys_keys = {"uptime", "ram", "cpu"}
    if secilen & sys_keys:
        uptime, ram, cpu = scraper._get_system(driver)
        if "uptime" in secilen: result["uptime"] = uptime
        if "ram"    in secilen: result["ram"]    = ram
        if "cpu"    in secilen: result["cpu"]    = cpu

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

    # Network sayfası: download + upload + wan_ip aynı sayfadan
    net_keys = {"download", "upload", "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime"}
    if secilen & net_keys:
        dl, ul, wan = scraper._get_network(driver)
        if "download"           in secilen: result["download"]           = dl
        if "upload"             in secilen: result["upload"]             = ul
        if "ipv4_internet_ip"   in secilen: result["ipv4_internet_ip"]   = wan
        if "ipv4_internet_status" in secilen: result["ipv4_internet_status"] = "N/A"
        if "ipv4_internet_uptime" in secilen: result["ipv4_internet_uptime"] = "N/A"

    # Desteklenmeyen alanlar
    unsupported = {
        "ipv4_voice_ip", "ipv4_voice_status", "ipv4_voice_uptime",
        "ipv4_iptv_ip",  "ipv4_iptv_status",  "ipv4_iptv_uptime",
        "ipv6_ip",       "ipv6_status",       "ipv6_uptime",
        "dhcp_count",
    }
    for k in secilen & unsupported:
        result[k] = "N/A"

    return result
