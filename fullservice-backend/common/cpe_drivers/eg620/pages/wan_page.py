import logging
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, NAVIGATE


def get_wan(driver, logger: logging.Logger):
    logger.debug("WAN verileri çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A", "N/A"),
        "ipv6_internet": ("N/A", "N/A", "N/A"),
    }
    try:
        NAVIGATE(driver, logger, "/cgi-bin/sta-network.asp", "Ağ")

        ipv4_durum = safe_find_text(driver, By.ID, "ipv4_conn_status", logger)
        ipv4_ip    = safe_find_text(driver, By.ID, "ipv4_ip_addr",     logger)
        ipv4_sure  = safe_find_text(driver, By.ID, "ipv4_conn_time",   logger)
        ipv6_durum = safe_find_text(driver, By.ID, "ipv6_conn_status", logger)
        ipv6_ip    = safe_find_text(driver, By.ID, "ipv6_ip_addr",     logger)
        ipv6_sure  = safe_find_text(driver, By.ID, "ipv6_conn_time",   logger)

        result["ipv4_internet"] = (ipv4_ip, ipv4_durum, ipv4_sure)
        result["ipv6_internet"] = (ipv6_ip, ipv6_durum, ipv6_sure)
        logger.info(f"WAN: {result}")
    except Exception as e:
        logger.error(f"WAN hatası: {e}")
    return result