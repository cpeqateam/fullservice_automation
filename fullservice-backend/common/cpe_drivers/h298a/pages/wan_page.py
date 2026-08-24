import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import HANDLE_ALERT, safe_find_text


def get_wan(driver, logger: logging.Logger):
    logger.debug("WAN verileri çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A", "N/A"),
        "ipv6_internet": ("N/A", "N/A", "N/A"),
    }
    try:
        # WAN Bilgi sekmesine git
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(),'WAN Bilgi')]"))
        )
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'WAN Bilgi')]"))
        ).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)

        # IPTV → HP_IPMask:0, HP_ConnStatus:0
        iptv_ip     = safe_find_text(driver, By.ID, "HP_IPMask:0",     logger)
        iptv_durum  = safe_find_text(driver, By.ID, "HP_ConnStatus:0", logger)

        # VoIP → HP_IPMask:1, HP_ConnStatus:1
        voip_ip     = safe_find_text(driver, By.ID, "HP_IPMask:1",     logger)
        voip_durum  = safe_find_text(driver, By.ID, "HP_ConnStatus:1", logger)

        # Internet → HP_IPMask:3, HP_ConnStatus:3
        inet_ip     = safe_find_text(driver, By.ID, "HP_IPMask:3",     logger)
        inet_durum  = safe_find_text(driver, By.ID, "HP_ConnStatus:3", logger)

        result["ipv4_internet"] = (inet_ip,  inet_durum,  "N/A")
        result["ipv4_voice"]    = (voip_ip,  voip_durum,  "N/A")
        result["ipv4_iptv"]     = (iptv_ip,  iptv_durum,  "N/A")

        logger.info(f"WAN sonuçları: {result}")
    except Exception:
        logger.error(f"WAN veri çekme hatası:\n{traceback.format_exc()}")

    return result