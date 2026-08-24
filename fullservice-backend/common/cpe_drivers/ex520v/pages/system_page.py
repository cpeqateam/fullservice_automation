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


def get_uptime(driver, logger: logging.Logger):
    logger.debug("Uptime çekiliyor")
    _go_to_status(driver, logger)
    try:
        val = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "UpTime"))
        ).get_attribute("value")
        logger.info(f"Uptime: {val}")
        return val if val else "N/A"
    except Exception:
        logger.error(f"Uptime hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_ram(driver, logger: logging.Logger):
    logger.debug("RAM bilgisi çekiliyor")
    _go_to_status(driver, logger)  # ✅ ekle
    try:
        val = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mem_gitem"))
        ).text.strip()
        logger.info(f"RAM: {val}")
        return val
    except Exception:
        logger.error(f"RAM hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_cpu(driver, logger: logging.Logger):
    logger.debug("CPU bilgisi çekiliyor")
    try:
        val = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cpu_gitem"))
        ).text.strip()
        logger.info(f"CPU: {val}")
        return val
    except Exception:
        logger.error(f"CPU hatası:\n{traceback.format_exc()}")
        return "N/A"