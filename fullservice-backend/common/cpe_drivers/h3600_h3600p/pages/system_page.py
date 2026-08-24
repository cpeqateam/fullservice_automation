import logging
import traceback
import time
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, wait_click


def get_device_info(driver, logger: logging.Logger):
    logger.debug("Cihaz bilgileri çekiliyor")
    try:
        wait_click(driver, By.ID, "mgrAndDiag", logger)
        time.sleep(1)
        yazilim = safe_find_text(driver, By.ID, "SoftwareVer", logger)
        donanim = safe_find_text(driver, By.ID, "HardwareVer", logger)
        seri    = safe_find_text(driver, By.ID, "SerialNumber", logger)
        logger.info(f"Yazılım={yazilim} | Donanım={donanim} | Seri={seri}")
        return yazilim, donanim, seri
    except Exception:
        logger.error(f"Cihaz bilgisi hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_uptime(driver, logger: logging.Logger) -> str:
    logger.debug("Uptime çekiliyor")
    val = safe_find_text(driver, By.ID, "cUpTime", logger)
    logger.info(f"Uptime: {val}")
    return val


def get_ram(driver, logger: logging.Logger) -> str:
    logger.debug("RAM çekiliyor")
    val = safe_find_text(driver, By.ID, "cMemoryUsage", logger)
    logger.info(f"RAM: {val}")
    return val


def get_cpu(driver, logger: logging.Logger) -> str:
    logger.debug("CPU çekiliyor")
    val = safe_find_text(driver, By.ID, "cCPUUsage", logger)
    logger.info(f"CPU: {val}")
    return val


def go_to_system_page(driver, logger: logging.Logger):
    logger.debug("Sistem sayfasına gidiliyor")
    try:
        wait_click(driver, By.ID, "mgrAndDiag", logger)
        time.sleep(1)
        logger.debug("Sistem sayfası yüklendi")
    except Exception:
        logger.error(f"Sistem sayfasına gidilemedi:\n{traceback.format_exc()}")
        raise