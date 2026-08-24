"""
EX520V scraper köprüsü.

browser.py + pages/ modüllerini sarmalar; driver.py'nin beklediği
logger-parametresiz imzaları burada sağlar. Kaynak modüllere dokunulmaz.
"""
import logging
import time
import traceback

from .browser import (
    LOGINPANEL          as _lp,
    HANDLE_LOGIN_POPUP  as _hlp,
    SKIP_PASSWORD_CHANGE as _spc,
    SKIP_CONFIRM_POPUP  as _scp,
    ADVANCED_SECTION    as _adv,
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

_log = logging.getLogger("cpe.ex520v")


# ── Giriş ──────────────────────────────────────────────────────────────────

def LOGINPANEL(driver):           return _lp(driver, _log)
def HANDLE_LOGIN_POPUP(driver):   return _hlp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def SKIP_CONFIRM_POPUP(driver):   return _scp(driver, _log)
def ADVANCED_SECTION(driver):     return _adv(driver, _log)


# ── Scraper fonksiyonları ──────────────────────────────────────────────────

def _get_wan(driver):             return _get_wan_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)
def _get_dhcp_count(driver):      return _get_dhcp_p(driver, _log)


def _get_device_info(driver):
    """Orijinal akıştaki JS inline okuma kopyası."""
    try:
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
        yazilim = (yazilim or "").replace("Yazılım Sürümü:", "").strip()
        donanim = (donanim or "").replace("Donanım Sürümü:", "").strip()
        seri    = (seri    or "").replace("Seri numarası:", "").strip()
        return yazilim or "N/A", donanim or "N/A", seri or "N/A"
    except Exception:
        _log.error(f"EX520V cihaz bilgileri hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"
