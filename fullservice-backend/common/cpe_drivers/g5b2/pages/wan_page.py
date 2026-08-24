import logging
import time
from ..browser import safe_find_text, HANDLE_ALERT
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_wan(driver, logger: logging.Logger):
    logger.debug("WAN verileri çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A", "N/A"),
        "ipv6_internet": ("N/A", "N/A", "N/A"),
    }
    try:
        # Sistem → Cihaz Bilgileri sayfasına git
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='system']"))
        ).click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-trans='device_information']"))
        ).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)

        # IPv4 Internet IP
        ipv4 = safe_find_text(driver, By.XPATH, "//label[contains(@data-bind,'wanIpAddress')]", logger)
        # IPv6 Internet IP
        ipv6 = safe_find_text(driver, By.XPATH, "//label[contains(@data-bind,'wanIpv6Address')]", logger)

        # Uptime anasayfadan alındığı için durum "Bağlı" varsayıyoruz
        result["ipv4_internet"] = (ipv4, "N/A", "N/A")
        result["ipv6_internet"] = (ipv6, "N/A", "N/A")

        logger.info(f"WAN sonuçları: {result}")
    except Exception as e:
        logger.error(f"WAN veri çekme hatası: {e}")

    return result