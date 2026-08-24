"""
TP-LINK Archer C5v driver adapter.

Connect akışı (orijinal main.py akışındaki sıraya göre):
    driver.get(modem_ip) → OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE

ArcherC5v tüm FRONTEND_KEYS alanlarını destekliyor:
    uptime, ipv4_*, ipv6_*, ram, cpu, ssid/ch/bw (2.4 + 5), download/upload, dhcp_count
N/A fallback yok — tüm alanlar gerçek scraper çağırıyor.
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "TP-LINK"
MODEL = "ArcherC5v"


def connect(driver, modem_ip: str) -> None:
    """Modem arayüzünü açar, login + şifre değiştirme ekranını geçer."""
    # Kaynak kodda OPENINTERFACE hardcoded 192.168.1.1'e gidiyor;
    # biz önce frontend'den gelen IP ile aç, ardından referans akışı çağır.
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    # OPENINTERFACE içinde tekrar driver.get(192.168.1.1) çağrılıyor — eğer
    # frontend'den farklı IP geldiyse kaynak koddaki hardcoded IP'yi aşmak için
    # OPENINTERFACE'i atla; aksi halde davranış aynı.
    if modem_ip.strip() in ("192.168.1.1", ""):
        scraper.OPENINTERFACE(driver)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)


def get_device_info(driver) -> tuple:
    """(yazılım, donanım, seri) — ana sayfada sver/hver/sernum ID'lerinden."""
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    """
    Frontend'den seçilen alanları kazır.
    Set-intersection ile gereksiz sayfa gezintisini önler.
    """
    result: dict = {}

    # WAN tek bir tablodan IPv4 internet/voice/iptv + IPv6 internet'i toplu çekiyor;
    # bu yüzden herhangi biri seçildiyse tek seferde get_wan() çağırıyoruz.
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
        # Kaynak koddaki wan_page.py şu anahtarları döner:
        #   ipv4_internet / ipv4_voice / ipv4_iptv / ipv6_internet
        # Bu anahtarları FRONTEND_KEYS prefiks'lerine eşliyoruz.
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
        # Trafik sayfası kendi navigasyonunu (menu_infomenu → traffic) yapıyor.
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    if "dhcp_count" in secilen:
        # DHCP sayfası kendi navigasyonunu (menu_dhcp → menu_dhcpclient) yapıyor.
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    # Bir sonraki tur için ana sayfaya dön (orijinal akışta da aynı davranış).
    try:
        host = urlparse(driver.current_url).hostname
        if host:
            driver.get(f"http://{host}/")
            time.sleep(2)
    except Exception:
        pass

    return result
