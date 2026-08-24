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
        # Sistem Araçları ana menüsü
        sistem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[url='time.htm']"))
        )
        driver.execute_script("arguments[0].click();", sistem)
        time.sleep(1)

        # Trafik İstatistikleri alt menü
        trafik = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[url='stat.htm']"))
        )
        driver.execute_script("arguments[0].click();", trafik)
        time.sleep(3)
        HANDLE_ALERT(driver, logger)
        logger.debug("Trafik sayfasına geçildi")

        # Toggle açık mı kontrol et
        t_on = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "t_on"))
        )
        if "selected" not in t_on.get_attribute("class"):
            driver.execute_script("arguments[0].click();", t_on)
            time.sleep(3)
            logger.debug("Trafik toggle açıldı")
        else:
            logger.debug("Trafik toggle zaten açık")

        # Tablo bekle
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#table-stat tbody tr"))
        )
        time.sleep(1)

        rows = driver.find_elements(By.CSS_SELECTOR, "#table-stat tbody tr")
        cols = rows[0].find_elements(By.CLASS_NAME, "table-content")
        logger.debug(f"Trafik sütun sayısı: {len(cols)}")

        ul = cols[9].text.strip()
        dl = cols[10].text.strip()
        logger.info(f"Download={dl}, Upload={ul}")
        return dl, ul

    except Exception:
        logger.error(f"Trafik veri çekme hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"