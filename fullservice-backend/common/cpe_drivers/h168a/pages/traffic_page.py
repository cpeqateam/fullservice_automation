import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import HANDLE_ALERT, safe_find_text


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("Download/Upload verisi çekiliyor")
    try:
        # WAN üst menüsüne git
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "mmInternet"))
        ).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)

        # DSL Bağlantı Durumu accordion'u aç
        dsl_bar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "DslStateDevBar"))
        )
        driver.execute_script("arguments[0].click();", dsl_bar)
        time.sleep(2)

        # receive → "dl/ul" formatında
        receive = safe_find_text(driver, By.ID, "receive:1", logger)
        if "/" in receive:
            parts = receive.split("/")
            dl = parts[0].strip()
            ul = parts[1].strip()
        else:
            dl = receive
            ul = "N/A"

        logger.info(f"Download={dl}, Upload={ul}")
        return dl, ul
    except Exception:
        logger.error(f"Download/Upload hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"