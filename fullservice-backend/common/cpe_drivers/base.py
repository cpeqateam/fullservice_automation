"""
CPE driver contract.

Her marka/model için bir alt-paket oluşturulur:
    backend/app/cpe_drivers/<klasor>/
        ├── __init__.py
        ├── scraper.py      # Kaynak kodun kopyası
        └── driver.py       # Bu dosyadaki sözleşmeyi karşılayan adapter

driver.py modülü şu üst-seviye sembolleri açar:

    BRAND: str   # Marka (büyük/küçük fark etmez, registry upper'a çevirir)
    MODEL: str   # Model

    def connect(driver, modem_ip: str) -> None:
        Modem arayüzünü açar, login ve şifre değiştirme ekranını geçer.

    def get_device_info(driver) -> tuple[str, str, str]:
        (yazilim, donanim, seri) döner.

    def collect(driver, secilen: set[str]) -> dict[str, str]:
        FRONTEND_KEYS içinden seçili alanları kazır ve {anahtar: değer} döner.
        secilen'de olmayan anahtarları döndürmek zorunda değildir.

Excel/DB yazımı, threading ve durum takibi orkestratörde (cpe_service.py)
yapılır. Driver dosya açmaz, DB bağlantısı kurmaz.
"""

# Frontend'in CpeControlView.vue'da tanımladığı tüm parametre anahtarları.
# Excel sütun sırası bu listenin sırasıyla aynıdır.
FRONTEND_KEYS = [
    "uptime",
    "ipv4_internet_ip", "ipv4_internet_status", "ipv4_internet_uptime",
    "ipv4_voice_ip",    "ipv4_voice_status",    "ipv4_voice_uptime",
    "ipv4_iptv_ip",     "ipv4_iptv_status",     "ipv4_iptv_uptime",
    "ipv6_ip",          "ipv6_status",          "ipv6_uptime",
    "ram", "cpu",
    "ssid_24", "ch_24", "bw_24",
    "ssid_5",  "ch_5",  "bw_5",
    "download", "upload", "dhcp_count",
]

# Excel başlıklarında kullanılacak insan-okur etiketler.
KEY_LABELS = {
    "uptime":               "Uptime",
    "ipv4_internet_ip":     "IPv4 Internet IP",
    "ipv4_internet_status": "IPv4 Internet Durum",
    "ipv4_internet_uptime": "IPv4 Internet Süre",
    "ipv4_voice_ip":        "IPv4 Voice IP",
    "ipv4_voice_status":    "IPv4 Voice Durum",
    "ipv4_voice_uptime":    "IPv4 Voice Süre",
    "ipv4_iptv_ip":         "IPv4 IPTV IP",
    "ipv4_iptv_status":     "IPv4 IPTV Durum",
    "ipv4_iptv_uptime":     "IPv4 IPTV Süre",
    "ipv6_ip":              "IPv6 IP",
    "ipv6_status":          "IPv6 Durum",
    "ipv6_uptime":          "IPv6 Süre",
    "ram":                  "RAM",
    "cpu":                  "CPU",
    "ssid_24":              "SSID 2.4",
    "ch_24":                "Kanal 2.4",
    "bw_24":                "BW 2.4",
    "ssid_5":               "SSID 5",
    "ch_5":                 "Kanal 5",
    "bw_5":                 "BW 5",
    "download":             "Download",
    "upload":               "Upload",
    "dhcp_count":           "Client Sayısı",
}
