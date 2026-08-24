import time
import traceback
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import _get_frames, get_value_from_frames, click_in_frames


def _get_wan_row(driver, record_id: str, logger: logging.Logger):
    """WAN tablosunda belirtilen satırdan IP ve durum bilgilerini çeker."""
    logger.debug(f"WAN satırı çekiliyor: {record_id!r}")
    frames = _get_frames(driver)
    for i, frame in enumerate(frames):
        try:
            driver.switch_to.frame(frame)
            row = driver.find_elements(By.ID, record_id)
            if row:
                tds = row[0].find_elements(By.TAG_NAME, "td")
                if len(tds) >= 3:
                    durum = tds[1].text.strip()
                    ip    = tds[2].text.strip()
                    driver.switch_to.default_content()
                    logger.debug(f"WAN satır {record_id!r} → IP={ip}, Durum={durum}")
                    return ip, durum
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
    logger.warning(f"WAN satırı bulunamadı: {record_id!r}")
    return "N/A", "N/A"


def _get_wan_details(driver, logger: logging.Logger) -> dict:
    """WAN sayfasına gidip IPv4 Internet, Voice, IPTV ve IPv6 verilerini çeker."""
    logger.debug("WAN detayları çekiliyor")
    wait = WebDriverWait(driver, 10)
    driver.switch_to.default_content()

    result = {
        "internet_ip": "N/A", "internet_durum": "N/A", "internet_sure": "N/A",
        "voice_ip":    "N/A", "voice_durum":    "N/A", "voice_sure":    "N/A",
        "iptv_ip":     "N/A", "iptv_durum":     "N/A", "iptv_sure":     "N/A",
        "ipv6_ip":     "N/A", "ipv6_durum":     "N/A", "ipv6_sure":     "N/A",
        "dl": "0", "ul": "0",
    }

    try:
        wait.until(EC.element_to_be_clickable((By.ID, "icon_Systeminfo"))).click()
        time.sleep(1)
        wan_btn = wait.until(EC.element_to_be_clickable((By.ID, "name_waninfo")))
        driver.execute_script("arguments[0].click();", wan_btn)
        time.sleep(3)
        logger.debug("WAN sayfasına gidildi")

        for key, record_id in [
            ("internet", "record_1"),
            ("voice",    "record_2"),
            ("iptv",     "record_3"),
        ]:
            ip, durum = _get_wan_row(driver, record_id, logger)
            result[f"{key}_ip"]    = ip
            result[f"{key}_durum"] = durum
            click_in_frames(driver, record_id, logger)
            time.sleep(1)
            result[f"{key}_sure"] = get_value_from_frames(driver, "V4UpTime", logger)
            logger.info(f"IPv4 {key.upper()} → IP={ip}, Durum={durum}, Süre={result[f'{key}_sure']}")

        logger.debug("IPv6 verisi çekiliyor")
        frames = _get_frames(driver)
        for frame in frames:
            try:
                driver.switch_to.frame(frame)
                row = driver.find_elements(By.ID, "ipv6record_1")
                if row:
                    tds = row[0].find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 4:
                        result["ipv6_durum"] = tds[1].text.strip()
                        result["ipv6_ip"]    = tds[3].text.strip()
                    driver.execute_script("arguments[0].click();", row[0])
                    time.sleep(1)
                    sure_els = driver.find_elements(By.ID, "V6UpTime")
                    if sure_els:
                        result["ipv6_sure"] = sure_els[0].text.strip()
                    logger.info(f"IPv6 → IP={result['ipv6_ip']}, Durum={result['ipv6_durum']}, Süre={result['ipv6_sure']}")
                    driver.switch_to.default_content()
                    break
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()

    except Exception:
        logger.error(f"WAN veri hatası:\n{traceback.format_exc()}")

    logger.info(f"WAN sonuçları: {result}")
    return result