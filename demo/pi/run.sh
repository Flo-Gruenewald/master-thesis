#!/bin/bash
# Starts the room on the Pi: the host (controller) and, if switched on, the ultrasonic presence sensor. Calling it again restarts
# everything (older copies are stopped first, so there is never more than one host).
# Each process restarts by itself if it crashes. Logs: ~/easteregged/host.log, presence.log
# Autostart: crontab line  @reboot sleep 20 && /home/pi/easteregged/run.sh     Stop: ~/easteregged/stop.sh
cd /home/pi/easteregged
# Home Assistant token (only on the Pi, never synced): ~/.easteregged_ha_token, readable only by pi
[ -f /home/pi/.easteregged_ha_token ] && export HA_TOKEN="$(cat /home/pi/.easteregged_ha_token)"
/home/pi/easteregged/stop.sh >/dev/null
(while true; do venv/bin/python -u /home/pi/easteregged/host/main.py --no-browser >> host.log 2>&1; sleep 3; done) &
# Presence comes from the LD2450 radar on the TOP subnode (WLED usermod, MQTT). The old HC-SR04 script only
# runs if ~/easteregged/use_ultrasonic exists (touch it to switch back; both at once would fight).
if [ -f /home/pi/easteregged/use_ultrasonic ]; then
  (sleep 5; while true; do venv/bin/python -u /home/pi/easteregged/presence.py 127.0.0.1 >> presence.log 2>&1; sleep 3; done) &
fi
