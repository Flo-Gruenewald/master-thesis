"""Presence subnode (Raspberry Pi 5 + HC-SR04): publishes the measured distance to the host.

The host decides what counts as "someone is here" (room.toml [presence]), so this script stays dumb.
Wiring: VCC → pin 2 (5V), GND → pin 6, TRIG → GPIO23 (pin 16), ECHO → 1 kΩ → GPIO24 (pin 18), 2 kΩ GPIO24 → GND.

Install once:  sudo apt install -y python3-gpiozero python3-lgpio python3-paho-mqtt
Run:           python3 presence.py 192.168.178.101        (the host's IP; 127.0.0.1 when the host runs on this Pi)
"""
import json
import sys
import time

import paho.mqtt.client as mqtt
from gpiozero import DistanceSensor

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.178.101"
PREFIX = "easteregged"
RATE_HZ = 5

sensor = DistanceSensor(echo=24, trigger=23, max_distance=4.0)

try:  # paho 2.x
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="presence-pi")
except AttributeError:  # paho 1.x (Raspberry Pi OS apt package)
    client = mqtt.Client(client_id="presence-pi")
client.will_set(f"{PREFIX}/status/presence", "offline", retain=True)
client.on_connect = lambda c, *a: c.publish(f"{PREFIX}/status/presence", "online", retain=True)
client.connect_async(HOST, 1883)
client.loop_start()
print(f"publishing distance to {HOST}:1883 every {1 / RATE_HZ:.1f} s, Ctrl+C to stop")

try:
    while True:
        cm = round(sensor.distance * 100, 1)  # 400 = nothing in range
        client.publish(f"{PREFIX}/in/presence", json.dumps({"distance_cm": cm, "src": "pi"}))
        if sys.stdout.isatty():
            print(f"\r{cm:6.1f} cm ", end="", flush=True)
        time.sleep(1 / RATE_HZ)
except KeyboardInterrupt:
    pass
finally:
    client.publish(f"{PREFIX}/status/presence", "offline", retain=True)
    client.loop_stop()
    client.disconnect()
