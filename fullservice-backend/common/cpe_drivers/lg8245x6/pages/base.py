import logging

from selenium.webdriver.common.by import By


def _get_frames(driver) -> list:
    """Tüm iframe'leri bir kez çeker — her fonksiyon bunu kullanır."""
    driver.switch_to.default_content()
    return driver.find_elements(By.TAG_NAME, "iframe")


def get_value_from_frames(driver, element_id: str, logger: logging.Logger,
                           is_input=False, default="N/A") -> str:
    """iframe içindeki elementin text veya value değerini döndürür."""
    logger.debug(f"Frame'lerde aranıyor: {element_id!r}")
    frames = _get_frames(driver)
    logger.debug(f"{len(frames)} iframe bulundu")
    for i, frame in enumerate(frames):
        try:
            driver.switch_to.frame(frame)
            els = driver.find_elements(By.ID, element_id)
            if els and els[0].is_displayed():
                res = els[0].get_attribute("value") if is_input else els[0].text
                driver.switch_to.default_content()
                val = res.strip() if res else default
                logger.debug(f"Frame {i}'de bulundu | {element_id!r} = {val!r}")
                return val
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
    logger.warning(f"Element hiçbir frame'de bulunamadı: {element_id!r} → default: {default!r}")
    return default


def get_text_from_frames_xpath(driver, xpath: str, logger: logging.Logger,
                                default="N/A") -> str:
    """iframe içindeki elementin XPath ile text değerini döndürür."""
    logger.debug(f"Frame'lerde XPath aranıyor: {xpath!r}")
    frames = _get_frames(driver)
    for i, frame in enumerate(frames):
        try:
            driver.switch_to.frame(frame)
            els = driver.find_elements(By.XPATH, xpath)
            if els and els[0].is_displayed():
                res = els[0].text.strip()
                driver.switch_to.default_content()
                logger.debug(f"Frame {i}'de XPath bulundu | değer: {res!r}")
                return res if res else default
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
    logger.warning(f"XPath hiçbir frame'de bulunamadı: {xpath!r}")
    return default


def click_in_frames(driver, element_id: str, logger: logging.Logger) -> bool:
    """iframe içindeki elemente tıklar."""
    logger.debug(f"Frame'lerde tıklanıyor: {element_id!r}")
    frames = _get_frames(driver)
    for i, frame in enumerate(frames):
        try:
            driver.switch_to.frame(frame)
            els = driver.find_elements(By.ID, element_id)
            if els and els[0].is_displayed():
                driver.execute_script("arguments[0].click();", els[0])
                driver.switch_to.default_content()
                logger.debug(f"Frame {i}'de tıklandı: {element_id!r}")
                return True
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
    logger.warning(f"Tıklanacak element bulunamadı: {element_id!r}")
    return False