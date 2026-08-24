import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import safe_find_text, HANDLE_ALERT


def _go_to_status(driver, logger):
    try:
        from .system_page import _go_to_status as gts
        gts(driver, logger)
    except Exception:
        logger.error(f"WiFi status navigasyon hatası:\n{traceback.format_exc()}")


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz bilgisi çekiliyor")
    try:
        _go_to_status(driver, logger)
        ssid = driver.find_element(By.ID, "ssid_multi_2g").get_attribute("value") or "N/A"
        ch   = driver.find_element(By.ID, "channel_multi_2g").get_attribute("value") or "N/A"
        bw   = driver.find_element(By.ID, "channelWidth_multi_2g").get_attribute("value") or "N/A"
        logger.info(f"Wi-Fi 2.4 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 2.4 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz bilgisi çekiliyor")
    try:
        _go_to_status(driver, logger)
        # 5GHz sekmesine tıkla
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "showWireless_multi_5g"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
        ssid = driver.find_element(By.ID, "ssid_multi_5g").get_attribute("value") or "N/A"
        ch   = driver.find_element(By.ID, "channel_multi_5g").get_attribute("value") or "N/A"
        bw   = driver.find_element(By.ID, "channelWidth_multi_5g").get_attribute("value") or "N/A"
        logger.info(f"Wi-Fi 5 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 5 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"