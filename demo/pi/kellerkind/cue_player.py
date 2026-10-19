#!/usr/bin/env python3
"""Cue player for a Raspberry Pi subnode (kellerkind): plays sounds on the Pi's own audio jack (AUX → the
Marsboy speaker) when the host sends a cue over MQTT.

Topic  easteregged/node/<hostname>/play   payload {"sound": "accent/bird_cross", "gain": 0.7} or "test"
Status easteregged/status/<hostname>      "online" (retained; "offline" as last will)
Sounds: ~/easteregged/stems/<sound>.wav (copied from the host's stems/). "test" = a short 440 Hz tone.

Settings (environment): BROKER=dexy.local  ALSA_DEV=plughw:Headphones  STEMS=~/easteregged/stems
Needs paho-mqtt (in ~/easteregged/venv). Run: venv/bin/python cue_player.py
"""
import json
import os
import socket
import subprocess
import tempfile
import wave

import numpy as np
import paho.mqtt.client as mqtt

NAME = socket.gethostname()
BROKER = os.environ.get("BROKER", "dexy.local")
DEV = os.environ.get("ALSA_DEV", "plughw:Headphones")
SINK = os.environ.get("SINK", "alsa_output.platform-3f00b840.mailbox.stereo-fallback")   # the AUX jack in PipeWire
STEMS = os.path.expanduser(os.environ.get("STEMS", "~/easteregged/stems"))
TOPIC = f"easteregged/node/{NAME}/play"
STATUS = f"easteregged/status/{NAME}"
ACK = f"easteregged/node/{NAME}/ack"          # {"sound", "ok"} after each cue
client = None
playing = []


def tone_file():
    p = os.path.join(tempfile.gettempdir(), "cue_test.wav")
    if not os.path.exists(p):
        t = np.arange(int(0.6 * 48000)) / 48000
        y = (np.sin(2 * np.pi * 440 * t) * np.minimum(1, (0.6 - t) * 20) * 0.5 * 32767).astype(np.int16)
        with wave.open(p, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(y.tobytes())
    return p


def play(sound, gain=1.0):
    global playing
    playing = [p for p in playing if p.poll() is None][-6:]      # at most a few at once
    path = tone_file() if sound == "test" else os.path.join(STEMS, sound + ".wav")
    if not os.path.exists(path):
        print("missing sound:", path, flush=True)
        ack(sound, False)
        return
    vol = max(0.0, min(1.0, float(gain)))
    # PipeWire mixes it with the ground stream on the same output; aplay only as a fallback
    cmd = (["pw-play", "--target", SINK, "--volume", f"{vol:.2f}", path] if _has("pw-play")
           else ["aplay", "-q", "-D", DEV, path])
    playing.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    print("play", sound, f"{vol:.2f}", flush=True)
    ack(sound, True)


def ack(sound, ok):
    if client is not None:
        client.publish(ACK, json.dumps({"sound": sound, "ok": ok}))


def _has(prog):
    return any(os.access(os.path.join(d, prog), os.X_OK) for d in os.environ.get("PATH", "").split(":"))


def on_connect(c, userdata, flags, rc, props=None):
    c.subscribe(TOPIC)
    c.publish(STATUS, "online", retain=True)
    print("connected to", BROKER, "· listening on", TOPIC, flush=True)


def on_message(c, userdata, msg):
    raw = msg.payload.decode(errors="replace").strip()
    try:
        d = json.loads(raw)
    except ValueError:
        d = raw
    if isinstance(d, str):
        play(d)
    elif isinstance(d, dict) and d.get("sound"):
        play(str(d["sound"]), d.get("gain", 1.0))


if __name__ == "__main__":
    c = client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"cue-{NAME}")
    c.will_set(STATUS, "offline", retain=True)
    c.on_connect, c.on_message = on_connect, on_message
    c.reconnect_delay_set(1, 10)
    c.connect_async(BROKER, 1883, keepalive=30)
    c.loop_forever(retry_first_connection=True)
