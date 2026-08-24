"""
Modem arayüzünden firmware çekme — "Arayüzden Al" butonunun arkasındaki servis.

GRK'daki `app/controllers/cpe_controller.py:fetch_firmware` akışının FULL Servis
portudur. Marka/modele ait entegre CPE driver'ı ile headless Chrome üzerinden
modem arayüzüne girer, cihaz bilgisini (yazılım/donanım/seri) okur, yazılım
string'inden TARİHİ ayıklar ve bu tarih `firmware` tablosunda yoksa oraya EKLER.

Akış:
  1. Registry'den driver bulunur (common/cpe_drivers). Yoksa 404 + entegrasyon mesajı.
  2. Headless tarayıcı açılır — önce Chrome, kurulu değilse Firefox
     (Selenium Manager sürücüyü kendi indirir).
  3. driver.connect(...) + driver.get_device_info(...) çalıştırılır.
  4. Yazılım string'inden tarih ayıklanır, DB'de yoksa eklenir.
  5. Combobox'a yazılacak nihai değer (final_firmware) + was_added döner.

Kullanıcıya kısa Türkçe mesaj dönerken backend log'una ham hata yazılır (debug
için); böylece son kullanıcı sade görür, sistem yöneticisi log'a bakar.
"""
import re
import traceback as _tb
from typing import Optional

from fastapi import HTTPException

from common import firmware_db


# ── Firmware tarih ayıklayıcısı ──────────────────────────────────────────
#
# 3 öncelik:
#   1. Ayraç (_ veya -) ile sınırlı 6/8 haneli sayı VEYA ISO tire formatlı tarih
#      Örnek: '_260513_'     -> '260513'
#             '-20241107'    -> '20241107'
#             '_2026-05-14_' -> '20260514' (tireler silinir)
#   2. Noktalı tarih: YY.MM.DD veya YYYY.MM.DD
#      Örnek: '22.02.14' -> '220214'
#      v4.1.0.61 ile karışmaması için (2 veya 4 hane).(2).(2) pattern'i kullanılır.
#   3. Yalın 6/8 haneli sayı (çevresinde rakam OLMAMA şartıyla)
#
# Marka istisnası:
#   - Tilgin firmware'leri tarih bilgisi içermiyor (örn. 'CS5000-01_09_15_04'),
#     yanlışlıkla yakalanmaması için Tilgin markası gelirse hiç denenmez.
#
# Hiçbir kalıp eşleşmezse None döner.

# Kalıp 1: ayraç (_/-) ile sınırlı 6/8 haneli VEYA ISO tarih (YYYY-MM-DD)
# Sıra önemli: 8 hane > ISO > 6 hane. Böylece '20260527' ile '2026-05-27' karışmaz.
_DATE_SEP    = re.compile(r'(?:_|-)(\d{8}|\d{4}-\d{2}-\d{2}|\d{6})(?:_|-|\.|$|[a-zA-Z])')
_DATE_DOTTED = re.compile(r'(?<!\d)(\d{2}|\d{4})\.(\d{2})\.(\d{2})')
_DATE_BARE   = re.compile(r'(?<!\d)(\d{8}|\d{6})(?!\d)')

# Tarih bilgisi taşımayan markalar — bu markalarda hiç parse denenmez
_BRAND_SKIP = ("tilgin",)


def extract_firmware_date(firmware: Optional[str], brand: Optional[str] = None) -> Optional[str]:
    """Firmware string'inden tarih bilgisini ayıklar.
    Çıktı: bulunduğu hâli ile (6 veya 8 hane), eşleşme yoksa None.

    brand: Marka adı (case-insensitive). Tilgin gibi tarih içermeyen marka ise
           hiç parse yapılmaz — None döner."""
    if not firmware:
        return None

    if brand:
        bl = brand.lower().strip()
        if any(skip in bl for skip in _BRAND_SKIP):
            return None

    s = str(firmware).strip()

    # 1) Ayraç ile sınırlı sayı (ISO format dahil; tireleri sil)
    m = _DATE_SEP.search(s)
    if m:
        return m.group(1).replace("-", "")

    # 2) Noktalı tarih (YY.MM.DD veya YYYY.MM.DD)
    m = _DATE_DOTTED.search(s)
    if m:
        return m.group(1) + m.group(2) + m.group(3)

    # 3) Yalın sayı (sınır kontrolü ile)
    m = _DATE_BARE.search(s)
    if m:
        return m.group(1)

    return None


def _open_browser():
    """Headless tarayıcı açar: önce Chrome, olmazsa Firefox. İkisi de yoksa 503."""
    from selenium import webdriver

    chrome_opts = webdriver.ChromeOptions()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--window-size=1920,1080")
    try:
        return webdriver.Chrome(options=chrome_opts)
    except Exception:
        print(f"[FETCH_FIRMWARE] Chrome baslatilamadi, Firefox deneniyor:\n{_tb.format_exc()}")

    firefox_opts = webdriver.FirefoxOptions()
    firefox_opts.add_argument("-headless")
    firefox_opts.add_argument("--width=1920")
    firefox_opts.add_argument("--height=1080")
    try:
        return webdriver.Firefox(options=firefox_opts)
    except Exception:
        print(f"[FETCH_FIRMWARE] Firefox baslatma hatasi:\n{_tb.format_exc()}")

    raise HTTPException(
        status_code=503,
        detail="Tarayıcı başlatılamadı (Chrome/Firefox). Sistem yöneticisi ile iletişime geçin.",
    )


def fetch(brand: str, model: str, modem_ip: str = "192.168.1.1") -> dict:
    """Modem arayüzüne girip firmware bilgisini çeker ve DB'ye ekler.
    Hata durumlarında HTTPException fırlatır (404/502/503/500)."""
    # 1) Entegrasyon kontrolü
    from common.cpe_drivers import get_driver
    try:
        cpe_driver = get_driver(brand, model)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Cihazın entegrasyonu sistemde yok. Sistem yöneticisi ile iletişime geçin.",
        )

    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException, TimeoutException

    sel_driver = None
    try:
        # 2) Headless tarayıcı — sürücüyü Selenium Manager kendi indirir.
        #    Önce Chrome (youtube_runner ile aynı), kurulu değilse Firefox'a düşülür.
        #    CPE driver'ları standart Selenium API'si kullandığı için ikisi de çalışır.
        sel_driver = _open_browser()

        # 2c) Modem arayüzüne bağlanma — driver.connect login akışını yürütür
        try:
            cpe_driver.connect(sel_driver, modem_ip)
        except (WebDriverException, TimeoutException):
            print(f"[FETCH_FIRMWARE] Modem baglanti hatasi ({modem_ip}):\n{_tb.format_exc()}")
            raise HTTPException(
                status_code=502,
                detail="Modeme bağlanılamadı. Modem IP'sini ve ağ bağlantısını kontrol edin.",
            )
        except Exception:
            print(f"[FETCH_FIRMWARE] Modem baglanti hatasi ({modem_ip}):\n{_tb.format_exc()}")
            raise HTTPException(
                status_code=502,
                detail="Modeme bağlanılamadı. Modem IP'sini ve ağ bağlantısını kontrol edin.",
            )

        # 2d) Cihaz bilgisi okuma
        try:
            yazilim, donanim, seri = cpe_driver.get_device_info(sel_driver)
        except Exception:
            print(f"[FETCH_FIRMWARE] Cihaz bilgisi okuma hatasi:\n{_tb.format_exc()}")
            raise HTTPException(
                status_code=502,
                detail="Cihaz bilgileri okunamadı. Sistem yöneticisi ile iletişime geçin.",
            )

        # 3) Tarih ayıkla + DB kontrol/insert
        parsed_date = extract_firmware_date(yazilim, brand=brand)
        final_firmware = None
        was_added = False

        if parsed_date:
            final_firmware, was_added = firmware_db.ensure_version(brand, model, parsed_date)

        return {
            "firmware":       yazilim,
            "hardware":       donanim,
            "serial":         seri,
            "parsed_date":    parsed_date,
            "final_firmware": final_firmware,   # combobox'a atanacak nihai değer
            "was_added":      was_added,        # DB'ye yeni eklendiyse True
        }

    except HTTPException:
        raise
    except Exception:
        print(f"[FETCH_FIRMWARE] Beklenmedik hata:\n{_tb.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="Beklenmedik bir hata oluştu. Sistem yöneticisi ile iletişime geçin.",
        )
    finally:
        if sel_driver is not None:
            try:
                sel_driver.quit()
            except Exception:
                pass
