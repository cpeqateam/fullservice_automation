"""
Huawei H3600 / H3600P driver adapter.

Connect akışı (kaynak main.py'deki sıraya birebir):
    OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE → HANDLE_ALERT

Modem IP parametrik — kaynak koddaki sabit `http://192.168.1.1/` yerine
frontend'den gelen IP kullanılır (browser.OPENINTERFACE içindeki sabiti
geçersiz kılmak için connect() önce direkt `driver.get(http://<modem_ip>/)`
çağırır; sonra LOGINPANEL/SKIP_PASSWORD_CHANGE akışı çalışır).

FRONTEND_KEYS → kaynak fonksiyon eşlemesi:
    uptime                                          → system_page.get_uptime
    ram                                             → system_page.get_ram
    cpu                                             → system_page.get_cpu
    ipv4_iptv_(ip|status|uptime)                    → wan_page.get_ipv4_iptv
    ipv4_voice_(ip|status|uptime)                   → wan_page.get_ipv4_voice
    ipv4_internet_(ip|status|uptime)                → wan_page.get_ipv4_internet
    ipv6_(status|uptime)                            → wan_page.get_ipv6_internet
    ipv6_ip                                         → "N/A"   (kaynak kod IPv6 IP çekmiyor)
    ssid_24 / ch_24 / bw_24                         → wifi_page.get_wifi_24
    ssid_5  / ch_5  / bw_5                          → wifi_page.get_wifi_5
    download / upload                               → traffic_page.get_download_upload
    dhcp_count                                      → dhcp_page.get_dhcp_count
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "Huawei"
# MODEL = "H3600" — hem "H3600 V9" hem "H3600P V9.0" frontend modellerini kapsar.
# "H3600" stringi "H3600P" ifadesinin substring'i olduğu için her ikisi de substring
# eşleşmesi ile bu driver'a yönlenir. "H3601P" gibi farklı modellerle çakışmaz.
MODEL = "H3600"


def connect(driver, modem_ip: str) -> None:
    # Kaynak kod modem IP'sini sabit (192.168.1.1) açıyordu; biz frontend'den
    # gelen IP'yi kullanmak için arayüzü kendimiz açıyoruz, ardından login akışı.
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)
    scraper.HANDLE_ALERT(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # Kaynak koddaki veri_topla() fonksiyonunda her grup için önce ilgili sayfaya
    # gidiliyor. Aynı sırayı koruyoruz: sistem → wan → wifi → trafik → dhcp.

    # ----- Sistem sayfası -----
    sistem_keys = {"uptime", "ram", "cpu"}
    if sistem_keys & secilen:
        try:
            scraper.go_to_system_page(driver)
        except Exception:
            pass
        if "uptime" in secilen: result["uptime"] = scraper._get_uptime(driver)
        if "ram"    in secilen: result["ram"]    = scraper._get_ram(driver)
        if "cpu"    in secilen: result["cpu"]    = scraper._get_cpu(driver)

    # ----- WAN sayfası -----
    wan_v4_iptv_keys     = {"ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime"}
    wan_v4_voice_keys    = {"ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime"}
    wan_v4_internet_keys = {"ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime"}
    wan_v6_keys          = {"ipv6_ip", "ipv6_status", "ipv6_uptime"}
    wan_all = wan_v4_iptv_keys | wan_v4_voice_keys | wan_v4_internet_keys | wan_v6_keys

    if wan_all & secilen:
        try:
            scraper.go_to_wan_page(driver)
        except Exception:
            pass

        if wan_v4_iptv_keys & secilen:
            ip, durum, sure = scraper._get_ipv4_iptv(driver)
            if "ipv4_iptv_ip"     in secilen: result["ipv4_iptv_ip"]     = ip
            if "ipv4_iptv_status" in secilen: result["ipv4_iptv_status"] = durum
            if "ipv4_iptv_uptime" in secilen: result["ipv4_iptv_uptime"] = sure

        if wan_v4_voice_keys & secilen:
            ip, durum, sure = scraper._get_ipv4_voice(driver)
            if "ipv4_voice_ip"     in secilen: result["ipv4_voice_ip"]     = ip
            if "ipv4_voice_status" in secilen: result["ipv4_voice_status"] = durum
            if "ipv4_voice_uptime" in secilen: result["ipv4_voice_uptime"] = sure

        if wan_v4_internet_keys & secilen:
            ip, durum, sure = scraper._get_ipv4_internet(driver)
            if "ipv4_internet_ip"     in secilen: result["ipv4_internet_ip"]     = ip
            if "ipv4_internet_status" in secilen: result["ipv4_internet_status"] = durum
            if "ipv4_internet_uptime" in secilen: result["ipv4_internet_uptime"] = sure

        if wan_v6_keys & secilen:
            durum, sure = scraper._get_ipv6_internet(driver)
            # Kaynak kod IPv6 IP'sini çekmiyor; frontend istiyorsa N/A dön.
            if "ipv6_ip"     in secilen: result["ipv6_ip"]     = "N/A"
            if "ipv6_status" in secilen: result["ipv6_status"] = durum
            if "ipv6_uptime" in secilen: result["ipv6_uptime"] = sure

    # ----- Wi-Fi -----
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

    # ----- Trafik -----
    if {"download", "upload"} & secilen:
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    # ----- DHCP -----
    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
