import logging
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..browser import HANDLE_ALERT, wait_loading


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("WAN trafik verisi çekiliyor")
    wan_sent = "N/A"
    wan_recv = "N/A"
    try:
        driver.get("http://192.168.1.1/TrafficStatus")
        wait_loading(driver, logger)
        HANDLE_ALERT(driver, logger)

        wait = WebDriverWait(driver, 10)
        wan_sent = wait.until(EC.presence_of_element_located(
            (By.ID, "SystemMonitor_TrafficStatus_WAN_Sent")
        )).text.strip()

        wan_recv = driver.find_element(
            By.ID, "SystemMonitor_TrafficStatus_WAN_Received"
        ).text.strip()

        logger.info(f"WAN Gönderilen: {wan_sent} | Alınan: {wan_recv}")

    except TimeoutException:
        logger.error("Trafik sayfası zaman aşımı")
    except Exception:
        logger.error(f"Trafik verisi hatası:\n{traceback.format_exc()}")

    return wan_sent, wan_recv