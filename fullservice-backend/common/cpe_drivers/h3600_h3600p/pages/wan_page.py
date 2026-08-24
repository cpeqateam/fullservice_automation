import logging
import traceback
import time
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, wait_click


def go_to_wan_page(driver, logger: logging.Logger):
    logger.debug("WAN sayfasına gidiliyor")
    try:
        wait_click(driver, By.ID, "internet", logger)
        time.sleep(1)
        wait_click(driver, By.ID, "EthStateDevBar", logger)
        time.sleep(1)
        logger.debug("WAN sayfası yüklendi")
    except Exception:
        logger.error(f"WAN sayfasına gidilemedi:\n{traceback.format_exc()}")
        raise


def get_ipv4_iptv(driver, logger: logging.Logger):
    logger.debug("IPv4 IPTV çekiliyor")
    ip    = safe_find_text(driver, By.ID, "cIPAddress:0", logger)
    durum = safe_find_text(driver, By.ID, "cConnStatus:0", logger)
    sure  = safe_find_text(driver, By.ID, "cUpTime:0", logger)
    ip    = ip.split("/")[0].strip()
    logger.info(f"IPv4 IPTV → IP={ip}, Durum={durum}, Süre={sure}")
    return ip, durum, sure


def get_ipv4_voice(driver, logger: logging.Logger):
    logger.debug("IPv4 Voice çekiliyor")
    ip    = safe_find_text(driver, By.ID, "cIPAddress:1", logger)
    durum = safe_find_text(driver, By.ID, "cConnStatus:1", logger)
    sure  = safe_find_text(driver, By.ID, "cUpTime:1", logger)
    ip    = ip.split("/")[0].strip()
    logger.info(f"IPv4 Voice → IP={ip}, Durum={durum}, Süre={sure}")
    return ip, durum, sure


def get_ipv4_internet(driver, logger: logging.Logger):
    logger.debug("IPv4 Internet çekiliyor")
    ip    = safe_find_text(driver, By.ID, "cIPAddress:2", logger)
    durum = safe_find_text(driver, By.ID, "cConnStatus:2", logger)
    sure  = safe_find_text(driver, By.ID, "cUpTime:2", logger)
    ip    = ip.split("/")[0].strip()
    logger.info(f"IPv4 Internet → IP={ip}, Durum={durum}, Süre={sure}")
    return ip, durum, sure


def get_ipv6_internet(driver, logger: logging.Logger):
    logger.debug("IPv6 Internet çekiliyor")
    durum = safe_find_text(driver, By.ID, "cConnStatus6:2", logger)
    sure  = safe_find_text(driver, By.ID, "cUpTimeV6:2", logger)
    logger.info(f"IPv6 → Durum={durum}, Süre={sure}")
    return durum, sure