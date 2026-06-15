#!/usr/bin/env bash
# Linux — FULL Servis sunucusunu boot'ta otomatik baslatan systemd servisi kurar.
#
# Kullanim:  sudo ./install-server-systemd.sh
# Onsart:    fullservice-backend/venv kurulu olmali (yoksa sistem python'u kullanilir).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$(cd "$SCRIPT_DIR/../.." && pwd)"          # fullservice-backend
RUN_USER="${SUDO_USER:-$(whoami)}"
VENV_PY="$WORKDIR/venv/bin/python"
PYTHON="$([[ -x "$VENV_PY" ]] && echo "$VENV_PY" || command -v python3)"
UNIT_DEST="/etc/systemd/system/fullservice-server.service"

mkdir -p "$WORKDIR/logs"

sed -e "s|__PYTHON__|$PYTHON|g" \
    -e "s|__WORKDIR__|$WORKDIR|g" \
    -e "s|__USER__|$RUN_USER|g" \
    "$SCRIPT_DIR/fullservice-server.service" > "$UNIT_DEST"

systemctl daemon-reload
systemctl enable fullservice-server.service
systemctl restart fullservice-server.service
echo "[Linux] systemd servisi kuruldu: fullservice-server"
echo "        Durum: systemctl status fullservice-server"
echo "        Loglar: journalctl -u fullservice-server -f"
