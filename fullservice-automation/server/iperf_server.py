"""
iperf3 server yaşam döngüsü (Linux sunucuda).

Mac düğümleri iperf3 client olarak buraya bağlanır. Bir oturum başlarken (ve
herhangi bir düğümde 'iperf' rolü varsa) server süreci ayağa kaldırılır.

NOT (TODO Faz 4): Tek iperf3 server portu aynı anda gelen birden fazla client'i
sıraya alabilir. İki Mac'i gerçekten EŞ ZAMANLI bastırmak için her Mac'e ayrı
port vermek (ör. 5201/5202) veya 'iperf3 -s' örneklerini çoğaltmak gerekebilir.
Şimdilik tek port ile başlıyoruz.
"""
import subprocess
import threading

_proc: subprocess.Popen | None = None
_lock = threading.Lock()


def ensure_running(port: int = 5201) -> bool:
    """iperf3 -s çalışmıyorsa başlatır. iperf3 kurulu değilse False döner."""
    global _proc
    with _lock:
        if _proc is not None and _proc.poll() is None:
            return True
        try:
            _proc = subprocess.Popen(
                ["iperf3", "-s", "-p", str(port)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print(f"[IPERF] server baslatildi (port {port})")
            return True
        except FileNotFoundError:
            print("[IPERF] iperf3 bulunamadi. Kurulum: sudo apt install iperf3")
            return False
        except Exception as e:
            print(f"[IPERF] server baslatilamadi: {e}")
            return False


def stop():
    global _proc
    with _lock:
        if _proc is not None and _proc.poll() is None:
            _proc.terminate()
            print("[IPERF] server durduruldu")
        _proc = None


def is_running() -> bool:
    return _proc is not None and _proc.poll() is None
