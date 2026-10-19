"""Audio engine: one transport that keeps everything in time.

- beds:    looping stems (the backbone), aligned to the loop start
- layers:  captured sounds replayed every loop at a snapped position (ephemeral, they fade)
- shots:   one-shots
- ambient: room sounds (Ground beds, Middle accents) on the room output, see ambient.py
Each sound is routed to output channels (the spots' speakers). Only the asyncio thread
changes the voice lists (by replacing them); the audio callback only reads them.
"""
import collections
import logging
import threading
import time
from math import gcd
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample_poly

from .ambient import AVoice, Mixer, RoomOut
from .mic import Mic

log = logging.getLogger("audio")


def load_wav(path, sr):
    data, fsr = sf.read(str(path), dtype="float32", always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    data = data[:, :2]
    if fsr != sr:
        g = gcd(int(sr), int(fsr))
        data = resample_poly(data, sr // g, fsr // g, axis=0).astype(np.float32)
    return np.ascontiguousarray(data)


def pick_device(name, kind, hostapi):
    apis = sd.query_hostapis()
    api = next((i for i, a in enumerate(apis) if hostapi.lower() in a["name"].lower()), None)
    if name:
        for i, d in enumerate(sd.query_devices()):
            if (name.lower() in d["name"].lower() and d[f"max_{kind}_channels"] > 0
                    and (api is None or d["hostapi"] == api)):
                return i
        log.warning("%s device '%s' not found, using the default", kind, name)
    if api is not None and apis[api][f"default_{kind}_device"] >= 0:
        return apis[api][f"default_{kind}_device"]
    return None


def waveform(x, n=160):
    """Smoothed loudness envelope of a buffer, n points 0..1 (the web page draws recorded rows with it)."""
    env = np.array([float(np.sqrt(np.mean(b * b))) if len(b) else 0.0 for b in np.array_split(x, n)])
    env = np.convolve(env, np.array([1, 2, 3, 2, 1]) / 9, mode="same")
    return [round(float(v), 2) for v in env / (env.max() + 1e-6)]


class Voice:
    """A buffer with a smoothly ramped gain. Extra fields are set by the engine."""

    def __init__(self, buf, gain, fade, sr):
        self.buf = buf
        self.sr = sr
        self.g = 0.0
        self.target = 0.0
        self.step = 1.0
        self.ramp(gain, fade)

    def ramp(self, target, seconds=0.0):
        self.target = float(target)
        self.step = max(abs(self.target - self.g) / max(1.0, seconds * self.sr), 1e-9)

    def gains(self, n):
        g0 = self.g
        if g0 == self.target:
            return g0
        d = self.target - g0
        g1 = self.target if abs(d) <= self.step * n else g0 + np.sign(d) * self.step * n
        self.g = float(g1)
        return np.linspace(g0, g1, n, dtype=np.float32)

    @property
    def silent(self):
        return self.g == 0.0 and self.target == 0.0


def _scale(s, g):
    if isinstance(g, np.ndarray) and s.ndim == 2:
        return s * g[:, None]
    return s * g


class AudioEngine:
    def __init__(self, cfg, spots, emit):
        a, t, m = cfg["audio"], cfg["tempo"], cfg["mic"]
        self.cfg = a
        self.sr = int(a["samplerate"])
        self.block = int(a["blocksize"])
        self.nch = int(a["output_channels"])
        self.master = float(a["master_volume"])
        self.offset_s = float(a.get("latency_offset_ms", 0)) / 1000
        self.bpm = float(t["bpm"])
        self.beats = int(t["beats_per_loop"])
        self.steps_per_beat = int(t["steps_per_beat"])
        self.L = int(round(self.beats * 60 / self.bpm * self.sr))
        self.loop_seconds = self.L / self.sr
        self.spots = spots
        self.all_chans = sorted({c for s in spots for c in s["channels"]})
        self.max_layers = int(m["max_layers"])
        self.layer_loops = int(m["layer_loops"])
        self.layer_gain = float(m["layer_gain"])
        self.stems = Path(a["stems_dir"])
        self.samples = {}
        self.frame = 0
        self.origin = 0
        self.ref = (0, time.perf_counter())   # (frame, time it reaches the speaker)
        self.out_latency = 0.0
        self.in_latency = 0.0
        self.beds, self.layers, self.shots = [], [], []
        self.triggers = collections.deque(maxlen=128)
        self._k = np.arange(4096)
        self._id = 0
        self._rr = 0
        self.out_name = self.in_name = None
        self.out_level = 0.0
        self.out_ok = False
        self._fake = None
        self.mic = Mic(self.sr, m, self, emit)
        rc = cfg.get("room", {})
        self.amb = Mixer(self.sr)        # ambient on the main output (start/end of travelling sounds)
        self.room = RoomOut(rc.get("room_output", "main"), self.sr, self.block, a.get("hostapi", ""))
        self.room_delay = float(rc.get("room_latency_ms", 0)) / 1000

    # ---- devices -------------------------------------------------------------------------

    def start(self):
        api = self.cfg.get("hostapi", "WASAPI")
        extra = sd.WasapiSettings(auto_convert=True) if "wasapi" in api.lower() else None
        try:
            dev = pick_device(self.cfg.get("output_device", ""), "output", api)
            self.out = sd.OutputStream(device=dev, samplerate=self.sr, blocksize=self.block,
                                       channels=self.nch, dtype="float32", latency="low",
                                       callback=self._out_cb, extra_settings=extra)
            self.out.start()
            self.out_latency = float(self.out.latency)
            self.out_name = sd.query_devices(self.out.device)["name"]
            self.out_ok = True
            log.info("audio out: %s (%.0f ms)", self.out_name, self.out_latency * 1000)
        except Exception as e:
            log.error("audio output failed (%s); running on a silent clock", e)
            self._fake = threading.Thread(target=self._fake_clock, daemon=True)
            self._fake.start()
        try:
            dev = pick_device(self.cfg.get("input_device", ""), "input", api)
            self.inp = sd.InputStream(device=dev, samplerate=self.sr, blocksize=self.block,
                                      channels=1, dtype="float32", latency="low",
                                      callback=self._in_cb, extra_settings=extra)
            self.inp.start()
            self.in_latency = float(self.inp.latency)
            self.in_name = sd.query_devices(self.inp.device)["name"]
            self.mic.ok = True
            log.info("mic: %s (%.0f ms)", self.in_name, self.in_latency * 1000)
        except Exception as e:
            log.error("mic failed (%s); only the simulator can add sounds", e)
        self.room.start()

    def stop(self):
        self.room.stop()
        for s in ("out", "inp"):
            st = getattr(self, s, None)
            if st is not None:
                st.stop()
                st.close()
        self._fake = None

    def _fake_clock(self):
        buf = np.zeros((self.block, self.nch), np.float32)
        nxt = time.perf_counter()
        while self._fake is not None:
            self._out_cb(buf, self.block, None, None)
            nxt += self.block / self.sr
            time.sleep(max(0.0, nxt - time.perf_counter()))

    # ---- time ----------------------------------------------------------------------------

    def frame_at(self, t):
        """Transport frame that is audible at perf_counter time t."""
        f, tr = self.ref
        return f + (t - tr + self.offset_s) * self.sr

    def loop_frac(self, t):
        if not self.beds:
            return None
        f = self.frame_at(t)
        if f < self.origin:
            return None
        return ((f - self.origin) % self.L) / self.L

    def beat(self, t):
        """(beat index, phase 0..1) of what is audible at t, or None without a loop."""
        frac = self.loop_frac(t)
        if frac is None:
            return None
        x = frac * self.beats
        return int(x), x % 1.0

    def seconds_to_loop_end(self):
        frac = self.loop_frac(time.perf_counter())
        return 0.0 if frac is None else (1 - frac) * self.loop_seconds

    # ---- sounds --------------------------------------------------------------------------

    def sample(self, name):
        if name not in self.samples:
            self.samples[name] = load_wav(self.stems / f"{name}.wav", self.sr)
        return self.samples[name]

    def start_bed(self, name, gain=0.8, fade=0.0):
        if any(b.name == name and b.target > 0 for b in self.beds):
            return
        buf = self.sample(name)
        buf = np.pad(buf, ((0, max(0, self.L - len(buf))), (0, 0)))[: self.L]
        if not self.beds:
            self.origin = self.frame + self.block * 4
        v = Voice(buf, gain, fade, self.sr)
        v.name = name
        self.beds = self.beds + [v]

    def stop_beds(self, fade=1.0):
        for b in self.beds:
            b.ramp(0.0, fade)

    def oneshot(self, sound, gain=1.0, delay=0.0, chans=None):
        buf = self.sample(sound) if isinstance(sound, str) else sound
        v = Voice(buf, gain, 0.0, self.sr)
        v.start = self.frame + self.block * 2 + int(delay * self.sr)
        v.chans = chans or self.all_chans
        v.name = sound if isinstance(sound, str) else getattr(sound, "name", "sound")
        self.shots = self.shots + [v]

    def add_layer(self, buf, t, kind, spot=None):
        """Snap a captured sound to the loop grid and replay it every loop."""
        if not self.beds:
            return {"accepted": False, "reason": "no loop running"}
        steps = self.beats * (self.steps_per_beat if kind == "hit" else 1)
        stepf = self.L / steps
        rel = (self.frame_at(t) - self.origin) % self.L
        slot = int(round(rel / stepf)) % steps
        if any(ly.kind == kind and ly.slot == slot and ly.target > 0 for ly in self.layers):
            return {"accepted": False, "reason": "slot taken", "slot": slot}
        live = [ly for ly in self.layers if ly.target > 0]
        if len(live) >= self.max_layers:
            live[0].ramp(0.0, 1.0)
        if spot is None:
            sounding = [s for s in self.spots if s.get("channels")] or self.spots   # spots that have a speaker
            spot = sounding[self._rr % len(sounding)]
            self._rr += 1
        v = Voice(self._shape(buf), self.layer_gain, 0.0, self.sr)
        self._id += 1
        v.id, v.kind, v.slot, v.steps = self._id, kind, slot, steps
        v.offset = (int(round(slot * stepf)) - int(0.01 * self.sr)) % self.L
        v.spot = spot["id"]
        v.chans = spot["channels"]
        v.first = (self.frame - self.origin - v.offset) // self.L + 1
        self.layers = self.layers + [v]
        return {"accepted": True, "slot": slot, "steps": steps, "spot": v.spot, "id": v.id}

    def add_row(self, rec, spot=None):
        """A recorded loop from the table mic (RowRecorder): plays from now on at the same place in every loop."""
        if not self.beds:
            return {"accepted": False, "reason": "no loop running"}
        x = np.asarray(rec, np.float32)[: self.L]
        x = np.pad(x - float(np.mean(x)), (0, self.L - len(x)))
        x *= min(0.7 / (float(np.max(np.abs(x))) + 1e-6), 8.0)
        e = int(0.004 * self.sr)                       # tiny fades at the loop seam: no click
        x[:e] *= np.linspace(0, 1, e, dtype=np.float32)
        x[-e:] *= np.linspace(1, 0, e, dtype=np.float32)
        live = [ly for ly in self.layers if ly.target > 0]
        if len(live) >= self.max_layers:
            live[0].ramp(0.0, 1.0)
        if spot is None:
            sounding = [s for s in self.spots if s.get("channels")] or self.spots
            spot = sounding[self._rr % len(sounding)]
            self._rr += 1
        v = Voice(x, self.layer_gain, 0.05, self.sr)
        self._id += 1
        v.id, v.kind, v.slot, v.steps = self._id, "row", 0, 1
        v.offset = 0
        v.spot = spot["id"]
        v.chans = spot["channels"]
        v.first = (self.frame - self.origin) // self.L     # plays right away, sample-aligned to the loop
        v.env = waveform(x)
        self.layers = self.layers + [v]
        return {"accepted": True, "spot": v.spot, "id": v.id}

    def clear_layers(self, fade=0.3):
        for ly in self.layers:
            ly.ramp(0.0, fade)

    def fade_all(self, seconds=2.0):
        self.stop_beds(seconds)
        self.clear_layers(seconds)
        for s in self.shots:
            s.ramp(0.0, seconds)

    def housekeeping(self):
        for ly in self.layers:
            if ly.target > 0 and self.layer_age(ly) >= self.layer_loops:
                ly.ramp(0.0, 2 * self.loop_seconds)
        self.layers = [ly for ly in self.layers if not ly.silent]
        self.beds = [b for b in self.beds if not b.silent]
        self.shots = [s for s in self.shots if not (s.silent or self.frame > s.start + len(s.buf))]
        self.amb.prune()
        self.room.mixer.prune()

    # ---- ambient (room levels) -----------------------------------------------------------

    def ambient_bed(self, buf, gain, fade, where="room", loop=True):
        """A soundscape bed (loop=True) or a longer one-shot. where: "room" = the room output,
        "table" = the Top speaker."""
        mixer = self.amb if where == "table" else self.room.mixer
        return mixer.add(AVoice(buf, gain, fade, self.sr, loop=loop))

    def move_bed(self, voice, buf, gain, seconds, to="room"):
        """Let a bed travel to the other speaker: fade it out here, fade the same sound in there."""
        voice.ramp(0.0, seconds)
        return self.ambient_bed(buf, gain, seconds, where=to)

    # ---- traces (a jam kept for a later "rewind") -----------------------------------------

    def snapshot_layers(self):
        return [{"buf": ly.buf.copy(), "offset": ly.offset, "kind": ly.kind, "slot": ly.slot,
                 "steps": ly.steps, "spot": ly.spot, "chans": ly.chans, "env": getattr(ly, "env", None)}
                for ly in self.layers if ly.target > 0]

    def restore_layers(self, snap, gain=0.6):
        """Replay kept layers on the running loop (from the next loop on)."""
        for t in snap:
            v = Voice(t["buf"], gain, 0.5, self.sr)
            self._id += 1
            v.id, v.kind, v.slot, v.steps = self._id, t["kind"], t["slot"], t["steps"]
            v.offset, v.spot, v.chans = int(t["offset"]) % self.L, t["spot"], list(t["chans"])
            v.env = t.get("env")
            v.first = (self.frame - self.origin - v.offset) // self.L + 1
            self.layers = self.layers + [v]

    def ambient_shot(self, buf, gain, travel=None, name=None):
        """A weather accent on the main output. travel "table>room" / "room>table" moves it to / from the room
        output (equal-power crossfade over its length); with only the main output it pans left/right instead."""
        buf = buf if buf.ndim == 2 else np.column_stack([buf, buf])
        if not travel:
            return [self.amb.add(AVoice(buf, gain, 0.0, self.sr))]
        x = np.linspace(0.0, 1.0, len(buf), dtype=np.float32)
        a, b = np.cos(x * np.pi / 2), np.sin(x * np.pi / 2)
        if travel.startswith("room"):
            a, b = b, a
        if self.room.kind == "main":    # one output: pan left/right
            mono = buf.mean(axis=1)
            return [self.amb.add(AVoice(np.column_stack([mono * a, mono * b]).astype(np.float32), gain, 0.0, self.sr))]
        delay = int(self.room_delay * self.sr)     # the main part waits for the slower room output
        return [self.amb.add(AVoice(buf, gain, 0.0, self.sr, env=a, delay=delay)),
                self.room.mixer.add(AVoice(buf, gain, 0.0, self.sr, env=b))]

    def layer_age(self, ly):
        return (self.frame - self.origin - ly.offset) // self.L - ly.first

    def take_triggers(self, now):
        out = []
        while self.triggers and self.triggers[0][0] <= now:
            out.append(self.triggers.popleft())
        return out

    def _shape(self, buf):
        x = np.asarray(buf, np.float32)
        if x.ndim == 2:
            x = x.mean(axis=1)
        x = x[: self.L // 2] - float(np.mean(x))
        peak = float(np.max(np.abs(x))) + 1e-6
        x *= min(0.7 / peak, 8.0)
        a, r = int(0.002 * self.sr), min(int(0.025 * self.sr), len(x) // 2)
        x[:a] *= np.linspace(0, 1, a, dtype=np.float32)
        if r:
            x[-r:] *= np.linspace(1, 0, r, dtype=np.float32)
        return x

    def sim_sound(self, kind):
        """Stand-in sounds for the web simulator."""
        if kind == "hit":
            return self.sample("SFX_Tap_Player").mean(axis=1)
        n = int(1.4 * self.sr)
        t = np.arange(n) / self.sr
        f = 196.0 * (1 + 0.006 * np.sin(2 * np.pi * 5 * t))
        ph = 2 * np.pi * np.cumsum(f) / self.sr
        x = 0.6 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
        env = np.minimum(1, t / 0.08) * np.minimum(1, (t[-1] - t) / 0.3)
        return (x * env * 0.5).astype(np.float32)

    # ---- callbacks (audio threads) -------------------------------------------------------

    def _route(self, out, s, chans):
        if s.ndim == 2:
            if len(chans) == 2:
                out[:, chans[0]] += s[:, 0]
                out[:, chans[1]] += s[:, 1]
                return
            s = s.mean(axis=1)
        for c in chans:
            out[:, c] += s

    def _out_cb(self, out, n, tinfo, status):
        now = time.perf_counter()
        f0 = self.frame
        self.ref = (f0, now + self.out_latency)
        out.fill(0.0)
        k = self._k[:n] if n <= len(self._k) else np.arange(n)
        o, L = self.origin, self.L
        for b in self.beds:
            g = b.gains(n)
            if f0 + n <= o:
                continue
            s = _scale(b.buf[(f0 - o + k) % L], g)
            if f0 < o:
                s[: o - f0] = 0
            self._route(out, s, self.all_chans)
        for ly in self.layers:
            g = ly.gains(n)
            pos = f0 - o - ly.offset + k
            r = pos % L
            m = (r < len(ly.buf)) & (pos // L >= ly.first)
            if not m.any():
                continue
            s = np.zeros(n, np.float32)
            s[m] = ly.buf[r[m]]
            self._route(out, _scale(s, g), ly.chans)
            z = np.flatnonzero(m & (r == 0))
            if z.size:
                self.triggers.append((self.ref[1] + z[0] / self.sr, ly.spot, ly.kind))
        for sh in self.shots:
            g = sh.gains(n)
            r = f0 - sh.start + k
            m = (r >= 0) & (r < len(sh.buf))
            if not m.any():
                continue
            s = np.zeros((n, sh.buf.shape[1]) if sh.buf.ndim == 2 else n, np.float32)
            s[m] = sh.buf[r[m]]
            self._route(out, _scale(s, g), sh.chans)
        amb = self.amb.mix(n)
        if self.room.kind == "main":
            amb += self.room.mixer.mix(n)
        self._route(out, amb, self.all_chans)
        out *= self.master
        np.clip(out, -1.0, 1.0, out=out)
        self.out_level = max(float(np.sqrt(np.mean(out * out))), self.out_level * 0.9)
        self.frame = f0 + n

    def _in_cb(self, indata, n, tinfo, status):
        t0 = time.perf_counter() - self.in_latency - n / self.sr
        self.mic.process(indata[:, 0].copy(), t0)
