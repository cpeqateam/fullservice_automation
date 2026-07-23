"""
iperf3 server çalıştırıcı — kablolu Mac düğümünde çalışır.

FULL Servis topolojisi: kablolu Mac `iperf3 -s` ile SERVER olur, wifi Mac ona
CLIENT (`iperf3 -c <kablolu_mac_ip>`) olarak bağlanıp hattı doldurur. Trafik
iki Mac arasında modem üzerinden aktığı için modeme yük biner ("abanma").

Komut:  iperf3 -s -p <port>
Server, test süresi boyunca dinler; süre dolunca veya /stop gelince temiz kapanır.
iperf3 kurulu değilse anlaşılır hata verir.

Kurulum:  macOS → brew install iperf3
"""
import subprocess
import time
from datetime import datetime

from common.protocol import TestStatus
from common.runners.base import RunContext, NO_WINDOW, open_log_viewer, close_terminal


def run(params, ctx: RunContext) -> list[str]:
    """`iperf3 -s` sunucusunu (kablolu Mac) dinlemeye alır; client bağlanabilsin diye
    test süresinden biraz uzun ayakta tutar. Üretilen log dosyası yollarını döner."""
    # GRK ile aynı standart: FULL_Service_iperf_server_<brand>_<model>_<fw>_<port>_<ts>.txt
    log_file = ctx.grk_log_path("iperfServer", params.brand, params.model, params.firmware,
                                str(params.iperf_port))
    duration = max(1, int(params.duration))
    # Server'ı client'tan biraz daha uzun ayakta tut: client'ın bağlanması ve
    # bitirmesi için küçük bir tampon (client retry ile başlangıç gecikmesini tolere eder).
    listen_secs = duration + 5
    cmd = ["iperf3", "-s", "-p", str(params.iperf_port)]

    ctx.progress(0.0, TestStatus.RUNNING.value, f"iperf3 server dinliyor :{params.iperf_port}")

    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"FULL Servis iperf3 SERVER — Node: {ctx.node_id}\n")
            f.write(f"Komut: {' '.join(cmd)}\nBaslangic: {datetime.now()}\n" + "-" * 30 + "\n")
            f.flush()
            viewer = open_log_viewer(log_file, f"iperf SERVER :{params.iperf_port} [{ctx.node_id}]")
            try:
                proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                                        text=True, creationflags=NO_WINDOW)
            except FileNotFoundError:
                msg = "iperf3 bulunamadı. Kurulum: brew install iperf3 / apt install iperf3"
                f.write(msg + "\n")
                close_terminal(viewer)
                ctx.progress(100.0, TestStatus.ERROR.value, msg)
                return [log_file]

            for i in range(listen_secs):
                if ctx.stop.is_set():
                    proc.terminate()
                    close_terminal(viewer)
                    ctx.progress(100.0, TestStatus.STOPPED.value, "iperf server durduruldu")
                    f.write(f"\nDurduruldu: {datetime.now()}\n")
                    return [log_file]
                if proc.poll() is not None:
                    break
                time.sleep(1)
                # Server pasif dinler; ilerleme süreyi yansıtır (client'ın yükü buraya gelir).
                pct = min(100.0, ((i + 1) / duration) * 100)
                ctx.progress(pct, TestStatus.RUNNING.value,
                             f"iperf server dinliyor {min(i + 1, duration)}/{duration}s")

            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
            f.write("\n" + "-" * 30 + f"\nBitis: {datetime.now()}\n")

        close_terminal(viewer)
        ctx.progress(100.0, TestStatus.COMPLETED.value, "iperf server tamamlandı (dinleme bitti)")
        return [log_file]

    except Exception as e:
        ctx.progress(100.0, TestStatus.ERROR.value, f"iperf server hatası: {e}")
        return [log_file]
