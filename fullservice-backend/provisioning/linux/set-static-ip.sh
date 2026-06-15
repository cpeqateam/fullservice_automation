#!/usr/bin/env bash
# Linux (NetworkManager / nmcli) — sunucuya config.json'daki statik IP'yi atar.
#
# Kullanim:  sudo ./set-static-ip.sh [node_id]   (varsayilan: server)
# Ornek:     sudo ./set-static-ip.sh server
#
# config.json "network" bolumunden ip / subnet_mask / gateway / dns ve
# assignments[node_id].interface (or. "eth0") okunur. nmcli baglanti adini
# arayuze gore bulur.
set -euo pipefail

NODE_ID="${1:-server}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${FULLSERVICE_CONFIG:-$SCRIPT_DIR/../../config.json}"

read_cfg() {
  python3 - "$CONFIG" "$NODE_ID" <<'PY'
import json, sys, ipaddress
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
nid = sys.argv[2]
net = cfg["network"]
a   = net["assignments"][nid]
prefix = ipaddress.IPv4Network(f"0.0.0.0/{net['subnet_mask']}").prefixlen
print(a["interface"]); print(a["ip"]); print(prefix); print(net["gateway"]); print(",".join(net.get("dns", [])))
PY
}

mapfile -t CFG < <(read_cfg)
IFACE="${CFG[0]}"; IP="${CFG[1]}"; PREFIX="${CFG[2]}"; GW="${CFG[3]}"; DNS="${CFG[4]}"

# Arayuze bagli nmcli baglanti adini bul (yoksa arayuz adini kullan)
CON="$(nmcli -g GENERAL.CONNECTION device show "$IFACE" 2>/dev/null || true)"
[[ -z "$CON" || "$CON" == "--" ]] && CON="$IFACE"

echo "[Linux] $NODE_ID → arayuz='$IFACE' baglanti='$CON' ip=$IP/$PREFIX gw=$GW dns=$DNS"
nmcli con mod "$CON" ipv4.addresses "$IP/$PREFIX"
nmcli con mod "$CON" ipv4.gateway "$GW"
nmcli con mod "$CON" ipv4.dns "$DNS"
nmcli con mod "$CON" ipv4.method manual
nmcli con up "$CON"
echo "[Linux] Statik IP atandi. Kontrol: ip addr show $IFACE"
