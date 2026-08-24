"""
ZTE EX3501 — DHCP sayfası
Menü yapısı bu modeme uygun değilse buradaki fonksiyon N/A döndürür.
İhtiyaç halinde selector'lar güncellenebilir.
"""
import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT


def get_dhcp_count(driver, logger: logging.Logger) -> str:
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        wait = WebDriverWait(driver, 10)
        # Ağ Ayarı → DHCP menüsü
        wait.until(EC.element_to_be_clickable((By.ID, "h_menu_list"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='#network']")
        )).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href,'DHCP') or contains(@href,'dhcp')]")
        )).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)

        rows = driver.find_elements(
            By.XPATH, "//table[contains(@class,'dhcp') or @id='dhcpTable']//tr[position()>1]"
        )
        count = str(len(rows))
        logger.info(f"DHCP Client Sayısı: {count}")
        return count

    except TimeoutException:
        logger.warning("DHCP sayfası bulunamadı")
        return "N/A"
    except Exception:
        logger.error(f"DHCP sayısı hatası:\n{traceback.format_exc()}")
        return "N/A"
