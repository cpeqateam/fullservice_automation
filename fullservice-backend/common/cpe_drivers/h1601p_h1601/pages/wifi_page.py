import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import HANDLE_ALERT, safe_find_text


def _go_localnet(driver, logger: logging.Logger):
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "localnet"))
        ).click()
        time.sleep(2)
        logger.debug("Yerel Ağ sayfasına girildi")
    except Exception:
        logger.error(f"Yerel Ağ navigasyon hatası:\n{traceback.format_exc()}")


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz bilgisi çekiliyor")
    try:
        _go_localnet(driver, logger)
        HANDLE_ALERT(driver, logger)

        ssid = safe_find_text(driver, By.ID, "ESSID:0",           logger)
        ch   = safe_find_text(driver, By.ID, "ChannelInUsed_0",   logger)
        bw   = safe_find_text(driver, By.ID, "BandWidthInUsed_0", logger)

        logger.info(f"Wi-Fi 2.4 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 2.4 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz bilgisi çekiliyor")
    try:
        _go_localnet(driver, logger)
        HANDLE_ALERT(driver, logger)

        ssid = safe_find_text(driver, By.ID, "ESSID:4",           logger)
        ch   = safe_find_text(driver, By.ID, "ChannelInUsed_1",   logger)
        bw   = safe_find_text(driver, By.ID, "BandWidthInUsed_1", logger)

        logger.info(f"Wi-Fi 5 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 5 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"