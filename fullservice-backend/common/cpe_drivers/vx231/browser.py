"""
VX231 tarayıcı/login adımları.

Kaynak koddaki VX231/main2.py dosyasından çıkartılmıştır. Login
ID'leri (pv-login-user, pc-login-password, pc-login-btn), şifre ("turktelekom"),
Advanced section tıklaması — hepsi orijinal koddaki gibi korunmuştur.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def safe_text(driver, by, value, default="N/A", wait=5):
    """Kaynak koddaki safe_text helper'ı — element yoksa default."""
    try:
        return WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((by, value))
        ).text
    except Exception:
        return default


def safe_value(driver, by, value, default="N/A"):
    """Kaynak koddaki safe_value helper'ı — input value'yu döner."""
    try:
        return driver.find_element(by, value).get_attribute("value")
    except Exception:
        return default


def LOGINPANEL(driver, logger):
    """admin / turktelekom ile giriş."""
    try:
        username = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pv-login-user"))
        )
        password = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pc-login-password"))
        )
        login_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "pc-login-btn"))
        )
        username.send_keys("admin")
        password.send_keys("turktelekom")
        login_btn.click()
        logger.info("Login basıldı")
        time.sleep(3)
    except Exception as e:
        logger.warning(f"Login hatası (zaten girilmiş olabilir): {e}")


def HANDLE_ALERTS(driver, logger):
    """Açık olan tüm alert'leri accept eder."""
    try:
        while True:
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            logger.info(f"Alert: {alert.text}")
            alert.accept()
            time.sleep(1)
    except Exception:
        pass


def ADVANCED_SECTION(driver, logger):
    """Sol menüdeki '.T_adv' linkine tıklar — gelişmiş ayar paneli."""
    try:
        driver.switch_to.default_content()
        try:
            WebDriverWait(driver, 3).until(
                EC.frame_to_be_available_and_switch_to_it((By.TAG_NAME, "iframe"))
            )
        except Exception:
            pass

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".T_adv"))
        ).click()
        time.sleep(2)
    except Exception as e:
        logger.warning(f"Advanced section açılamadı: {e}")
