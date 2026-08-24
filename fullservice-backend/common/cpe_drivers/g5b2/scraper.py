"""
G5B2 scraper köprüsü.

Connect adımları: OPENINTERFACE + SIMACCEPT + LOGINPANEL + GIZLILIK
                 + SKIP_PASSWORD_CHANGE
DHCP yok — G5B2 modeminde DHCP client sayısı kazınmıyor.
"""
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .browser import (
    LOGINPANEL          as _lp,
    SIMACCEPT           as _sa,
    GIZLILIK            as _gz,
    SKIP_PASSWORD_CHANGE as _spc,
    safe_find_text,
)
from .pages.wan_page     import get_wan as _get_wan_p
from .pages.system_page  import (
    get_uptime as _get_uptime_p,
    get_ram    as _get_ram_p,
    get_cpu    as _get_cpu_p,
)
from .pages.wifi_page    import get_wifi_24 as _get_wifi24_p, get_wifi_5 as _get_wifi5_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p

_log = logging.getLogger("cpe.g5b2")


def LOGINPANEL(driver):           return _lp(driver, _log)
def SIMACCEPT(driver):            return _sa(driver, _log)
def GIZLILIK(driver):             return _gz(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)


def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)


def _open_device_info_page(driver):
    """Sistem → Cihaz Bilgileri sayfasına navigate eder (cihaz bilgisi alımı için)."""
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='system']"))
    ).click()
    time.sleep(1)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='device_information']"))
    ).click()
    time.sleep(2)


def _get_device_info(driver):
    try:
        _open_device_info_page(driver)
        time.sleep(2)
        yazilim = safe_find_text(driver, By.XPATH, "//label[contains(@data-bind,'sw_version')]", _log, wait=3)
        donanim = safe_find_text(driver, By.XPATH, "//label[contains(@data-bind,'hw_version')]", _log, wait=3)
        seri    = safe_find_text(driver, By.XPATH, "//label[contains(@data-bind,'modem_msn')]",  _log, wait=3)
        return yazilim, donanim, seri
    except Exception:
        _log.error("G5B2 cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Orijinal akışta her veri toplama turunda ana sayfaya dönülüyor."""
    driver.get(f"http://{modem_ip}/index.html")
    time.sleep(3)
