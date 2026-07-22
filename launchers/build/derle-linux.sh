#!/bin/bash
# =============================================================================
#  FULL Servis — LINUX SUNUCU uygulamasini derler (gelistirici calistirir)
#
#  Once paneli (Vue) derler, sonra paneli exe'nin icine gomerek tek dosya uretir:
#     cikti/FULLSERVIS-SUNUCU/FULLSERVIS-SUNUCU        <- cift tiklanan uygulama
#     cikti/FULLSERVIS-SUNUCU/ayarlar/config.json      <- topoloji/IP
#     cikti/FULLSERVIS-SUNUCU/ayarlar/secrets.json     <- Telegram/mail/DB (USB ile)
#     cikti/FULLSERVIS-SUNUCU/ayarlar/certs/           <- FTP/DB sertifikalari
#     cikti/FULLSERVIS-SUNUCU/FULL-Servis-Sunucu.desktop  <- masaustu kisayolu
#
#  Calistirma (Linux'ta, proje kokunden):
#     chmod +x launchers/build/derle-linux.sh
#     ./launchers/build/derle-linux.sh
# =============================================================================
set -e
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/venv/bin/python"
[ -x "$PY" ] || PY="python3"
APP="FULLSERVIS-SUNUCU"

echo
echo "[1/5] Panel (Vue) derleniyor..."
if command -v npm >/dev/null 2>&1; then
    (cd "$REPO/fullservice-frontend" && npm install --silent && npm run build)
else
    echo "  npm yok — mevcut fullservice-frontend/dist kullanilacak."
    [ -d "$REPO/fullservice-frontend/dist" ] || { echo "  HATA: dist de yok. npm kurun."; exit 1; }
fi

echo "[2/5] Bagimliliklar kontrol ediliyor..."
"$PY" -m pip install --quiet --disable-pip-version-check -r "$REPO/fullservice-backend/requirements.txt"
"$PY" -m pip install --quiet --disable-pip-version-check pyinstaller

echo "[3/5] Eski cikti temizleniyor..."
rm -rf build dist "cikti/$APP"

echo "[4/5] Uygulama derleniyor (birkac dakika surebilir)..."
FS_APP_NAME="$APP" "$PY" -m PyInstaller --noconfirm --clean fullservis_server.spec

echo "[5/5] Dagitim klasoru hazirlaniyor..."
mkdir -p "cikti/$APP/ayarlar/certs"
cp "dist/$APP" "cikti/$APP/"
chmod +x "cikti/$APP/$APP"
cp "$REPO/fullservice-backend/config.json" "cikti/$APP/ayarlar/"
# Sirlar ve sertifikalar repoda YOK — varsa gelistirme makinesindekiler kopyalanir
[ -f "$REPO/fullservice-backend/secrets.json" ] && cp "$REPO/fullservice-backend/secrets.json" "cikti/$APP/ayarlar/" || true
[ -d "$REPO/fullservice-backend/certs" ] && cp -r "$REPO/fullservice-backend/certs/." "cikti/$APP/ayarlar/certs/" || true

# Masaustu kisayolu: dosya yoneticisinde cift tiklaninca terminalde acilsin
cat > "cikti/$APP/FULL-Servis-Sunucu.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FULL Servis Sunucu
Comment=FULL Servis testlerini baslatir ve paneli acar
Exec=bash -c 'cd "\$(dirname "%k")" && ./$APP'
Terminal=true
Categories=Network;
EOF
chmod +x "cikti/$APP/FULL-Servis-Sunucu.desktop"

echo
echo "============================================================"
echo " TAMAM. Dagitilacak klasor:"
echo "   $(pwd)/cikti/$APP"
echo
echo " Linux makinede: klasoru kopyalayin, 'FULL-Servis-Sunucu.desktop'"
echo " dosyasina cift tiklayin (ilk seferde 'Guven / Calistir' deyin)."
echo " ayarlar/secrets.json ve ayarlar/certs/ dolu olmali (USB ile)."
echo "============================================================"
