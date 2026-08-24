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
    """Çıkış yap — bu modelde oturum otomatik kapanıyor, direkt login sayfasına git"""
    logger.debug("Çıkış yapılıyor")
    try:
        driver.get("http://192.168.1.1/")
        time.sleep(3)
        logger.info("Çıkış başarılı")
    except Exception:
        logger.error(f"Çıkış hatası:\n{traceback.format_exc()}")


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
            EC.presence_of_element_located((By.NAME, "ui_user"))
        )
        username.clear()
        username.send_keys("admin")
        password = driver.find_element(By.NAME, "ui_pws")
        password.clear()
        password.send_keys("turktelekom")
        # Oturum Aç butonu
        driver.find_element(By.XPATH, "//span[text()='Oturum Aç']").click()
        time.sleep(3)
        HANDLE_ALERT(driver, logger)
        logger.info("Giriş başarılı")
    except TimeoutException:
        logger.warning("Giriş formu bulunamadı")
    except Exception:
        logger.error(f"Giriş hatası:\n{traceback.format_exc()}")


def SKIP_PASSWORD_CHANGE(driver, logger: logging.Logger):
    logger.debug("Şifre değiştirme ekranı kontrol ediliyor")
    try:
        # 1. Adım: "Ayarları kaydet" — JS onclick çağır
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "100001"))
        )
        driver.execute_script("document.getElementById('100001').click();")
        logger.debug("Ayarları kaydet tıklandı")

        # 2. Adım: Yeni sayfa yüklenince İptal butonunu JS ile tıkla
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                "//span[contains(@class,'ButtonMiddle') and not(contains(@class,'green')) and text()='İptal']"))
        )
        driver.execute_script(
            "document.querySelector(\"span.ButtonMiddle:not(.green)\").click();"
        )
        logger.info("Şifre değiştirme atlandı")
        time.sleep(2)
    except TimeoutException:
        logger.debug("Şifre değiştirme ekranı çıkmadı (normal)")
    except Exception:
        logger.error(f"Şifre atlama hatası:\n{traceback.format_exc()}")


def SWITCH_TO_CONTENT_FRAME(driver, logger: logging.Logger):
    """İçerik iframe'ine geç"""
    try:
        frame = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "frm_main2"))
        )
        driver.switch_to.frame(frame)
        logger.debug("iframe'e geçildi: frm_main2")
    except Exception:
        logger.error(f"iframe geçiş hatası:\n{traceback.format_exc()}")


def SWITCH_TO_DEFAULT(driver, logger: logging.Logger):
    """Ana frame'e dön"""
    driver.switch_to.default_content()
    logger.debug("Ana frame'e dönüldü")


def SELECT_MENU(driver, logger: logging.Logger, menu_id: str, label: str):
    """Verilen ID'li menüye JS select_menu() ile tıkla"""
    logger.debug(f"{label} menüsü seçiliyor: {menu_id}")
    try:
        SWITCH_TO_DEFAULT(driver, logger)
        driver.execute_script(f"select_menu('{menu_id}');")
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        logger.debug(f"{label} menüsü seçildi")
    except Exception:
        logger.error(f"{label} menü seçim hatası:\n{traceback.format_exc()}")