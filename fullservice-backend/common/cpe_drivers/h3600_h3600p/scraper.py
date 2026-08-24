"""
H3600 / H3600P scraper köprüsü.

Kaynak modüldeki fonksiyonlar `(driver, logger)` imzasıyla yazılmıştır;
orkestratör (cpe_service.py) ise logger göndermediği için burada her fonksiyonu
tek-argümanlı (`driver`) bir wrapper'a sarıyoruz. Modül kapsamında oluşturulan
`_log` logger'ı tüm çağrılarda inject edilir.

Orijinal akıştaki (`main.py`) connect sırası:
    OPENINTERFACE → LOGINPANEL → SKIP_PASSWORD_CHANGE → HANDLE_ALERT

Sayfa modülleri:
    - system_page  : uptime / ram / cpu / device_info
    - wan_page     : IPv4 internet / voice / iptv + IPv6 internet
    - wifi_page    : Wi-Fi 2.4 / 5
    - traffic_page : download / upload
    - dhcp_page    : DHCP client sayısı (placeholder, modeller arası selector
                     farkı olabilir — kaynak kod olduğu gibi bırakıldı)
"""
import logging
import time

from .browser import (
    OPENINTERFACE        as _oi,
    LOGINPANEL           as _lp,
    SKIP_PASSWORD_CHANGE as _spc,
    HANDLE_ALERT         as _ha,
    is_logged_in         as _ili,
    safe_find_text,
)
from .pages.system_page import (
    get_device_info   as _get_device_info_p,
    get_uptime        as _get_uptime_p,
    get_ram           as _get_ram_p,
    get_cpu           as _get_cpu_p,
    go_to_system_page as _go_to_system_page_p,
)
from .pages.wan_page import (
    go_to_wan_page    as _go_to_wan_page_p,
    get_ipv4_iptv     as _get_ipv4_iptv_p,
    get_ipv4_voice    as _get_ipv4_voice_p,
    get_ipv4_internet as _get_ipv4_internet_p,
    get_ipv6_internet as _get_ipv6_internet_p,
)
from .pages.wifi_page    import get_wifi_24 as _get_wifi24_p, get_wifi_5 as _get_wifi5_p
from .pages.traffic_page import get_download_upload as _get_dl_ul_p
from .pages.dhcp_page    import get_dhcp_count       as _get_dhcp_count_p

_log = logging.getLogger("cpe.h3600_h3600p")


# ---- Connect akışı ----
def OPENINTERFACE(driver):        return _oi(driver, _log)
def LOGINPANEL(driver):           return _lp(driver, _log)
def SKIP_PASSWORD_CHANGE(driver): return _spc(driver, _log)
def HANDLE_ALERT(driver):         return _ha(driver, _log)
def is_logged_in(driver):         return _ili(driver, _log)


# ---- Sistem ----
def go_to_system_page(driver):    return _go_to_system_page_p(driver, _log)
def _get_uptime(driver):          return _get_uptime_p(driver, _log)
def _get_ram(driver):             return _get_ram_p(driver, _log)
def _get_cpu(driver):             return _get_cpu_p(driver, _log)


# ---- WAN ----
def go_to_wan_page(driver):       return _go_to_wan_page_p(driver, _log)
def _get_ipv4_iptv(driver):       return _get_ipv4_iptv_p(driver, _log)
def _get_ipv4_voice(driver):      return _get_ipv4_voice_p(driver, _log)
def _get_ipv4_internet(driver):   return _get_ipv4_internet_p(driver, _log)
def _get_ipv6_internet(driver):   return _get_ipv6_internet_p(driver, _log)


# ---- Wi-Fi ----
def _get_wifi_24(driver):         return _get_wifi24_p(driver, _log)
def _get_wifi_5(driver):          return _get_wifi5_p(driver, _log)


# ---- Trafik ----
def _get_download_upload(driver): return _get_dl_ul_p(driver, _log)


# ---- DHCP ----
def _get_dhcp_count(driver):      return _get_dhcp_count_p(driver, _log)


def _get_device_info(driver):
    """
    Orijinal akışta device_info `system_page.get_device_info` ile
    alınıyor — sayfa navigasyonunu kendi içinde yapıyor (mgrAndDiag'a tıklıyor).
    Burada doğrudan o fonksiyonu logger inject ederek çağırıyoruz.
    """
    return _get_device_info_p(driver, _log)
