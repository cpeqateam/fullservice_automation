import logging


def get_dhcp_count(driver, logger: logging.Logger):
    # ⚠️ H298A: DHCP client sayfası henüz tespit edilmedi
    logger.warning("DHCP client sayısı bu modelde henüz desteklenmiyor → N/A")
    return "N/A"