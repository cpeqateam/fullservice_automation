import logging
import traceback
from selenium.webdriver.common.by import By
from ..browser import wait_loading
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _get_all_elements(driver):
    """data-v-20ebdd02 olan tüm leaf elementleri sırayla döndürür"""
    items = driver.find_elements(
        By.XPATH,
        "//*[@data-v-20ebdd02 and normalize-space(text()) and not(*)]"
    )
    return [el.text.strip() for el in items]


def get_uptime(driver, logger: logging.Logger) -> str:
    logger.debug("Uptime çekiliyor")
    try:
        items = _get_all_elements(driver)
        val = items[10] if len(items) > 10 else "N/A"
        logger.info(f"Uptime: {val}")
        return val
    except Exception:
        logger.error(f"Uptime hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_cpu(driver, logger: logging.Logger) -> str:
    logger.debug("CPU çekiliyor")
    try:
        driver.get("http://192.168.1.1/CPUStatus")
        wait_loading(driver, logger)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "VdslInfoDisplay"))
        )
        content = textarea.get_attribute("value").strip()
        logger.debug(f"CPU raw: {content[:100]}")  # ilk 100 karakteri logla

        for line in content.split('\n'):
            if 'CPU Usage' in line or 'cpu usage' in line.lower():
                cpu_val = line.split(':')[1].strip() + "%"
                logger.info(f"CPU: {cpu_val}")
                return cpu_val

        logger.warning("CPU Usage satırı bulunamadı")
        return "N/A"
    except Exception:
        logger.error(f"CPU hatası:\n{traceback.format_exc()}")
        return "N/A"

def get_ram(driver, logger: logging.Logger) -> str:
    logger.debug("RAM çekiliyor")
    try:
        driver.get("http://192.168.1.1/MemoryStatus")
        wait_loading(driver, logger)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "VdslInfoDisplay"))
        )
        content = textarea.get_attribute("value")

        # MemTotal ve MemFree'den kullanım yüzdesi hesapla
        mem_total = mem_free = None
        for line in content.strip().split('\n'):
            if line.startswith("MemTotal:"):
                mem_total = int(line.split()[1])
            elif line.startswith("MemFree:"):
                mem_free = int(line.split()[1])

        if mem_total and mem_free is not None:
            used = mem_total - mem_free
            percent = round((used / mem_total) * 100, 1)
            ram_val = f"{percent}%"
        else:
            ram_val = "N/A"

        logger.info(f"RAM: {ram_val}")
        return ram_val
    except Exception:
        logger.error(f"RAM hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_device_info(driver, logger: logging.Logger):
    logger.debug("Cihaz bilgileri çekiliyor")
    try:
        items = _get_all_elements(driver)
        yazilim = items[8]  if len(items) > 8  else "N/A"
        seri    = items[6]  if len(items) > 6  else "N/A"
        logger.info(f"Yazılım: {yazilim} | Seri: {seri}")
        return yazilim, seri
    except Exception:
        logger.error(f"Cihaz bilgisi hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"


def get_wan_info(driver, logger: logging.Logger) -> dict:
    logger.debug("WAN bilgileri sistem sayfasından çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A"),
        "ipv6_internet": "N/A",
    }
    try:
        items = _get_all_elements(driver)
        # IPv6 index 37
        result["ipv6_internet"] = items[37] if len(items) > 37 else "N/A"
        # WAN IP bu modelde bağlantı yokken N/A kalır
        logger.info(f"WAN bilgileri: {result}")
    except Exception:
        logger.error(f"WAN bilgisi hatası:\n{traceback.format_exc()}")
    return result


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz çekiliyor")
    try:
        items = _get_all_elements(driver)
        ssid = items[56] if len(items) > 56 else "N/A"
        ch   = items[59] if len(items) > 59 else "N/A"
        logger.info(f"Wi-Fi 2.4 → SSID={ssid}, Kanal={ch}")
        return ssid, ch
    except Exception:
        logger.error(f"Wi-Fi 2.4 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz çekiliyor")
    try:
        items = _get_all_elements(driver)
        ssid = items[57] if len(items) > 57 else "N/A"
        ch   = items[60] if len(items) > 60 else "N/A"
        logger.info(f"Wi-Fi 5 → SSID={ssid}, Kanal={ch}")
        return ssid, ch
    except Exception:
        logger.error(f"Wi-Fi 5 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"