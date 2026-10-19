#!/bin/bash
# Laptop-controller mode: keep only the HC-SR04 presence publisher on the Pi.
# The optional first argument overrides automatic SSID-based host selection.
set -u

ROOT=/home/pi/easteregged
HOST="${1:-}"

if [ -z "$HOST" ]; then
    SSID="$(nmcli -t -f active,ssid dev wifi | awk -F: '$1 == "yes" { print $2; exit }')"
    case "$SSID" in
        FLO-WORK) HOST=192.168.137.1 ;;  # Windows Mobile Hotspot gateway
        G) HOST=192.168.178.163 ;;        # laptop address last verified on the home network
        *)
            echo "No laptop MQTT target configured for Wi-Fi SSID '$SSID'." >&2
            exit 2
            ;;
    esac
fi

cd "$ROOT"
pkill -f "easteregged/host/main.py" 2>/dev/null || true
pkill -f "easteregged/presence.py" 2>/dev/null || true

echo "Publishing presence to $HOST:1883"
exec "$ROOT/venv/bin/python" -u "$ROOT/presence.py" "$HOST"