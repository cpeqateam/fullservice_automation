import time
import traceback
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import get_value_from_frames


def _get_sistem_bilgisi(driver, logger: logging.Logger):
    """Uptime, RAM ve CPU bilgilerini sistem sayfasından çeker."""
    logger.debug("Sistem bilgisi çekiliyor")
    wait = WebDriverWait(driver, 10)
    try:
        driver.switch_to.default_content()
        wait.until(EC.element_to_be_clickable((By.ID, "icon_Systeminfo"))).click()
        time.sleep(3)
        cpu    = get_value_from_frames(driver, "td9_2", logger)
        ram    = get_value_from_frames(driver, "td10_2", logger)
        uptime = get_value_from_frames(driver, "ShowTime", logger)
        logger.info(f"Sistem bilgisi → Uptime={uptime}, RAM={ram}, CPU={cpu}")
        return uptime, ram, cpu
    except Exception:
        logger.error(f"Sistem bilgisi hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"

def _get_device_info(driver, logger: logging.Logger):
    """Modem yazılım, donanım ve seri numarasını döndürür."""
    logger.debug("Cihaz bilgileri çekiliyor")
    wait = WebDriverWait(driver, 10)
    try:
        driver.switch_to.default_content()
        wait.until(EC.element_to_be_clickable((By.ID, "icon_Systeminfo"))).click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.ID, "name_deviceinfo"))).click()
        time.sleep(2)
        yazilim = get_value_from_frames(driver, "td5_2", logger)
        donanim = get_value_from_frames(driver, "td4_2", logger)
        seri    = get_value_from_frames(driver, "td3_2", logger)
        logger.info(f"Cihaz bilgileri → Yazılım={yazilim}, Donanım={donanim}, Seri={seri}")
        return yazilim, donanim, seri
    except Exception:
        logger.error(f"Cihaz bilgileri hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"