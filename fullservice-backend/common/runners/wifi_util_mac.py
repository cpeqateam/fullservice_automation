# -*- coding: utf-8 -*-
"""
Wi-Fi izleme — macOS versiyonu.

GRK functionBase_wifi.py'deki readWlan'ın macOS (darwin) kolunun BİREBİR AYNISIDIR.
`system_profiler SPAirPortDataType` çıktısını netsh-benzeri satırlara çevirir; böylece
parse/yazma fonksiyonları (getSignalInfo, getSystemInfo, getOneTimeInfo,
getPeriodicData, createFileName, writeLogsToFile, SPACER) Windows ile AYNI olur —
bunlar wifi_util'den paylaşılarak alınır (tek kaynak, tek standart).
"""
import subprocess
import re

from common.runners.wifi_util import (
    NO_WINDOW, SPACER,
    getSignalInfo, getSystemInfo, writeLogsToFile, getOneTimeInfo,
    createFileName, getPeriodicData,
)


def readWlan():
    """macOS: system_profiler çıktısını netsh-benzeri satır listesine çevirir
    (GRK functionBase_wifi.py darwin kolu, birebir)."""
    cmd = "system_profiler SPAirPortDataType"
    shellOutput = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=NO_WINDOW).stdout

    simulated_netsh = []

    bssid = "00:00:00:00:00:00"
    ssid = "Unknown"
    state = "disconnected"
    signal = "0%"
    rx_rate = "0"
    tx_rate = "0"
    channel = "1"
    radio = "802.11"
    mac_address = "00:00:00:00:00:00"

    is_connected = False

    for line in shellOutput.split("\n"):
        line = line.strip()
        if line.startswith("Status: Connected"):
            state = "connected"
            is_connected = True
        elif line.startswith("MAC Address:") and mac_address == "00:00:00:00:00:00":
            mac_address = line.split(":", 1)[1].strip()
        elif is_connected and line.startswith("Channel:"):
            ch_match = re.search(r'Channel:\s*(\d+)', line)
            if ch_match: channel = ch_match.group(1)
        elif is_connected and line.startswith("Signal / Noise:"):
            sig_match = re.search(r'Signal / Noise:\s*([-\d]+)', line)
            if sig_match:
                rssi = int(sig_match.group(1))
                pct = max(0, min(100, 2 * (rssi + 100)))
                signal = f"{pct}%"
        elif is_connected and line.startswith("Transmit Rate:"):
            tx_rate = line.split(":", 1)[1].strip()
            rx_rate = tx_rate
        elif is_connected and line.startswith("PHY Mode:"):
            radio = line.split(":", 1)[1].strip()

    simulated_netsh.append(f"    Name                   : Wi-Fi")
    simulated_netsh.append(f"    Description            : AirPort")
    simulated_netsh.append(f"    State                  : {state}")
    simulated_netsh.append(f"    Physical address       : {mac_address}")

    if state == "connected":
        simulated_netsh.append(f"    SSID                   : {ssid}")
        simulated_netsh.append(f"    BSSID                  : {bssid}")
        simulated_netsh.append(f"    Network type           : Infrastructure")
        simulated_netsh.append(f"    Radio type             : {radio}")
        simulated_netsh.append(f"    Channel                : {channel}")
        simulated_netsh.append(f"    Receive rate (Mbps)    : {rx_rate}")
        simulated_netsh.append(f"    Transmit rate (Mbps)   : {tx_rate}")
        simulated_netsh.append(f"    Signal                 : {signal}")

    return simulated_netsh
