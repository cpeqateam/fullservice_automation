"""
Huawei EB810V driver adapter.

Kaynak modül EB810V/main.py'deki login + veri-toplama akışını
backend sözleşmesine (base.py) uyarlar.

Connect sırası (main.py loop'undan):
    OPENINTERFACE → LOGINPANEL → HANDLE_LOGIN_POPUP →
    SKIP_PASSWORD_CHANGE → SKIP_CONFIRM_POPUP → ADVANCED_SECTION

Desteklenen FRONTEND_KEYS:
    uptime, ipv4_internet_*, ipv4_voice_*, ipv4_iptv_*, ipv6_*,
    ram, cpu, ssid_24/ch_24/bw_24, ssid_5/ch_5/bw_5,
    download, upload, dhcp_count

Tüm 25 frontend alanı destekleniyor — N/A fallback gerekmiyor.

Modem arayüzü kaynak kodda https://192.168.1.1/ ile açılıyor; ancak
`connect(driver, modem_ip)` parametrik olduğu için frontend'den ne IP
gelirse o kullanılır. Şema yine https'tir (kaynak koddaki OPENINTERFACE
https URL kullanıyor).
"""
import time
from urllib.parse import urlparse

from . import scraper

BRAND = "Huawei"
MODEL = "EB810V"


def connect(driver, modem_ip: str) -> None:
    """
    Modem web arayüzünü aç ve login + popup zincirini geç.

    Kaynak kodda OPENINTERFACE hardcoded `https://192.168.1.1/` URL'sini
    açıyor; burada parametrik IP ile aynı şemayı kullanarak adresliyoruz,
    sonra browser.py'deki yardımcı popup-geçiş fonksiyonlarını
    orijinal akıştaki sırayla çağırıyoruz.
    """
    driver.get(f"https://{modem_ip}/")
    time.sleep(3)
    scraper.LOGINPANEL(driver)
    scraper.HANDLE_LOGIN_POPUP(driver)
    scraper.SKIP_PASSWORD_CHANGE(driver)
    scraper.SKIP_CONFIRM_POPUP(driver)
    scraper.ADVANCED_SECTION(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    """(yazilim, donanim, seri) tuple'ı döndür."""
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    """
    Seçili alanları kazı ve {frontend_key: deger} sözlüğü döndür.

    Kaynak main.py'deki `veri_topla()` fonksiyonunun dallanma mantığı
    burada FRONTEND_KEYS (base.py) anahtar isimleriyle yeniden eşleniyor.
    Set-intersection ile gereksiz sayfa gezintisi atlanır (örn. hiçbir
    WAN alanı seçili değilse `get_wan` çağrılmaz).
    """
    result: dict = {}

    # WAN sayfasından çekilen frontend anahtarları
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }

    # --- Uptime (system_page sekmesi) ---
    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    # --- WAN dört grup: internet / voice / iptv / ipv6 ---
    if secilen & wan_keys:
        wan = scraper._get_wan(driver)
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

    # --- RAM / CPU (system_page üzerinde) ---
    if "ram" in secilen: result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen: result["cpu"] = scraper._get_cpu(driver)

    # --- Wi-Fi 2.4 GHz ---
    if {"ssid_24", "ch_24", "bw_24"} & secilen:
        ssid, ch, bw = scraper._get_wifi_24(driver)
        if "ssid_24" in secilen: result["ssid_24"] = ssid
        if "ch_24"   in secilen: result["ch_24"]   = ch
        if "bw_24"   in secilen: result["bw_24"]   = bw

    # --- Wi-Fi 5 GHz ---
    if {"ssid_5", "ch_5", "bw_5"} & secilen:
        ssid, ch, bw = scraper._get_wifi_5(driver)
        if "ssid_5" in secilen: result["ssid_5"] = ssid
        if "ch_5"   in secilen: result["ch_5"]   = ch
        if "bw_5"   in secilen: result["bw_5"]   = bw

    # --- Download / Upload (Sistem > İstatistik) ---
    if {"download", "upload"} & secilen:
        dl, ul = scraper._get_download_upload(driver)
        if "download" in secilen: result["download"] = dl
        if "upload"   in secilen: result["upload"]   = ul

    # --- DHCP Client Sayısı (Ağ > LAN Ayarları) ---
    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)

    return result
