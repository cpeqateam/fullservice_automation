"""
EX20V WiFi sayfasi kaziyici — 2.4 GHz ve 5 GHz bilgilerini okur.

Her bant icin (SSID, kanal, bant genisligi) uclusu doner.
Eleman bulunamazsa ("N/A", "N/A", "N/A") tuple'i doner.
"""
import logging
import traceback
from selenium.webdriver.common.by import By
from ..browser import safe_find_text


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz bilgisi çekiliyor")
    try:
        ssid = safe_find_text(driver, By.XPATH, "//div[@id='wlan1']/p[3]/span", logger)
        ch   = safe_find_text(driver, By.ID, "wlchl0", logger)
        bw   = safe_find_text(driver, By.ID, "wlbw0", logger)
        logger.info(f"Wi-Fi 2.4 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 2.4 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz bilgisi çekiliyor")
    try:
        ssid = safe_find_text(driver, By.XPATH, "(//div[@id='wlan1']/p[3]/span)[2]", logger)
        ch   = safe_find_text(driver, By.ID, "wlchl1", logger)
        bw   = safe_find_text(driver, By.ID, "wlbw1", logger)
        logger.info(f"Wi-Fi 5 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 5 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"
