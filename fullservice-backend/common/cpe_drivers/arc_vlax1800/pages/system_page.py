import logging
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, SELECT_MENU, SWITCH_TO_CONTENT_FRAME


def get_device_info(driver, logger: logging.Logger):
    logger.debug("Cihaz bilgileri çekiliyor")
    SELECT_MENU(driver, logger, "idx_5", "Yönlendirici Bilgisi")
    SWITCH_TO_CONTENT_FRAME(driver, logger)
    yazilim = safe_find_text(driver, By.ID, "runtime_code_version", logger, wait=5)
    donanim = safe_find_text(driver, By.ID, "hardware_version",     logger, wait=5)
    seri    = safe_find_text(driver, By.ID, "serial_number",        logger, wait=5)
    logger.info(f"Cihaz → Yazılım={yazilim}, Donanım={donanim}, Seri={seri}")
    return yazilim, donanim, seri


def get_uptime(driver, logger: logging.Logger):
    logger.debug("Uptime çekiliyor")
    SELECT_MENU(driver, logger, "idx_5", "Yönlendirici Bilgisi")
    SWITCH_TO_CONTENT_FRAME(driver, logger)
    val = safe_find_text(driver, By.ID, "uptime", logger)
    logger.info(f"Uptime: {val}")
    return val


def get_ram(driver, logger: logging.Logger):
    logger.warning("RAM bu modelde desteklenmiyor → N/A")
    return "N/A"


def get_cpu(driver, logger: logging.Logger):
    logger.warning("CPU bu modelde desteklenmiyor → N/A")
    return "N/A"