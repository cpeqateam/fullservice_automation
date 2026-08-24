import logging
from ..browser import safe_find_text
from selenium.webdriver.common.by import By


def get_uptime(driver, logger: logging.Logger):
    logger.debug("Uptime çekiliyor")
    val = safe_find_text(driver, By.ID, "HP_systemTime", logger)
    logger.info(f"Uptime: {val}")
    return val


def get_ram(driver, logger: logging.Logger):
    logger.debug("RAM bilgisi çekiliyor")
    val = safe_find_text(driver, By.ID, "HP_cMemoryUsage", logger)
    logger.info(f"RAM: {val}")
    return val


def get_cpu(driver, logger: logging.Logger):
    logger.debug("CPU bilgisi çekiliyor")
    from selenium.webdriver.common.by import By
    from ..browser import safe_find_text
    # Yönetim sayfasına git
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "mmManagDiag"))
        ).click()
        import time; time.sleep(2)
        val = safe_find_text(driver, By.ID, "cCPUUsage", logger)
        logger.info(f"CPU: {val}")
        return val
    except Exception:
        logger.warning("CPU bu modelde desteklenmiyor → N/A")
        return "N/A"