"""
EX3301-T0 scraper köprüsü (ZTE).

Kaynak kod yapısı:
  - browser.py → OPENINTERFACE, LOGINPANEL, SKIP_SCREENS, SKIP_SCREENS_2,
                  OPEN_SISTEM_PANELI, GO_HOME, HANDLE_ALERT, wait_loading.
  - pages/system_page → get_uptime / get_cpu / get_ram (CPU & RAM ayrı URL'lere
                         gidiyor, dolayısıyla sonrasında GO_HOME + OPEN_SISTEM_PANELI
                         çağrısı gerekir), get_device_info → (yazilim, seri),
                         get_wan_info → dict (ipv4_*: (ip, sure), ipv6_internet: ip),
                         get_wifi_24 / get_wifi_5 → (ssid, kanal).
  - pages/wifi_page  → get_wifi_bw → (bw24, bw5) (kablosuz sayfasına navigasyon).
  - pages/traffic_page → get_download_upload → (sent, recv) (trafik sayfasına navigasyon).
  - pages/dhcp_page → get_dhcp_count → str (geniş bant sayfasına navigasyon).

Frontend logger göndermez; bu wrapper her çağrıya tek bir `cpe.ex3301_t0`
logger'ı enjekte eder.
"""
import logging

from .browser import (
    LOGINPANEL          as _lp,
    SKIP_SCREENS        as _ss,
    SKIP_SCREENS_2      as _ss2,
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
from .pages.wifi_page    import get_wifi_bw           as _get_wifi_bw_p
from .pages.traffic_page import get_download_upload   as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count        as _get_dhcp_p

_log = logging.getLogger("cpe.ex3301_t0")


# ---------- Connect adımları (logger inject eden tek-argümanlı sarmalayıcılar) ----------
def LOGINPANEL(driver):         return _lp(driver, _log)
def SKIP_SCREENS(driver):       return _ss(driver, _log)
def SKIP_SCREENS_2(driver):     return _ss2(driver, _log)
def OPEN_SISTEM_PANELI(driver): return _osp(driver, _log)
def GO_HOME(driver):            return _gh(driver, _log)


# ---------- Veri çekme sarmalayıcıları ----------
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
    """Kaynak kod (yazilim, seri) döner; biz contract gereği (yazilim, donanim, seri)
    olarak normalize ediyoruz — bu modemde donanım versiyonu sistem panelinden
    okunmuyor, "N/A" sabitleniyor."""
    try:
        yazilim, seri = _get_device_info_p(driver, _log)
        return yazilim, "N/A", seri
    except Exception:
        _log.error("EX3301-T0 cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"
