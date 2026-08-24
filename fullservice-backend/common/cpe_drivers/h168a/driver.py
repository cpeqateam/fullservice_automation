"""
H168A (Huawei) driver adapter.

Kaynak koddaki H168A/main.py dosyasında:
    LOGOUT → OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE
sırasıyla giriş yapılıyor; SIMACCEPT veya GIZLILIK adımı yok.

OPENINTERFACE içinde modem IP'si hardcoded "192.168.1.1" — fakat orkestratör
parametre olarak farklı bir IP yollayabilir. Bu yüzden burada OPENINTERFACE'i
çağırmıyoruz; doğrudan driver.get(http://{modem_ip}/) ile açıyoruz.

WAN destekleri (kaynak modüldeki wan_page.py'ye göre):
    - IPv4 Internet ✔
    - IPv4 IPTV     ✔
    - IPv4 Voice    ✘ (sayfada yok → N/A)
    - IPv6 Internet ✔

DHCP client sayısı DESTEKLENİYOR.
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "Huawei"
MODEL = "H168A"


def connect(driver, modem_ip: str) -> None:
    """Modem arayüzünü açar, mevcut oturumu kapatır, giriş yapar ve şifre
    değiştirme ekranını atlar. Orijinal akıştaki sırayı koruruz."""
    # OPENINTERFACE içinde IP hardcoded olduğundan onu kullanmıyoruz;
    # modem_ip frontend'den parametrik geliyor.
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGOUT(driver)
    # LOGOUT sonrası bazen tekrar arayüze gitmek gerekebilir.
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    """(yazilim, donanim, seri) döner. Ana sayfadaki label'lardan okunur."""
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    """FRONTEND_KEYS içinden seçili alanları kazır. base.py'deki tüm anahtarlar
    burada eşlenir; desteklenmeyenler için 'N/A' döner."""
    result: dict = {}

    # Her tur başında ana sayfaya dön (uptime/ram/wan menüsü oradan açılıyor).
    # Modem IP'sini driver.current_url'den çıkarıp güvenli şekilde tekrar git.
    try:
        host = urlparse(driver.current_url).hostname
        if host:
            driver.get(f"http://{host}/")
            time.sleep(3)
    except Exception:
        pass

    # WAN ile ilgili tüm anahtar grubu — herhangi biri seçildiyse get_wan'ı bir kez çağır.
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    # ---- Uptime --------------------------------------------------------
    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    # ---- WAN (IPv4 internet/voice/iptv + IPv6) -------------------------
    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
        # Kaynak modüldeki wan_page.py'nin döndürdüğü sözlük anahtarları:
        #   ipv4_internet, ipv4_voice (yok), ipv4_iptv, ipv6_internet
        for prefix, group_key in (
            ("ipv4_internet_", "ipv4_internet"),
            ("ipv4_voice_",    "ipv4_voice"),     # H168A'da yok → ("N/A","N/A","N/A")
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

    # ---- RAM / CPU -----------------------------------------------------
    if "ram" in secilen:
        result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen:
        result["cpu"] = scraper._get_cpu(driver)

    # ---- Wi-Fi 2.4 / 5 -------------------------------------------------
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

    # ---- Download / Upload --------------------------------------------
    if {"download", "upload"} & secilen:
        # Trafik DSL accordion'undan okunuyor; tekrar ana sayfaya dönmeye gerek yok,
        # get_download_upload kendi içinde mmInternet üzerinden gidiyor.
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    # ---- DHCP Client sayısı -------------------------------------------
    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
