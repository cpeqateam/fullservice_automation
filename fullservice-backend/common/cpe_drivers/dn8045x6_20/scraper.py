"""
DN8045X6-20 scraper köprüsü.

Yapısı diğerlerinden farklı:
  - pages/base.py frame yapısını yönetir.
  - _get_sistem_bilgisi → (uptime, ram, cpu) tek seferde döner.
  - _get_wan_details → flat dict (internet_ip/durum/sure, iptv_*, ipv6_*, dl, ul).
  - _get_wifi(driver, logger, band) → (ssid, ch, bw); band=1 → 2.4 GHz, band=2 → 5 GHz.
  - VoIP/voice ve dhcp_count desteklenmiyor.
"""
import logging

from .browser import LOGINPANEL as _lp, is_logged_in as _ili
from .pages.system_page import (
    _get_sistem_bilgisi as _gsb,
    _get_device_info    as _gdi,
)
from .pages.wan_page  import _get_wan_details as _gwd
from .pages.wifi_page import _get_wifi as _gw

_log = logging.getLogger("cpe.dn8045x6_20")


def LOGINPANEL(driver):   return _lp(driver, _log)
def is_logged_in(driver): return _ili(driver, _log)


def _get_sistem_bilgisi(driver):  return _gsb(driver, _log)  # (uptime, ram, cpu)
def _get_wan_details(driver):     return _gwd(driver, _log)  # flat dict
def _get_wifi(driver, band):      return _gw(driver, _log, band=band)  # (ssid, ch, bw)
def _get_device_info(driver):
    try:
        return _gdi(driver, _log)  # (yaz, don, seri)
    except Exception:
        return "N/A", "N/A", "N/A"
