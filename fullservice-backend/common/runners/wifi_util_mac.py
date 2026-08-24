# -*- coding: utf-8 -*-
"""
Wi-Fi izleme — macOS versiyonu.

Windows'taki `netsh wlan show interfaces` ile AYNI davranışı verir: kartın o anki
bağlantı durumunu sürücünün hafızasından okur, **Wi-Fi taraması YAPMAZ**, diğer
testleri etkilemez. Çıktı yine netsh-benzeri satır listesidir; böylece parse/yazma
fonksiyonları (getSignalInfo, getSystemInfo, getOneTimeInfo, getPeriodicData,
createFileName, writeLogsToFile) Windows ile AYNI kalır — wifi_util'den paylaşılır.

NEDEN CoreWLAN:
  Eskiden `system_profiler SPAirPortDataType` kullanılıyordu. O komut çıktısındaki
  "Other Local Wi-Fi Networks" bölümü için macOS AKTİF TARAMA yapar: radyo bağlı
  olduğu kanaldan ayrılıp tüm 2.4/5 GHz kanallarını gezer ve bu sırada veri taşıyamaz.
  Çağrı başına ~7 saniye sürüyordu ve saniyede bir çağrıldığı için Wi-Fi'yi sürekli
  kanaldan koparıyordu. Ölçüldü: aynı hatta iperf 630 Mbit/sn iken wifi_track açıkken
  201 Mbit/sn'ye düşüyordu (%68 kayıp) — bkz. IPERF_MANUEL_TEST.md.
  CoreWLAN (Apple'ın resmi Wi-Fi API'si) aynı bilgiyi ~4 ms'de, tarama yapmadan verir.

NEDEN YEDEK YOL YOK:
  system_profiler eskiden "CoreWLAN yoksa buna düş" yedeği olarak duruyordu. Kaldırıldı.
  Sebep: sessizce yedeğe düşmek, testin çalışmaya DEVAM EDİP tüm ölçümleri %68 düşük
  üretmesi demekti — kimsenin fark etmediği yanlış veri. Artık CoreWLAN yoksa Wi-Fi
  izleme hiç başlamaz ve net bir hata verir. Yanlış ölçmektense hiç ölçmemek.

Gereksinim: pyobjc-framework-CoreWLAN (requirements.txt'te, yalnızca macOS'a kurulur).
  Bu paket CoreWLAN'ı KURMAZ — CoreWLAN zaten macOS'un parçasıdır. Kurulan şey,
  Python'un o Apple kütüphanesini çağırmasını sağlayan köprüdür (PyObjC).

  Kurulum (Mac düğümlerinde, fullservice-backend içinde):
      source venv/bin/activate && pip install -r requirements.txt
  Doğrulama:
      python -c "import CoreWLAN; print('ok')"
"""
from common.runners.wifi_util import (
    getSignalInfo, getSystemInfo, writeLogsToFile, getOneTimeInfo,
    createFileName, getPeriodicData,
)

# CoreWLAN istemcisi bir kez kurulur (her okumada yeniden yaratmaya gerek yok).
try:
    import CoreWLAN as _CoreWLAN
    _WIFI_CLIENT = _CoreWLAN.CWWiFiClient.sharedWiFiClient()
    _IMPORT_ERROR = None
except Exception as _e:            # PyObjC yoksa Wi-Fi izleme HİÇ çalışmaz (yedek yok)
    _CoreWLAN = None
    _WIFI_CLIENT = None
    _IMPORT_ERROR = _e
    print(f"[WIFI] CoreWLAN yuklenemedi ({_e}) — macOS'ta Wi-Fi izleme CALISMAZ. "
          f"Cozum: venv aktifken 'pip install -r requirements.txt'")


def _yok_mesaji() -> str:
    """CoreWLAN kullanılamıyorsa kullanıcıya gösterilecek tek ve net mesaj."""
    return (f"macOS'ta Wi-Fi izleme icin CoreWLAN gerekli, yuklenemedi ({_IMPORT_ERROR}). "
            f"Cozum: fullservice-backend icinde venv aktifken "
            f"'pip install -r requirements.txt', ardindan "
            f"'python -c \"import CoreWLAN\"' ile dogrula.")


def is_available() -> bool:
    """CoreWLAN okunabilir durumda mı? wifi_track testi BAŞLAMADAN önce buna bakar."""
    return _WIFI_CLIENT is not None


# activePHYMode() enum'u → netsh'in "Radio type" karşılığı
_PHY_MODES = {0: "802.11", 1: "802.11a", 2: "802.11b", 3: "802.11g",
              4: "802.11n", 5: "802.11ac", 6: "802.11ax"}


def _rssi_to_percent(rssi: int) -> int:
    """RSSI (dBm) → yüzde. Windows netsh'in verdiği "Signal : %x" ile aynı ölçek."""
    return max(0, min(100, 2 * (int(rssi) + 100)))


def _netsh_lines(state, mac_address, ssid, bssid, radio, channel, rx_rate, tx_rate, signal):
    """netsh wlan show interfaces çıktısının birebir aynı biçimini üretir."""
    lines = [
        "    Name                   : Wi-Fi",
        "    Description            : AirPort",
        f"    State                  : {state}",
        f"    Physical address       : {mac_address}",
    ]
    if state == "connected":
        lines += [
            f"    SSID                   : {ssid}",
            f"    BSSID                  : {bssid}",
            "    Network type           : Infrastructure",
            f"    Radio type             : {radio}",
            f"    Channel                : {channel}",
            f"    Receive rate (Mbps)    : {rx_rate}",
            f"    Transmit rate (Mbps)   : {tx_rate}",
            f"    Signal                 : {signal}",
        ]
    return lines


def _read_corewlan():
    """CoreWLAN ile TARAMASIZ okuma. Kart bilgisi alınamazsa None döner."""
    iface = _WIFI_CLIENT.interface()
    if iface is None:
        return None

    channel_obj = iface.wlanChannel()
    # Kanal yoksa kart bir AP'ye bağlı değildir.
    connected = bool(iface.powerOn()) and channel_obj is not None
    if not connected:
        return _netsh_lines("disconnected", iface.hardwareAddress() or "00:00:00:00:00:00",
                            "", "", "", "", "", "", "")

    tx_rate = iface.transmitRate() or 0
    return _netsh_lines(
        state="connected",
        mac_address=iface.hardwareAddress() or "00:00:00:00:00:00",
        # SSID/BSSID macOS'ta Konum Servisleri izni istiyor; izin yoksa None gelir.
        ssid=iface.ssid() or "Unknown",
        bssid=iface.bssid() or "00:00:00:00:00:00",
        # activePHYMode() SAYI döndürür (CWPHYMode enum'u: 4=n, 5=ac, 6=ax). netsh ise
        # "Radio type : 802.11ax" gibi METİN yazar; _PHY_MODES o sayıyı bu metne çevirir.
        # `or 0` kart mod bilgisi vermezse (None) çökmeyi, get'in "802.11" varsayılanı da
        # tabloda olmayan yeni bir mod (ör. Wi-Fi 7 = 7) gelirse KeyError'ı önler.
        radio=_PHY_MODES.get(int(iface.activePHYMode() or 0), "802.11"),
        channel=channel_obj.channelNumber(),
        # netsh RX ve TX'i ayrı verir; CoreWLAN tek link hızı verdiği için ikisi de aynı.
        rx_rate=int(tx_rate),
        tx_rate=int(tx_rate),
        signal=f"{_rssi_to_percent(iface.rssiValue())}%",
    )


def readWlan():
    """macOS: aktif WLAN arayüzünün bilgilerini netsh-benzeri satır listesi olarak döner.
    Windows'taki `netsh wlan show interfaces` gibi TARAMASIZ ve anlıktır.

    Okuyamazsa HATA FIRLATIR. Eskiden burada system_profiler'a düşülüyordu; o yol
    Wi-Fi taraması yaptığı için aynı karttaki iperf/YouTube ölçümlerini bozuyordu."""
    if _WIFI_CLIENT is None:
        raise RuntimeError(_yok_mesaji())
    lines = _read_corewlan()
    if not lines:
        raise RuntimeError("CoreWLAN Wi-Fi arayuzunu bulamadi (kart kapali olabilir).")
    return lines
