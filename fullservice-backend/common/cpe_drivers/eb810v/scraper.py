"""
EB810V scraper köprüsü.

Kaynak modüldeki fonksiyonlar `(driver, logger)` imzasıyla yazılmış; bu
modül her birini tek-argümanlı (driver-only) bir wrapper'a sarmalar ve
modül-ölçekli `_log` logger'ını inject eder. Böylece orkestratör
(cpe_service.py) sadece `driver` parametresi ile çağırabilir.

Connect adımları (orijinal main.py akışından):
    OPENINTERFACE + LOGINPANEL + HANDLE_LOGIN_POPUP +
    SKIP_PASSWORD_CHANGE + SKIP_CONFIRM_POPUP + ADVANCED_SECTION

Device info ise orijinal akışta index sayfasındaki
`bot_sver` / `bot_hver` / `bot_serial_number` JS elementlerinden okunuyor;
burada da aynı yöntem `_get_device_info` içinde tekrarlanır.
"""
import logging
import time
import traceback

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    HANDLE_LOGIN_POPUP   as _hlp,
    SKIP_PASSWORD_CHANGE as _spc,
    SKIP_CONFIRM_POPUP   as _scp,
    ADVANCED_SECTION     as _adv,
    HANDLE_ALERT         as _ha,
    WAIT_MASK            as _wm,
    safe_find_text,
)
from .pages.wan_page     import get_wan            as _get_wan_p
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

_log = logging.getLogger("cpe.eb810v")


# --- Connect / popup wrapper'ları (driver-only imza) ---
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def HANDLE_LOGIN_POPUP(driver):   return _hlp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def SKIP_CONFIRM_POPUP(driver):   return _scp(driver, _log)
def ADVANCED_SECTION(driver):     return _adv(driver, _log)
def HANDLE_ALERT(driver):         return _ha(driver, _log)
def WAIT_MASK(driver):            return _wm(driver, _log)


# --- Page scraper wrapper'ları (driver-only imza) ---
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
    Cihaz yazılım/donanım/seri numarasını al.

    Kaynak main.py'deki `get_device_info` tam olarak buraya taşındı.
    Index sayfası DOM'unda `bot_sver`, `bot_hver`, `bot_serial_number`
    ID'li elementler vardır; bu metin değerleri JavaScript ile okunur.
    Yazılım bilgisinin geç yüklenme ihtimaline karşı 15 saniyelik polling
    döngüsü kullanılır.
    """
    _log.debug("EB810V cihaz bilgileri çekiliyor")
    try:
        yazilim = ""
        for _ in range(15):
            yazilim = driver.execute_script(
                "var el = document.getElementById('bot_sver');"
                "return el ? el.innerText.trim() : '';"
            )
            if yazilim and len(yazilim) > 5:
                break
            time.sleep(1)
        donanim = driver.execute_script(
            "var el = document.getElementById('bot_hver');"
            "return el ? el.innerText.trim() : '';"
        )
        seri = driver.execute_script(
            "var el = document.getElementById('bot_serial_number');"
            "return el ? el.innerText.trim() : '';"
        )
        yazilim = (yazilim or "").replace("Yazılım Sürümü:", "").strip() or "N/A"
        donanim = (donanim or "").replace("Donanım Sürümü:", "").strip() or "N/A"
        seri    = (seri    or "").replace("Seri numarası:", "").strip()    or "N/A"
        _log.info(f"EB810V cihaz bilgileri → Yazılım={yazilim}, Donanım={donanim}, Seri={seri}")
        return yazilim, donanim, seri
    except Exception:
        _log.error(f"EB810V cihaz bilgisi hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def go_home(driver, modem_ip: str):
    """
    Ana sayfaya dön. Orijinal akışta her tur başında
    OPENINTERFACE çağrılır (https://<ip>/ ye gider). Burada da
    benzer bir dönüş sağlanır.
    """
    driver.get(f"https://{modem_ip}/")
    time.sleep(3)
