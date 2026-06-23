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
import shlex
import stat
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

# Windows'ta subprocess çağrılarında siyah CMD penceresi açılmasını engeller (GRK ile aynı yaklaşım)
NO_WINDOW = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
# Windows'ta ayrı/görünür bir konsol penceresi açar (canlı çıktı için)
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

# İlerleme bildirimi imzası: (yüzde 0..100, status, mesaj)
ProgressCb = Callable[[float, str, str], None]

# Nihai sonuç bildirimi imzası: (kind, stats) — test bitince DB'ye yazılacak özet.
#   kind: "ping" | "iperf" | "wifi"   stats: teste özgü alanları içeren dict
ResultCb = Callable[[str, dict], None]


@dataclass
class RunContext:
    """Bir test koşumu için ortam: log klasörü, durdurma sinyali, ilerleme geri çağrısı."""
    node_id: str
    session_id: str
    log_dir: str
    progress: ProgressCb
    stop: threading.Event = field(default_factory=threading.Event)
    # Test bitince yapısal özet bildirmek için (opsiyonel). Ayarlanmamışsa runner
    # sadece log/progress üretir, DB'ye bir şey yazılmaz.
    result: Optional[ResultCb] = None

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


def is_linux() -> bool:
    return platform.system().lower() == "linux"


# ─────────────────────────────────────────────────────────────────────────────
# Görünür terminal yardımcıları (kullanıcı isteri: testler başlayınca işlerin
# canlı aktığı terminal pencereleri açılsın). Bunlar yalnızca GİRİŞ YAPILMIŞ bir
# masaüstü oturumunda (agent elle/oturumda çalışırken) işe yarar; tamamen
# arka plan servisinde (Windows SYSTEM görevi, Linux systemd) pencere açılmaz —
# o durumda sessizce None döner ve test arka planda normal devam eder.
# ─────────────────────────────────────────────────────────────────────────────
def _osascript_terminal(command: str):
    """macOS Terminal.app'te verilen kabuk komutunu yeni pencerede çalıştırır."""
    script = f'tell application "Terminal" to do script "{command}"'
    return subprocess.Popen(["osascript", "-e", script])


def _write_launch_script(inner_cmd: str, title: str) -> str:
    """Komutu geçici bir .sh dosyasına yazar (tırnak/`-e` ayrıştırma sorunlarını
    tamamen aşmak için). Terminal sadece `bash <script>` çalıştırır."""
    fd, path = tempfile.mkstemp(prefix="fs_term_", suffix=".sh")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f"printf '\\033]0;{title}\\007'\n")   # pencere başlığı
        f.write(f"{inner_cmd}\n")
        f.write("echo; echo '[bitti — kapatmak için pencereyi kapatın]'\n")
        f.write("exec bash\n")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IRUSR)
    return path


def _linux_terminal(inner_cmd: str, title: str):
    """Bir Linux terminal emülatöründe komutu çalıştırır (script dosyası üzerinden).

    Görünür pencere için grafik oturum (DISPLAY/WAYLAND) gerekir. Sunucu systemd
    ile veya SSH'tan çalışıyorsa DISPLAY olmaz → pencere açılmaz (None döner).
    """
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print("[TERM] DISPLAY yok (masaustu oturumu degil) — terminal acilmadi. "
              "Sunucuyu masaustundeki Terminal'den 'python run_server.py' ile baslatin.")
        return None

    script = _write_launch_script(inner_cmd, title)
    # Hepsi script'i AYRI argüman olarak alır (tek-string -e tuzağı yok).
    candidates = [
        ["gnome-terminal", "--", "bash", script],
        ["xfce4-terminal", "-x", "bash", script],
        ["mate-terminal", "-x", "bash", script],
        ["konsole", "-e", "bash", script],
        ["xterm", "-e", "bash", script],
        ["x-terminal-emulator", "-e", "bash", script],
    ]
    for term in candidates:
        if not _which(term[0]):
            continue
        try:
            return subprocess.Popen(term)
        except Exception as e:
            print(f"[TERM] {term[0]} acilamadi: {e}")
            continue
    print("[TERM] Terminal emulatoru bulunamadi. Kur: sudo apt install gnome-terminal")
    return None


def _which(name: str) -> bool:
    """PATH'te yürütülebilir var mı (shutil.which sarmalayıcı)."""
    import shutil
    return shutil.which(name) is not None


def open_terminal_running(argv, title: str = "FULL Servis"):
    """`argv` komutunu GÖRÜNÜR bir terminal penceresinde çalıştırır (çıktı canlı).
    Açılamazsa None döner — test arka planda normal devam eder."""
    try:
        if is_windows():
            # CMD'nin 'start' komutu yeni görünür pencereyi en güvenilir şekilde açar.
            args_str = " ".join(str(a) for a in argv)
            return subprocess.Popen(f'start "{title}" cmd /k {args_str}', shell=True)
        inner = " ".join(shlex.quote(str(a)) for a in argv)
        if is_mac():
            return _osascript_terminal(f"{inner} ; echo ; echo [bitti]")
        return _linux_terminal(inner, title)
    except Exception as e:
        print(f"[TERM] Gorunur terminal acilamadi: {e}")
        return None


def open_log_viewer(log_file: str, title: str = "FULL Servis"):
    """`log_file`'ı canlı gösteren görünür bir terminal açar (tail -f benzeri).
    Python tarafı log'a yazdıkça pencerede akar. Açılamazsa None döner."""
    try:
        if is_windows():
            # 'start' ile yeni PowerShell penceresi aç; -NoExit ile açık kalsın.
            log_esc = log_file.replace('"', '`"')
            ps = f"Get-Content -LiteralPath \\\"{log_esc}\\\" -Wait -Tail 200"
            return subprocess.Popen(
                f'start "{title}" powershell -NoExit -Command "{ps}"',
                shell=True,
            )
        tail = f"tail -n 200 -f {shlex.quote(log_file)}"
        if is_mac():
            return _osascript_terminal(tail)
        return _linux_terminal(tail, title)
    except Exception as e:
        print(f"[VIEWER] Log izleyici acilamadi: {e}")
        return None


def close_terminal(proc):
    """Açılan görünür terminali (best-effort) kapatır."""
    try:
        if proc and proc.poll() is None:
            proc.terminate()
    except Exception:
        pass
