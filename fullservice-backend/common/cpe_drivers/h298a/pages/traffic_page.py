import logging


def get_download_upload(driver, logger: logging.Logger):
    # ⚠️ H298A: Trafik sayfası henüz tespit edilmedi
    logger.warning("Download/Upload bu modelde henüz desteklenmiyor → N/A")
    return "N/A", "N/A"