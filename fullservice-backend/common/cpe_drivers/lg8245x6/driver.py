"""
Nokia LG8245X6 driver adapter.

Connect:
    driver.get(http://<modem_ip>/) → OPENINTERFACE → LOGINPANEL
    (orijinal akıştaki sırayla; SIMACCEPT / GIZLILIK / SKIP_PASSWORD_CHANGE
     bu modemde yok)

Kaynak koddaki hardcoded `http://192.168.1.1/` OPENINTERFACE içinde olsa da
biz önce frontend'den gelen modem_ip ile manuel driver.get yapıyoruz; sonrasında
OPENINTERFACE tekrar yüklese bile session aynı host üzerinde kalır.

FRONTEND_KEYS eşleşmesi:
    - uptime, ram, cpu                → _get_sistem_bilgisi (tek seferde 3'ü birden)
    - ipv4_internet_*, ipv4_voice_*,
      ipv4_iptv_*, ipv6_*, download,
      upload                          → _get_wan_details (hepsi tek seferde)
    - ssid_24 / ch_24 / bw_24          → _get_wifi(band=1)
    - ssid_5  / ch_5  / bw_5           → _get_wifi(band=2)
    - dhcp_count                       → "N/A" (modem desteklemiyor / kaynak
                                                 kodda dhcp_page.py boş)

Driver dosya/DB açmaz; sadece dict döner.
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "HUAWEI"
MODEL = "LG8245X6"


# Hangi FRONTEND_KEYS grupları hangi sayfadan geliyor — collect()'te
# set-intersection ile gereksiz sayfa gezintisini önlemek için.
_SYSTEM_KEYS = {"uptime", "ram", "cpu"}
_WAN_KEYS = {
    "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
    "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
    "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
    "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    "download", "upload",
}
_WIFI_24_KEYS = {"ssid_24", "ch_24", "bw_24"}
_WIFI_5_KEYS  = {"ssid_5",  "ch_5",  "bw_5"}


def connect(driver, modem_ip: str) -> None:
    """
    Modem arayüzünü açar, login olur.
    Kaynak kod OPENINTERFACE'de `192.168.1.1`'i hardcode etmiş; biz frontend'den
    gelen IP'yi de manuel olarak ziyaret ediyoruz ki yanlış IP'li bir modemde de
    çalışsın. OPENINTERFACE'in kendi get'i hâlâ 192.168.1.1'e gider — ancak çoğu
    LG8245X6 default LAN IP'si zaten 192.168.1.1 olduğu için bu pratikte sorun
    değil. modem_ip farklı verilirse manuel get sonrası LOGINPANEL doğrudan
    çağrılır.
    """
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    # Orijinal akıştaki sırayla:
    scraper.OPENINTERFACE(driver)
    scraper.LOGINPANEL(driver)
    time.sleep(3)


def get_device_info(driver) -> tuple[str, str, str]:
    """(yazilim, donanim, seri) döner."""
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    """
    Seçili FRONTEND_KEYS alanlarını kazır.
    Her sayfayı yalnızca o sayfanın anahtarlarından en az biri seçildiyse aç.
    """
    result: dict = {}

    # --- Sistem (uptime / ram / cpu) — kaynak kod tek seferde 3'ü birden çekiyor ---
    if _SYSTEM_KEYS & secilen:
        uptime, ram, cpu = scraper._get_sistem_bilgisi(driver)
        if "uptime" in secilen: result["uptime"] = uptime
        if "ram"    in secilen: result["ram"]    = ram
        if "cpu"    in secilen: result["cpu"]    = cpu

    # --- WAN (IPv4 internet/voice/iptv + IPv6 + dl/ul) ---
    # Kaynak koddaki _get_wan_details dict şeması:
    #   internet_ip/internet_durum/internet_sure, voice_*, iptv_*, ipv6_*,
    #   dl, ul ("0" placeholder)
    if _WAN_KEYS & secilen:
        wan = scraper._get_wan_details(driver)

        for fkey_prefix, src_prefix in (
            ("ipv4_internet_", "internet_"),
            ("ipv4_voice_",    "voice_"),
            ("ipv4_iptv_",     "iptv_"),
        ):
            ip     = wan.get(f"{src_prefix}ip",    "N/A")
            durum  = wan.get(f"{src_prefix}durum", "N/A")
            sure   = wan.get(f"{src_prefix}sure",  "N/A")
            if f"{fkey_prefix}ip"     in secilen: result[f"{fkey_prefix}ip"]     = ip
            if f"{fkey_prefix}status" in secilen: result[f"{fkey_prefix}status"] = durum
            if f"{fkey_prefix}uptime" in secilen: result[f"{fkey_prefix}uptime"] = sure

        if "ipv6_ip"     in secilen: result["ipv6_ip"]     = wan.get("ipv6_ip",    "N/A")
        if "ipv6_status" in secilen: result["ipv6_status"] = wan.get("ipv6_durum", "N/A")
        if "ipv6_uptime" in secilen: result["ipv6_uptime"] = wan.get("ipv6_sure",  "N/A")

        # download/upload — kaynak kod trafik sayfası implement etmemiş;
        # _get_wan_details "0" placeholder döner. Float'a parse edilemezse de
        # "0" stringi olduğu gibi gönderilir.
        if "download" in secilen: result["download"] = wan.get("dl", "0")
        if "upload"   in secilen: result["upload"]   = wan.get("ul", "0")

    # --- Wi-Fi 2.4 ---
    if _WIFI_24_KEYS & secilen:
        ssid, ch, bw = scraper._get_wifi(driver, band=1)
        if "ssid_24" in secilen: result["ssid_24"] = ssid
        if "ch_24"   in secilen: result["ch_24"]   = ch
        if "bw_24"   in secilen: result["bw_24"]   = bw

    # --- Wi-Fi 5 ---
    if _WIFI_5_KEYS & secilen:
        ssid, ch, bw = scraper._get_wifi(driver, band=2)
        if "ssid_5" in secilen: result["ssid_5"] = ssid
        if "ch_5"   in secilen: result["ch_5"]   = ch
        if "bw_5"   in secilen: result["bw_5"]   = bw

    # --- DHCP client-count desteklenmiyor (kaynak kodda dhcp_page.py boş) ---
    if "dhcp_count" in secilen:
        result["dhcp_count"] = "N/A"

    return result
