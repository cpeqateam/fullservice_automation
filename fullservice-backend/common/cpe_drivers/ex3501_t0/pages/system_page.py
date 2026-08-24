"""
ZTE EX3501 — Sistem Bilgisi sayfası
Ana sayfada "Sistem" cardbox'ı açıkken çalışır.
Çekilen veriler:
  - CPU, RAM  : li[@data-v-05b1c222] içindeki % değerleri
  - Uptime    : li içinde "dakika/saat/gün" geçen metin
  - Seri No   : 12 haneli hex string
  - Yazılım   : V\d+\.\d+ formatındaki versiyon string'i
  - IPv4 İnternet / VoIP / IPTV : ip_address1/2/3 + ipoeUpTime1/2/3
  - IPv6      : lan_ipv6_link_local_address
  - Wi-Fi 2.4 : wifi_2.4G_SSID, wifi_2.4G_Channel
  - Wi-Fi 5   : wifi_5G_SSID,   wifi_5G_Channel
"""

import re
import logging
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _li_texts(driver):
    items = driver.find_elements(By.XPATH, "//li[@data-v-05b1c222]")
    return [i.text.strip() for i in items if i.text.strip()]


def get_uptime(driver, logger: logging.Logger) -> str:
    logger.debug("Uptime çekiliyor")
    try:
        texts = _li_texts(driver)
        val = next((t for t in texts if any(k in t for k in ("dakika", "saat", "gün"))), "N/A")
        logger.info(f"Uptime: {val}")
        return val
    except Exception:
        logger.error(f"Uptime hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_cpu(driver, logger: logging.Logger) -> str:
    logger.debug("CPU çekiliyor")
    try:
        percents = [t for t in _li_texts(driver) if "%" in t]
        val = percents[0] if percents else "N/A"
        logger.info(f"CPU: {val}")
        return val
    except Exception:
        logger.error(f"CPU hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_ram(driver, logger: logging.Logger) -> str:
    logger.debug("RAM çekiliyor")
    try:
        percents = [t for t in _li_texts(driver) if "%" in t]
        val = percents[1] if len(percents) > 1 else "N/A"
        logger.info(f"RAM: {val}")
        return val
    except Exception:
        logger.error(f"RAM hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_device_info(driver, logger: logging.Logger):
    """Yazılım versiyonu ve seri numarasını döndürür."""
    logger.debug("Cihaz bilgileri çekiliyor")
    yazilim = "N/A"
    seri    = "N/A"
    try:
        texts = _li_texts(driver)
        for t in texts:
            if re.fullmatch(r'[A-Fa-f0-9]{12}', t):
                seri = t
            if re.search(r'V\d+\.\d+', t) and '-' in t:
                yazilim = t
        logger.info(f"Yazılım: {yazilim} | Seri: {seri}")
    except Exception:
        logger.error(f"Cihaz bilgisi hatası:\n{traceback.format_exc()}")
    return yazilim, seri


def get_wan_info(driver, logger: logging.Logger) -> dict:
    """
    Sistem Bilgisi sayfasından WAN IP ve süre bilgilerini çeker.
    Döndürür: {
        "ipv4_internet": (ip, sure),
        "ipv4_voice":    (ip, sure),
        "ipv4_iptv":     (ip, sure),
        "ipv6_internet": ip,
    }
    """
    logger.debug("WAN bilgileri sistem sayfasından çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A"),
        "ipv6_internet": "N/A",
    }

    def _ip(element_id):
        try:
            el = driver.find_element(By.ID, element_id)
            # IP adresi div içindeki buton metninden önce geliyor
            raw = el.text.strip().split('\n')[0].strip()
            return raw
        except Exception:
            return "N/A"

    def _sure(element_id):
        try:
            return driver.find_element(By.ID, element_id).text.strip()
        except Exception:
            return "N/A"

    try:
        result["ipv4_internet"] = (_ip("ip_address1"),  _sure("ipoeUpTime1"))
        result["ipv4_voice"]    = (_ip("ip_address2"),  _sure("ipoeUpTime2"))
        result["ipv4_iptv"]     = (_ip("ip_address3"),  _sure("ipoeUpTime3"))
        result["ipv6_internet"] = _ip("lan_ipv6_link_local_address")
        logger.info(f"WAN bilgileri: {result}")
    except Exception:
        logger.error(f"WAN bilgisi hatası:\n{traceback.format_exc()}")

    return result


def get_wifi_24(driver, logger: logging.Logger):
    """Sistem Bilgisi sayfasından 2.4 GHz SSID ve Kanal bilgisi"""
    logger.debug("Wi-Fi 2.4 GHz çekiliyor")
    try:
        wait  = WebDriverWait(driver, 10)
        ssid  = wait.until(EC.presence_of_element_located((By.ID, "wifi_2.4G_SSID"))).text.strip()
        ch    = driver.find_element(By.ID, "wifi_2.4G_Channel").text.strip()
        logger.info(f"Wi-Fi 2.4 → SSID={ssid}, Kanal={ch}")
        return ssid, ch
    except Exception:
        logger.error(f"Wi-Fi 2.4 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    """Sistem Bilgisi sayfasından 5 GHz SSID ve Kanal bilgisi"""
    logger.debug("Wi-Fi 5 GHz çekiliyor")
    try:
        ssid = driver.find_element(By.ID, "wifi_5G_SSID").text.strip()
        ch   = driver.find_element(By.ID, "wifi_5G_Channel").text.strip()
        logger.info(f"Wi-Fi 5 → SSID={ssid}, Kanal={ch}")
        return ssid, ch
    except Exception:
        logger.error(f"Wi-Fi 5 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"
