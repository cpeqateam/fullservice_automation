import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from ..browser import safe_find_text, NAVIGATE, OPEN_LAN_MENU


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("WiFi 2.4GHz çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-wlan-24g.asp", "2.4GHz Kablosuz")
    ssid = safe_find_text(driver, By.XPATH, "(//td[not(@id)])[1]", logger)
    ch   = safe_find_text(driver, By.ID, "wlan_channel", logger)
    bw   = _get_bw(driver, logger, "wlan_bandwidth")
    logger.info(f"WiFi 2.4 → SSID={ssid}, Kanal={ch}, BW={bw}")
    return ssid, ch, bw


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("WiFi 5GHz çekiliyor")
    NAVIGATE(driver, logger, "/cgi-bin/sta-wlan-5g.asp", "5GHz Kablosuz")
    ssid = safe_find_text(driver, By.XPATH, "(//td[not(@id)])[1]", logger)
    ch   = safe_find_text(driver, By.ID, "wlan_channel", logger)
    bw   = _get_bw(driver, logger, "wlan_bandwidth_5g")
    logger.info(f"WiFi 5 → SSID={ssid}, Kanal={ch}, BW={bw}")
    return ssid, ch, bw


def _get_bw(driver, logger: logging.Logger, select_id: str):
    try:
        OPEN_LAN_MENU(driver, logger)
        NAVIGATE(driver, logger, "/cgi-bin/lan-wlan.asp", "Kablosuz Ağ Ayarları")
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        # Her iki Gelişmiş butonunu da dene
        for btn_id in ["advanceButton_5g", "advanceButton"]:
            try:
                adv_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.ID, btn_id))
                )
                driver.execute_script("arguments[0].click();", adv_btn)
                time.sleep(1)
                break
            except Exception:
                pass
        sel = Select(driver.find_element(By.ID, select_id))
        return sel.first_selected_option.text
    except Exception:
        return "N/A"