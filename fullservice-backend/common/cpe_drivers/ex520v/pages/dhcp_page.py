import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT


def get_dhcp_count(driver, logger: logging.Logger):
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        # Ağ ana menüsü
        ag = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[@class='ml1']/a[@url='ethWan.htm']")
            )
        )
        driver.execute_script("arguments[0].click();", ag)
        time.sleep(1)

        # LAN Ayarları
        lan = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//li[@class='ml2']/a[@url='dhcp.htm']")
            )
        )
        driver.execute_script("arguments[0].click();", lan)

        # Tablo yüklenene kadar bekle
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script(
                "var rows = document.querySelectorAll('table tbody tr');"
                "return rows.length > 0;"
            )
        )
        time.sleep(1)
        HANDLE_ALERT(driver, logger)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        count = 0
        for row in rows:
            tds = row.find_elements(By.CSS_SELECTOR, "td")
            if tds and tds[0].text.strip().isdigit():
                count += 1

        logger.info(f"DHCP Client Sayısı: {count}")
        return str(count)

    except TimeoutException:
        logger.error("DHCP sayfası zaman aşımı")
        return "0"
    except Exception:
        logger.error(f"DHCP sayısı çekme hatası:\n{traceback.format_exc()}")
        return "0"