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


def wait_loading(driver, logger: logging.Logger, timeout=15):
    """LoadingBox kaybolana kadar bekle"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "LoadingBox"))
        )
        logger.debug("LoadingBox kayboldu, sayfa hazır")
    except TimeoutException:
        logger.warning("LoadingBox zaman aşımı — devam ediliyor")


def OPENINTERFACE(driver, logger: logging.Logger):
    url = "http://192.168.1.1/"
    logger.info(f"Modem arayüzü açılıyor: {url}")
    try:
        driver.get(url)
        wait_loading(driver, logger)
        logger.debug("Arayüz sayfası yüklendi")
    except Exception:
        logger.error(f"Arayüz açma hatası:\n{traceback.format_exc()}")
        raise


def LOGINPANEL(driver, logger: logging.Logger):
    logger.info("Giriş paneli dolduruluyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys("admin")
        driver.find_element(By.ID, "userpassword").send_keys("turktelekom")
        driver.find_element(By.XPATH, "//span[text()='Giriş Yap']").click()
        time.sleep(2)

        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "alertOKBtn"))
            ).click()
            logger.info("Eski oturum kapatıldı")
            time.sleep(3)
        except TimeoutException:
            pass

        HANDLE_ALERT(driver, logger)
        logger.info("Giriş başarılı")
        wait_loading(driver, logger)

    except TimeoutException:
        logger.warning("Giriş formu bulunamadı (muhtemelen zaten giriş yapılmış)")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def SKIP_SCREENS(driver, logger: logging.Logger):
    logger.debug("Atlama ekranları kontrol ediliyor")
    for _ in range(3):
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Atla']"))
            )
            driver.execute_script("arguments[0].click();", btn)
            logger.info("Atlama ekranı geçildi")
            wait_loading(driver, logger)
        except TimeoutException:
            logger.debug("Atlama ekranı çıkmadı (normal)")
            break
        except Exception:
            logger.debug("Atlama ekranı geçme hatası, devam ediliyor")
            time.sleep(1)


def SKIP_SCREENS_2(driver, logger: logging.Logger):
    logger.debug("Atlama ekranları kontrol ediliyor")
    for _ in range(3):
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "qkSkip"))
            )
            driver.execute_script("arguments[0].click();", btn)
            logger.info("Atlama ekranı geçildi")
            wait_loading(driver, logger)
        except TimeoutException:
            logger.debug("Atlama ekranı çıkmadı (normal)")
            break
        except Exception:
            logger.debug("Atlama ekranı geçme hatası, devam ediliyor")
            time.sleep(1)


def OPEN_SISTEM_PANELI(driver, logger: logging.Logger):
    logger.debug("Sistem paneli açılıyor")
    try:
        wait_loading(driver, logger)
        cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "cardbox"))
        )
        for card in cards:
            if "Sistem" in card.text:
                arrow = card.find_element(By.CLASS_NAME, "icon-wizard-arrow-gray")
                driver.execute_script("arguments[0].click();", arrow)
                logger.info("Sistem paneli açıldı")
                wait_loading(driver, logger)
                return
        logger.warning("Sistem cardbox'ı bulunamadı")
    except Exception:
        logger.error(f"Sistem paneli açma hatası:\n{traceback.format_exc()}")


def GO_HOME(driver, logger: logging.Logger):
    logger.debug("Ana sayfaya dönülüyor")
    try:
        driver.get("http://192.168.1.1/")
        wait_loading(driver, logger)
        logger.debug("Ana sayfa yüklendi")
    except Exception:
        logger.error(f"Ana sayfaya dönüş başarısız:\n{traceback.format_exc()}")