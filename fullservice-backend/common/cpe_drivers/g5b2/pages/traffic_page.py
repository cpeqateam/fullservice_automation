import logging
from ..browser import safe_find_text
from selenium.webdriver.common.by import By


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("Download/Upload verisi çekiliyor")
    # Anasayfada görünür, navigasyon gerekmez
    dl = safe_find_text(driver, By.XPATH, "//span[contains(@data-bind,'down_Speed')]", logger)
    ul = safe_find_text(driver, By.XPATH, "//span[contains(@data-bind,'up_Speed')]", logger)
    logger.info(f"Download={dl}, Upload={ul}")
    return dl, ul