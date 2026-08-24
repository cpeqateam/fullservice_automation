import logging
from ..browser import safe_find_text
from selenium.webdriver.common.by import By


def get_uptime(driver, logger: logging.Logger):
    logger.debug("Uptime çekiliyor")
    val = safe_find_text(driver, By.ID, "HP_systemTime", logger)
    logger.info(f"Uptime: {val}")
    return val


def get_ram(driver, logger: logging.Logger):
    # H298A: RAM arayüzde mevcut değil
    logger.warning("RAM bu modelde desteklenmiyor → N/A")
    return "N/A"


def get_cpu(driver, logger: logging.Logger):
    # H298A: CPU arayüzde mevcut değil
    logger.warning("CPU bu modelde desteklenmiyor → N/A")
    return "N/A"