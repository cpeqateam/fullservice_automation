"""
ZTE EX3301-T0 — Kablosuz (Wireless) sayfası
"""

import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT, wait_loading


def _navigate_to_wireless(driver, logger: logging.Logger):
    wait = WebDriverWait(driver, 10)
    wait_loading(driver, logger)
    driver.execute_script("document.getElementById('h_menu_list').click()")
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='#network']"))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/Wireless']"))).click()
    wait_loading(driver, logger)
    HANDLE_ALERT(driver, logger)
    logger.debug("Kablosuz sayfasına geçildi")


def get_wifi_bw(driver, logger: logging.Logger):
    logger.debug("Bant genişlikleri çekiliyor")
    bw_24 = "N/A"
    bw_5  = "N/A"
    try:
        _navigate_to_wireless(driver, logger)
        wait = WebDriverWait(driver, 10)

        # Sayfa açılınca varsayılan 2.4GHz seçili geliyor — önce 2.4'ü oku
        radio_select = Select(wait.until(
            EC.presence_of_element_located((By.ID, "wifi_radio_general"))
        ))
        radio_select.select_by_value("0")  # 2.4GHz
        time.sleep(2)

        bw_select = Select(wait.until(
            EC.presence_of_element_located((By.ID, "wifi_bandwidth_general"))
        ))
        bw_24 = bw_select.first_selected_option.text.strip()
        logger.info(f"2.4 GHz BW: {bw_24}")

        # 5GHz'e geç
        radio_select = Select(driver.find_element(By.ID, "wifi_radio_general"))
        radio_select.select_by_value("4")  # 5GHz value="4"
        time.sleep(2)

        bw_select = Select(wait.until(
            EC.presence_of_element_located((By.ID, "wifi_bandwidth_general"))
        ))
        bw_5 = bw_select.first_selected_option.text.strip()
        logger.info(f"5 GHz BW: {bw_5}")

    except TimeoutException:
        logger.error("Kablosuz sayfası zaman aşımı")
    except Exception:
        logger.error(f"BW çekme hatası:\n{traceback.format_exc()}")

    return bw_24, bw_5