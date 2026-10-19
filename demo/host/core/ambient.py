"""Ambient audio for the room levels (Ground beds, Middle accents).

Ambient sounds don't need to sit on the beat. The room output is "main" (mixed into the main output, default)
or another sound card by (part of) its name, with its own clock and latency.
"""
import logging

import numpy as np
import sounddevice as sd

log = logging.getLogger("ambient")


class AVoice:
    """A stereo buffer with ramped gain; loops or plays once, with an optional gain envelope."""

    def __init__(self, buf, gain, fade, sr, loop=False, env=None, delay=0):
        self.buf = buf if buf.ndim == 2 else np.column_stack([buf, buf])
        self.sr = sr
        self.loop = loop
        self.env = env
        self.pos = -int(delay)
        self.g = 0.0
        self.target = 0.0
        self.step = 1.0
        self.ramp(gain, fade)
        self.done = False
        self.name = ""

    def ramp(self, target, seconds=0.0):
        self.target = float(target)
        self.step = max(abs(self.target - self.g) / max(1.0, seconds * self.sr), 1e-9)

    def render(self, n):
        """Return (n, 2) or None; advances the voice."""
        p0 = self.pos
        self.pos += n
        g0 = self.g
        if g0 != self.target:
            d = self.target - g0
            self.g = self.target if abs(d) <= self.step * n else g0 + np.sign(d) * self.step * n
        if self.g == 0.0 and self.target == 0.0 and g0 == 0.0:
            self.done = True
            return None
        L = len(self.buf)
        idx = p0 + np.arange(n)
        if self.loop:
            m = idx >= 0
            idx = idx % L
        else:
            m = (idx >= 0) & (idx < L)
            if p0 >= L:
                self.done = True
                return None
        if not m.any():
            return None
        s = np.zeros((n, 2), np.float32)
        s[m] = self.buf[idx[m]]
        g = np.linspace(g0, self.g, n, dtype=np.float32) if g0 != self.g else g0
        if self.env is not None and not self.loop:
            e = np.zeros(n, np.float32)
            e[m] = self.env[idx[m]]
            g = g * e
        return s * (g[:, None] if isinstance(g, np.ndarray) else g)


class Mixer:
    """Voices are added/removed from the asyncio thread by replacing the list."""

    def __init__(self, sr):
        self.sr = sr
        self.voices = []
        self.gain = 1.0
        self.level = 0.0

    def add(self, v):
        self.voices = self.voices + [v]
        return v

    def prune(self):
        self.voices = [v for v in self.voices if not v.done]

    def mix(self, n):
        acc = np.zeros((n, 2), np.float32)
        for v in self.voices:
            s = v.render(n)
            if s is not None:
                acc += s
        acc *= self.gain
        self.level = max(float(np.abs(acc).max()) if n else 0.0, self.level * 0.9)
        return acc


class RoomOut:
    """Where the room's ambient sound plays: "main" (mixed into the main output, default) or the name of another
    sound card (e.g. the room speakers on a second output). mixer.mix() is pulled by the chosen output."""

    def __init__(self, target, sr, block, hostapi):
        self.target = (target or "main").strip()
        self.sr = sr
        self.block = block
        self.hostapi = hostapi
        self.mixer = Mixer(sr)
        self.kind = "main"
        self.name = "main output (shared)"
        self.ok = True
        self._stream = None

    def start(self):
        if self.target == "main":
            return
        try:
            from .audio import pick_device
            dev = pick_device(self.target, "output", self.hostapi)
            if dev is None:
                raise RuntimeError("device not found")

            def cb(out, n, tinfo, status):
                out[:, :2] = np.clip(self.mixer.mix(n), -1, 1)

            self._stream = sd.OutputStream(device=dev, samplerate=self.sr, blocksize=self.block * 2,
                                           channels=2, dtype="float32", latency="high", callback=cb)
            self._stream.start()
            self.kind, self.name = "device", sd.query_devices(dev)["name"]
            log.info("room output: %s", self.name)
        except Exception as e:
            log.error("room output '%s' failed (%s); using the main output", self.target, e)
            self.kind, self.name, self.ok = "main", f"main output (fallback: {e})", False

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
