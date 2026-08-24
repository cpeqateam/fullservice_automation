import logging
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, NAVIGATE


def get_device_info(driver, logger: logging.Logger):
    logger.debug("Cihaz bilgileri çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-device.asp", "Cihaz Bilgileri")
    yazilim = safe_find_text(driver, By.ID, "swverLabel",      logger, wait=5)
    seri    = safe_find_text(driver, By.ID, "serial_num_info", logger, wait=5)
    logger.info(f"Cihaz → Yazılım={yazilim}, Seri={seri}")
    return yazilim, seri


def get_uptime(driver, logger: logging.Logger):
    logger.debug("Uptime çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-device.asp", "Cihaz Bilgileri")
    val = safe_find_text(driver, By.XPATH,
        "//div[contains(@class,'item') and contains(text(),':')]", logger)
    logger.info(f"Uptime: {val}")
    return val


def get_ram(driver, logger: logging.Logger):
    logger.debug("RAM çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-device.asp", "Cihaz Bilgileri")
    val = safe_find_text(driver, By.XPATH,
        "//div[contains(@class,'item') and contains(text(),'MB')]", logger)
    logger.info(f"RAM: {val}")
    return val


def get_cpu(driver, logger: logging.Logger):
    logger.debug("CPU çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-device.asp", "Cihaz Bilgileri")
    cpu1 = safe_find_text(driver, By.ID, "cpu_usage_1", logger)
    cpu2 = safe_find_text(driver, By.ID, "cpu_usage_2", logger)
    val = f"{cpu1} | {cpu2}"
    logger.info(f"CPU: {val}")
    return val