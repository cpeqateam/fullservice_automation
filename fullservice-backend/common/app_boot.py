"""
Uygulama açılış yardımcıları — çift tıklanan (paketlenmiş) uygulamalar için.

Son kullanıcı artık terminal kullanmadığı için, `launchers/` altındaki eski
başlatıcıların elle yaptığı işleri (eski süreci kapat → yeniden başlat →
tarayıcıyı aç) uygulamanın KENDİSİ yapar:

  • free_port()          : o portta takılı kalmış ESKİ örneği kapatır
                           (kullanıcı ikinci kez çift tıklarsa "port kullanımda"
                           hatası almasın; durdur/başlat derdi olmasın)
  • open_browser_later() : sunucu ayağa kalkınca dashboard'ı varsayılan
                           tarayıcıda açar
  • banner()             : pencerede ne olduğunu anlatan kısa bilgi yazısı
  • hold_on_error()      : çökme durumunda pencere kapanmasın, hata okunabilsin

psutil zaten bir bağımlılıktır (wifi_track/torrent kullanıyor); yoksa port
temizliği sessizce atlanır, uygulama yine çalışır.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

# Windows konsolu varsayılan olarak cp1254'tür; Türkçe karakterli çıktı print()'i
# çökertmesin (agent/server modülleri de aynısını yapar, biz onlardan ÖNCE çalışırız).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def free_port(port: int, timeout: float = 5.0) -> bool:
    """`port`'u dinleyen ESKİ süreci (kendimiz hariç) kapatır.

    Kullanıcı uygulamayı ikinci kez çalıştırdığında eskisi kapanıp yenisi
    açılsın diye vardır — eski `launchers/*.bat|sh|command` dosyalarının
    "önce eskisini öldür" adımının uygulama içine taşınmış hali.
    Bir şey kapatıldıysa True döner."""
    try:
        import psutil
    except Exception:
        return False

    me = os.getpid()
    killed = []
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["pid"] == me:
            continue
        try:
            for conn in proc.net_connections(kind="inet"):
                if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.laddr.port == port:
                    print(f"[BASLAT] Eski surec kapatiliyor: pid={proc.pid} ({proc.info['name']})")
                    proc.terminate()
                    killed.append(proc)
                    break
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
        except Exception:
            continue

    if not killed:
        return False
    gone, alive = psutil.wait_procs(killed, timeout=timeout)
    for proc in alive:                      # nazikçe kapanmadıysa zorla
        try:
            proc.kill()
        except Exception:
            pass
    # Port'un işletim sistemi tarafından bırakılmasını kısa süre bekle
    for _ in range(20):
        if not _port_in_use(port):
            break
        time.sleep(0.25)
    return True


def _port_in_use(port: int) -> bool:
    """Port hâlâ dinleniyor mu (bağlanmayı deneyerek bakar)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex(("127.0.0.1", port)) == 0


def open_browser_later(url: str, wait_seconds: float = 25.0):
    """Sunucu cevap vermeye başlayınca `url`'i varsayılan tarayıcıda açar
    (arka planda bekler; uvicorn'un açılışını bloke etmez). Kullanıcı sunucu
    uygulamasına çift tıkladığında dashboard kendiliğinden gelsin diye.

    FS_NO_BROWSER=1 ile kapatılabilir (masaüstü oturumu olmayan/uzaktan koşumlar)."""
    if os.environ.get("FS_NO_BROWSER"):
        print(f"[BASLAT] FS_NO_BROWSER ayarli — panel elle acilabilir: {url}")
        return

    def _wait_and_open():
        """Port dinlemeye başlayana kadar bekleyip tarayıcıyı açar (thread hedefi)."""
        deadline = time.time() + wait_seconds
        port = int(url.rsplit(":", 1)[-1].split("/")[0])
        while time.time() < deadline:
            if _port_in_use(port):
                try:
                    webbrowser.open(url)
                    print(f"[BASLAT] Panel tarayicida acildi: {url}")
                except Exception as e:
                    print(f"[BASLAT] Tarayici acilamadi ({e}). Elle acin: {url}")
                return
            time.sleep(0.4)
        print(f"[BASLAT] Sunucu zamaninda ayaga kalkmadi; panel elle acilabilir: {url}")

    threading.Thread(target=_wait_and_open, daemon=True).start()


def banner(title: str, lines: list[str]):
    """Pencerede görünen kısa bilgi kutusu (son kullanıcı ne olduğunu anlasın).
    Kutu genişliği 100 karakterle sınırlıdır — uzun dosya yolları kutuyu bozmasın."""
    width = min(max([len(title)] + [len(x) for x in lines]) + 4, 100)
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    for line in lines:
        print(f"  {line}")
    print("-" * width)


def hold_on_error(exc: BaseException):
    """Uygulama hata verdiyse pencereyi açık tutar — kullanıcı hatayı okuyup
    ekran görüntüsü alabilsin (çift tıklanan pencere anında kapanmasın)."""
    import traceback
    print("\n" + "!" * 60)
    print("HATA: Uygulama baslatilamadi.")
    print("!" * 60)
    traceback.print_exception(type(exc), exc, exc.__traceback__)
    print("\nBu pencereyi kapatmak icin ENTER'a basin...")
    try:
        input()
    except Exception:
        time.sleep(30)
    sys.exit(1)
