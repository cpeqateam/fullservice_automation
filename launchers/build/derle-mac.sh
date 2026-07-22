#!/bin/bash
# =============================================================================
#  FULL Servis — MAC AGENT uygulamalarini derler (gelistirici calistirir)
#
#  Ayni koddan İKİ ayri isimli uygulama uretir; her biri kendi dosya adindan
#  hangi bilgisayar oldugunu cozer:
#     cikti/FULLSERVIS-MAC-WIFI/FULLSERVIS-MAC-WIFI     -> mac_wifi
#     cikti/FULLSERVIS-MAC-KABLO/FULLSERVIS-MAC-KABLO   -> mac_cable
#
#  Calistirma (Mac'te, proje kokunden):
#     chmod +x launchers/build/derle-mac.sh
#     ./launchers/build/derle-mac.sh
# =============================================================================
set -e
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/venv/bin/python"
[ -x "$PY" ] || PY="python3"

echo
echo "[1/4] Bagimliliklar kontrol ediliyor..."
"$PY" -m pip install --quiet --disable-pip-version-check -r "$REPO/fullservice-backend/requirements.txt"
"$PY" -m pip install --quiet --disable-pip-version-check pyinstaller

echo "[2/4] Eski cikti temizleniyor..."
rm -rf build dist cikti/FULLSERVIS-MAC-WIFI cikti/FULLSERVIS-MAC-KABLO

for APP in FULLSERVIS-MAC-WIFI FULLSERVIS-MAC-KABLO; do
    echo "[3/4] $APP derleniyor (birkac dakika surebilir)..."
    FS_APP_NAME="$APP" "$PY" -m PyInstaller --noconfirm --clean fullservis_agent.spec

    echo "[4/4] $APP dagitim klasoru hazirlaniyor..."
    mkdir -p "cikti/$APP/ayarlar"
    cp "dist/$APP" "cikti/$APP/"
    chmod +x "cikti/$APP/$APP"
    cp "$REPO/fullservice-backend/config.json" "cikti/$APP/ayarlar/"

    # Finder'da cift tiklaninca Terminal'de acilan sarmalayici (Gatekeeper dostu).
    # Kullanici isterse dogrudan binary'ye de cift tiklayabilir.
    cat > "cikti/$APP/BASLAT-$APP.command" <<EOF
#!/bin/bash
cd "\$(dirname "\$0")"
./$APP
EOF
    chmod +x "cikti/$APP/BASLAT-$APP.command"
done

echo
echo "============================================================"
echo " TAMAM. Dagitilacak klasorler:"
echo "   $(pwd)/cikti/FULLSERVIS-MAC-WIFI     -> MAC (Wi-Fi) makinesine"
echo "   $(pwd)/cikti/FULLSERVIS-MAC-KABLO    -> MAC (Kablo) makinesine"
echo
echo " Ilk acilista macOS 'gelistirici dogrulanamadi' derse, o makinede bir kez:"
echo "   xattr -dr com.apple.quarantine /uygulamanin/bulundugu/klasor"
echo " ya da: sag tik -> Ac -> Ac"
echo "============================================================"
