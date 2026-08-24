"""
H168A scraper köprüsü.

Kaynak modüllerdeki `browser.py` ve `pages/*.py` (driver, logger)
imzasıyla çağrılır; frontend ise logger geçmediği için her fonksiyonu burada
sarmalayıp tek-argümanlı (driver-only) hale getiriyoruz.

Connect adımları (orijinal akıştaki sırayla):
    LOGOUT → OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE

H168A (Huawei) için ekstra GIZLILIK / SIMACCEPT adımı YOKTUR.
DHCP client sayısı DESTEKLENİYOR (dhcp_page.get_dhcp_count).
"""
import logging
import time
from selenium.webdriver.common.by import By

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    LOGOUT               as _lo,
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

_log = logging.getLogger("cpe.h168a")


# ---- browser/connect fonksiyonları (driver-only sarmalayıcılar) ------------
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def LOGOUT(driver):               return _lo(driver, _log)
def HANDLE_ALERT(driver):         return _ha(driver, _log)


# ---- page kazıyıcılar (driver-only sarmalayıcılar) ------------------------
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
    H168A ana sayfasındaki HP_SoftwareVer / HP_HardwareVer / HP_SerialNumber
    label'larından cihaz bilgisini okur. Orijinal akıştaki get_device_info
    fonksiyonu da bu üç ID'yi doğrudan okuyor — ayrı bir sayfa navigasyonu yok.
    """
    try:
        time.sleep(2)
        yazilim = safe_find_text(driver, By.ID, "HP_SoftwareVer",  _log, wait=3)
        donanim = safe_find_text(driver, By.ID, "HP_HardwareVer",  _log, wait=3)
        seri    = safe_find_text(driver, By.ID, "HP_SerialNumber", _log, wait=3)
        return yazilim, donanim, seri
    except Exception:
        _log.error("H168A cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Orijinal akışta her turda OPENINTERFACE/LOGIN tekrar çağrılıyor;
    burada sadece ana sayfaya gitmek isteyen orkestratör için yardımcı."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
