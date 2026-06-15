#!/usr/bin/env bash
# macOS — FULL Servis agent'ini boot'ta otomatik baslatan launchd servisi kurar.
#
# Kullanim:
#   ./install-agent-launchd.sh <node_id> <server_url> [port]
# Ornek:
#   ./install-agent-launchd.sh mac_cable http://192.168.1.10:8770 7531
#
# Not: Tek Mac'te iki dugum (mac_cable + mac_wifi) kosturulacaksa her birine
# FARKLI port verin ve bu scripti iki kez calistirin (Label otomatik ayrisir).
set -euo pipefail

NODE_ID="${1:-}"; SERVER_URL="${2:-}"; PORT="${3:-7531}"
if [[ -z "$NODE_ID" || -z "$SERVER_URL" ]]; then
  echo "Kullanim: $0 <node_id> <server_url> [port]"
  echo "Ornek:    $0 mac_cable http://192.168.1.10:8770 7531"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$(cd "$SCRIPT_DIR/../.." && pwd)"          # fullservice-backend
PYTHON="$(command -v python3)"
LABEL="com.tt.fullservice.agent.${NODE_ID}"
PLIST_DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$WORKDIR/logs"

sed -e "s|__PYTHON__|$PYTHON|g" \
    -e "s|__WORKDIR__|$WORKDIR|g" \
    -e "s|__NODE_ID__|$NODE_ID|g" \
    -e "s|__SERVER_URL__|$SERVER_URL|g" \
    -e "s|__PORT__|$PORT|g" \
    -e "s|com.tt.fullservice.agent</string>|${LABEL}</string>|" \
    "$SCRIPT_DIR/com.tt.fullservice.agent.plist" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"
echo "[macOS] launchd servisi kuruldu: $LABEL"
echo "        plist: $PLIST_DEST"
echo "        Durum: launchctl list | grep fullservice"
echo "        Kaldir: launchctl unload \"$PLIST_DEST\" && rm \"$PLIST_DEST\""
