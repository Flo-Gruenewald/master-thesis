#!/usr/bin/env python3
"""LED node for a Raspberry Pi subnode (kellerkind, the GROUND wall unit).

Looks like a WLED to the host: it takes the host's DDP frames (UDP 4048) and answers the two JSON calls the
host uses (GET /json/info, POST /json/state) on HTTP port 8081. Frames go to a SK6812 RGBW strip on the
Pi's SPI MOSI pin (GPIO10 / pin 19): 2.4 MHz, 3 SPI bits per LED bit (same method as core/light.py).
The strip's current is capped in software (there is no WLED limiter). No frames for 10 s → strip dark.

Settings (environment): LEDS=60  RGBW=1  SPI_BUS=0  SPI_DEV=0  MAX_MA=600  HTTP_PORT=8081
Stdlib + numpy + spidev only (both come with Raspberry Pi OS). Run: python3 led_node.py
"""
import json
import os
import signal
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import spidev

N = int(os.environ.get("LEDS", 60))
RGBW = os.environ.get("RGBW", "1") == "1"
CH = 4 if RGBW else 3
MAX_MA = float(os.environ.get("MAX_MA", 600))
HTTP_PORT = int(os.environ.get("HTTP_PORT", 8081))
NAME = socket.gethostname()

LUT = np.zeros((256, 3), np.uint8)
for v in range(256):
    b = 0
    for i in range(7, -1, -1):
        b = (b << 3) | (0b110 if (v >> i) & 1 else 0b100)
    LUT[v] = [(b >> 16) & 255, (b >> 8) & 255, b & 255]

spi = spidev.SpiDev()
spi.open(int(os.environ.get("SPI_BUS", 0)), int(os.environ.get("SPI_DEV", 0)))
spi.max_speed_hz = 2_400_000
spi.mode = 0

state = {"on": True, "last": 0.0, "frames": 0, "ma": 0.0, "dark": True}
lock = threading.Lock()
frame = np.zeros(N * CH, np.uint8)          # wire bytes as the host sends them: R G B (W) per LED


def show(rgbw):
    """rgbw: uint8 (N, CH) in R,G,B(,W) order → current cap → G,R,B(,W) on the wire."""
    x = rgbw.astype(np.float32) / 255
    est = float(x.sum()) * 12.0 + N * 1.0              # ~12 mA per fully lit channel + ~1 mA per chip
    if MAX_MA and est > MAX_MA:
        x *= max(0.0, (MAX_MA - N) / max(est - N, 1e-6))
        est = MAX_MA
    b = (x * 255 + 0.5).astype(np.uint8)
    b[:, [0, 1]] = b[:, [1, 0]]
    spi.writebytes2(np.concatenate([LUT[b.reshape(-1)].reshape(-1), np.zeros(64, np.uint8)]))
    state["ma"] = est


def black():
    show(np.zeros((N, CH), np.uint8))
    state["dark"] = True


def ddp_loop():
    """DDP: 10-byte header (flags, seq, type, id, offset u32, length u16), then pixel data."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 4048))
    while True:
        pkt, _ = s.recvfrom(4096)
        if len(pkt) < 10:
            continue
        flags = pkt[0]
        off = int.from_bytes(pkt[4:8], "big")
        ln = int.from_bytes(pkt[8:10], "big")
        data = np.frombuffer(pkt[10:10 + ln], np.uint8)
        with lock:
            end = min(off + len(data), frame.size)
            if off < frame.size:
                frame[off:end] = data[:end - off]
            if flags & 0x01 and state["on"]:           # PUSH: show the frame
                show(frame.reshape(N, CH))
                state["last"], state["dark"] = time.monotonic(), False
                state["frames"] += 1


def watchdog():
    while True:
        time.sleep(1)
        with lock:
            if not state["dark"] and time.monotonic() - state["last"] > 10:
                black()                                 # host gone: don't leave the wall lit


class Api(BaseHTTPRequestHandler):
    def _send(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/json/info"):
            live = time.monotonic() - state["last"] < 3
            self._send({"ver": "led_node 1.0", "name": NAME, "live": live, "frames": state["frames"],
                        "leds": {"count": N, "rgbw": RGBW, "pwr": round(state["ma"]), "maxpwr": MAX_MA}})
        elif self.path.startswith("/json/state"):
            self._send({"on": state["on"], "bri": 255})
        else:
            self.send_error(404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            d = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            d = {}
        if "on" in d:
            with lock:
                state["on"] = bool(d["on"])
                if not state["on"]:
                    black()
        self._send({"success": True})

    def log_message(self, *a):
        pass


def stop(*_):
    with lock:
        black()
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    black()
    threading.Thread(target=ddp_loop, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()
    print(f"led_node: {N} LEDs {'RGBW' if RGBW else 'RGB'}, max {MAX_MA:.0f} mA, DDP :4048, HTTP :{HTTP_PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Api).serve_forever()
