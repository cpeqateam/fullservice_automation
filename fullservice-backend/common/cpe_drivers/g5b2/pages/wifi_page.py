import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT, safe_find_text


def _go_wifi_advanced(driver, logger: logging.Logger):
    try:
        # Önce farklı bir menüye tıkla ki WiFi menüsü kapansın, sonra tekrar aç
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='wifi']"))
        ).click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='wifi_advance']"))
        ).click()
        time.sleep(3)
        logger.debug("WiFi Gelişmiş sayfasına girildi")
    except Exception:
        logger.error(f"WiFi menü navigasyon hatası:\n{traceback.format_exc()}")


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz bilgisi çekiliyor")
    try:
        _go_wifi_advanced(driver, logger)
        HANDLE_ALERT(driver, logger)

        bw_select = Select(driver.find_element(By.ID, "wifi_channel_bandwidth"))
        ch_select  = Select(driver.find_element(By.ID, "channel"))
        bw = bw_select.first_selected_option.text
        ch = ch_select.first_selected_option.text

        # SSID
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='multi_ssid_1']"))
        ).click()
        time.sleep(2)
        ssid = driver.find_element(By.ID, "ssid").get_attribute("value")

        logger.info(f"Wi-Fi 2.4 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 2.4 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz bilgisi çekiliyor")
    try:
        # Anasayfaya dön ki WiFi menüsü sıfırlansın
        driver.get("http://192.168.0.1/index.html")
        time.sleep(2)
        _go_wifi_advanced(driver, logger)
        HANDLE_ALERT(driver, logger)

        bw_select = Select(driver.find_element(By.ID, "wifi_channel_bandwidth_5g"))
        ch_select  = Select(driver.find_element(By.ID, "channels_5g"))
        bw = bw_select.first_selected_option.text
        ch = ch_select.first_selected_option.text

        # 5GHz SSID → Sistem > Cihaz Bilgileri sayfasında
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='system']"))
        ).click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='device_information']"))
        ).click()
        time.sleep(2)
        ssid = safe_find_text(driver, By.XPATH, "//label[contains(@data-bind,'wifiSsid5gMain')]", logger)

        logger.info(f"Wi-Fi 5 GHz → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"Wi-Fi 5 GHz hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"