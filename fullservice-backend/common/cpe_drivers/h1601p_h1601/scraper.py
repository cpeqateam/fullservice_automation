"""
H1601P-H1601 scraper koprusu.

browser.py + pages/*.py modullerindeki fonksiyonlar
(driver, logger) imzasiyla cagriliyor. Frontend tarafi logger gondermez;
bu modul her birini sarmalar ve modul seviyesindeki `_log` ile cagirir.

Connect adimlari (orijinal akistan):
    OPENINTERFACE -> LOGINPANEL -> SKIP_PASSWORD_CHANGE
    (LOGOUT her tur basinda once cagriliyor; orkestrator burada
     gerekirse driver.connect tekrar cagirir)

H1601P-H1601 ozellikleri:
    - DHCP client sayisi YOK (dhcp_page.py "N/A" doner)
    - IPv4 voice ayri bir kanal degil, sadece IPTV + Internet + IPv6 var
    - CPU "Yonetim" sayfasinda (mgrAndDiag butonu)
    - Device info ana sayfada (SoftwareVer, HardwareVer, SerialNumber ID'leri)
"""
import logging
import time

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    LOGOUT               as _logout,
    HANDLE_ALERT         as _ha,
    safe_find_text,
)
from .pages.wan_page     import get_wan              as _get_wan_p
from .pages.system_page  import (
    get_uptime as _get_uptime_p,
    get_ram    as _get_ram_p,
    get_cpu    as _get_cpu_p,
)
from .pages.wifi_page    import get_wifi_24 as _get_wifi24_p, get_wifi_5 as _get_wifi5_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count      as _get_dhcp_p

from selenium.webdriver.common.by import By

_log = logging.getLogger("cpe.h1601p_h1601")


# ----- Connect/oturum sarmacilari -----
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def LOGOUT(driver):               return _logout(driver, _log)
def HANDLE_ALERT(driver):         return _ha(driver, _log)


# ----- Veri kazima sarmacilari -----
def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


def _get_device_info(driver):
    """
    Orijinal akistaki get_device_info() davranisini taklit eder.
    Login sonrasi ana sayfada SoftwareVer/HardwareVer/SerialNumber ID'leri okur.
    """
    try:
        time.sleep(2)
        yazilim = safe_find_text(driver, By.ID, "SoftwareVer",  _log, wait=3)
        donanim = safe_find_text(driver, By.ID, "HardwareVer",  _log, wait=3)
        seri    = safe_find_text(driver, By.ID, "SerialNumber", _log, wait=3)
        return yazilim, donanim, seri
    except Exception:
        _log.error("H1601P-H1601 cihaz bilgileri cekme hatasi")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Ana sayfaya dondur — uptime/RAM ana ekranda olduğu icin gerektiginde cagrilir."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
