"""
DX3300-T1 scraper köprüsü.

Kaynak modüllerdeki `browser.py` ve `pages/*.py` fonksiyonları `(driver, logger)`
imzasıyla çağrılır; ancak driver sözleşmesi (driver.py) sadece `driver` alır.
Bu modül her kaynak fonksiyonu sarmalayarak `cpe.dx3300_t1` logger'ını
otomatik inject eder.

Connect adımları (orijinal akıştaki sıra):
  OPENINTERFACE → LOGINPANEL → SKIP_SCREENS → SKIP_SCREENS_2 → OPEN_SISTEM_PANELI

Bu modemde WAN sayfası YOK — IPv4 Internet/Voice/IPTV bilgileri kaynak
kodda da "N/A" döner; sadece IPv6 IP system_page'den çıkar.
"""
import logging
import time

from .browser import (
    OPENINTERFACE       as _oi,
    LOGINPANEL          as _lp,
    SKIP_SCREENS        as _ss,
    SKIP_SCREENS_2      as _ss2,
    OPEN_SISTEM_PANELI  as _osp,
    GO_HOME             as _gh,
)
from .pages.system_page import (
    get_uptime      as _get_uptime_p,
    get_cpu         as _get_cpu_p,
    get_ram         as _get_ram_p,
    get_device_info as _get_device_info_p,
    get_wan_info    as _get_wan_info_p,
    get_wifi_24     as _get_wifi_24_p,
    get_wifi_5      as _get_wifi_5_p,
)
from .pages.wifi_page    import get_wifi_bw         as _get_wifi_bw_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count      as _get_dhcp_count_p

_log = logging.getLogger("cpe.dx3300_t1")


# --- Connect / navigasyon wrapperları ----------------------------------------
def OPENINTERFACE(driver):      return _oi(driver, _log)
def LOGINPANEL(driver):         return _lp(driver, _log)
def SKIP_SCREENS(driver):       return _ss(driver, _log)
def SKIP_SCREENS_2(driver):     return _ss2(driver, _log)
def OPEN_SISTEM_PANELI(driver): return _osp(driver, _log)
def GO_HOME(driver):            return _gh(driver, _log)


# --- Veri çekme wrapperları ---------------------------------------------------
def _get_uptime(driver):    return _get_uptime_p(driver, _log)
def _get_cpu(driver):       return _get_cpu_p(driver, _log)
def _get_ram(driver):       return _get_ram_p(driver, _log)
def _get_wan_info(driver):  return _get_wan_info_p(driver, _log)
def _get_wifi_24(driver):   return _get_wifi_24_p(driver, _log)
def _get_wifi_5(driver):    return _get_wifi_5_p(driver, _log)
def _get_wifi_bw(driver):   return _get_wifi_bw_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver): return _get_dhcp_count_p(driver, _log)


def _get_device_info(driver):
    """
    Kaynak koddaki get_device_info yazılım + seri döner (donanım yok).
    Driver sözleşmesi (yazilim, donanim, seri) üçlüsü beklediği için
    donanım için "N/A" döneriz.
    """
    try:
        yazilim, seri = _get_device_info_p(driver, _log)
        return yazilim, "N/A", seri
    except Exception:
        _log.error("DX3300-T1 cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Manuel ana sayfa dönüşü; collect() içinde GO_HOME wrapper'ı kullanılıyor."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
