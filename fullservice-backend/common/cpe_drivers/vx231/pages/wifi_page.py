"""
VX231 Wi-Fi sayfası — 2.4 GHz ve 5 GHz.
Kaynak modüldeki GET_WIFI_24 / GET_WIFI_5 fonksiyonlarından alındı.
"""
import time
from selenium.webdriver.common.by import By
from ..browser import safe_value


def get_wifi_24(driver, logger):
    """2.4 GHz: SSID/Kanal/BW."""
    ssid = safe_value(driver, By.ID, "ssid_2g")
    ch   = safe_value(driver, By.ID, "channel_2g")
    bw   = safe_value(driver, By.ID, "channelWidth_2g")
    logger.info(f"2.4 -> {ssid} | {ch} | {bw}")
    return ssid, ch, bw


def get_wifi_5(driver, logger):
    """5 GHz: önce 'showWireless_5g' tıkla, sonra SSID/Kanal/BW."""
    try:
        driver.find_element(By.ID, "showWireless_5g").click()
        time.sleep(2)
    except Exception:
        pass

    ssid = safe_value(driver, By.ID, "ssid_5g")
    ch   = safe_value(driver, By.ID, "channel_5g")
    bw   = safe_value(driver, By.ID, "channelWidth_5g")
    logger.info(f"5 -> {ssid} | {ch} | {bw}")
    return ssid, ch, bw
