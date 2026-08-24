"""
Huawei EG620 driver adapter.

Connect akışı (orijinal akıştaki sıraya birebir):
    OPENINTERFACE → LOGINPANEL → OPEN_STATUS_MENU

Modem IP default: 192.168.1.1 (kaynak koddaki sabit). Frontend'den
gelen IP `connect(driver, modem_ip)` ile parametrik geçer.

FRONTEND_KEYS karşılığı:
    - WAN sayfası SADECE ipv4_internet ve ipv6_internet veriyor;
      ipv4_voice ve ipv4_iptv EG620 arayüzünde modellenmemiş → "N/A".
    - dhcp_count destekleniyor.
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "Huawei"
MODEL = "EG620"


def connect(driver, modem_ip: str) -> None:
    """Kaynak koddaki OPENINTERFACE 192.168.1.1'i hardcoded açıyor;
    biz frontend'den gelen IP'yi kullanıyoruz."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(3)
    scraper.LOGINPANEL(driver)
    scraper.OPEN_STATUS_MENU(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    """Kaynak koddaki pages.system_page.get_device_info (yazilim, seri) döner;
    scraper donanim alanını N/A ile doldurur."""
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    """
    Kaynak koddaki `veri_topla` mantığını FRONTEND_KEYS sözleşmesine map eder.
    Her tur başında Durum menüsünü tekrar açar (orijinal akışta da
    her loop'ta OPEN_STATUS_MENU çağrılıyor).
    """
    result: dict = {}

    # Her tur başında Durum menüsünü aç — uptime/ram/cpu/WAN için kök.
    try:
        scraper.OPEN_STATUS_MENU(driver)
    except Exception:
        pass

    # ---- WAN grubu (ipv4 internet/voice/iptv + ipv6) ---------------------
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    # uptime/ram/cpu: kaynak kodda her biri cihaz bilgileri sayfasına
    # ayrı navigate ediyor — biz de aynısını yapıyoruz (cache yok).
    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
        # Kaynak kodda voice/iptv için kayıt yok → boş tuple kalır → N/A
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

    # ---- Wi-Fi 2.4 / 5 ----------------------------------------------------
    if {"ssid_24", "ch_24", "bw_24"} & secilen:
        ssid, ch, bw = scraper._get_wifi_24(driver)
        if "ssid_24" in secilen: result["ssid_24"] = ssid
        if "ch_24"   in secilen: result["ch_24"]   = ch
        if "bw_24"   in secilen: result["bw_24"]   = bw
        # Kaynak kod: BW alındıktan sonra Yerel Ağ'da kalıyor → tekrar Durum'a dön
        try:
            scraper.OPEN_STATUS_MENU(driver)
        except Exception:
            pass

    if {"ssid_5", "ch_5", "bw_5"} & secilen:
        ssid, ch, bw = scraper._get_wifi_5(driver)
        if "ssid_5" in secilen: result["ssid_5"] = ssid
        if "ch_5"   in secilen: result["ch_5"]   = ch
        if "bw_5"   in secilen: result["bw_5"]   = bw
        try:
            scraper.OPEN_STATUS_MENU(driver)
        except Exception:
            pass

    # ---- Trafik (Ağ sayfası) ---------------------------------------------
    if {"download", "upload"} & secilen:
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    # ---- DHCP client sayısı ----------------------------------------------
    # Kaynak koddaki dhcp_page.py modem IP'sini 192.168.1.1 olarak hardcoded
    # tutuyor (dosyaya dokunmadık). Çoğu kurulumda EG620 zaten 192.168.1.1
    # üzerinde — sorun yaşanırsa go_home + manuel navigasyon gerekebilir.
    if "dhcp_count" in secilen:
        try:
            scraper.OPEN_STATUS_MENU(driver)
        except Exception:
            pass
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
