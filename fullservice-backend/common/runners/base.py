"""
Test çalıştırıcı (runner) sözleşmesi ve ortak yardımcılar.

Her test tipi (ping, youtube, iperf, ...) bu sözleşmeyi uygulayan bir `run()`
fonksiyonu sağlar. Hem agent hem sunucu-yerel testler aynı runner'ları kullanır;
böylece test mantığı tek yerde durur ve cross-platform tutulur.

Sözleşme:
    run(params: TestParams, ctx: RunContext) -> list[str]
        - Testi çalıştırır, ilerlemeyi ctx.progress(...) ile bildirir.
        - ctx.stop (threading.Event) set edilirse erken ve temiz çıkar.
        - Ürettiği log dosyalarının yollarını liste olarak döner.
"""
import os
import platform
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

# Windows'ta subprocess çağrılarında siyah CMD penceresi açılmasını engeller (GRK ile aynı yaklaşım)
NO_WINDOW = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0

# İlerleme bildirimi imzası: (yüzde 0..100, status, mesaj)
ProgressCb = Callable[[float, str, str], None]


@dataclass
class RunContext:
    """Bir test koşumu için ortam: log klasörü, durdurma sinyali, ilerleme geri çağrısı."""
    node_id: str
    session_id: str
    log_dir: str
    progress: ProgressCb
    stop: threading.Event = field(default_factory=threading.Event)

    def stamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_path(self, name: str) -> str:
        """node ve oturum bilgisini içeren benzersiz bir log dosyası yolu üretir."""
        safe = name.replace(" ", "").replace(":", "").replace("/", "")
        fname = f"full_{self.node_id}_{safe}_{self.stamp()}.txt"
        os.makedirs(self.log_dir, exist_ok=True)
        return os.path.join(self.log_dir, fname)


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_mac() -> bool:
    return platform.system().lower() == "darwin"
