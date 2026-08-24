import logging
from selenium.webdriver.common.by import By
from ..browser import SELECT_MENU, SWITCH_TO_CONTENT_FRAME


def get_dhcp_count(driver, logger: logging.Logger):
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        SELECT_MENU(driver, logger, "idx_2", "Bağlı Cihazlar")
        SWITCH_TO_CONTENT_FRAME(driver, logger)
        rows = driver.find_elements(By.XPATH, "//table[@id='table_eth']//tr[td]")
        count = str(len(rows))
        logger.info(f"DHCP Client Sayısı: {count}")
        return count
    except Exception as e:
        logger.error(f"DHCP hatası: {e}")
        return "N/A"