"""
EG620 scraper köprüsü.

Kaynak modüllerdeki `browser.py` ve `pages/*.py` fonksiyonları
`(driver, logger)` imzasıyla yazıldığı için frontend tarafı sadece `driver`
gönderiyor. Bu modül her fonksiyonun başına bir logger inject eder ve
driver-only bir arayüz sunar.

Connect adımları: OPENINTERFACE + LOGINPANEL + OPEN_STATUS_MENU
Wi-Fi BW alımı sonrası kaynak kod yerel ağda kalıyor, collect()
içinde tekrar OPEN_STATUS_MENU çağrılır.
DHCP destekleniyor — `get_dhcp_count` sayfası modemin IP'sini
hardcoded `192.168.1.1` ile açtığı için orijinal hâliyle bırakıldı;
modem farklı bir IP'deyse collect() runtime'da uyarı verebilir.
"""
import logging
import time

from .browser import (
    OPENINTERFACE       as _oi,
    LOGINPANEL          as _lp,
    OPEN_STATUS_MENU    as _osm,
    OPEN_LAN_MENU       as _olm,
    NAVIGATE            as _nav,
    HANDLE_ALERT        as _ha,
    safe_find_text,
)
from .pages.wan_page     import get_wan as _get_wan_p
from .pages.system_page  import (
    get_uptime      as _get_uptime_p,
    get_ram         as _get_ram_p,
    get_cpu         as _get_cpu_p,
    get_device_info as _get_device_info_p,
)
from .pages.wifi_page    import get_wifi_24 as _get_wifi24_p, get_wifi_5 as _get_wifi5_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count as _get_dhcp_p

_log = logging.getLogger("cpe.eg620")


# ---- Bağlantı / Navigasyon (driver-only wrapper'lar) ---------------------
def OPENINTERFACE(driver):     return _oi(driver, _log)
def LOGINPANEL(driver):        return _lp(driver, _log)
def OPEN_STATUS_MENU(driver):  return _osm(driver, _log)
def OPEN_LAN_MENU(driver):     return _olm(driver, _log)
def HANDLE_ALERT(driver):      return _ha(driver, _log)
def NAVIGATE(driver, href, label):
    return _nav(driver, _log, href, label)


# ---- Veri kazıma fonksiyonları -------------------------------------------
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
    Kaynak koddaki `pages/system_page.get_device_info` fonksiyonu
    (yazilim, seri) döner. base.py sözleşmesi (yazilim, donanim, seri)
    bekliyor — donanim için 'N/A' fallback'i veriyoruz.
    """
    try:
        yazilim, seri = _get_device_info_p(driver, _log)
        return yazilim or "N/A", "N/A", seri or "N/A"
    except Exception:
        _log.error("EG620 cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Status menüsünü tekrar aç; orijinal akışta her döngü
    başında OPEN_STATUS_MENU çağrılıyor."""
    try:
        driver.get(f"http://{modem_ip}/")
        time.sleep(2)
        _osm(driver, _log)
    except Exception:
        _log.warning("EG620 go_home başarısız")
