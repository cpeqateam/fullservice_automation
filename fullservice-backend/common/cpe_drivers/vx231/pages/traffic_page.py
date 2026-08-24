"""
VX231 trafik/WAN sayfası — download, upload, WAN IP.
Kaynak modüldeki GET_NETWORK() fonksiyonundan alındı.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import safe_text


def get_network(driver, logger):
    """Sol menüden Network sayfasına gidip download/upload/wan_ip çeker."""
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ml1:nth-child(10) > .click > .text"))
        ).click()
        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".ml2:nth-child(9) .text"))
        ).click()
        time.sleep(3)
    except Exception as e:
        logger.warning(f"Network sayfası açılamadı: {e}")

    download = safe_text(driver, By.CSS_SELECTOR, "tr:nth-child(3) > .table-content:nth-child(13)")
    upload   = safe_text(driver, By.CSS_SELECTOR, "tr:nth-child(3) > .table-content:nth-child(12)")
    wan_ip   = safe_text(driver, By.CSS_SELECTOR, "tr:nth-child(2) > .table-content:nth-child(4)")

    logger.info(f"DL: {download} | UL: {upload} | WAN: {wan_ip}")
    return download, upload, wan_ip
