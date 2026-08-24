import logging
import traceback
from selenium.webdriver.common.by import By
from ..browser import wait_loading
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _get_all_elements(driver):
    """data-v-24ffdecb olan tüm leaf elementleri DOM index'iyle dict olarak döndürür"""
    js_result = driver.execute_script("""
        var all = document.querySelectorAll('[data-v-24ffdecb]');
        var out = {};
        for(var i=0; i<all.length; i++){
            var txt = all[i].textContent.trim();
            if(txt && all[i].children.length === 0){
                out[String(i)] = txt;
            }
        }
        return out;
    """)
    # JS integer key'leri Python'da string olarak gelir, int'e çevir
    return {int(k): v for k, v in js_result.items()}


def get_uptime(driver, logger: logging.Logger) -> str:
    logger.debug("Uptime çekiliyor")
    try:
        items = _get_all_elements(driver)
        val = items.get(15, "N/A")
        logger.info(f"Uptime: {val}")
        return val
    except Exception:
        logger.error(f"Uptime hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_cpu(driver, logger: logging.Logger) -> str:
    logger.debug("CPU çekiliyor")
    try:
        items = _get_all_elements(driver)
        val = items.get(17, "N/A")
        logger.info(f"CPU: {val}")
        return val
    except Exception:
        logger.error(f"CPU hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_ram(driver, logger: logging.Logger) -> str:
    logger.debug("RAM çekiliyor")
    try:
        items = _get_all_elements(driver)
        val = items.get(19, "N/A")
        logger.info(f"RAM: {val}")
        return val
    except Exception:
        logger.error(f"RAM hatası:\n{traceback.format_exc()}")
        return "N/A"


def get_device_info(driver, logger: logging.Logger):
    logger.debug("Cihaz bilgileri çekiliyor")
    try:
        items = _get_all_elements(driver)
        yazilim = items.get(13, "N/A")
        seri    = items.get(11, "N/A")
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
        result["ipv6_internet"] = items.get(68, "N/A")
        logger.info(f"WAN bilgileri: {result}")
    except Exception:
        logger.error(f"WAN bilgisi hatası:\n{traceback.format_exc()}")
    return result


def get_wifi_24(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 2.4 GHz çekiliyor")
    try:
        items = _get_all_elements(driver)
        ssid = items.get(97, "N/A")
        ch   = items.get(101, "N/A")
        logger.info(f"Wi-Fi 2.4 → SSID={ssid}, Kanal={ch}")
        return ssid, ch
    except Exception:
        logger.error(f"Wi-Fi 2.4 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"


def get_wifi_5(driver, logger: logging.Logger):
    logger.debug("Wi-Fi 5 GHz çekiliyor")
    try:
        items = _get_all_elements(driver)
        ssid = items.get(98, "N/A")
        ch   = items.get(102, "N/A")
        logger.info(f"Wi-Fi 5 → SSID={ssid}, Kanal={ch}")
        return ssid, ch
    except Exception:
        logger.error(f"Wi-Fi 5 hatası:\n{traceback.format_exc()}")
        return "N/A", "N/A"