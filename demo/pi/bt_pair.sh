#!/bin/bash
# Pairs a Bluetooth speaker (e.g. the JBL) with the Pi as the room speaker. No sudo needed.
# Usage: put the speaker in pairing mode, then   ./bt_pair.sh            (scan, list devices)
#                                                ./bt_pair.sh AA:BB:CC:DD:EE:FF   (pair + trust + connect)
# Afterwards set in ~/easteregged/host/machine.toml:  [room] room_output = "pw:JBL"  room_latency_ms = 200
MAC="$1"
if [ -z "$MAC" ]; then
  echo "Scanning 15 s … (speaker in pairing mode?)"
  bluetoothctl --timeout 15 scan on >/dev/null 2>&1
  bluetoothctl devices | grep -v "^$"
  echo; echo "Run again with the speaker's MAC, e.g.: ./bt_pair.sh AA:BB:CC:DD:EE:FF"
  exit 0
fi
bluetoothctl --timeout 10 scan on >/dev/null 2>&1
bluetoothctl pair "$MAC" && bluetoothctl trust "$MAC" && bluetoothctl connect "$MAC"
sleep 3
echo; echo "PipeWire sinks now:"; wpctl status | sed -n '/Sinks:/,/Sources:/p'
