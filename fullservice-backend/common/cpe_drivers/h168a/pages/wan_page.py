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
        # Ana sayfadaki sol menüden WAN Bilgisi'ne tıkla
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space(text())='WAN Bilgi']"))
        ).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        time.sleep(2)
        HANDLE_ALERT(driver, logger)

        # IPTV → index 0
        iptv_ip    = safe_find_text(driver, By.ID, "HP_IPMask_0",    logger)
        iptv_durum = safe_find_text(driver, By.ID, "HP_ConnStatus_0", logger)
        iptv_sure  = safe_find_text(driver, By.ID, "HP_UpTime_0",    logger)

        # Internet → index 1
        inet_ip    = safe_find_text(driver, By.ID, "HP_IPMask_1",    logger)
        inet_durum = safe_find_text(driver, By.ID, "HP_ConnStatus_1", logger)
        inet_sure  = safe_find_text(driver, By.ID, "HP_UpTime_1",    logger)

        result["ipv4_internet"] = (inet_ip,  inet_durum,  inet_sure)
        result["ipv4_iptv"]     = (iptv_ip,  iptv_durum,  iptv_sure)

        # IPv6 → WAN üst menüsüne git, DSL Bağlantı Durumu accordion'u aç
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "mmInternet"))
            ).click()
            time.sleep(2)

            # DSL Bağlantı Durumu accordion'u aç
            dsl_bar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "DslStateDevBar"))
            )
            driver.execute_script("arguments[0].click();", dsl_bar)
            time.sleep(2)

            ipv6_ip    = safe_find_text(driver, By.ID, "cGuaNum:1",     logger)
            ipv6_durum = safe_find_text(driver, By.ID, "cConnStatus6:1", logger)
            ipv6_sure  = safe_find_text(driver, By.ID, "cUpTimeV6:1",   logger)
            result["ipv6_internet"] = (ipv6_ip, ipv6_durum, ipv6_sure)
            logger.debug(f"IPv6 → Durum={ipv6_durum}, Süre={ipv6_sure}")
        except Exception:
            logger.warning(f"IPv6 verisi alınamadı:\n{traceback.format_exc()}")

        logger.info(f"WAN sonuçları: {result}")
    except Exception:
        logger.error(f"WAN veri çekme hatası:\n{traceback.format_exc()}")

    return result