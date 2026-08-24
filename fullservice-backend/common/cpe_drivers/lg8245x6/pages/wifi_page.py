import time
import traceback
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import _get_frames, get_value_from_frames, get_text_from_frames_xpath, click_in_frames


def _get_wifi(driver, logger: logging.Logger, band: int):
    """
    Wi-Fi bilgilerini çeker.
    band=1 → 2.4 GHz, band=2 → 5 GHz
    """
    band_label = "2.4 GHz" if band == 1 else "5 GHz"
    logger.debug(f"Wi-Fi {band_label} bilgisi çekiliyor")
    wait = WebDriverWait(driver, 15)
    try:
        driver.switch_to.default_content()
        wait.until(EC.element_to_be_clickable((By.ID, "icon_Systeminfo"))).click()
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.ID, "name_wlaninfo"))).click()
        time.sleep(2)

        frames = _get_frames(driver)
        for frame in frames:
            try:
                driver.switch_to.frame(frame)
                els = driver.find_elements(By.XPATH, f"//input[@name='WlanMethod'][@value='{band}']")
                if els:
                    driver.execute_script("arguments[0].checked = true;", els[0])
                    driver.execute_script("onClickMethod();")
                    time.sleep(3)
                    driver.switch_to.default_content()
                    logger.debug(f"{band_label} radio butonu seçildi")
                    break
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()

        click_in_frames(driver, "tab4", logger)
        time.sleep(3)

        kanal = get_value_from_frames(driver, "wlanChannel", logger)
        bw    = get_value_from_frames(driver, "channelWide", logger)
        ssid  = get_text_from_frames_xpath(
            driver, "//td[contains(text(),'SSID')]/following-sibling::td[1]", logger
        )
        logger.info(f"Wi-Fi {band_label} → SSID={ssid}, Kanal={kanal}, BW={bw}")
        return ssid, kanal, bw
    except Exception:
        logger.error(f"WiFi {band_label} hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"