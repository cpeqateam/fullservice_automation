import logging
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def get_dhcp_count(driver, logger: logging.Logger):
    try:
        logger.info("Cihaz Bilgi menüsüne giriliyor...")

        # Menüye tıkla
        cihaz_bilgi = driver.find_element(
            By.XPATH,
            '//a[contains(text(),"Cihaz")]'
        )
        cihaz_bilgi.click()

        time.sleep(2)

        logger.info("Tablo aranıyor...")
        table = driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        td_list = table.find_elements(By.TAG_NAME, "td")
        logger.info(f"Toplam satır sayısı: {len(rows)}")
        logger.info(f"Toplam td sayısı: {len(td_list)}")
        ethernet_count = 0
        for td in td_list:
            td_id = td.get_attribute("id")
            if td_id and "InterfaceType" in td_id:
                logger.info(
                    f"Bulundu -> ID: {td_id} | TEXT: {td.text}"
                )
                ethernet_count += 1
        logger.info(f"Toplam InterfaceType sayısı: {ethernet_count}")
        return ethernet_count
    except NoSuchElementException as e:
        logger.error(f"Element bulunamadı: {e}")
        return "N/A"
    except Exception as e:
        logger.error(f"DHCP bilgisi alınamadı: {e}")
        return "N/A"