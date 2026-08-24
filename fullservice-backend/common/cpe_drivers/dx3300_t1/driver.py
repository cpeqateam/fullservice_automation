"""
Nokia DX3300-T1 driver adapter.

Connect: OPENINTERFACE + LOGINPANEL + SKIP_SCREENS + SKIP_SCREENS_2 + OPEN_SISTEM_PANELI
(Orijinal akıştaki giriş sırası birebir.)

Kaynak kod hardcoded olarak http://192.168.1.1/ kullanıyor; biz connect()
içinde driver.get'i parametrik IP ile çağırıp ardından login/skip akışını
çalıştırıyoruz. Kaynak koddaki OPENINTERFACE de tekrar 192.168.1.1'e gider —
bu modem zaten o ağda olduğu için tipik kullanımda sorun olmaz, ama
frontend farklı bir IP gönderirse override etmek için önce driver.get yapıyoruz.

Bu modem WAN sayfasına sahip değil — IPv4 Internet/Voice/IPTV alanları
"N/A" döner (kaynak koddaki get_wan_info da öyle). IPv6 IP sistem
panelinden çıkar; IPv6 status/uptime desteklenmiyor.
"""
import time
from . import scraper

BRAND = "Nokia"
MODEL = "DX3300-T1"


def connect(driver, modem_ip: str) -> None:
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
    scraper.OPENINTERFACE(driver)
    scraper.LOGINPANEL(driver)
    scraper.SKIP_SCREENS(driver)
    scraper.SKIP_SCREENS_2(driver)
    scraper.OPEN_SISTEM_PANELI(driver)


def get_device_info(driver) -> tuple:
    return scraper._get_device_info(driver)


def collect(driver, secilen: set) -> dict:
    result: dict = {}

    # ----- 1. Sistem paneli (ana sayfa) -----
    if "uptime" in secilen:
        result["uptime"] = scraper._get_uptime(driver)

    # ----- 2. WAN bilgileri -----
    # DX3300-T1 kaynak kodunda WAN için ayrı sayfa yok; get_wan_info sadece
    # IPv6 IP'yi sistem panelinden çıkarıyor, gerisi "N/A".
    wan_keys = {
        "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
        "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
        "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
        "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    }
    if secilen & wan_keys:
        wan = scraper._get_wan_info(driver)

        # IPv4 Internet: kaynak kod tuple (ip, uptime) döndürür; status desteklenmiyor.
        ipv4_int_ip, ipv4_int_up = wan.get("ipv4_internet", ("N/A", "N/A"))
        if "ipv4_internet_ip"     in secilen: result["ipv4_internet_ip"]     = ipv4_int_ip
        if "ipv4_internet_status" in secilen: result["ipv4_internet_status"] = "N/A"
        if "ipv4_internet_uptime" in secilen: result["ipv4_internet_uptime"] = ipv4_int_up

        ipv4_voi_ip, ipv4_voi_up = wan.get("ipv4_voice", ("N/A", "N/A"))
        if "ipv4_voice_ip"     in secilen: result["ipv4_voice_ip"]     = ipv4_voi_ip
        if "ipv4_voice_status" in secilen: result["ipv4_voice_status"] = "N/A"
        if "ipv4_voice_uptime" in secilen: result["ipv4_voice_uptime"] = ipv4_voi_up

        ipv4_tv_ip, ipv4_tv_up = wan.get("ipv4_iptv", ("N/A", "N/A"))
        if "ipv4_iptv_ip"     in secilen: result["ipv4_iptv_ip"]     = ipv4_tv_ip
        if "ipv4_iptv_status" in secilen: result["ipv4_iptv_status"] = "N/A"
        if "ipv4_iptv_uptime" in secilen: result["ipv4_iptv_uptime"] = ipv4_tv_up

        # IPv6: sadece IP var
        if "ipv6_ip"     in secilen: result["ipv6_ip"]     = wan.get("ipv6_internet", "N/A")
        if "ipv6_status" in secilen: result["ipv6_status"] = "N/A"
        if "ipv6_uptime" in secilen: result["ipv6_uptime"] = "N/A"

    # ----- 3. RAM / CPU — ayrı sayfa; sonrasında ana sayfaya dön -----
    if "ram" in secilen:
        result["ram"] = scraper._get_ram(driver)
    if "cpu" in secilen:
        result["cpu"] = scraper._get_cpu(driver)
    if "ram" in secilen or "cpu" in secilen:
        scraper.GO_HOME(driver)
        scraper.OPEN_SISTEM_PANELI(driver)

    # ----- 4. Wi-Fi 2.4 / 5 GHz SSID + Kanal + BW -----
    need_wifi_24 = bool({"ssid_24", "ch_24", "bw_24"} & secilen)
    need_wifi_5  = bool({"ssid_5",  "ch_5",  "bw_5"}  & secilen)

    ssid24 = ch24 = bw24 = "N/A"
    ssid5  = ch5  = bw5  = "N/A"

    if need_wifi_24 or need_wifi_5:
        if need_wifi_24:
            ssid24, ch24 = scraper._get_wifi_24(driver)
        if need_wifi_5:
            ssid5, ch5 = scraper._get_wifi_5(driver)

        # BW için kablosuz sayfasına git, sonra geri dön
        bw24, bw5 = scraper._get_wifi_bw(driver)
        scraper.GO_HOME(driver)
        scraper.OPEN_SISTEM_PANELI(driver)

    if "ssid_24" in secilen: result["ssid_24"] = ssid24
    if "ch_24"   in secilen: result["ch_24"]   = ch24
    if "bw_24"   in secilen: result["bw_24"]   = bw24
    if "ssid_5"  in secilen: result["ssid_5"]  = ssid5
    if "ch_5"    in secilen: result["ch_5"]    = ch5
    if "bw_5"    in secilen: result["bw_5"]    = bw5

    # ----- 5. Trafik (download / upload) -----
    if {"download", "upload"} & secilen:
        sent, recv = scraper._get_download_upload(driver)
        # Kaynak koddaki etiket: sent = WAN Gönderilen (upload), recv = WAN Alınan (download)
        if "download" in secilen: result["download"] = recv
        if "upload"   in secilen: result["upload"]   = sent
        scraper.GO_HOME(driver)
        scraper.OPEN_SISTEM_PANELI(driver)

    # ----- 6. DHCP client sayısı -----
    if "dhcp_count" in secilen:
        result["dhcp_count"] = scraper._get_dhcp_count(driver)
        scraper.GO_HOME(driver)
        scraper.OPEN_SISTEM_PANELI(driver)

    return result
