"""Network mic (table unit, ESP32-C3 + INMP441) and the loop recorder for Morning Jam (Flo, 15.10.2026).

NetMic: the table unit streams raw audio over UDP: b"NMIC" + uint32 seq + int16 samples (mono, 16 kHz).
        Packets land in a ring; every sample gets a capture time (arrival clock, smoothed with a minimum filter
        over the last seconds, minus a fixed latency). Lost packets are filled with silence.
RowRecorder: no sound detection. The table mic is recorded loop by loop (the whole beat loop, 8 beats). A loop
        that got louder than `threshold` becomes a row: played back in every following loop at the same place
        (a tap on beat 2 and 6 comes back on 2 and 6). The network delay doesn't matter: it is a fixed offset,
        taken out by the capture time.
"""
import asyncio
import collections
import logging
import struct
import time

import numpy as np
from scipy.signal import resample_poly

log = logging.getLogger("netmic")
MAGIC = b"NMIC"


class NetMic(asyncio.DatagramProtocol):
    def __init__(self, cfg):
        self.port = int(cfg.get("port", 7010))
        self.sr = int(cfg.get("samplerate", 16000))
        self.latency = float(cfg.get("latency_ms", 60)) / 1000
        self.gain = float(cfg.get("gain", 1.0))
        self.ring = np.zeros(self.sr * 40, np.float32)
        self.w = 0                                   # absolute sample count written
        self.seq = None
        self.offs = collections.deque()              # (arrival time, offset) over the last seconds
        self.off = None                              # capture time of sample 0 (before latency)
        self.level = 0.0
        self.last_rx = 0.0
        self.lost = 0
        self.peer = None

    # ---- network ---------------------------------------------------------------------------
    async def start(self):
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=("0.0.0.0", self.port))
        log.info("listening for the table mic on UDP %d", self.port)

    def datagram_received(self, data, addr):
        if len(data) < 10 or data[:4] != MAGIC:
            return
        seq = struct.unpack_from("<I", data, 4)[0]
        x = np.frombuffer(data, "<i2", offset=8).astype(np.float32) * (self.gain / 32768.0)
        if self.seq is not None:
            gap = (seq - self.seq - 1) & 0xFFFFFFFF
            if 0 < gap < 50:                         # lost packets → silence, keeps the clock in step
                self._write(np.zeros(gap * len(x), np.float32))
                self.lost += gap
            elif gap >= 50:                          # restart of the unit: start a fresh clock
                self.offs.clear()
        self.seq = seq
        self._write(x)
        now = time.perf_counter()
        self.offs.append((now, now - self.w / self.sr))
        while self.offs and now - self.offs[0][0] > 4.0:
            self.offs.popleft()
        self.off = min(o for _, o in self.offs)      # least-delayed packets = the true clock
        self.level = max(float(np.sqrt(np.mean(x * x))) if len(x) else 0.0, self.level * 0.9)
        self.last_rx = now
        self.peer = addr[0]

    def _write(self, x):
        R, n = len(self.ring), len(x)
        j = self.w % R
        if j + n <= R:
            self.ring[j:j + n] = x
        else:
            k = R - j
            self.ring[j:] = x[:k]
            self.ring[:n - k] = x[k:]
        self.w += n

    # ---- time ------------------------------------------------------------------------------
    @property
    def ok(self):
        return self.off is not None and time.perf_counter() - self.last_rx < 2.0

    def index_at(self, t):
        """Ring index of the sample captured at perf_counter time t."""
        return int(round((t + self.latency - self.off) * self.sr))

    def segment(self, t0, t1):
        """Samples captured between t0 and t1, or None if not all have arrived (or are too old)."""
        i0, i1 = self.index_at(t0), self.index_at(t1)
        if i1 > self.w or i0 < self.w - len(self.ring) + self.sr or i1 <= i0:
            return None
        return self.ring[np.arange(i0, i1) % len(self.ring)].copy()


class RowRecorder:
    def __init__(self, cfg, engine, netmic, emit):
        self.e, self.nm, self.emit = engine, netmic, emit
        self.threshold = float(cfg.get("row_threshold", 0.004))   # RMS of a 20 ms window; web page: the mic line
        self.gate = bool(cfg.get("row_gate", True))
        self.active = False            # set by Morning Jam: loops may become rows
        self.next_k = None
        self.rows = 0

    def time_of_frame(self, F):
        f, tr = self.e.ref
        return tr + (F - f) / self.e.sr - self.e.offset_s

    def tick(self, now):
        """Called from the host loop. Handles every loop that has fully passed and fully arrived."""
        e = self.e
        if not e.beds or not self.nm.ok:
            self.next_k = None
            return
        cur = int((e.frame_at(now) - e.origin) // e.L)
        if self.next_k is None:
            self.next_k = cur                        # the loop now playing is the first one recorded
            return
        while self.next_k < cur:
            k = self.next_k
            F0 = e.origin + k * e.L
            x = self.nm.segment(self.time_of_frame(F0), self.time_of_frame(F0 + e.L))
            if x is None:
                if self.nm.index_at(self.time_of_frame(F0 + e.L)) > self.nm.w:
                    return                           # not arrived yet: try again next tick
                self.next_k += 1                     # too old / lost: skip
                continue
            self.next_k += 1
            self._loop(k, x)

    def _loop(self, k, x):
        win = max(1, int(0.02 * self.nm.sr))
        n = len(x) // win
        rms = np.sqrt(np.mean(x[: n * win].reshape(n, win) ** 2, axis=1)) if n else np.zeros(1)
        peak = float(rms.max())
        if not (self.active and peak > self.threshold):
            return
        if self.gate:                                # keep what was played, silence the room in between
            g = np.repeat((rms > self.threshold * 0.6).astype(np.float32), win)
            g = np.convolve(g, np.ones(win) / win, mode="same")[: len(x)]
            x = x[: len(g)] * g
        y = resample_poly(x, self.e.sr, self.nm.sr).astype(np.float32)
        y = np.pad(y, (0, max(0, self.e.L - len(y))))[: self.e.L]
        self.rows += 1
        self.emit({"type": "row", "k": k, "buf": y, "level": peak, "row": self.rows})
