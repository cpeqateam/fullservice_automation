"""
WR854GVR (Aidata) tarayıcı/login adımları.

Tek dosyalık WR854GVR/main.py kaynağından çıkartılmış.
Selektörler, login akışı, bekleme süreleri — hepsi kaynak koddaki gibi.
Sadece modüler hale getirildi: g5b2 vs. ile aynı kalıba uyumlu.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def LOGIN(driver, logger):
    """Kaynak koddaki login() fonksiyonu. admin/admin + sonraki ekrandaki 'cancel'."""
    try:
        if driver.find_elements(By.NAME, "username"):
            logger.info("[LOGIN] Giriş yapılıyor")
            driver.find_element(By.NAME, "username").send_keys("admin")
            driver.find_element(By.NAME, "password").send_keys("admin")
            driver.find_element(By.NAME, "save").click()
            time.sleep(5)

            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.NAME, "cancel"))
                ).click()
            except Exception:
                pass
        else:
            logger.info("[LOGIN] Oturum açık")
        return True
    except Exception as e:
        logger.error(f"Login hata: {e}")
        return False


def SWITCH_TO_CONTENT(driver):
    """İçerik iframe'ine geçiş — veri okumadan önce çağrılır."""
    driver.switch_to.default_content()
    WebDriverWait(driver, 15).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, "contentIframe"))
    )


def CLICK_MENU(driver, link_text: str):
    """Default content'e geçip sol menüdeki link'e tıklar."""
    driver.switch_to.default_content()
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, link_text))
    ).click()
    time.sleep(2)
