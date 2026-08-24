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
            EC.presence_of_element_located((By.ID, "pc-login-user"))
        ).send_keys("admin")
        driver.find_element(By.ID, "pc-login-password").send_keys("admin")
        driver.find_element(By.ID, "pc-login-btn").click()
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        logger.info("Giriş başarılı")
    except TimeoutException:
        logger.warning("Giriş formu bulunamadı (muhtemelen zaten giriş yapılmış)")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def WAIT_MASK(driver, logger: logging.Logger):
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "mask").value_of_css_property("display") == "none"
        )
    except:
        pass
    driver.execute_script("""
        var el = document.getElementById('mask');
        if(el){ el.style.display = 'none'; }
    """)
    logger.debug("Mask kaldırıldı")


def ADVANCED_SECTION(driver, logger: logging.Logger):
    logger.debug("Gelişmiş sekmesine geçiliyor")
    try:
        driver.switch_to.default_content()
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".T_adv"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)
        logger.info("Gelişmiş sekmesine girildi ✔")
    except Exception:
        logger.error(f"Gelişmiş sekme hatası:\n{traceback.format_exc()}")

def HANDLE_LOGIN_POPUP(driver, logger: logging.Logger):
    logger.debug("Login popup kontrol ediliyor")
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "confirm-yes"))
        ).click()
        logger.info("Login popup onaylandı")
        time.sleep(2)
    except TimeoutException:
        logger.debug("Login popup çıkmadı (normal)")
    except Exception:
        logger.error(f"Login popup hatası:\n{traceback.format_exc()}")


def SKIP_PASSWORD_CHANGE(driver, logger: logging.Logger):
    logger.debug("Şifre değiştirme ekranı kontrol ediliyor")
    try:
        WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.ID, "pc-skip-btn"))
        ).click()
        logger.info("Şifre değiştirme ekranı atlandı")
        time.sleep(2)
    except TimeoutException:
        logger.debug("Şifre değiştirme ekranı çıkmadı (normal)")
    except Exception:
        logger.error(f"Şifre atlama hatası:\n{traceback.format_exc()}")


def SKIP_CONFIRM_POPUP(driver, logger: logging.Logger):
    logger.debug("2. popup kontrol ediliyor")
    try:
        for _ in range(3):
            buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn-confirm")
            for btn in buttons:
                if "Atla" in btn.text:
                    driver.execute_script("arguments[0].click();", btn)
                    logger.info("2. popup ATLA geçildi")
                    time.sleep(3)
                    return
            time.sleep(1)
        logger.debug("2. popup ATLA butonu bulunamadı (normal)")
    except Exception:
        logger.error(f"2. popup hatası:\n{traceback.format_exc()}")