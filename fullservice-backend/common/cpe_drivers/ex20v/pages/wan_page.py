"""
EX20V WAN sayfasi kaziyici — IPv4/IPv6 baglanti verilerini okur.

Modem ana sayfasindaki wan_table elementinden Internet/Voice/IPTV satirlarini
parse eder; IPv6 tablosunu ayri bir following::table sorgusundan alir.

Doner: {'ipv4_internet': (ip, durum, sure), 'ipv4_voice': ..., ...}
"""
import logging
import traceback
import time
from selenium.webdriver.common.by import By
from ..browser import HANDLE_ALERT


def get_wan(driver, logger: logging.Logger):
    logger.debug("WAN verileri çekiliyor")
    result = {
        "ipv4_internet": ("N/A", "N/A", "N/A"),
        "ipv4_voice":    ("N/A", "N/A", "N/A"),
        "ipv4_iptv":     ("N/A", "N/A", "N/A"),
        "ipv6_internet": ("N/A", "N/A", "N/A"),
    }
    try:
        time.sleep(2)
        HANDLE_ALERT(driver, logger)
        time.sleep(2)
        driver.switch_to.default_content()

        def clean_ip(ip):
            return ip.split("/")[0].strip()

        table_v4 = driver.find_element(By.ID, "wan_table")
        rows = table_v4.find_elements(By.XPATH, ".//tr")[1:]
        logger.debug(f"IPv4 WAN tablosu bulundu, {len(rows)} satır işlenecek")

        for i, row in enumerate(rows):
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 8:
                logger.warning(f"WAN satır {i}: beklenen 8 sütun, bulunan {len(tds)} — atlanıyor")
                continue
            name  = tds[0].text.lower()
            entry = (clean_ip(tds[3].text), tds[6].text, tds[7].text)
            logger.debug(f"WAN satır {i}: name={name!r}, entry={entry}")

            if "internet" in name:
                result["ipv4_internet"] = entry
            elif "voice" in name or "voip" in name:
                result["ipv4_voice"] = entry
            elif "iptv" in name:
                result["ipv4_iptv"] = entry

        try:
            table_v6 = driver.find_element(
                By.XPATH, "//table[@id='wan_table']/following::table[1]"
            )
            ipv6_rows = table_v6.find_elements(By.XPATH, ".//tr")[1:]
            logger.debug(f"IPv6 WAN tablosu bulundu, {len(ipv6_rows)} satır")

            for row in ipv6_rows:
                tds = row.find_elements(By.TAG_NAME, "td")
                if len(tds) < 8:
                    continue
                if "internet" in tds[0].text.lower():
                    result["ipv6_internet"] = (clean_ip(tds[3].text), tds[6].text, tds[7].text)
                    logger.debug(f"IPv6 Internet: {result['ipv6_internet']}")
                    break
        except Exception:
            logger.warning(f"IPv6 tablosu bulunamadı:\n{traceback.format_exc()}")

    except Exception:
        logger.error(f"WAN veri çekme hatası:\n{traceback.format_exc()}")

    logger.info(f"WAN sonuçları: {result}")
    return result
