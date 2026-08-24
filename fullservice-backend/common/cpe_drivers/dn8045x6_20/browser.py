import time
import traceback
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def HANDLE_ALERT(driver, logger: logging.Logger):
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        logger.debug("Alert bulundu ve onaylandı")
        time.sleep(1)
    except TimeoutException:
        logger.debug("Alert beklendi ama bulunamadı (normal)")


def OPENINTERFACE(driver, logger: logging.Logger):
    url = "http://192.168.1.1/"
    logger.info(f"Modem arayüzü açılıyor: {url}")
    try:
        driver.get(url)
        time.sleep(2)
        logger.debug("Arayüz sayfası yüklendi")
    except Exception:
        logger.error(f"Arayüz açma hatası:\n{traceback.format_exc()}")
        raise


def is_logged_in(driver, logger: logging.Logger) -> bool:
    try:
        driver.find_element(By.ID, "txt_Username")
        logger.debug("Login sayfası tespit edildi → oturum kapalı")
        return False
    except Exception:
        logger.debug("Login sayfası yok → oturum açık")
        return True


def LOGINPANEL(driver, logger: logging.Logger):
    logger.info("Giriş paneli dolduruluyor")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txt_Username"))
        ).send_keys("admin")
        driver.find_element(By.ID, "txt_Password").send_keys("turktelekom")
        driver.execute_script("document.getElementById('loginbutton').click()")
        HANDLE_ALERT(driver, logger)
        time.sleep(3)
        logger.info("Giriş başarılı")
    except TimeoutException:
        logger.warning("Giriş formu bulunamadı (muhtemelen zaten giriş yapılmış)")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")