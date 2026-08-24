import logging
import time
from selenium.webdriver.common.by import By


def get_dhcp_count(driver, logger: logging.Logger):
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        driver.get("http://192.168.1.1/cgi-bin/sta-connect-client.asp")
        time.sleep(3)
        rows = driver.find_elements(By.CSS_SELECTOR, "#table_ethernet tbody tr.sub-title")
        count = str(len(rows))
        logger.info(f"DHCP Client Sayısı: {count}")
        return count
    except Exception as e:
        logger.error(f"DHCP hatası: {e}")
        return "N/A"