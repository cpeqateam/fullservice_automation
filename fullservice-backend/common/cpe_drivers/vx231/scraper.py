"""
VX231 scraper köprüsü.

browser.py ve pages/ modülleri (driver, logger) imzasıyla çalışır. Burada
modül-seviyesi logger inject ederek tek-argümanlı (driver-only) wrapper'lar
tanımlıyoruz.

Connect adımları (orijinal main_loop + __main__ akışından):
    OPENINTERFACE (driver.get) -> LOGINPANEL -> HANDLE_ALERTS -> ADVANCED_SECTION
DESTEKLENMEYEN: device_info (yazılım/donanım/seri), IPv6, Voice, IPTV, dhcp_count.
"""
import logging
import time

from .browser import (
    LOGINPANEL       as _lp,
    HANDLE_ALERTS    as _ha,
    ADVANCED_SECTION as _adv,
)
from .pages.system_page  import get_system as _get_sys_p
from .pages.wifi_page    import get_wifi_24 as _get_w24_p, get_wifi_5 as _get_w5_p
from .pages.traffic_page import get_network as _get_net_p

_log = logging.getLogger("cpe.vx231")


def LOGINPANEL(driver):       return _lp(driver, _log)
def HANDLE_ALERTS(driver):    return _ha(driver, _log)
def ADVANCED_SECTION(driver): return _adv(driver, _log)


def _get_system(driver):  return _get_sys_p(driver, _log)
def _get_wifi_24(driver): return _get_w24_p(driver, _log)
def _get_wifi_5(driver):  return _get_w5_p(driver, _log)
def _get_network(driver): return _get_net_p(driver, _log)


def _get_device_info(driver):
    """
    Kaynak kodda VX231 arayüzünden cihaz yazılım/donanım/seri çeken bölüm
    yok — üçü de "N/A" döner.
    """
    return "N/A", "N/A", "N/A"
