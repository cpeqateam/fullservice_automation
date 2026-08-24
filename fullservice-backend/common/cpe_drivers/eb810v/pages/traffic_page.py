import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("Download/Upload verisi çekiliyor")
    try:
        sistem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[url='time.htm']"))
        )
        driver.execute_script("arguments[0].click();", sistem)
        time.sleep(1)

        trafik = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[url='stat.htm']"))
        )
        driver.execute_script("arguments[0].click();", trafik)
        time.sleep(3)
        HANDLE_ALERT(driver, logger)
        logger.debug("Trafik sayfasına geçildi")

        t_on = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "t_on"))
        )
        if "selected" not in t_on.get_attribute("class"):
            driver.execute_script("arguments[0].click();", t_on)
            time.sleep(3)
            logger.debug("Trafik toggle açıldı")
        else:
            logger.debug("Trafik toggle zaten açık")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".pure-table-bordered tbody tr"))
        )
        time.sleep(1)

        rows = driver.find_elements(By.CSS_SELECTOR, ".pure-table-bordered tbody tr")
        cols = rows[0].find_elements(By.TAG_NAME, "td")
        logger.debug(f"Trafik sütun sayısı: {len(cols)}")

        dl = cols[7].text.strip() if len(cols) > 7 else "N/A"
        ul = cols[8].text.strip() if len(cols) > 8 else "N/A"
        logger.info(f"Download={dl}, Upload={ul}")
        return dl, ul

    except Exception:
        logger.error(f"Trafik veri çekme hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"