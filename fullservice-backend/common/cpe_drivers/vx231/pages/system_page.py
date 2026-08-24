"""
VX231 sistem sayfası — Uptime, RAM, CPU.
Kaynak modüldeki GET_SYSTEM() fonksiyonundan alındı.
"""
from selenium.webdriver.common.by import By
from ..browser import safe_text, safe_value


def get_system(driver, logger):
    """(uptime, ram, cpu) döner."""
    uptime = safe_value(driver, By.XPATH, "//input[contains(@id,'uptime')]")
    ram    = safe_text(driver, By.ID, "mem_gbar")
    cpu    = safe_text(driver, By.ID, "cpu_gbar")
    logger.info(f"Uptime: {uptime} | RAM: {ram} | CPU: {cpu}")
    return uptime, ram, cpu
