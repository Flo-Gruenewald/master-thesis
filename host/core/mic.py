"""Mic listener: finds taps/dings ("hit") and humming ("hum") and cuts them out of the input.

Runs inside the audio input callback, block by block. The loop that the speaker plays also
reaches the mic ("bleed"); because it repeats every loop, a per-position profile of the bleed
is learned and the detection threshold sits above it.
"""
import collections

import numpy as np

BINS = 192  # bleed profile resolution per loop (~30 ms at 84 BPM, 8 beats)


class Mic:
    def __init__(self, sr, cfg, engine, emit):
        self.sr = sr
        self.engine = engine
        self.emit = emit
        self.sensitivity = float(cfg["sensitivity"])
        self.min_level = float(cfg["min_level"])
        self.hum_after = cfg["hum_after_ms"] / 1000
        self.hit_len = cfg["hit_length_ms"] / 1000
        self.max_hum = engine.loop_seconds / 2
        self.ring = np.zeros(int(sr * 6), np.float32)
        self.w = 0                      # absolute write position in the ring
        self.floor = 1e-3
        self.hist = collections.deque(maxlen=6)
        self.prof = np.zeros(BINS, np.float32)
        self.cap = None
        self.last_onset = -1.0
        self.level = 0.0                # for the meter
        self.thr = 0.0
        self.excess = 0.0               # how far above threshold, 0..1, smoothed (for light)
        self.capture = False            # set by the scenario: record sounds as layers
        self.ok = False

    def process(self, x, t0):
        """x: mono block, t0: perf_counter time of its first sample."""
        n = len(x)
        i0 = self.w
        R = len(self.ring)
        j = i0 % R
        if j + n <= R:
            self.ring[j:j + n] = x
        else:
            k = R - j
            self.ring[j:] = x[:k]
            self.ring[:n - k] = x[k:]
        self.w += n

        env = float(np.sqrt(np.mean(x * x))) + 1e-7
        self.level = max(env, self.level * 0.9)
        self.floor += (env - self.floor) * (0.2 if env < self.floor else 0.0015)
        s = self.sensitivity
        thr = max(self.min_level * (1.5 - s), self.floor * (1.5 + (1 - s) * 5))
        frac = self.engine.loop_frac(t0)
        if frac is not None:
            b = int(frac * BINS) % BINS
            bleed = max(self.prof[b - 1], self.prof[b], self.prof[(b + 1) % BINS])
            thr = max(thr, bleed * (1.3 + (1 - s) * 2.4))
            self.prof[b] += (env - self.prof[b]) * (0.1 if env > self.prof[b] else 0.01)
        else:
            self.prof *= 0.999
        self.thr = thr
        self.excess += (min(1.0, max(0.0, env / thr - 1.0)) - self.excess) * 0.5

        prev = sum(self.hist) / len(self.hist) if self.hist else env
        self.hist.append(env)
        c = self.cap
        if c is None:
            if env > thr and env > 1.5 * prev and t0 - self.last_onset > 0.12:
                self.last_onset = t0
                self.emit({"type": "onset", "strength": min(1.0, env / thr / 4), "t": t0})
                if self.capture:
                    self.cap = {"t": t0, "i": i0, "peak": env, "last": t0, "hum": False}
            return

        c["peak"] = max(c["peak"], env)
        if env > max(c["peak"] * 0.25, self.floor * 2):
            c["last"] = t0
        dur = t0 + n / self.sr - c["t"]
        if dur < self.hum_after:
            return
        held = t0 - c["last"] < 0.06
        if not c["hum"]:
            if held:
                c["hum"] = True
            else:
                self._done("hit", c["i"] + int(self.hit_len * self.sr), c)
                return
        if not held or dur > self.max_hum:
            self._done("hum", self.w, c)

    def _done(self, kind, end, c):
        self.cap = None
        start = c["i"] - int(0.01 * self.sr)
        idx = np.arange(start, end) % len(self.ring)
        self.emit({"type": "sound", "kind": kind, "t": c["t"], "buf": self.ring[idx].copy(),
                   "strength": min(1.0, c["peak"] / max(self.thr, 1e-6) / 4), "src": "mic"})
