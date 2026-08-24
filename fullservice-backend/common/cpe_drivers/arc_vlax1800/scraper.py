"""
ARC-VLAX1800 scraper köprüsü.

Kaynak modüldeki fonksiyonlar `(driver, logger)` imzasıyla çalışıyor.
Driver/orkestratör logger göndermediği için bu modülde her fonksiyonu
sarmalayıp paket-içi `_log` logger'ını otomatik inject ediyoruz. Böylece
driver.py yalnızca `(driver)` ile çağırır.

Connect akışı (browser.py'de tanımlı):
    OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE
    (modelde SIMACCEPT/GIZLILIK ekranı yok)

Desteklenmeyenler (kaynak kod zaten "N/A" dönüyor):
    - RAM   (system_page.get_ram)
    - CPU   (system_page.get_cpu)
    - download / upload (traffic_page.get_download_upload)
    - IPv4 Voice & IPv6 (wan_page.get_wan içinde sadece Internet ve IPTV doluyor)
"""
import logging
import time

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    LOGOUT               as _lo,
    SELECT_MENU          as _sm,
    SWITCH_TO_CONTENT_FRAME as _scf,
    SWITCH_TO_DEFAULT       as _sd,
    HANDLE_ALERT            as _ha,
    safe_find_text,
)
from .pages.system_page  import (
    get_device_info as _get_device_info_p,
    get_uptime      as _get_uptime_p,
    get_ram         as _get_ram_p,
    get_cpu         as _get_cpu_p,
)
from .pages.wan_page     import get_wan as _get_wan_p
from .pages.wifi_page    import get_wifi_24 as _get_wifi24_p, get_wifi_5 as _get_wifi5_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count as _get_dhcp_p

_log = logging.getLogger("cpe.arc_vlax1800")


# ---- Browser / connect adımları (logger inject) ----
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def LOGOUT(driver):               return _lo(driver, _log)


# ---- Sayfa scraperları (logger inject) ----
def _get_device_info(driver):     return _get_device_info_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


def go_home(driver, modem_ip: str):
    """Opsiyonel; collect() iç akışta SELECT_MENU kullandığı için genelde gerekmez."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
