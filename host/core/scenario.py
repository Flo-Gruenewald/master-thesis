"""Base class for scenarios. A scenario only describes what happens when, using the core:
self.audio (beds, layers, one-shots), self.light (ground / accent / spotlight / pulse),
self.host (presence, moment, events). Scenarios 2 and 3 are new files next to morning_jam.py.
"""
import asyncio
import time
from pathlib import Path

from .audio import load_wav
from .light import hex_rgb


class Scenario:
    name = "base"
    title = "Scenario"
    order = 9                 # position on the web page
    hints = {}                # moment → a short line for visitors / the operator
    room_duck = None          # Ground level during this moment (None = room default, 0 = silent/dark)
    starts_on_presence = True

    def __init__(self, host):
        self.host = host
        self.audio = host.audio
        self.light = host.light
        self.cfg = host.cfg.get(self.name, {})
        self.colors = {k: hex_rgb(v) for k, v in host.cfg["colors"].items()}
        self.idle_level = host.cfg["light"]["idle_level"]
        self.stems = Path(host.cfg["audio"]["stems_dir"])
        self._voices = []
        self._tap = asyncio.Event()
        self.waiting_tap = False

    # ---- helpers -------------------------------------------------------------------------

    def sound(self, rel):
        """A sound from Sounds/ (e.g. "s3/lena_01"; .wav, else .mp3), resampled and cached."""
        if rel not in self.audio.samples:
            f = self.stems / f"{rel}.wav"
            self.audio.samples[rel] = load_wav(f if f.exists() else self.stems / f"{rel}.mp3", self.audio.sr)
        return self.audio.samples[rel]

    def has_sound(self, rel):
        return any((self.stems / f"{rel}.{ext}").exists() for ext in ("wav", "mp3"))

    def bed(self, rel, gain, fade=2.0, where="room", loop=True):
        """A scenario-owned ambient sound; faded out automatically when the scenario ends."""
        v = self.audio.ambient_bed(self.sound(rel), gain, fade, where=where, loop=loop)
        v.name, v.where = rel.split("/")[-1], where
        self._voices.append(v)
        return v

    def move(self, voice, rel, gain, seconds, to="room"):
        v = self.audio.move_bed(voice, self.sound(rel), gain, seconds, to=to)
        v.name, v.where = rel.split("/")[-1], to
        self._voices.append(v)
        return v

    def cleanup(self, fade=2.0):
        """Called by the host whenever a run ends or is stopped."""
        for v in self._voices:
            v.ramp(0.0, fade)
        self._voices = []
        self.waiting_tap = False

    async def wait_tap(self, timeout):
        """Wait for a tap on the table (any sound the mic notices, or Tap in the simulator).
        Returns True if someone tapped, False after timeout seconds."""
        self._tap.clear()
        self.waiting_tap = True
        try:
            await asyncio.wait_for(self._tap.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False
        finally:
            self.waiting_tap = False

    def color(self, key):
        return self.colors[key]

    def moment(self, name):
        self.host.set_moment(name)

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)

    def now(self):
        return time.monotonic()

    # ---- hooks ---------------------------------------------------------------------------

    async def run(self):
        """One pass of the scenario. Cancelled when someone presses Stop."""

    def wind_down(self):
        """Stop pressed while running. Return True if the scenario ends itself gently (then the host waits);
        False = the host cuts it at once."""
        return False

    def idle(self, fade=3.0):
        """Between runs: hand the light back to the room program (Ground: circadian day)."""
        self.light.spotlight(self.color("warm"), 0.0, fade=fade)
        self.light.release(fade=fade)

    def on_onset(self, ev):
        """Any sound the mic notices: a small ripple, even when idle (attentive)."""
        self.light.pulse(None, self.color("peach"), amp=0.15 + 0.35 * ev.get("strength", 0.5), decay=5.0)
        if self.waiting_tap and ev.get("strength", 1.0) >= self.host.cfg["mic"].get("tap_min_strength", 0.25):
            self._tap.set()
            self.host.event({"type": "tap", "scenario": self.name})

    def on_sound(self, ev):
        """A captured hit/hum. Return a dict like audio.add_layer() does."""
        return {"accepted": False, "reason": "not listening"}

    def on_row(self, ev):
        """A recorded loop became a row (table mic). Return a result dict like on_sound."""
        return {"accepted": False, "reason": "not listening"}

    def on_layer_play(self, t, spot, kind):
        """A layer starts playing (each loop)."""
