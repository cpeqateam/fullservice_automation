import logging


def get_download_upload(driver, logger: logging.Logger):
    logger.warning("Download/Upload bu modelde desteklenmiyor → N/A")
    return "N/A", "N/A"