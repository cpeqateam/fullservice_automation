"""
EX20V trafik sayfasi kaziyici — download ve upload degerlerini okur.

menu_infomenu -> menu_infomenutraffic menusunu tiklar, pvc_stat_table'dan
ilk satirin 9. (DL) ve 8. (UL) sutunlarini alir.
Doner: (download_str, upload_str)
"""
import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT, safe_find_text


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("Download/Upload verisi çekiliyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "menu_infomenu"))
        ).click()
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#menu_infomenutraffic"))
        ).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        logger.debug("Trafik sayfasına geçildi")
    except TimeoutException:
        logger.warning("Trafik menüsüne tıklama zaman aşımı")
    except Exception:
        logger.error(f"Trafik sayfası navigasyon hatası:\n{traceback.format_exc()}")

    dl = safe_find_text(driver, By.CSS_SELECTOR, "#pvc_stat_table tr:nth-child(1) > td:nth-child(9)", logger)
    ul = safe_find_text(driver, By.CSS_SELECTOR, "#pvc_stat_table tr:nth-child(1) > td:nth-child(8)", logger)
    logger.info(f"Download={dl}, Upload={ul}")
    return dl, ul
