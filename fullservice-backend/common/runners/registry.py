"""
Runner kayıt tablosu — TestType değerini ilgili çalıştırıcı fonksiyona eşler.

Hem agent (yerel testler) hem sunucu (kendi rolleri) buradan runner çözer.
Yeni bir test tipi eklemek için: runner dosyasını yaz, TestType'a değer ekle,
buraya bir satır ekle. Başka yeri değiştirmek gerekmez.
"""
from __future__ import annotations

from typing import Callable, Dict, List

from common.protocol import TestType, TestParams
from common.runners.base import RunContext
from common.runners import (
    ping_runner, youtube_runner, iperf_runner, iperf_server_runner,
    torrent_runner, wifi_track_runner,
)

# imza: (params, ctx) -> üretilen log dosyası yolları
RunnerFn = Callable[[TestParams, RunContext], List[str]]

RUNNERS: Dict[str, RunnerFn] = {
    TestType.PING_INTERNET.value: ping_runner.run_internet,
    TestType.PING_MODEM.value:    ping_runner.run_modem,
    TestType.YOUTUBE.value:       youtube_runner.run,
    TestType.IPERF_SERVER.value:  iperf_server_runner.run,
    TestType.IPERF.value:         iperf_runner.run,
    TestType.TORRENT.value:       torrent_runner.run,
    TestType.WIFI_TRACK.value:    wifi_track_runner.run,
}


def get_runner(test_type: str) -> RunnerFn | None:
    """Test tipi adına karşılık gelen runner fonksiyonunu döner; yoksa None."""
    return RUNNERS.get(test_type)
