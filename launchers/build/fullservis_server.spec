# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller tarifi — SUNUCU uygulaması (Linux orkestratör + dashboard).

Tek dosya (onefile) üretir. Dashboard'ın derlenmiş hali (Vue `dist/`) uygulamanın
İÇİNE gömülür → client'ta node/npm gerekmez, tarayıcı doğrudan exe'den servis edilir.

    FS_APP_NAME=FULLSERVIS-SUNUCU pyinstaller fullservis_server.spec

Genelde doğrudan çağrılmaz; `derle-linux.sh` bunu kullanır (dashboard'ı da derler).

Sunucu Excel/DB katmanını kullandığı için agent'tan farklı olarak pandas,
matplotlib, openpyxl, sqlalchemy, psycopg2 pakete DAHİL edilir.
"""
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

HERE = SPECPATH                                        # launchers/build
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND = os.path.join(REPO, "fullservice-backend")

# collect_submodules paketi GERCEKTEN import edebilmeli; backend'i yola ekliyoruz.
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
FRONTEND_DIST = os.path.join(REPO, "fullservice-frontend", "dist")

APP_NAME = os.environ.get("FS_APP_NAME", "FULLSERVIS-SUNUCU")

if not os.path.isdir(FRONTEND_DIST):
    raise SystemExit(
        "HATA: fullservice-frontend/dist bulunamadi. Once panel derlenmeli:\n"
        "  cd fullservice-frontend && npm install && npm run build"
    )

datas = [
    (os.path.join(BACKEND, "config.json"), "."),
    (FRONTEND_DIST, "dashboard"),      # common/config.py bunu DASHBOARD_DIR olarak bulur
]

hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("selenium")           # sunucunun kendi youtube rolü
    # "Arayuzden Al" (firmware fetch) CPE driver'lari. common/cpe_drivers/__init__.py
    # bunlari importlib ile DINAMIK yukler; PyInstaller dinamik import'u goremez, bu
    # satir olmazsa paketlenmis uygulamada HIC driver bulunmaz ve buton 404 doner.
    + collect_submodules("common.cpe_drivers")
    + ["psutil", "requests", "multipart", "fastapi", "pydantic",
       "xlsxwriter", "openpyxl", "psycopg2", "sqlalchemy",
       "matplotlib.backends.backend_agg"]
)

# macOS'ta derleniyorsa Wi-Fi track icin CoreWLAN kopruleri de girsin.
if sys.platform == "darwin":
    hiddenimports += ["CoreWLAN", "objc", "Foundation"]

a = Analysis(
    [os.path.join(HERE, "server_app.py")],
    pathex=[BACKEND],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PySide2", "IPython", "notebook"],
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
    console=True,        # sunucu logları görünsün (pencere kapanınca sunucu durur)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
