import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT, wait_loading


def get_dhcp_count(driver, logger: logging.Logger) -> str:
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        wait = WebDriverWait(driver, 10)

        # 1. Hamburger menüyü aç
        wait_loading(driver, logger)
        driver.execute_script("document.getElementById('h_menu_list').click()")
        time.sleep(1)

        # 2. Ağ Ayarı
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='#network']")
        )).click()
        time.sleep(1)

        # 3. Geniş Bant
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='/Broadband']")
        )).click()
        wait_loading(driver, logger)
        HANDLE_ALERT(driver, logger)

        # 4. Tablodaki son td'yi al
        rows = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//td[@scope='row']")
        ))
        count = rows[-1].text.strip()
        logger.info(f"DHCP Client Sayısı: {count}")
        return count

    except TimeoutException:
        logger.warning("DHCP sayfası bulunamadı")
        return "N/A"
    except Exception:
        logger.error(f"DHCP sayısı hatası:\n{traceback.format_exc()}")
        return "N/A"