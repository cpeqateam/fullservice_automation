#!/usr/bin/env bash
# =====================================================================
#  FULL Servis - Server (Linux)
#  Calistirma:  ./baslat-server.sh
#  Ilk kez:     chmod +x baslat-server.sh
#  (Dosya yoneticisinden cift tiklamak icin: sag tik -> "Programi Calistir")
# =====================================================================

# ====== AYARLAR (yalnizca BIR KEZ duzenle) ======
SERVER_PORT=8770
# REPO_DIR: fullservice_automation klasorunun tam yolu.
REPO_DIR="$HOME/Desktop/aliimran/fullservice_automation"
# ================================================
# NOT: Bu dosya git pull YAPMAZ. Kod guncellemesi USB ile REPO_DIR'e elle
#      kopyalanir; bu dosya sadece eskisini durdurup yenisini baslatir.
# ================================================

cd "$REPO_DIR" || { echo "Repo klasoru bulunamadi: $REPO_DIR"; read -n1; exit 1; }

echo ""
echo "[1/2] Calisan eski server kapatiliyor (port $SERVER_PORT)..."
if command -v lsof >/dev/null 2>&1; then
    lsof -ti "tcp:$SERVER_PORT" | xargs -r kill -9 2>/dev/null
elif command -v fuser >/dev/null 2>&1; then
    fuser -k "$SERVER_PORT/tcp" 2>/dev/null
fi

echo ""
echo "[2/2] Server baslatiliyor..."
cd fullservice-backend || { echo "fullservice-backend yok"; exit 1; }
source venv/bin/activate
python run_server.py
