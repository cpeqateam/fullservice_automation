import logging
import traceback
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def HANDLE_ALERT(driver, logger: logging.Logger):
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
        logger.debug("Alert bulundu ve onaylandı")
        time.sleep(1)
    except TimeoutException:
        logger.debug("Alert beklendi ama bulunamadı (normal)")


def safe_find_text(driver, by, locator, logger: logging.Logger, default="N/A", wait=10):
    try:
        HANDLE_ALERT(driver, logger)
        text = WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((by, locator))
        ).text.strip()
        logger.debug(f"Element bulundu | Locator: {locator!r} | Değer: {text!r}")
        return text
    except TimeoutException:
        logger.warning(f"Element zaman aşımı | Locator: {locator!r} | Default: {default!r}")
        return default
    except Exception:
        logger.error(f"Element hatası | Locator: {locator!r}\n{traceback.format_exc()}")
        return default


def LOGOUT(driver, logger: logging.Logger):
    logger.debug("Çıkış yapılıyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "LogOffLnk"))
        ).click()
        logger.info("Çıkış başarılı")
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
    except TimeoutException:
        logger.debug("Çıkış butonu bulunamadı (normal)")
    except Exception:
        logger.error(f"Çıkış hatası:\n{traceback.format_exc()}")


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


def LOGINPANEL(driver, logger: logging.Logger):
    logger.info("Giriş paneli dolduruluyor")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Frm_Username"))
        ).send_keys("admin")
        driver.find_element(By.ID, "Frm_Password").send_keys("turktelekom")
        driver.find_element(By.ID, "LoginId").click()
        time.sleep(3)
        HANDLE_ALERT(driver, logger)
        logger.info("Giriş başarılı")
    except TimeoutException:
        logger.warning("Giriş formu bulunamadı (muhtemelen zaten giriş yapılmış)")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def SKIP_PASSWORD_CHANGE(driver, logger: logging.Logger):
    logger.debug("Şifre değiştirme ekranı kontrol ediliyor")
    try:
        WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.ID, "Btn_cancel"))
        ).click()
        logger.info("Şifre değiştirme atlandı")
        time.sleep(1)
        HANDLE_ALERT(driver, logger)
        time.sleep(2)
    except TimeoutException:
        logger.debug("Şifre değiştirme ekranı çıkmadı (normal)")
    except Exception:
        logger.error(f"Şifre atlama hatası:\n{traceback.format_exc()}")