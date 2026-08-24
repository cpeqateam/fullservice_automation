"""
ZTE EX3501 — Kablosuz (Wireless) sayfası
Menü: h_menu_list → #network → /Wireless
Çekilen: Bant genişliği (BW) 2.4 GHz ve 5 GHz
SSID ve Kanal bilgileri system_page'den alınır (login sonrası ana sayfa).
"""

import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT


def _navigate_to_wireless(driver, logger: logging.Logger):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.ID, "h_menu_list"))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#network']"))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/Wireless']"))).click()
    time.sleep(3)
    HANDLE_ALERT(driver, logger)
    logger.debug("Kablosuz sayfasına geçildi")


def get_wifi_bw(driver, logger: logging.Logger):
    """
    Kablosuz sayfasına giderek 2.4 GHz ve 5 GHz bant genişliklerini döndürür.
    Returns: (bw_24, bw_5)
    """
    logger.debug("Bant genişlikleri çekiliyor")
    bw_24 = "N/A"
    bw_5  = "N/A"
    try:
        _navigate_to_wireless(driver, logger)
        wait = WebDriverWait(driver, 10)

        # Varsayılan görünen bant: 5 GHz (radio_general değeri "1")
        bw_select = Select(wait.until(
            EC.presence_of_element_located((By.ID, "wifi_bandwidth_general"))
        ))
        bw_5 = bw_select.first_selected_option.text.strip()
        logger.info(f"5 GHz BW: {bw_5}")

        # 2.4 GHz'e geç
        radio_select = Select(wait.until(
            EC.presence_of_element_located((By.ID, "wifi_radio_general"))
        ))
        radio_select.select_by_value("0")
        time.sleep(2)

        bw_select = Select(wait.until(
            EC.presence_of_element_located((By.ID, "wifi_bandwidth_general"))
        ))
        bw_24 = bw_select.first_selected_option.text.strip()
        logger.info(f"2.4 GHz BW: {bw_24}")

    except TimeoutException:
        logger.error("Kablosuz sayfası zaman aşımı")
    except Exception:
        logger.error(f"BW çekme hatası:\n{traceback.format_exc()}")

    return bw_24, bw_5
