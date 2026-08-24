import logging
import traceback
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, SELECT_MENU, SWITCH_TO_CONTENT_FRAME


def get_wan(driver, logger: logging.Logger):
    logger.debug("WAN verileri çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A", "N/A"),
        "ipv6_internet": ("N/A", "N/A", "N/A"),
    }
    try:
        SELECT_MENU(driver, logger, "idx_35", "WAN Servisleri")
        SWITCH_TO_CONTENT_FRAME(driver, logger)
        rows = driver.find_elements(By.XPATH, "//table//tr[td]")
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            logger.debug(f"WAN satır {i}: {[c.text.strip() for c in cells]}")
            if len(cells) >= 6:
                isim = cells[0].text.strip()
                if "Internet" in isim or "İnternet" in isim:
                    ip    = cells[3].text.strip()
                    durum = cells[5].text.strip()
                    result["ipv4_internet"] = (ip, durum, "N/A")
                elif "IPTV" in isim:
                    ip    = cells[3].text.strip()
                    durum = cells[5].text.strip()
                    result["ipv4_iptv"] = (ip, durum, "N/A")

        logger.info(f"WAN: {result}")
    except Exception:
        logger.error(f"WAN hatası:\n{traceback.format_exc()}")
    return result