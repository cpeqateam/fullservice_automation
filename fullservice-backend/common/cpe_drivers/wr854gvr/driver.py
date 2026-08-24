"""
WR854GVR (Aidata) driver adapter.

Kaynak modül WR854GVR/main.py tek dosyada login + scrape yapıyordu.
Bizim sistemimize entegre ederken kaynak koddaki XPath/selektör/login akışı AYNEN
korunarak modüler hale getirildi (browser.py + pages/*.py + scraper.py + driver.py).

Login akışı (kaynak koddaki login() fonksiyonu):
    driver.get(http://modem_ip/) -> LOGIN (admin/admin + cancel)

Desteklenen alanlar (kaynak koddaki collect_data + get_bandwidths fonksiyonlarından):
    uptime, ram, cpu, ipv4_internet_ip,
    ssid_24, ch_24, bw_24,
    ssid_5,  ch_5,  bw_5

Desteklenmeyen alanlar (arayüzde bulunamamış / kaynak kodda yok):
    download, upload, dhcp_count, ipv4_voice_*, ipv4_iptv_*, ipv6_*
"""
import time
from . import scraper

BRAND = "Aidata"
MODEL = "WR854GVR"


def connect(driver, modem_ip: str) -> None:
    driver.get(f"http://{modem_ip}/")
    time.sleep(5)
    scraper.LOGIN(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # Kaynak kod CPU/RAM/WAN IP'yi aynı iframe içinde okuyor — bir defada çek
    sys_keys = {"cpu", "ram", "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime"}
    if secilen & sys_keys:
        cpu, ram, wan = scraper._get_cpu_ram_wan(driver)
        if "cpu" in secilen: result["cpu"] = cpu
        if "ram" in secilen: result["ram"] = ram
        if "ipv4_internet_ip" in secilen:     result["ipv4_internet_ip"]     = wan
        # WR854GVR arayüzünde status/uptime ayrı kazınmıyor
        if "ipv4_internet_status" in secilen: result["ipv4_internet_status"] = "N/A"
        if "ipv4_internet_uptime" in secilen: result["ipv4_internet_uptime"] = "N/A"

    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

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

    # Desteklenmeyen alanlar — istek geldiyse "N/A" döner
    unsupported = {
        "ipv4_voice_ip", "ipv4_voice_status", "ipv4_voice_uptime",
        "ipv4_iptv_ip",  "ipv4_iptv_status",  "ipv4_iptv_uptime",
        "ipv6_ip",       "ipv6_status",       "ipv6_uptime",
        "download", "upload", "dhcp_count",
    }
    for k in secilen & unsupported:
        result[k] = "N/A"

    return result
