import logging
from ..browser import safe_find_text
from selenium.webdriver.common.by import By


def get_uptime(driver, logger: logging.Logger):
    logger.debug("Uptime çekiliyor")
    val = safe_find_text(driver, By.XPATH, "//div[@id='main']/div/div/p[5]/span", logger)
    logger.info(f"Uptime: {val}")
    return val


def get_ram(driver, logger: logging.Logger):
    logger.debug("RAM bilgisi çekiliyor")
    total_ram = 423064
    ram_free_text = safe_find_text(driver, By.ID, "memFree", logger, default="0")
    try:
        usage = round((total_ram - int(ram_free_text)) / total_ram * 100, 2)
        result = f"%{usage}"
        logger.info(f"RAM: {result} (free={ram_free_text})")
        return result
    except ValueError:
        logger.error(f"RAM hesaplama hatası: '{ram_free_text}' sayıya çevrilemedi")
        return "%N/A"


def get_cpu(driver, logger: logging.Logger):
    logger.debug("CPU bilgisi çekiliyor")
    cpu_text = safe_find_text(driver, By.ID, "cpuinfo", logger, default="0")
    try:
        result = f"%{cpu_text.replace('%', '').strip()}"
        logger.info(f"CPU: {result}")
        return result
    except Exception:
        logger.error("CPU parse hatası")
        return "%N/A"