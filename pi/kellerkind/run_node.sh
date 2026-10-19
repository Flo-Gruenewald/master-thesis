#!/bin/bash
# Starts kellerkind's subnode programs; each restarts itself after a crash. Calling it again restarts everything.
#   led_node.py      host light frames (DDP) → wall strip on pin 38 (GPIO20, SPI1; needs dtoverlay=spi1-1cs)
#   ground_player.py soundscape loops + cues from MQTT → AUX jack (Marsboy), sounds stored on the Pi
# Autostart: crontab  @reboot sleep 15 && /home/pi/easteregged/run_node.sh
# Stop: pkill -f run_node.sh; pkill -f led_node.py; pkill -f ground_player.py
cd /home/pi/easteregged
exec </dev/null >/dev/null 2>&1          # detach from the terminal (ssh returns at once)
pgrep -f "^/bin/bash /home/pi/easteregged/run_node.sh" | grep -vx "$$" | xargs -r kill   # only older copies of this script
for p in led_node.py ground_player.py cue_player.py; do pkill -f "^[^ ]*python[^ ]* -u /home/pi/easteregged/$p" ; done
pkill -f "^curl -sN --max-time 0 http://dexy.local:8080/room.wav"; pkill -f "^pw-cat --playback --raw --format s16"
export LEDS=60 RGBW=1 MAX_MA=400 HTTP_PORT=8081 SPI_BUS=1 SPI_DEV=0 BROKER=dexy.local
export XDG_RUNTIME_DIR=/run/user/1000                       # reach the desktop session's PipeWire
export SINK=alsa_output.platform-3f00b840.mailbox.stereo-fallback LATENCY_MS=300   # the AUX jack (Marsboy)
# LED node off since 06.10: the wall strip runs on the Gledopto (3.3 V data too weak for it). To use the Pi again:
# (while true; do python3 -u /home/pi/easteregged/led_node.py >> led_node.log 2>&1; sleep 3; done) &
(while true; do venv/bin/python -u /home/pi/easteregged/ground_player.py >> ground_player.log 2>&1; sleep 3; done) &
