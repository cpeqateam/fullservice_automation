# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller tarifi — AGENT uygulaması (Mac / Windows client).

Tek dosya (onefile) üretir: Python + kod + bağımlılıklar tek çalıştırılabilirde.
Uygulama adı ortam değişkeninden gelir; aynı tariften her makineye ÖZEL isimli
uygulama üretilir (kimlik dosya adından çözülür — bkz. common/config.py):

    FS_APP_NAME=FULLSERVIS-MAC-WIFI      pyinstaller fullservis_agent.spec
    FS_APP_NAME=FULLSERVIS-MAC-KABLO     pyinstaller fullservis_agent.spec
    FS_APP_NAME=FULLSERVIS-WINDOWS-WIFI  pyinstaller fullservis_agent.spec

Genelde doğrudan çağrılmaz; `derle-mac.sh` / `derle-windows.bat` bunu kullanır.

Excel/DB kütüphaneleri (pandas, matplotlib, sqlalchemy…) agent'ta GEREKMEZ —
excluded: dosya boyutu ~4 kat küçülür, açılış hızlanır.
"""
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

HERE = SPECPATH                                        # launchers/build
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND = os.path.join(REPO, "fullservice-backend")

APP_NAME = os.environ.get("FS_APP_NAME", "FULLSERVIS-AGENT")

# config.json uygulamanın İÇİNE de gömülür (yedek). Dışarıdaki `ayarlar/config.json`
# varsa o kazanır — topoloji/IP değişince exe'yi yeniden derlemek gerekmesin.
datas = [(os.path.join(BACKEND, "config.json"), ".")]

hiddenimports = (
    collect_submodules("uvicorn")          # protokol/loop/lifespan modülleri dinamik yüklenir
    + collect_submodules("selenium")       # YouTube testi (kalite seçimi)
    + ["psutil", "requests", "multipart", "fastapi", "pydantic"]
)

# macOS agent'i Wi-Fi track icin CoreWLAN'a MECBUR (yedek yol kaldirildi).
# Paket icine girmezse uygulama acilir ama Wi-Fi izleme testi hata verir.
if sys.platform == "darwin":
    hiddenimports += ["CoreWLAN", "objc", "Foundation"]

a = Analysis(
    [os.path.join(HERE, "agent_app.py")],
    pathex=[BACKEND],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "pandas", "numpy", "matplotlib", "openpyxl", "xlsxwriter",
        "sqlalchemy", "psycopg2", "psycopg2-binary",
        "tkinter", "PyQt5", "PySide2", "IPython", "notebook",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,        # testlerin akışı görünsün (kullanıcı "çalışıyor" desin)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
