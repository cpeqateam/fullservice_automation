import logging
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from ..browser import safe_find_text, SELECT_MENU, SWITCH_TO_CONTENT_FRAME


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("WiFi 2.4GHz çekiliyor")
    try:
        SELECT_MENU(driver, logger, "idx_3", "Ağ Durumu")
        SWITCH_TO_CONTENT_FRAME(driver, logger)
        # 2.4GHz tdText elementleri — Ağ Durumu sayfasında ilk satır 2.4GHz
        rows = driver.find_elements(By.XPATH, "//td[@class='tdText']")
        # 2.4GHz: index 9 = SSID, index 11 = Kanal
        ssid = rows[9].text.strip()  if len(rows) > 9  else "N/A"
        ch   = rows[11].text.strip() if len(rows) > 11 else "N/A"

        SELECT_MENU(driver, logger, "group_3", "WiFi")
        SELECT_MENU(driver, logger, "dropdown_72", "2.4GHz")
        SELECT_MENU(driver, logger, "idx_73", "2.4GHz Temel")
        SWITCH_TO_CONTENT_FRAME(driver, logger)
        try:
            # BW değeri arcTransformSelectWrapper içindeki span'da
            bw_span = driver.find_element(By.XPATH,
                "//div[contains(@class,'arcTransformSelectWrapper')]//span[@tabindex]")
            bw = bw_span.text.strip()
        except Exception:
            bw = "N/A"
        logger.info(f"WiFi 2.4 → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"WiFi 2.4 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("WiFi 5GHz çekiliyor")
    try:
        SELECT_MENU(driver, logger, "idx_3", "Ağ Durumu")
        SWITCH_TO_CONTENT_FRAME(driver, logger)
        rows = driver.find_elements(By.XPATH, "//td[@class='tdText_odd']")
        logger.debug(f"5GHz tdText_odd tümü: {[r.text.strip() for r in rows]}")
        # index 1 = SSID, index 3 = Kanal
        ssid = rows[1].text.strip() if len(rows) > 1 else "N/A"
        ch   = rows[3].text.strip() if len(rows) > 3 else "N/A"

        SELECT_MENU(driver, logger, "group_3", "WiFi")
        SELECT_MENU(driver, logger, "dropdown_75", "5GHz")
        SELECT_MENU(driver, logger, "idx_76", "5GHz Temel")
        SWITCH_TO_CONTENT_FRAME(driver, logger)
        try:
            bw_spans = driver.find_elements(By.XPATH,
                "//div[contains(@class,'arcTransformSelectWrapper')]//span[@tabindex]")
            bw = bw_spans[-1].text.strip() if bw_spans else "N/A"
        except Exception:
            bw = "N/A"
        logger.info(f"WiFi 5 → SSID={ssid}, Kanal={ch}, BW={bw}")
        return ssid, ch, bw
    except Exception:
        logger.error(f"WiFi 5 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A", "N/A"