"""
VC220 scraper köprüsü.

Kaynak modüllerdeki browser.py ve pages/*.py (driver, logger) imzasıyla
çalışır. Frontend logger sağlamadığı için bu modül her fonksiyona
modül-seviyesi bir logger inject eden tek-argümanlı (driver-only)
wrapper'lar tanımlar.

Connect adımları (main.py'deki sıra):
    OPENINTERFACE -> LOGINPANEL -> SKIP_PASSWORD_CHANGE
VC220'de SIMACCEPT/GIZLILIK yoktur; bu modemde sadece basit login + opsiyonel
şifre değiştirme ekranı vardır.

Device info: orijinal akışta get_device_info, modem ana sayfasında
By.ID = sver/hver/sernum alanlarını okur. Bu yüzden _get_device_info
ekstra bir navigasyon yapmaz; sadece ana sayfada doğru ID'leri okur.
"""
import logging
import time
from selenium.webdriver.common.by import By

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    HANDLE_ALERT         as _ha,
    safe_find_text,
)
from .pages.wan_page     import get_wan              as _get_wan_p
from .pages.system_page  import (
    get_uptime as _get_uptime_p,
    get_ram    as _get_ram_p,
    get_cpu    as _get_cpu_p,
)
from .pages.wifi_page    import (
    get_wifi_24 as _get_wifi24_p,
    get_wifi_5  as _get_wifi5_p,
)
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count      as _get_dhcp_p

_log = logging.getLogger("cpe.vc220")


# ---- browser.py wrapper'ları ---------------------------------------------
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def HANDLE_ALERT(driver):         return _ha(driver, _log)


# ---- pages/*.py wrapper'ları ---------------------------------------------
def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


# ---- device info ---------------------------------------------------------
def _get_device_info(driver):
    """Orijinal akıştaki get_device_info'nun adapter karşılığı.
    VC220'de cihaz bilgileri ana sayfada By.ID = sver/hver/sernum
    alanlarında durur; ek navigasyon gerekmez.
    """
    try:
        time.sleep(2)
        yazilim = safe_find_text(driver, By.ID, "sver",   _log)
        donanim = safe_find_text(driver, By.ID, "hver",   _log)
        seri    = safe_find_text(driver, By.ID, "sernum", _log)
        return yazilim, donanim, seri
    except Exception:
        _log.error("VC220 cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Trafik / DHCP gibi navigasyondan sonra ana arayüze geri dön."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
