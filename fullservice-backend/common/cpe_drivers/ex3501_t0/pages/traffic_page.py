"""
ZTE EX3501 — Trafik Durumu sayfası
Menü: h_menu_list → #system (Sistem Monitörü) → span[Trafik Durumu]
Çekilen:
  - WAN Gönderilen : SystemMonitor_TrafficStatus_WAN_Sent
  - WAN Alınan     : SystemMonitor_TrafficStatus_WAN_Received
"""

import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT


def get_download_upload(driver, logger: logging.Logger):
    """
    WAN trafik istatistiklerini döndürür.
    Returns: (wan_sent, wan_received)
    """
    logger.debug("WAN trafik verisi çekiliyor")
    wan_sent = "N/A"
    wan_recv = "N/A"

    try:
        wait = WebDriverWait(driver, 10)

        # Menüyü aç
        wait.until(EC.element_to_be_clickable((By.ID, "h_menu_list"))).click()
        time.sleep(1)

        # Sistem Monitörü
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='#system']")
        )).click()
        time.sleep(1)

        # Trafik Durumu
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//span[text()='Trafik Durumu']")
        )).click()
        time.sleep(3)
        HANDLE_ALERT(driver, logger)

        # WAN Gönderilen
        wan_sent = wait.until(EC.presence_of_element_located(
            (By.ID, "SystemMonitor_TrafficStatus_WAN_Sent")
        )).text.strip()

        # WAN Alınan
        wan_recv = driver.find_element(
            By.ID, "SystemMonitor_TrafficStatus_WAN_Received"
        ).text.strip()

        logger.info(f"WAN Gönderilen: {wan_sent} | Alınan: {wan_recv}")

    except TimeoutException:
        logger.error("Trafik sayfası zaman aşımı")
    except Exception:
        logger.error(f"Trafik verisi hatası:\n{traceback.format_exc()}")

    return wan_sent, wan_recv
