"""
WR854GVR scraper köprüsü.

browser.py ve pages/ modülleri (driver, logger) imzasıyla çalışır. Burada
modül-seviyesi bir logger inject ederek tek-argümanlı (driver-only) wrapper'lar
tanımlıyoruz; driver.py bu wrapper'ları çağırır.

Connect adımları (kaynak koddaki main.py login() fonksiyonundan):
    LOGIN — admin/admin, sonra "cancel" butonu
DESTEKLENMEYEN: device_info (yazılım/donanım/seri), download/upload, IPv6, Voice, IPTV, dhcp_count.
Kaynak koddaki not: "DL UL VERİLERİ ARAYÜZDE OLMADIĞI İÇİN N/A".
"""
import logging

from .browser import LOGIN as _login
from .pages.system_page import (
    get_cpu_ram_wan as _get_sys_p,
    get_uptime      as _get_uptime_p,
)
from .pages.wifi_page import (
    get_wifi_24 as _get_w24_p,
    get_wifi_5  as _get_w5_p,
)

_log = logging.getLogger("cpe.wr854gvr")


def LOGIN(driver):              return _login(driver, _log)


def _get_cpu_ram_wan(driver):   return _get_sys_p(driver, _log)
def _get_uptime(driver):        return _get_uptime_p(driver, _log)
def _get_wifi_24(driver):       return _get_w24_p(driver, _log)
def _get_wifi_5(driver):        return _get_w5_p(driver, _log)


def _get_device_info(driver):
    """
    WR854GVR arayüzünde sağ üst köşede yazılım sürümü "V4.x.x[.x][_YYYYMMDD]"
    formatında gösteriliyor (Aidata kalıbı). Kaynak kodda bu bölüm yoktu;
    sayfa kaynağını dolaşıp pattern'i regex ile yakalıyoruz.

    Strateji:
      1. default content'e geç (iframe varsa çık)
      2. Tüm iframe'leri ve ana sayfayı tarayıp V4 pattern'ini ara
      3. Donanım ve seri için ayrı kazıma yok — "N/A" döner
    """
    import re

    # Aidata yazılım sürüm pattern'i: V<rakam>.<rakam>[.<rakam>][_YYYYMMDD]
    # Ornekler: V4.0, V4.0.18, V4.0.18_20260527
    _PATTERN = re.compile(r'V\d+\.\d+(?:\.\d+)?(?:_\d{6,8})?')

    yazilim = "N/A"
    try:
        # 1) Ana sayfa (default content) kaynağı
        driver.switch_to.default_content()
        match = _PATTERN.search(driver.page_source or '')
        if match:
            yazilim = match.group(0)
        else:
            # 2) Bulunamadıysa iframe'lere bak — bazı modemlerde header iframe'de
            iframes = driver.find_elements("tag name", "iframe")
            for frame in iframes:
                try:
                    driver.switch_to.default_content()
                    driver.switch_to.frame(frame)
                    match = _PATTERN.search(driver.page_source or '')
                    if match:
                        yazilim = match.group(0)
                        break
                except Exception:
                    continue
            driver.switch_to.default_content()
    except Exception as e:
        _log.warning(f"Device info okunamadi: {e}")

    return yazilim, "N/A", "N/A"
