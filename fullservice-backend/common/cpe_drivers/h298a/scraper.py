"""
H298A scraper köprüsü (Huawei — element ID'leri HP_ prefix'li).
"""
import logging
from selenium.webdriver.common.by import By

from .browser import (
    LOGINPANEL          as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    LOGOUT              as _lo,
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
from .pages.dhcp_page    import get_dhcp_count as _get_dhcp_p

_log = logging.getLogger("cpe.h298a")


def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def LOGOUT(driver):               return _lo(driver, _log)


def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


def _get_device_info(driver):
    """Huawei H298A: element ID'leri HP_ prefix'li."""
    try:
        return (
            safe_find_text(driver, By.ID, "HP_SoftwareVer",  _log, wait=3),
            safe_find_text(driver, By.ID, "HP_HardwareVer",  _log, wait=3),
            safe_find_text(driver, By.ID, "HP_SerialNumber", _log, wait=3),
        )
    except Exception:
        return "N/A", "N/A", "N/A"
