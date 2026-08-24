import logging
import traceback
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


def get_dhcp_count(driver, logger: logging.Logger) -> str:
    """
    H3600'de DHCP client sayfası — selector güncellenmeli.
    Şimdilik placeholder.
    """
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        rows = driver.find_elements(
            By.XPATH, "//table//tr[position()>1 and normalize-space(.)!='']"
        )
        count = str(len(rows))
        logger.info(f"DHCP Client Sayısı: {count}")
        return count
    except Exception:
        logger.error(f"DHCP hatası:\n{traceback.format_exc()}")
        return "N/A"