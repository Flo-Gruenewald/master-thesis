#!/usr/bin/env python3
"""Ground player for a Raspberry Pi subnode (kellerkind, the GROUND wall unit).

Plays the room's soundscape from local files instead of a stream: the host only sends what to play.
  easteregged/node/<host>/beds  (retained) {"beds": {"wind": 0.15, …}, "fade": 6.0, "master": 1.0}
        → loops these beds (stems/ground/<name>.wav), ramps each to its gain over `fade` seconds,
          beds not listed fade out. Retained, so after a reboot the current soundscape comes back at once.
  easteregged/node/<host>/play  {"sound": "accent/bird_cross", "gain": 0.7, "env": "in"|"out"} or "test"
        → a one-shot on top (env "in"/"out": rises/falls over its length, for sounds travelling to/from
          the table speaker). Each play is acknowledged on easteregged/node/<host>/ack {"sound", "ok"}.
  easteregged/status/<host>     "online" (retained; "offline" as last will)
One mixer (numpy, 48 kHz stereo) → one pw-cat stream on the AUX jack (PipeWire sink SINK).

Settings (environment): BROKER=dexy.local  SINK=<pipewire sink>  STEMS=~/easteregged/stems  LATENCY_MS=300
Needs paho-mqtt (venv). Run: venv/bin/python ground_player.py
"""
import json
import os
import socket
import subprocess
import threading
import time
import wave

import numpy as np
import paho.mqtt.client as mqtt

NAME = socket.gethostname()
BROKER = os.environ.get("BROKER", "dexy.local")
SINK = os.environ.get("SINK", "alsa_output.platform-3f00b840.mailbox.stereo-fallback")
STEMS = os.path.expanduser(os.environ.get("STEMS", "~/easteregged/stems"))
LAT = int(os.environ.get("LATENCY_MS", 300))
SR, BLOCK = 48000, 2400                                   # 50 ms blocks
BASE = f"easteregged/node/{NAME}"
STATUS = f"easteregged/status/{NAME}"

cache = {}
lock = threading.Lock()
beds = {}                 # name → {"buf", "pos", "g", "target", "rate"}
shots = []                # {"buf", "pos", "gain", "env"}
master = {"g": 1.0}
client = None


def load(rel):
    """stems/<rel>.wav → float32 (n, 2), cached. None if missing."""
    if rel in cache:
        return cache[rel]
    p = os.path.join(STEMS, rel + ".wav")
    if not os.path.exists(p):
        cache[rel] = None
        return None
    with wave.open(p) as w:
        ch, sw, n = w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        cache[rel] = None
        return None
    x = np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, ch) / 32768
    if ch == 1:
        x = np.repeat(x, 2, axis=1)
    cache[rel] = x[:, :2].copy()
    return cache[rel]


def tone():
    t = np.arange(int(0.6 * SR)) / SR
    y = (np.sin(2 * np.pi * 440 * t) * np.minimum(1, (0.6 - t) * 20) * 0.5).astype(np.float32)
    return np.column_stack([y, y])


def set_beds(msg):
    want = {str(k): float(v) for k, v in (msg.get("beds") or {}).items()}
    fade = max(0.05, float(msg.get("fade", 4.0)))
    master["g"] = float(msg.get("master", 1.0))
    with lock:
        for name, b in beds.items():
            if name not in want:
                b["target"], b["rate"] = 0.0, b["g"] / fade + 1e-6
        for name, g in want.items():
            b = beds.get(name)
            if b is None:
                buf = load(f"ground/{name}")
                if buf is None:
                    print("missing bed:", name, flush=True)
                    continue
                b = beds[name] = {"buf": buf, "pos": 0, "g": 0.0, "target": 0.0, "rate": 1.0}
            b["target"], b["rate"] = g, abs(g - b["g"]) / fade + 1e-6
    print("beds", {k: round(v, 3) for k, v in want.items()}, f"fade {fade:.1f}s master {master['g']:.2f}", flush=True)


def play(sound, gain=1.0, env=None):
    buf = tone() if sound == "test" else load(sound)
    ok = buf is not None
    if ok:
        with lock:
            shots.append({"buf": buf, "pos": 0, "gain": max(0.0, min(1.5, float(gain))), "env": env})
            del shots[:-8]
    print("play", sound, gain, env or "", "" if ok else "(missing)", flush=True)
    if client is not None:
        client.publish(f"{BASE}/ack", json.dumps({"sound": sound, "ok": ok}))


def mix(n):
    out = np.zeros((n, 2), np.float32)
    dt = n / SR
    with lock:
        for name in list(beds):
            b = beds[name]
            g0 = b["g"]
            step = b["rate"] * dt
            b["g"] = b["target"] if abs(b["target"] - g0) <= step else g0 + (step if b["target"] > g0 else -step)
            if g0 <= 1e-4 and b["g"] <= 1e-4:
                if b["target"] == 0.0:
                    del beds[name]
                continue
            buf, L = b["buf"], len(b["buf"])
            idx = (b["pos"] + np.arange(n)) % L
            ramp = np.linspace(g0, b["g"], n, dtype=np.float32)[:, None]
            out += buf[idx] * ramp
            b["pos"] = (b["pos"] + n) % L
        keep = []
        for s in shots:
            buf, p = s["buf"], s["pos"]
            seg = buf[p:p + n]
            if len(seg):
                g = s["gain"]
                if s["env"] in ("in", "out"):
                    x = (p + np.arange(len(seg))) / len(buf)
                    e = np.sin(x * np.pi / 2) if s["env"] == "in" else np.cos(x * np.pi / 2)
                    out[:len(seg)] += seg * (g * e.astype(np.float32))[:, None]
                else:
                    out[:len(seg)] += seg * g
                s["pos"] = p + n
            if s["pos"] < len(buf):
                keep.append(s)
        shots[:] = keep
    return np.clip(out * master["g"], -1, 1)


def audio_loop():
    """Keeps one pw-cat fed, ~LATENCY_MS ahead of real time; restarts it if it dies."""
    while True:
        p = subprocess.Popen(["pw-cat", "--playback", "--raw", "--format", "s16", "--rate", str(SR),
                              "--channels", "2", "--target", SINK, "--latency", f"{LAT}ms", "-"],
                             stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        nxt = time.perf_counter()
        try:
            while p.poll() is None:
                p.stdin.write((mix(BLOCK) * 32767).astype(np.int16).tobytes())
                nxt += BLOCK / SR
                ahead = nxt - time.perf_counter()
                if ahead > LAT / 1000:
                    time.sleep(ahead - LAT / 1000)
        except (BrokenPipeError, OSError):
            pass
        print("pw-cat stopped, restarting", flush=True)
        time.sleep(2)


def on_connect(c, userdata, flags, rc, props=None):
    c.subscribe([(f"{BASE}/beds", 0), (f"{BASE}/play", 0)])
    c.publish(STATUS, "online", retain=True)
    print("connected to", BROKER, flush=True)


def on_message(c, userdata, msg):
    raw = msg.payload.decode(errors="replace").strip()
    try:
        d = json.loads(raw)
    except ValueError:
        d = raw
    if msg.topic.endswith("/beds") and isinstance(d, dict):
        set_beds(d)
    elif msg.topic.endswith("/play"):
        if isinstance(d, str):
            play(d)
        elif isinstance(d, dict) and d.get("sound"):
            play(str(d["sound"]), d.get("gain", 1.0), d.get("env"))


if __name__ == "__main__":
    threading.Thread(target=audio_loop, daemon=True).start()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ground-{NAME}")
    client.will_set(STATUS, "offline", retain=True)
    client.on_connect, client.on_message = on_connect, on_message
    client.reconnect_delay_set(1, 10)
    client.connect_async(BROKER, 1883, keepalive=30)
    print(f"ground_player: sink {SINK}, latency {LAT} ms, stems {STEMS}", flush=True)
    client.loop_forever(retry_first_connection=True)
