import logging
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, NAVIGATE


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("Download/Upload çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-network.asp", "Ağ")
    dl = safe_find_text(driver, By.ID, "sta_rx_bytes", logger)
    ul = safe_find_text(driver, By.ID, "sta_tx_bytes", logger)
    logger.info(f"Download={dl}, Upload={ul}")
    return dl, ul