#!/usr/bin/env bash
# macOS — bir düğüme config.json'daki statik IP'yi atar.
#
# Kullanim:  sudo ./set-static-ip.sh <node_id>
# Ornek:     sudo ./set-static-ip.sh mac_cable
#
# config.json'un "network" bolumunden ip / subnet_mask / gateway / dns ve
# "assignments[node_id].interface" (macOS ag servisi adi, or. "Ethernet" / "Wi-Fi")
# okunur. Ag servisi adlarini gormek icin:  networksetup -listallnetworkservices
set -euo pipefail

NODE_ID="${1:-}"
if [[ -z "$NODE_ID" ]]; then
  echo "Kullanim: sudo $0 <node_id>   (or. mac_cable | mac_wifi)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${FULLSERVICE_CONFIG:-$SCRIPT_DIR/../../config.json}"

read_cfg() {
  python3 - "$CONFIG" "$NODE_ID" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
nid = sys.argv[2]
net = cfg["network"]
a   = net["assignments"][nid]
dns = " ".join(net.get("dns", []))
print(a["interface"]); print(a["ip"]); print(net["subnet_mask"]); print(net["gateway"]); print(dns)
PY
}

mapfile -t CFG < <(read_cfg)
IFACE="${CFG[0]}"; IP="${CFG[1]}"; MASK="${CFG[2]}"; GW="${CFG[3]}"; DNS="${CFG[4]}"

echo "[macOS] $NODE_ID → servis='$IFACE' ip=$IP mask=$MASK gw=$GW dns=($DNS)"
networksetup -setmanual "$IFACE" "$IP" "$MASK" "$GW"
if [[ -n "$DNS" ]]; then
  # shellcheck disable=SC2086
  networksetup -setdnsservers "$IFACE" $DNS
fi
echo "[macOS] Statik IP atandi. Kontrol: ifconfig | networksetup -getinfo \"$IFACE\""
