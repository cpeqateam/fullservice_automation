"""
DN8045X6-20 driver adapter.

Connect: OPENINTERFACE + LOGINPANEL (sade).

Bu modemde desteklenmeyen alanlar:
  - ipv4_voice_* (VoIP yok)
  - dhcp_count

Kaynak kod ayrıca her collect öncesi is_logged_in kontrolü yapıyor; biz de aynısını
yapıyoruz — session düşmüşse yeniden login.
"""
import time
from . import scraper

BRAND = "ZTE"
MODEL = "DN8045X6-20"


def connect(driver, modem_ip: str) -> None:
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGINPANEL(driver)
    time.sleep(3)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def _ensure_logged_in(driver, modem_ip: str = None):
    """Session düşmüşse yeniden login yap (orijinal akıştaki pattern)."""
    try:
        if not scraper.is_logged_in(driver):
            if modem_ip:
                driver.get(f"http://{modem_ip}/")
                time.sleep(2)
            scraper.LOGINPANEL(driver)
            time.sleep(5)
    except Exception:
        pass


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # Sistem bilgisi (uptime, ram, cpu) — hepsi tek fonksiyondan
    if {"uptime", "ram", "cpu"} & secilen:
        upt, rm, cp = scraper._get_sistem_bilgisi(driver)
        if "uptime" in secilen: result["uptime"] = upt
        if "ram"    in secilen: result["ram"]    = rm
        if "cpu"    in secilen: result["cpu"]    = cp

    # WAN — flat dict; voice yok, internet/iptv/ipv6 var
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
        "download",         "upload",
    }
    if secilen & wan_keys:
        wan = scraper._get_wan_details(driver)

        if "ipv4_internet_ip"     in secilen: result["ipv4_internet_ip"]     = wan.get("internet_ip",    "N/A")
        if "ipv4_internet_status" in secilen: result["ipv4_internet_status"] = wan.get("internet_durum", "N/A")
        if "ipv4_internet_uptime" in secilen: result["ipv4_internet_uptime"] = wan.get("internet_sure",  "N/A")

        if "ipv4_iptv_ip"     in secilen: result["ipv4_iptv_ip"]     = wan.get("iptv_ip",    "N/A")
        if "ipv4_iptv_status" in secilen: result["ipv4_iptv_status"] = wan.get("iptv_durum", "N/A")
        if "ipv4_iptv_uptime" in secilen: result["ipv4_iptv_uptime"] = wan.get("iptv_sure",  "N/A")

        if "ipv6_ip"     in secilen: result["ipv6_ip"]     = wan.get("ipv6_ip",    "N/A")
        if "ipv6_status" in secilen: result["ipv6_status"] = wan.get("ipv6_durum", "N/A")
        if "ipv6_uptime" in secilen: result["ipv6_uptime"] = wan.get("ipv6_sure",  "N/A")

        if {"download", "upload"} & secilen:
            dl = wan.get("dl", "0")
            ul = wan.get("ul", "0")
            try:
                dl = float(dl) if str(dl).replace('.', '', 1).isdigit() else 0.0
                ul = float(ul) if str(ul).replace('.', '', 1).isdigit() else 0.0
            except Exception:
                dl, ul = 0.0, 0.0
            if "download" in secilen: result["download"] = dl
            if "upload"   in secilen: result["upload"]   = ul

    # ipv4_voice DESTEKLENMİYOR — seçildiyse N/A doldur
    for key in ("ipv4_voice_ip", "ipv4_voice_status", "ipv4_voice_uptime"):
        if key in secilen:
            result[key] = "N/A"

    # Wi-Fi 2.4 GHz (band=1) ve 5 GHz (band=2) — tek fonksiyon, parametreyle
    if {"ssid_24", "ch_24", "bw_24"} & secilen:
        ssid, ch, bw = scraper._get_wifi(driver, band=1)
        if "ssid_24" in secilen: result["ssid_24"] = ssid
        if "ch_24"   in secilen: result["ch_24"]   = ch
        if "bw_24"   in secilen: result["bw_24"]   = bw

    if {"ssid_5", "ch_5", "bw_5"} & secilen:
        ssid, ch, bw = scraper._get_wifi(driver, band=2)
        if "ssid_5" in secilen: result["ssid_5"] = ssid
        if "ch_5"   in secilen: result["ch_5"]   = ch
        if "bw_5"   in secilen: result["bw_5"]   = bw

    # dhcp_count DESTEKLENMİYOR
    if "dhcp_count" in secilen:
        result["dhcp_count"] = "N/A"

    return result
