"""
EX3501-T0 scraper köprüsü (ZTE).

Kaynak kod yapısı EX20V'den farklı:
  - get_wan_info → her tuple 2 elemanlı (ip, sure); status yok.
  - get_wifi_24/get_wifi_5 → 2 elemanlı (ssid, kanal); BW ayrı sayfadan get_wifi_bw.
  - get_device_info → 2 elemanlı (yazilim, seri); donanım yok.
  - Wifi/Traffic/DHCP sonrası GO_HOME + OPEN_SISTEM_PANELI çağrısı gerek.
"""
import logging

from .browser import (
    LOGINPANEL          as _lp,
    SKIP_SCREENS        as _ss,
    OPEN_SISTEM_PANELI  as _osp,
    GO_HOME             as _gh,
)
from .pages.system_page  import (
    get_uptime      as _get_uptime_p,
    get_cpu         as _get_cpu_p,
    get_ram         as _get_ram_p,
    get_device_info as _get_device_info_p,
    get_wan_info    as _get_wan_info_p,
    get_wifi_24     as _get_wifi24_p,
    get_wifi_5      as _get_wifi5_p,
)
from .pages.wifi_page    import get_wifi_bw as _get_wifi_bw_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count as _get_dhcp_p

_log = logging.getLogger("cpe.ex3501_t0")


def LOGINPANEL(driver):         return _lp(driver, _log)
def SKIP_SCREENS(driver):       return _ss(driver, _log)
def OPEN_SISTEM_PANELI(driver): return _osp(driver, _log)
def GO_HOME(driver):            return _gh(driver, _log)


def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wan_info(driver):        return _get_wan_info_p(driver, _log)     # dict
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)        # (ssid, ch)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)         # (ssid, ch)
def _get_wifi_bw(driver):         return _get_wifi_bw_p(driver, _log)       # (bw24, bw5)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)         # (sent, recv)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


def _get_device_info(driver):
    """EX3501-T0 → (yazilim, seri); biz (yazilim, "N/A", seri) olarak normalize ediyoruz."""
    try:
        yazilim, seri = _get_device_info_p(driver, _log)
        return yazilim, "N/A", seri
    except Exception:
        return "N/A", "N/A", "N/A"
