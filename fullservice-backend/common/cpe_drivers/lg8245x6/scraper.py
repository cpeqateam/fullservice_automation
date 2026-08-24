"""
LG8245X6 scraper köprüsü.

Kaynak modüldeki fonksiyonlar `(driver, logger)` imzasıyla çağrılır;
ancak orkestratör (cpe_service.py) logger göndermez. Bu yüzden burada
her fonksiyonu tek-argümanlı (driver-only) wrapper ile sarmalıyoruz ve
modül seviyesindeki `_log` üzerinden logger inject ediyoruz.

Connect adımları (orijinal akıştan):
    OPENINTERFACE → LOGINPANEL  (+ session düştüyse is_logged_in kontrolü)

Bu modemde GİZLİLİK / SİM ekranı / PASSWORD CHANGE yoktur — kaynak kodda
da çağrılmıyor. Bu yüzden sadece OPENINTERFACE + LOGINPANEL adımlarını
açıyoruz. is_logged_in helper'ı orkestratörün ileride yeniden-login
mantığı için kullanması amacıyla expose edilir.

Veri toplama sayfaları:
    - pages.system_page._get_sistem_bilgisi  → (uptime, ram, cpu)
    - pages.system_page._get_device_info     → (yazilim, donanim, seri)
    - pages.wan_page._get_wan_details        → ipv4 internet/voice/iptv + ipv6 + dl/ul
    - pages.wifi_page._get_wifi              → (ssid, kanal, bw)  band=1 → 2.4GHz, band=2 → 5GHz

Bu modem için ayrı bir trafik (download/upload) ve DHCP client-count sayfası
kaynak kodda implementlenmemiştir; dl/ul, _get_wan_details'in döndürdüğü
"0" placeholder'ı üzerinden gelir. DHCP client-count desteklenmiyor → driver
seviyesinde "N/A" döner.
"""
import logging
import time

from .browser import (
    OPENINTERFACE as _oi,
    LOGINPANEL    as _lp,
    is_logged_in  as _ili,
    HANDLE_ALERT  as _ha,
)
from .pages.system_page import (
    _get_sistem_bilgisi as _get_sistem_bilgisi_p,
    _get_device_info    as _get_device_info_p,
)
from .pages.wan_page  import _get_wan_details as _get_wan_details_p
from .pages.wifi_page import _get_wifi        as _get_wifi_p

_log = logging.getLogger("cpe.lg8245x6")


# ===================== Connect katmanı =====================

def OPENINTERFACE(driver):  return _oi(driver, _log)
def LOGINPANEL(driver):     return _lp(driver, _log)
def HANDLE_ALERT(driver):   return _ha(driver, _log)
def is_logged_in(driver):   return _ili(driver, _log)


# ===================== Sayfa scraper'ları =====================

def _get_sistem_bilgisi(driver):
    """(uptime, ram, cpu) döner."""
    return _get_sistem_bilgisi_p(driver, _log)


def _get_device_info(driver):
    """(yazilim, donanim, seri) döner — system_page zaten bu sırayla döndürüyor."""
    return _get_device_info_p(driver, _log)


def _get_wan_details(driver):
    """
    WAN sayfasından tüm IPv4/IPv6 detaylarını ve dl/ul placeholder'larını döner.
    Dict anahtarları kaynak koddaki orijinal şemadaki gibi:
        internet_ip / internet_durum / internet_sure,
        voice_ip / voice_durum / voice_sure,
        iptv_ip / iptv_durum / iptv_sure,
        ipv6_ip / ipv6_durum / ipv6_sure,
        dl / ul   ("0" placeholder)
    """
    return _get_wan_details_p(driver, _log)


def _get_wifi(driver, band: int):
    """(ssid, kanal, bw) döner. band=1 → 2.4 GHz, band=2 → 5 GHz."""
    return _get_wifi_p(driver, _log, band=band)


# ===================== Yardımcılar =====================

def go_home(driver, modem_ip: str):
    """
    Orijinal akışta her tur arasında ana sayfaya dönülmüyor; ancak
    bazı sayfa geçişleri sonrasında default content'e dönmek gerekiyor.
    Orkestratör bu yardımcıyı opsiyonel olarak çağırabilir.
    """
    driver.get(f"http://{modem_ip}/")
    time.sleep(2)
