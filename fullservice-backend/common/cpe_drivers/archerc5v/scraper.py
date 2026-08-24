"""
ArcherC5v scraper köprüsü.

Kaynak modüldeki fonksiyonlar (driver, logger) imzasıyla geliyor;
frontend logger göndermediği için her birini logger inject eden tek-argümanlı
(driver-only) wrapper'lar sarmalıyoruz.

Connect adımları (orijinal akıştaki sıraya göre):
    OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE
ArcherC5v'de SIMACCEPT / GIZLILIK akışı YOK; HANDLE_ALERT yardımcı fonksiyon.

Cihaz bilgisi (yazılım/donanım/seri) login sonrası ana sayfada doğrudan
sver / hver / sernum ID'lerinden okunuyor — ekstra navigasyon gerekmiyor.
"""
import logging
import time

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    HANDLE_ALERT         as _ha,
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

from selenium.webdriver.common.by import By

_log = logging.getLogger("cpe.archerc5v")


# ---- Connect / yardımcı sarmalayıcılar -------------------------------------
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def HANDLE_ALERT(driver):         return _ha(driver, _log)


# ---- Veri toplayıcı sarmalayıcılar -----------------------------------------
def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


# ---- Cihaz bilgisi ---------------------------------------------------------
def _get_device_info(driver):
    """
    Kaynak koddaki main.get_device_info() karşılığı:
    Login sonrası ana sayfada sver/hver/sernum ID'lerinden okunur.
    Ek navigasyon yok — sadece doğrudan ID erişimi.
    """
    try:
        time.sleep(2)
        yazilim = safe_find_text(driver, By.ID, "sver",   _log)
        donanim = safe_find_text(driver, By.ID, "hver",   _log)
        seri    = safe_find_text(driver, By.ID, "sernum", _log)
        return yazilim, donanim, seri
    except Exception:
        _log.error("ArcherC5v cihaz bilgileri çekme hatası")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """Ana sayfaya geri dön (tekrar veri toplama turu öncesi)."""
    driver.get(f"http://{modem_ip}/")
    time.sleep(3)
