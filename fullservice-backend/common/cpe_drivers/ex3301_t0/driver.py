"""
EX3301-T0 driver adapter (ZTE).

Connect: OPENINTERFACE benzeri sayfa açımı (driver.get) + LOGINPANEL
         + SKIP_SCREENS + SKIP_SCREENS_2 + OPEN_SISTEM_PANELI
         (orijinal akıştaki sırayı koruyoruz).

Bu modelde:
  - WAN bilgileri sistem panelindeki DOM index'lerinden okunuyor; tuple 2 elemanlı
    (ip, sure), 'status' alanı her zaman "N/A" yazılır.
  - IPv6 internet WAN'ında sadece IP döner (sure/status yok).
  - Wi-Fi: SSID+Kanal sistem panelinden, BW kablosuz sayfasından (ayrı navigasyon).
  - Wi-Fi/trafik/DHCP turundan sonra ana sayfaya GO_HOME + OPEN_SISTEM_PANELI ile
    geri dönülür (kaynak koddaki veri_topla akışıyla aynı).
"""
import time
from . import scraper

BRAND = "ZTE"
MODEL = "EX3301-T0"


def connect(driver, modem_ip: str) -> None:
    # Kaynak koddaki OPENINTERFACE hardcoded http://192.168.1.1/ açıyordu;
    # burada frontend'den gelen modem_ip kullanılır.
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_SCREENS(driver)
    scraper.SKIP_SCREENS_2(driver)
    scraper.OPEN_SISTEM_PANELI(driver)


def get_device_info(driver) -> tuple[str, str, str]:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # ----- 1. Uptime (sistem panelinden, ana sayfada) -----
    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    # ----- 2. WAN (sistem panelinden) — tuple 2 elemanlı, 'status' yok -----
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }
    if secilen & wan_keys:
        wan = scraper._get_wan_info(driver)
        for prefix, group_key in (
            ("ipv4_internet_", "ipv4_internet"),
            ("ipv4_voice_",    "ipv4_voice"),
            ("ipv4_iptv_",     "ipv4_iptv"),
        ):
            ip, uptime = wan.get(group_key, ("N/A", "N/A"))
            for fkey, val in (
                (f"{prefix}ip",     ip),
                (f"{prefix}status", "N/A"),  # bu modem status alanı vermiyor
                (f"{prefix}uptime", uptime),
            ):
                if fkey in secilen:
                    result[fkey] = val
        # IPv6 internet — sadece IP string'i; status/uptime "N/A"
        ipv6_ip = wan.get("ipv6_internet", "N/A")
        if "ipv6_ip"     in secilen: result["ipv6_ip"]     = ipv6_ip
        if "ipv6_status" in secilen: result["ipv6_status"] = "N/A"
        if "ipv6_uptime" in secilen: result["ipv6_uptime"] = "N/A"

    # ----- 3. RAM / CPU — ayrı URL'lere gidiyor; sonrasında ana sayfaya dön -----
    if "ram" in secilen: result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen: result["cpu"] = scraper._get_cpu(driver)
    if "ram" in secilen or "cpu" in secilen:
        try:
            scraper.GO_HOME(driver)
            scraper.OPEN_SISTEM_PANELI(driver)
        except Exception:
            pass

    # ----- 4. Wi-Fi: SSID+Kanal sistem sayfasından, BW kablosuz sayfasından -----
    need_24 = bool({"ssid_24", "ch_24", "bw_24"} & secilen)
    need_5  = bool({"ssid_5",  "ch_5",  "bw_5"}  & secilen)

    if need_24 or need_5:
        ssid24 = ch24 = ssid5 = ch5 = bw24 = bw5 = "N/A"
        if need_24:
            ssid24, ch24 = scraper._get_wifi_24(driver)
        if need_5:
            ssid5, ch5 = scraper._get_wifi_5(driver)

        # BW için kablosuz sayfasına geç, sonra ana sayfaya dön (referans akış)
        try:
            bw24, bw5 = scraper._get_wifi_bw(driver)
        finally:
            try:
                scraper.GO_HOME(driver)
                scraper.OPEN_SISTEM_PANELI(driver)
            except Exception:
                pass

        if "ssid_24" in secilen: result["ssid_24"] = ssid24
        if "ch_24"   in secilen: result["ch_24"]   = ch24
        if "bw_24"   in secilen: result["bw_24"]   = bw24
        if "ssid_5"  in secilen: result["ssid_5"]  = ssid5
        if "ch_5"    in secilen: result["ch_5"]    = ch5
        if "bw_5"    in secilen: result["bw_5"]    = bw5

    # ----- 5. Trafik (WAN sent/recv) — ayrı navigasyon, sonra ana sayfaya dön -----
    if {"download", "upload"} & secilen:
        sent, recv = scraper._get_download_upload(driver)
        # Orijinal akışta sent → download, recv → upload sırasıyla yazılıyor.
        if "download" in secilen: result["download"] = sent
        if "upload"   in secilen: result["upload"]   = recv
        try:
            scraper.GO_HOME(driver)
            scraper.OPEN_SISTEM_PANELI(driver)
        except Exception:
            pass

    # ----- 6. DHCP client sayısı — ayrı sayfa, sonra ana sayfaya dön -----
    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)
        try:
            scraper.GO_HOME(driver)
            scraper.OPEN_SISTEM_PANELI(driver)
        except Exception:
            pass

    return result
