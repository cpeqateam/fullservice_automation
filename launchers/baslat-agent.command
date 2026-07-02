#!/bin/bash
# =====================================================================
#  FULL Servis - Agent (macOS)  -  Finder'da CIFT TIKLA ile calisir
#  Ilk kez: bu dosyaya calistirma izni ver ->  chmod +x baslat-agent.command
# =====================================================================

# ====== BU MAC ICIN AYARLAR (yalnizca BIR KEZ duzenle) ======
NODE_ID="mac_wifi"          # bu mac hangisi:  mac_cable  ya da  mac_wifi
SERVER_URL="http://192.168.1.10:8770"
AGENT_PORT=7531
# REPO_DIR: fullservice_automation klasorunun tam yolu.
REPO_DIR="$HOME/fullservice_automation"
# ============================================================
# NOT: Bu dosya git pull YAPMAZ. Kod guncellemesi USB ile REPO_DIR'e elle
#      kopyalanir; bu dosya sadece eskisini durdurup yenisini baslatir.
# ============================================================

cd "$REPO_DIR" || { echo "Repo klasoru bulunamadi: $REPO_DIR"; read -n1; exit 1; }

echo ""
echo "[1/2] Calisan eski agent kapatiliyor (port $AGENT_PORT)..."
lsof -ti "tcp:$AGENT_PORT" | xargs kill -9 2>/dev/null

echo ""
echo "[2/2] Agent baslatiliyor: $NODE_ID  ->  $SERVER_URL"
cd fullservice-backend || { echo "fullservice-backend yok"; read -n1; exit 1; }
source venv/bin/activate
python run_agent.py "$NODE_ID" "$SERVER_URL"

echo ""
echo "Agent durdu. Bu pencereyi kapatabilirsiniz."
read -n1
