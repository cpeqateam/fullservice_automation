"""
VC220 driver adapter.

Marka/Model: TP-LINK VC220
Connect akışı (orijinal main.py'de): OPENINTERFACE -> LOGINPANEL ->
                                      SKIP_PASSWORD_CHANGE
Kaynak koddaki browser.OPENINTERFACE hardcoded 192.168.1.1'e gidiyor; biz
frontend'den gelen modem_ip parametresine saygı duymak için connect()
içinde önce driver.get(modem_ip) yapıyoruz; LOGINPANEL/SKIP zaten URL
bağımsız çalışır.

FRONTEND_KEYS karşılığı:
    uptime              -> pages.system_page.get_uptime
    ipv4_internet/voice/iptv + ipv6  -> pages.wan_page.get_wan
    ram, cpu            -> pages.system_page.get_ram / get_cpu
    ssid_24/ch_24/bw_24 -> pages.wifi_page.get_wifi_24
    ssid_5 /ch_5 /bw_5  -> pages.wifi_page.get_wifi_5
    download, upload    -> pages.traffic_page.get_download_upload
    dhcp_count          -> pages.dhcp_page.get_dhcp_count

VC220 tüm FRONTEND_KEYS alanlarını destekler; "N/A" fallback kullanılmaz.
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "TP-LINK"
MODEL = "VC220"


def connect(driver, modem_ip: str) -> None:
    # Kaynak koddaki browser.OPENINTERFACE hardcoded 192.168.1.1'e gidiyor;
    # frontend'den gelen IP'yi kullanmak için manuel get yapıyoruz.
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def _go_home(driver) -> None:
    """Trafik veya DHCP gezintisinden sonra mevcut host'un ana sayfasına dön.
    Orijinal akışta her tur başında modem arayüzü yeniden açılıyor;
    biz tek session içinde olduğumuz için ana sayfaya navigate ediyoruz.
    """
    try:
        host = urlparse(driver.current_url).hostname
        if host:
            driver.get(f"http://{host}/")
            time.sleep(2)
    except Exception:
        pass


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    # Ana sayfada okunan alanlar (uptime, ram, cpu, wifi). Önce ana sayfaya dön.
    home_needed = bool(secilen & ({"uptime", "ram", "cpu",
                                   "ssid_24", "ch_24", "bw_24",
                                   "ssid_5", "ch_5", "bw_5"} | wan_keys))
    if home_needed:
        _go_home(driver)

    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
        # wan dict anahtarları: ipv4_internet, ipv4_voice, ipv4_iptv, ipv6_internet
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
        # Trafik sayfası menü navigasyonu yapar; sayfa ana sayfa değildir.
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    if "dhcp_count" in secilen:
        # DHCP de ayrı bir menüye gider — trafiğin ardından bu sırayla
        # çağrılması orijinal akıştaki sırayla aynıdır.
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
