"""
EX20V DHCP istemci sayfasi kaziyici — bagli cihaz sayisini sayar.

menu_dhcp -> menu_dhcpclient sayfasina gider; tablodaki son satirin
%5 genisligindeki ID sutunundan sayiyi alir.
Doner: str (sayi) veya "0".
"""
import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT


def get_dhcp_count(driver, logger: logging.Logger):
    logger.debug("DHCP client sayısı çekiliyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "menu_dhcp"))
        ).click()
        time.sleep(1)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "menu_dhcpclient"))
        ).click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table"))
        )
        time.sleep(2)

        id_cells = driver.find_elements(By.XPATH, "//td[@width='5%']")
        if not id_cells:
            logger.warning("DHCP tablosunda hiç hücre bulunamadı → 0 döndürülüyor")
            return "0"

        last_id = id_cells[-1].text.strip()
        logger.debug(f"Son DHCP ID hücresi: {last_id!r}")

        if last_id.isdigit():
            logger.info(f"DHCP Client Sayısı: {last_id}")
            return last_id
        else:
            logger.warning(f"DHCP son ID sayısal değil: {last_id!r} → 0 döndürülüyor")
            return "0"

    except TimeoutException:
        logger.error("DHCP sayfası zaman aşımı")
        return "0"
    except Exception:
        logger.error(f"DHCP sayısı çekme hatası:\n{traceback.format_exc()}")
        return "0"
