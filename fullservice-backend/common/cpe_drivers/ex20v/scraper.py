"""
EX20V scraper köprüsü.

Güncellenmiş modüler kaynak kodu (browser.py + pages/) sarmalar.
driver.py'nin beklediği imzalar (logger parametresiz) burada sağlanır —
driver.py'ye dokunmadan yeni modüler koda geçiş bu dosyayla yapılır.
"""
import logging
from selenium.webdriver.common.by import By

from .browser import (
    LOGINPANEL as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    safe_find_text,
)
from .pages.wan_page import get_wan as _get_wan_p
from .pages.system_page import (
    get_uptime as _get_uptime_p,
    get_ram    as _get_ram_p,
    get_cpu    as _get_cpu_p,
)
from .pages.wifi_page import (
    get_wifi_24 as _get_wifi24_p,
    get_wifi_5  as _get_wifi5_p,
)
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page import get_dhcp_count as _get_dhcp_p

_log = logging.getLogger("cpe.ex20v")


# ── Giriş ──────────────────────────────────────────────────────────────────

def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)


# ── Scraper fonksiyonları ──────────────────────────────────────────────────

def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


def _get_device_info(driver):
    try:
        return (
            safe_find_text(driver, By.ID, "sver",   _log),
            safe_find_text(driver, By.ID, "hver",   _log),
            safe_find_text(driver, By.ID, "sernum", _log),
        )
    except Exception:
        return "N/A", "N/A", "N/A"
