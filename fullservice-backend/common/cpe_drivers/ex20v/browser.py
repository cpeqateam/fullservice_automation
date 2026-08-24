"""
EX20V modem tarayici otomasyon yardimcilari — login ve eleman okuma.

Guncellenmiş kaynak kodun birebir kopyasidir (kaynak: EX20V/browser.py).
Tek fark: tum fonksiyonlar logger parametresi alir (scraper.py koprusu logları enjekte eder).

Fonksiyon ozeti:
  HANDLE_ALERT(driver, logger)                      Tarayici uyarilarini otomatik onaylar.
  safe_find_text(driver, by, locator, logger, ...)  Elementi güvenli okur, bulamazsa default doner.
  OPENINTERFACE(driver, logger)                     Modem arayuzunu acar (http://192.168.1.1/).
  LOGINPANEL(driver, logger)                        Kullanici adi/sifre ile giris yapar.
  SKIP_PASSWORD_CHANGE(driver, logger)              Sifre degistirme ekranini atlar.
"""
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
        time.sleep(2)
        logger.debug("Arayüz sayfası yüklendi")
    except Exception:
        logger.error(f"Arayüz açma hatası:\n{traceback.format_exc()}")
        raise


def LOGINPANEL(driver, logger: logging.Logger):
    logger.info("Giriş paneli dolduruluyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "userName"))
        ).send_keys("admin")
        driver.find_element(By.ID, "pcPassword").send_keys("admin")
        driver.find_element(By.ID, "loginBtn").click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        logger.info("Giriş başarılı")
    except TimeoutException:
        logger.warning("Giriş formu bulunamadı (muhtemelen zaten giriş yapılmış)")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def SKIP_PASSWORD_CHANGE(driver, logger: logging.Logger):
    logger.debug("Şifre değiştirme ekranı kontrol ediliyor")
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "skipBtn"))
        ).click()
        logger.info("Şifre değiştirme ekranı atlandı")
    except TimeoutException:
        logger.debug("Şifre değiştirme ekranı çıkmadı (normal)")
    except Exception:
        logger.error(f"Şifre atlama hatası:\n{traceback.format_exc()}")
