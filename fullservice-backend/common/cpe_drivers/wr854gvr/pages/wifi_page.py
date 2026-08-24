"""
WR854GVR Wi-Fi sayfaları — 2.4 GHz ve 5 GHz için ayrı menüler.
Kaynak koddaki collect_data() (SSID/CH) + get_bandwidths() (BW) fonksiyonlarından alındı.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..browser import SWITCH_TO_CONTENT, CLICK_MENU


def get_wifi_24(driver, logger):
    """WLAN (2.4GHz) menüsünden SSID, Kanal, BW."""
    ssid = ch = bw = "N/A"
    try:
        CLICK_MENU(driver, "WLAN (2.4GHz)")
        SWITCH_TO_CONTENT(driver)
        wait = WebDriverWait(driver, 15)
        ssid = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "show_space"))).text.strip()
        ch = driver.find_element(
            By.XPATH, "//td[@class='show_space']/following::td[@width='60%'][1]"
        ).text.strip()
        try:
            bw = wait.until(EC.presence_of_element_located((By.ID, "auto_chanwid"))).get_attribute("value")
        except Exception:
            pass
        logger.info(f"2.4 -> {ssid} | {ch} | {bw}")
    except Exception as e:
        logger.error(f"WiFi 2.4 hata: {e}")
    return ssid, ch, bw


def get_wifi_5(driver, logger):
    """WLAN (5GHz) menüsünden SSID, Kanal, BW."""
    ssid = ch = bw = "N/A"
    try:
        CLICK_MENU(driver, "WLAN (5GHz)")
        SWITCH_TO_CONTENT(driver)
        wait = WebDriverWait(driver, 15)
        ssid = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "show_space"))).text.strip()
        ch = driver.find_element(
            By.XPATH, "//td[@class='show_space']/following::td[@width='60%'][1]"
        ).text.strip()
        try:
            bw = wait.until(EC.presence_of_element_located((By.ID, "auto_chanwid"))).get_attribute("value")
        except Exception:
            pass
        logger.info(f"5 -> {ssid} | {ch} | {bw}")
    except Exception as e:
        logger.error(f"WiFi 5 hata: {e}")
    return ssid, ch, bw
