import logging
import traceback
import time
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, safe_find_value, wait_click


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz çekiliyor")
    try:
        wait_click(driver, By.ID, "localnet", logger)
        time.sleep(2)
        ssid = safe_find_text(driver, By.ID, "ESSID:0", logger)
        ch   = safe_find_text(driver, By.ID, "ChannelInUsed_0", logger)
        wait_click(driver, By.ID, "wlanConfig", logger)
        time.sleep(2)
        wait_click(driver, By.ID, "WlanBasicAdConfBar", logger)
        time.sleep(2)
        bw   = safe_find_value(driver, By.ID, "UI_BandWidth:0", logger)
        logger.info(f"Wi-Fi 2.4 → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 2.4 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz çekiliyor")
    try:
        wait_click(driver, By.ID, "localnet", logger)
        time.sleep(2)
        ssid = safe_find_text(driver, By.ID, "ESSID:4", logger)
        ch   = safe_find_text(driver, By.ID, "ChannelInUsed_1", logger)
        wait_click(driver, By.ID, "wlanConfig", logger)
        time.sleep(2)
        wait_click(driver, By.ID, "WlanBasicAdConfBar", logger)
        time.sleep(2)
        bw   = safe_find_value(driver, By.ID, "UI_BandWidth:1", logger)
        logger.info(f"Wi-Fi 5 → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 5 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"