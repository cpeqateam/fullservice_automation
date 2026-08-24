import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..browser import HANDLE_ALERT

def _go_to_internet(driver, logger):
    try:
        # 1. Ağ ana menüsünü aç (ml1 li içindeki .more olan)
        ag_li = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//li[@class='ml1']/a[@url='ethWan.htm']")
            )
        )
        driver.execute_script("arguments[0].click();", ag_li)
        time.sleep(1)

        # 2. İnternet alt menüsüne tıkla (ml2 içindeki)
        internet = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//li[@class='ml2']/a[@url='ethWan.htm']")
            )
        )
        driver.execute_script("arguments[0].click();", internet)

        # s_internet_setup görünür olana kadar bekle
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script(
                "var el = document.getElementById('s_internet_setup');"
                "return el && getComputedStyle(el).display !== 'none';"
            )
        )
        HANDLE_ALERT(driver, logger)
        logger.debug("İnternet (WAN) sayfasına gidildi")
    except Exception:
        logger.error(f"WAN sayfası navigasyon hatası:\n{traceback.format_exc()}")

def get_wan(driver, logger: logging.Logger):
    logger.debug("WAN verileri çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A", "N/A"),
        "ipv4_voice": ("N/A", "N/A", "N/A"),
        "ipv4_iptv": ("N/A", "N/A", "N/A"),
        "ipv6_internet": ("N/A", "N/A", "N/A"),
    }
    try:
        _go_to_internet(driver, logger)

        rows = driver.find_elements(By.CSS_SELECTOR, "#multiWanBody tr")
        data_rows = [
            r for r in rows
            if len(r.find_elements(By.CSS_SELECTOR, "td.table-content")) == 7
        ]

        logger.debug(f"WAN veri satır sayısı: {len(data_rows)}")

        keys = ["ipv4_internet", "ipv4_voice", "ipv4_iptv", "ipv6_internet"]
        for i, row in enumerate(data_rows[:4]):
            tds = row.find_elements(By.CSS_SELECTOR, "td.table-content")
            ad = tds[0].text.strip()
            durum = tds[3].text.strip()
            islem = tds[4].text.strip()
            logger.debug(f"WAN satır {i}: ad={ad}, durum={durum}, işlem={islem}")
            result[keys[i]] = (ad, durum, islem)

    except Exception:
        logger.error(f"WAN veri çekme hatası:\n{traceback.format_exc()}")

    logger.info(f"WAN sonuçları: {result}")
    return result