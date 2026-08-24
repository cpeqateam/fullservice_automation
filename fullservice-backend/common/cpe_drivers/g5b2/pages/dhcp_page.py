import logging


def get_dhcp_count(driver, logger: logging.Logger):
    # G5B2: DHCP client sayısı arayüzde mevcut değil
    logger.warning("DHCP client sayısı bu modelde desteklenmiyor → N/A")
    return "N/A"