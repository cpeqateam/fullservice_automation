import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import HANDLE_ALERT

def _go_to_status(driver, logger):
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[@class='ml1']/a[@url='status.htm']")
            )
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        logger.debug("Durum sayfasına gidildi")
    except Exception:
        logger.error(f"Durum sayfası navigasyon hatası:\n{traceback.format_exc()}")

def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz bilgisi çekiliyor")
    _go_to_status(driver, logger)
    try:
        ssid = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ssid_2g"))
        ).get_attribute("value")
        ch = driver.find_element(By.ID, "channel_2g").get_attribute("value")
        bw = driver.find_element(By.ID, "channelWidth_2g").get_attribute("value")
        logger.info(f"Wi-Fi 2.4 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 2.4 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz bilgisi çekiliyor")
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "showWireless_5g"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        ssid = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ssid_5g"))
        ).get_attribute("value")
        ch = driver.find_element(By.ID, "channel_5g").get_attribute("value")
        bw = driver.find_element(By.ID, "channelWidth_5g").get_attribute("value")
        logger.info(f"Wi-Fi 5 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 5 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"