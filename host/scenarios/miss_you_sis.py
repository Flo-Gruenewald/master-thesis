"""Scenario 3 · I Miss You, Sis (the tactile postcard). Day 455, Friday late evening.

A postcard from Earth arrives (web page "Postcard from Earth" or MQTT in/postcard). Lena is in Rome: holding
the postcard brings her evening piazza into the habitat — clearly somewhere else than the room's season.
arrived   the table breathes Earth-teal, a soft arrival sound; the card itself buzzes twice (postcard/arrived)
rome      held: the piazza fades in as far as the card is held (its intensity 0..1, in/postcard/touch):
          voices of the square, the fountain close at the table, swallows in the room, now and then a Vespa
          crosses the room; golden evening light. Letting go: Rome fades back into the habitat.
lena      held fully: the church bells ring once, then Lena's voice (s3/lena_rome, if the file is there)
home      the card lies still for a while (or was never picked up): everything settles back

The content of the message is never shown, only felt. No microphone here.
"""
import random
import time

import numpy as np

from core.scenario import Scenario as Base

PIAZZA = {"piazza": ("s3/rome/piazza", 0.30, "room"), "fountain": ("s3/rome/fountain", 0.24, "table"),
          "swallows": ("s3/rome/swallows", 0.16, "room")}       # sound, gain at full hold, where
GOLD = np.array([1.0, 0.62, 0.30])      # golden hour in Rome
FADE_IN, FADE_OUT = 0.6, 0.18          # (before 20.10) how fast Rome followed the card
# 20.10.2026 (Flo): pressing the card opens the photo of Lena and Alice on the clock (iPad); Rome fades in slowly,
# stays, and everything is gone 30 s after the press.
SHOW_S, RISE_S, FALL_S = 30.0, 10.0, 6.0
VOICE = "s3/lena_rome"                 # Flo records it (ElevenLabs); without the file: bells only


class Scenario(Base):
    name = "miss_you_sis"
    title = "I Miss You, Sis"
    order = 3
    hints = {"arrived": "A postcard from Earth. Pick it up and hold it", "rome": "Hold it: Lena's evening in Rome",
             "lena": "Lena", "home": "Back in the habitat"}
    room_duck = 0.0               # evening: the room goes quiet and dark around the postcard
    starts_on_presence = False    # it starts when a postcard arrives, not when someone walks by

    def __init__(self, host):
        super().__init__(host)
        self.held, self.card_i, self.sim_hold = False, 0.0, False
        host.bus.on("in/postcard/touch", self.on_touch)

    def on_touch(self, sub, p):
        """From the postcard (Wi-Fi/MQTT): {"held": 0|1, "i": 0..1}."""
        if isinstance(p, dict):
            self.held, self.card_i, self.touch_t = bool(p.get("held")), float(p.get("i", 0)), time.monotonic()

    def command(self, c, v):
        if c == "postcard_hold":                     # web page stand-in for the card
            self.sim_hold = not self.sim_hold if v is None else bool(v)

    def ui(self):
        return {"held": self.held or self.sim_hold, "rome": round(getattr(self, "h", 0.0), 2),
                "photo": bool(getattr(self, "photo", False))}

    def _hold(self, dt):
        """Target 0..1 from the card (or the web page's stand-in, which ramps like the card does)."""
        if self.sim_hold:
            self.sim_i = min(1.0, getattr(self, "sim_i", 0.0) + dt / 4.0)
            return self.sim_i
        self.sim_i = 0.0
        if time.monotonic() - getattr(self, "touch_t", 0.0) > 3.0:     # no news from the card: not held
            self.held = False
        return max(self.card_i, 0.25) if self.held else 0.0

    async def run(self):
        a, li, c = self.audio, self.light, self.cfg
        table = [s["id"] for s in self.host.spots if s.get("moment")] or None
        self.h, self.sim_hold, self.voices = 0.0, False, {}
        ever, bells_done, still_t, t0 = 0.0, False, None, time.monotonic()

        # ---- a postcard has arrived ----------------------------------------------------
        self.moment("arrived")
        li.ground(self.color("dawn"), 0.05, fade=3.0, breath=0.0)
        a.oneshot(self.sound("s3/arrive"), gain=0.3)
        self.host.bus.publish("postcard/arrived", 1)                    # the card buzzes twice
        next_vespa, last = time.monotonic() + 6.0, time.monotonic()
        next_pulse = time.monotonic() + 1.0
        press_t, self.photo = None, False
        while True:
            await self.sleep(0.1)
            now = time.monotonic()
            dt, last = now - last, now
            if press_t is None:
                auto = now - t0 >= float(c.get("auto_press_s", 20))   # Wizard of Oz: 20 s after arrival anyway
                if self._hold(dt) > 0.05 or auto:          # the card is pressed: photo + Rome
                    press_t, self.photo = now, True
                    self.moment("rome")
                    self.host.event({"type": "note", "text": ("20 s passed" if auto and self._hold(dt) <= 0.05 else "the card is pressed")
                                     + ": the photo of Lena and Alice opens; Rome fades in"})
                elif now - t0 > 240:                      # never picked up
                    break
                elif now >= next_pulse:                   # not picked up yet: the table pulses
                    li.accent(self.color("warm"), 0.55, seconds=1.6, mode="tint", name="postcard")
                    next_pulse = now + 2.8
                target = 0.0
            else:
                el = now - press_t
                if el >= SHOW_S:
                    break
                target = min(1.0, el / RISE_S) if el < SHOW_S - FALL_S else max(0.0, (SHOW_S - el) / FALL_S)
            self.h = target
            ever = max(ever, self.h)
            self._mix(table)
            if self.h > 0.4 and now >= next_vespa:                       # a Vespa crosses the room
                a.ambient_shot(self.sound("s3/rome/vespa"), 0.35 * self.h, random.choice(["room>table", "table>room"]))
                next_vespa = now + random.uniform(15, 25)
            if self.h > 0.95 and not bells_done:                         # Rome in full: bells, then Lena
                bells_done = True
                self.moment("lena")
                a.ambient_shot(self.sound("s3/rome/bells"), 0.45)
                if self.has_sound(VOICE):
                    a.oneshot(self.sound(VOICE), gain=float(c.get("voice_gain", 1.0)), delay=4.0)
                self.host.event({"type": "note", "text": "Rome: the bells" + (", then Lena" if self.has_sound(VOICE) else "")})
        self.photo = False

        # ---- home ------------------------------------------------------------------------
        self.moment("home")
        for v in self.voices.values():
            v.ramp(0.0, 4.0)
        li.spotlight(self.color("earth"), 0.0, fade=3.0)
        li.release(fade=8.0)
        await self.sleep(8.0)

    def _mix(self, table):
        h, li = self.h, self.light
        for name, (rel, gain, where) in PIAZZA.items():
            v = self.voices.get(name)
            if v is None:
                if h <= 0.01:
                    continue
                v = self.voices[name] = self.bed(rel, 0.0, fade=0.1, where=where)
            if abs(v.target - gain * h) > 1e-3:
                v.ramp(gain * h, 0.3)
        breathe = 0.5 + 0.5 * np.sin(time.monotonic() * 2.2)              # Earth-teal waits, gold arrives
        li.spotlight(self.color("earth"), (0.08 + 0.27 * breathe) * (1 - h), width=0.25, fade=0.3)
        li.ground(GOLD, 0.05 + 0.45 * h, fade=0.3, breath=0.0)

    def on_onset(self, ev):
        pass                            # no microphone in this scenario
