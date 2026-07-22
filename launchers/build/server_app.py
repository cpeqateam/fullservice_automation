"""
FULL Servis SUNUCU uygulaması — Linux bilgisayarda ÇİFT TIKLANAN giriş noktası.

Son kullanıcı akışı: uygulamaya çift tıklar →
  1) o portta takılı kalmış eski örnek kapatılır (durdur/başlat derdi yok),
  2) orkestratör + API ayağa kalkar,
  3) dashboard varsayılan tarayıcıda kendiliğinden açılır.

Bu dosya PyInstaller'ın giriş scriptidir (`fullservis_server.spec`). Kaynaktan da
çalışır: `python launchers/build/server_app.py` — davranış birebir aynıdır, tek fark
yolların proje kökünden çözülmesidir.

Not: sunucu makinesi aynı zamanda bir test düğümüdür ("server" rolü, LINUX klasörü);
kendi ping/youtube testlerini orchestrator in-process koşar — ayrıca agent açmak
GEREKMEZ.
"""
import os
import sys

# Kaynaktan çalışırken backend paketlerini (common/, server/) import yoluna ekle.
# Paketlenmiş modda kod zaten uygulamanın içindedir; bu satırlar zararsızdır.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.abspath(os.path.join(_HERE, "..", "..", "fullservice-backend"))
if os.path.isdir(_BACKEND) and _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def main():
    """Sunucuyu başlatır: eski örneği kapat → tarayıcıyı sıraya al → uvicorn'u koş."""
    from common import app_boot
    from common.config import APP_DIR, CONFIG_PATH, LOGS_DIR, load_config

    config = load_config()
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = int(config.get("server", {}).get("port", 8770))

    app_boot.banner("FULL SERVIS — SUNUCU (Linux)", [
        f"Ayarlar : {CONFIG_PATH}",
        f"Loglar  : {LOGS_DIR}",
        f"Klasor  : {APP_DIR}",
        "",
        "Panel acilinca testleri buradan baslatabilirsiniz.",
        "Bu pencereyi KAPATMAYIN — kapatirsaniz sunucu durur.",
    ])

    app_boot.free_port(port)

    # Sunucu import'u ağır (FastAPI + pandas/matplotlib) — banner'dan sonra yapılır ki
    # kullanıcı boş ekrana bakmasın.
    import uvicorn
    from server.main import app, orch

    print(f"[SUNUCU] Panel + API → http://{orch.server_lan_ip}:{port}")
    app_boot.open_browser_later(f"http://127.0.0.1:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SUNUCU] Kapatildi.")
    except BaseException as e:          # pencere anında kapanmasın, hata okunsun
        from common import app_boot
        app_boot.hold_on_error(e)
