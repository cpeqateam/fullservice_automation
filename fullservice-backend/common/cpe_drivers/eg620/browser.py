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


def OPENINTERFACE(driver, logger: logging.Logger):
    url = "http://192.168.1.1/"
    logger.info(f"Modem arayüzü açılıyor: {url}")
    try:
        driver.get(url)
        time.sleep(3)
        logger.debug("Arayüz sayfası yüklendi")
    except Exception:
        logger.error(f"Arayüz açma hatası:\n{traceback.format_exc()}")
        raise


def LOGINPANEL(driver, logger: logging.Logger):
    logger.info("Giriş paneli dolduruluyor")
    try:
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username.clear()
        username.send_keys("admin")
        password = driver.find_element(By.ID, "password")
        password.clear()
        password.send_keys("admin")
        driver.find_element(By.ID, "loginbutton").click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        logger.info("Giriş başarılı")
    except TimeoutException:
        logger.warning("Giriş formu bulunamadı")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def OPEN_STATUS_MENU(driver, logger: logging.Logger):
    """Durum ana menüsünü aç"""
    logger.debug("Durum menüsü açılıyor")
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@data-lang-id='status']"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
        logger.debug("Durum menüsü açıldı")
    except TimeoutException:
        logger.warning("Durum menüsü bulunamadı — zaten açık olabilir")
    except Exception:
        logger.error(f"Durum menüsü hatası:\n{traceback.format_exc()}")


def OPEN_LAN_MENU(driver, logger: logging.Logger):
    """Yerel Ağ ana menüsünü aç"""
    logger.debug("Yerel Ağ menüsü açılıyor")
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@data-lang-id='local_area_network']"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
        logger.debug("Yerel Ağ menüsü açıldı")
    except TimeoutException:
        logger.warning("Yerel Ağ menüsü bulunamadı — zaten açık olabilir")
    except Exception:
        logger.error(f"Yerel Ağ menüsü hatası:\n{traceback.format_exc()}")


def NAVIGATE(driver, logger: logging.Logger, href: str, label: str):
    """Alt menü linkine tıklayarak sayfaya git"""
    logger.debug(f"{label} sayfasına gidiliyor")
    try:
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[href='{href}']"))
        )
        driver.execute_script("arguments[0].click();", link)
        time.sleep(3)
        HANDLE_ALERT(driver, logger)
        logger.debug(f"{label} sayfasına girildi")
    except Exception:
        logger.error(f"{label} navigasyon hatası:\n{traceback.format_exc()}")