"""
WR854GVR sistem sayfası — CPU, RAM, Uptime, WAN IP.
Kaynak koddaki collect_data() fonksiyonundaki ilk iframe bölümünden alındı.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..browser import SWITCH_TO_CONTENT, CLICK_MENU


def get_cpu_ram_wan(driver, logger):
    """contentIframe içindeki CPU/RAM/WAN IP'yi okur."""
    cpu = ram = wan_ip = "N/A"
    try:
        SWITCH_TO_CONTENT(driver)
        wait = WebDriverWait(driver, 15)
        cpu = wait.until(EC.presence_of_element_located((By.ID, "cpuUsage"))).text.strip()
        ram = driver.find_element(By.ID, "memUsage").text.strip()

        # WAN IP: tüm td'leri tarayıp IP pattern'ine uyanı al
        cells = driver.find_elements(By.XPATH, "//td")
        for cell in cells:
            txt = cell.text.strip()
            if txt.count(".") == 3 and len(txt) <= 15:
                wan_ip = txt
                break
        logger.info(f"CPU: {cpu} | RAM: {ram} | WAN: {wan_ip}")
    except Exception as e:
        logger.error(f"CPU/RAM/WAN hata: {e}")
    return cpu, ram, wan_ip


def get_uptime(driver, logger):
    """Cihaz İstatistikler menüsüne tıklayıp uptime'ı okur."""
    uptime = "N/A"
    try:
        CLICK_MENU(driver, "Cihazİstatistikler")
        SWITCH_TO_CONTENT(driver)
        uptime = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//td[string-length(normalize-space())=8 and contains(text(),':')]")
            )
        ).text.strip()
        logger.info(f"Uptime: {uptime}")
    except Exception as e:
        logger.error(f"Uptime hata: {e}")
    return uptime
