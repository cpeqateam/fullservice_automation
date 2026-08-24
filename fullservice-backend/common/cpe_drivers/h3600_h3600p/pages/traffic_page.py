import logging
import traceback
import time
from selenium.webdriver.common.by import By
from ..browser import safe_find_text, wait_click, HANDLE_ALERT


def get_download_upload(driver, logger: logging.Logger):
    logger.debug("Download/Upload çekiliyor")
    try:
        wait_click(driver, By.ID, "internet", logger)
        time.sleep(2)
        HANDLE_ALERT(driver, logger)

        dl_text = safe_find_text(driver, By.ID, "cmaxrate:0", logger)
        ul_text = safe_find_text(driver, By.ID, "csend:0", logger)

        def parse_bytes(text):
            try:
                inner    = text.split("(")[1].replace(")", "").strip()
                val, unit = inner.split()
                val = float(val)
                if   unit == "KB": val *= 1024
                elif unit == "MB": val *= 1024 ** 2
                elif unit == "GB": val *= 1024 ** 3
                return round(val / 1048576, 4)
            except Exception:
                logger.warning(f"Byte parse hatası: {text!r}")
                return 0.0

        dl = parse_bytes(dl_text)
        ul = parse_bytes(ul_text)
        logger.info(f"Download={dl} MB | Upload={ul} MB")
        return dl, ul
    except Exception:
        logger.error(f"DL/UL hatası:\n{traceback.format_exc()}")
        return 0.0, 0.0