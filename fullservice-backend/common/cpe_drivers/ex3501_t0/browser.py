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
    """ZTE EX3501 login: ID=username / ID=userpassword / span[Giriş Yap]"""
    logger.info("Giriş paneli dolduruluyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys("admin")
        driver.find_element(By.ID, "userpassword").send_keys("admin")
        driver.find_element(By.XPATH, "//span[text()='Giriş Yap']").click()
        time.sleep(2)

        # Oturum çakışması — eski oturumu kapat
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
        time.sleep(4)

    except TimeoutException:
        logger.warning("Giriş formu bulunamadı (muhtemelen zaten giriş yapılmış)")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def SKIP_SCREENS(driver, logger: logging.Logger):
    """ZTE EX3501 'Atla' butonlarını geç"""
    logger.debug("Atlama ekranları kontrol ediliyor")
    for _ in range(2):
        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Atla']"))
            ).click()
            logger.info("Atlama ekranı geçildi")
            time.sleep(2)
        except TimeoutException:
            logger.debug("Atlama ekranı çıkmadı (normal)")


def OPEN_SISTEM_PANELI(driver, logger: logging.Logger):
    """Ana sayfadaki Sistem cardbox panelini aç"""
    logger.debug("Sistem paneli açılıyor")
    try:
        cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "cardbox"))
        )
        for card in cards:
            if "Sistem" in card.text:
                arrow = card.find_element(By.CLASS_NAME, "icon-wizard-arrow-gray")
                driver.execute_script("arguments[0].click();", arrow)
                logger.info("Sistem paneli açıldı")
                time.sleep(2)
                return
        logger.warning("Sistem cardbox'ı bulunamadı")
    except Exception:
        logger.error(f"Sistem paneli açma hatası:\n{traceback.format_exc()}")


def GO_HOME(driver, logger: logging.Logger):
    """Ana sayfaya (Sistem Bilgisi) dön — direkt URL ile"""
    logger.debug("Ana sayfaya dönülüyor")
    try:
        driver.get("http://192.168.1.1/")
        time.sleep(3)
        logger.debug("Ana sayfa yüklendi")
    except Exception:
        logger.error(f"Ana sayfaya dönüş başarısız:\n{traceback.format_exc()}")
