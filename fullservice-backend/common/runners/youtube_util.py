"""
YouTube en-yüksek-kalite zorlayıcı (Selenium).

Kullanıcı isteri: video İNTERNET'e göre piksel düşürmeden EN YÜKSEK çözünürlükte
oynamalı. YouTube watch sayfasında URL parametreleri (vq) yalnızca ipucudur ve
genelde yok sayılır; kaliteyi gerçekten sabitlemenin yolu oynatıcının
Ayarlar(⚙) → Kalite menüsünden en üst seçeneği seçmektir. Bunu Selenium ile
otomatik yaparız.

Ön koşul: makinede Chrome/Chromium kurulu olmalı + `pip install selenium`
(Selenium 4.6+ chromedriver'ı otomatik indirir). Bunlar yoksa çağıran taraf
basit `webbrowser.open` yöntemine geri düşer.

`detach=True` ile script bitince tarayıcı AÇIK kalır (kişi kapatana dek oynar).
Video TAM EKRAN açılmaz (kullanıcı isteri) — maksimize pencerede normal oynar.
"""
import time

_drivers = []  # açılan tarayıcıları referansta tut (erken kapanmasın)


def force_play_max(link: str) -> dict:
    """Videoyu Chrome'da açar, oynatır ve kaliteyi EN YÜKSEK'e ayarlar.
    Dönüş: {"opened": bool, "quality_set": bool}. Tarayıcı açılamazsa Exception."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--autoplay-policy=no-user-gesture-required")
    opts.add_experimental_option("detach", True)  # script bitince tarayıcı açık kalsın

    # ── YouTube otomasyon tespitini kapat ──────────────────────────────────
    # Belirti: ayni link ELLE acilinca sorunsuz oynuyor, Selenium ile acilinca
    # "Bir hata olustu, daha sonra tekrar deneyin" cikip video donuyordu — hem de
    # her makinede. Sebep bant genisligi degil; YouTube tarayicinin otomasyonla
    # surulduugunu anlayip oynatmayi reddediyor.
    # excludeSwitches TEK BASINA yetmiyor: navigator.webdriver hala true kaliyor.
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=opts)
    _drivers.append(driver)

    # Sayfa ACILMADAN once navigator.webdriver'i gizle (driver.get'ten ONCE olmali).
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
    except Exception as e:
        print(f"[YOUTUBE] webdriver gizlenemedi (video yine denenecek): {e}")
    wait = WebDriverWait(driver, 25)

    driver.get(link)

    # Çerez/onay penceresi (varsa) — best-effort kapat
    try:
        time.sleep(2)
        for xp in (
            "//button[.//span[contains(text(),'Tümünü kabul')]]",
            "//button[.//span[contains(text(),'Kabul')]]",
            "//button[contains(.,'Accept all')]",
            "//button[@aria-label='Accept all']",
        ):
            els = driver.find_elements(By.XPATH, xp)
            if els:
                els[0].click()
                break
    except Exception:
        pass

    # Video öğesi gelsin ve oynasın
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
    try:
        driver.execute_script("var v=document.querySelector('video'); if(v){v.muted=false; v.play();}")
    except Exception:
        pass

    quality_set = False
    try:
        # Ayarlar (dişli)
        settings = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-settings-button")))
        settings.click()
        time.sleep(0.5)
        # "Kalite / Quality" menü öğesi
        qitem = wait.until(EC.element_to_be_clickable((By.XPATH,
            "//div[contains(@class,'ytp-menuitem')]"
            "[.//div[contains(text(),'Kalite') or contains(text(),'Quality')]]")))
        qitem.click()
        time.sleep(0.5)
        # Listenin İLK öğesi = en yüksek çözünürlük
        top = wait.until(EC.element_to_be_clickable((By.XPATH,
            "(//div[contains(@class,'ytp-quality-menu')]//div[contains(@class,'ytp-menuitem')])[1]")))
        top.click()
        quality_set = True
    except Exception as e:
        print(f"[YOUTUBE] Kalite menusu ayarlanamadi (video yine oynuyor): {e}")

    # NOT: Tam ekran (fullscreen) AÇILMAZ — kullanıcı isteri. Video normal pencerede,
    # maksimize edilmiş tarayıcıda oynar (--start-maximized). Böylece kişi ekranda
    # başka işlem de görebilir.

    return {"opened": True, "quality_set": quality_set}
