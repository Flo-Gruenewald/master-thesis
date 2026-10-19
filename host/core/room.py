"""Room program: the GROUND and MIDDLE levels, independent of any scenario (top-down approach).

GROUND  a circadian day on every light, plus a quiet soundscape bed from the room speaker.
        The day is anchored to the crew's wake and sleep times (the same in every season) and follows
        the indoor-light recommendations of Brown et al. 2022 (PLOS Biol): a dawn simulation in the last
        30 min before waking (Thompson et al. 2014), a blue-enriched morning like the ISS "phase shift"
        mode and the Concordia winter study (Najjar et al. 2014), neutral white by day, warm and dim
        ("pre-sleep", <= 2700 K, no extra blue) in the 3 h before sleep, near-dark at night.
        The season changes what the body reads as photoperiod without moving the clock: the visible
        dusk (a long golden evening in summer, an early dim one in winter — Wehr 2001), the day's
        peak level and colour, and how strong the morning blue is (strongest in the dark season).
MIDDLE  every few minutes a weather accent: a light event on the middle spots (a passing cloud,
        a sun ray, rain-grey, lightning) and/or a short sound that travels between the speakers
        (a bird, a bee, a cat, a gust, thunder).
When a TOP moment runs (a scenario), Ground dims (duck) and Middle pauses.

Sounds: stems/ground/<name>.wav and stems/accent/<name>.wav if present (e.g. the ElevenLabs
files), otherwise procedural placeholders from synth.py.
"""
import datetime as dt
import logging
import random
import time
from pathlib import Path

import numpy as np

from . import synth
from .audio import load_wav
from .light import cct_rgb, hex_rgb  # noqa: F401  (cct_rgb is part of this module's API)

log = logging.getLogger("room")

# Weather accents: light (mode, colour key or hex, amp, seconds) and sound (name, travel)
ACCENTS = {
    "sun_ray":     {"light": ("glow", "#FFD9A8", 0.45, 9.0, 0.18), "sound": None},
    "cloud":       {"light": ("shade", None, 0.75, 12.0, 0.25), "sound": None},
    "bird_cross":  {"light": ("glow", "#F2EAE3", 0.35, 2.5, 0.08), "sound": ("bird_cross", "table>room")},
    "bee_pass":    {"light": ("glow", "#F2AD9D", 0.25, 3.0, 0.06), "sound": ("bee_pass", "room>table")},
    "cat_meow":    {"light": ("glow", "#EB8F7A", 0.5, 3.0, 0.2), "sound": ("cat_meow", None)},
    "wind_gust":   {"light": ("glow", "#9FB8C4", 0.5, 6.0, 0.35), "sound": ("wind_gust", "table>room")},
    "rain_pass":   {"light": ("tint", "#5A86B0", 0.65, 10.0, 0.0), "sound": ("rain_pass", None)},
    "thunder_far": {"light": ("flash", "#DDE6FF", 0.7, 1.2, 0.0), "sound": ("thunder_far", None)},
}

# circadian accent colour, in LED terms (not screen hex: on an RGBW strip a screen coral turns pink, because the
# white chip takes the shared part). Warm colours keep blue at ~0 so the white chip stays off.
LED_AMBER = np.array([1.0, 0.55, 0.06])      # the day: warm amber, no white
LED_ORANGE = np.array([1.0, 0.30, 0.08])     # evening / pre-sleep: Mars Rust (brown-red, a touch of orange)
LED_RUST = np.array([0.80, 0.20, 0.06])      # night: deep rust
LED_BLUE = np.array([0.18, 0.62, 1.0])       # the blue morning (melanopic boost)


def circadian_tint(k, blue=0.0):
    """The accent glow's colour: amber by day, orange from the golden evening on (≤ 3500 K), deep rust at night
    (≤ 2200 K); during the blue morning it leans towards blue in proportion to the room's blue boost."""
    if k >= 3600:
        c = LED_AMBER.copy()
    elif k >= 2700:
        t = smoothstep((k - 2700) / 900)
        c = LED_ORANGE * (1 - t) + LED_AMBER * t
    else:
        t = smoothstep((k - 2000) / 700)
        c = LED_RUST * (1 - t) + LED_ORANGE * t
    b = min(1.0, max(0.0, blue) * 1.4)
    return c * (1 - b) + LED_BLUE * b


# season colours (booklet 4.3): tint of the accent glow under the table
SEASON_TINT = {"summer": "#F2AD9D", "autumn": "#E37156", "winter": "#A14530", "spring": "#76DBD8"}

# blue added on top of the white light in the morning: the strip's blue LED (+ a little green)
# sits close to the melanopsin peak (~480 nm)
MELANOPIC = np.array([0.0, 0.3, 1.0])

DEFAULT_SEASONS = {
    "summer": {"peak_k": 6500, "dawn_h": 6.5, "dusk_h": 21.0, "peak_level": 0.55, "night_level": 0.04,
               "evening_level": 0.3, "blue": 0.5,
               "day_beds": ["crickets"], "night_beds": ["crickets"],
               "accents": ["sun_ray", "bird_cross", "bee_pass", "cloud", "thunder_far"]},
    "autumn": {"peak_k": 5000, "dawn_h": 6.5, "dusk_h": 19.0, "peak_level": 0.45, "night_level": 0.04,
               "evening_level": 0.2, "blue": 0.75,
               "day_beds": ["rain"], "night_beds": ["rain", "fire"],
               "accents": ["wind_gust", "rain_pass", "cloud", "cat_meow", "thunder_far"]},
    "winter": {"peak_k": 4500, "dawn_h": 6.5, "dusk_h": 17.5, "peak_level": 0.4, "night_level": 0.04,
               "evening_level": 0.14, "blue": 1.0,
               "day_beds": ["room_tone"], "night_beds": ["room_tone"],
               "accents": ["wind_gust", "cloud", "cat_meow"]},
    "spring": {"peak_k": 6000, "dawn_h": 6.5, "dusk_h": 20.0, "peak_level": 0.5, "night_level": 0.04,
               "evening_level": 0.24, "blue": 0.65,
               "day_beds": ["rain"], "night_beds": ["room_tone"],
               "accents": ["bird_cross", "rain_pass", "sun_ray", "cat_meow", "cloud"]},
}


# Earth seasons by date (northern hemisphere, astronomical): the room's calendar follows the mission
SEASON_START = [(3, 20, "spring"), (6, 21, "summer"), (9, 22, "autumn"), (12, 21, "winter")]


def earth_season(d):
    s = "winter"
    for m, day, name in SEASON_START:
        if (d.month, d.day) >= (m, day):
            s = name
    return s


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class Room:
    def __init__(self, host):
        self.host = host
        self.audio = host.audio
        self.light = host.light
        c = host.cfg.get("room", {})
        self.cfg = c
        self.seasons = {**DEFAULT_SEASONS, **host.cfg.get("seasons", {})}
        self.season = c.get("season", "summer")
        self.day_minutes = float(c.get("day_minutes", 0))
        self.sleep_h = float(c.get("sleep_h", 22.5))   # crew bedtime: the evening wind-down counts back from here
        self.offset_h = float(c.get("clock_offset_h", 0))
        self.ground_on = bool(c.get("ground", True))
        self.middle_on = bool(c.get("middle", True))
        self.gap = c.get("accent_every_s", [90, 240])
        self.gap_demo = c.get("accent_every_demo_s", [25, 60])
        self.duck_level = float(c.get("duck_level", 0.6))
        self.bed_gain = float(c.get("soundscape_gain", 0.25))
        self.accent_gain = float(c.get("accent_gain", 0.6))
        self.accent_colour = str(host.cfg.get("light", {}).get("accent_colour", "season"))   # expand | circadian | season
        self.stems = Path(host.cfg["audio"]["stems_dir"])
        self.top = False
        self.top_level = self.duck_level
        self._demo_t0 = time.monotonic()
        self._demo_h0 = self._real_h()
        self.beds = {}            # name → voice
        self.bed_names = []
        self.next_accent = time.monotonic() + random.uniform(20, 40)
        self.last_accent = None
        self.cache = {}
        self.playing = []         # accent voices currently sounding
        self.k = 2700
        self.level = 0.0
        self.blue = 0.0
        # mission calendar: launch (opposition class, April 2033) and the room's simulated date.
        # The date moves on when the room's clock passes midnight (also in the simulated speeds);
        # entering a new Earth season turns the room's season.
        # In real time the room's date is today in the mission year (2 Oct → 2 Oct 2033; days before
        # the launch fall into 2034) and the season follows it; a date set by hand holds until "now".
        self.launch = dt.date.fromisoformat(str(c.get("mission_launch", "2033-04-15")))
        self.follow_real = not c.get("date")
        self.date = self._mission_today() if self.follow_real else dt.date.fromisoformat(str(c["date"]))
        if self.follow_real and earth_season(self.date) in self.seasons:
            self.season = earth_season(self.date)
        self._last_h = None

    # ---- clock ---------------------------------------------------------------------------

    def _real_h(self):
        lt = time.localtime()
        return lt.tm_hour + lt.tm_min / 60 + lt.tm_sec / 3600

    def hour(self):
        if self.day_minutes > 0:
            h = self._demo_h0 + (time.monotonic() - self._demo_t0) / (self.day_minutes * 60) * 24
        else:
            h = self._real_h()
        return (h + self.offset_h) % 24

    def set_hour(self, h):
        """Jump the room's clock to h (keeps the speed and the date)."""
        if self.day_minutes > 0:
            self._demo_t0, self._demo_h0, self.offset_h = time.monotonic(), float(h), 0.0
        else:
            self.offset_h = (float(h) - self._real_h()) % 24
        self._last_h = None

    # ---- mission calendar ----------------------------------------------------------------

    def _mission_today(self):
        """Today's day and month in the mission (launch year; before the launch day: the year after)."""
        t, y = dt.date.today(), self.launch.year
        try:
            d = t.replace(year=y)
        except ValueError:                     # 29 February
            d = dt.date(y, 2, 28)
        return d if d >= self.launch else d.replace(year=y + 1, day=min(d.day, 28) if d.month == 2 else d.day)

    def _first_date(self, season):
        """The first day of the mission that falls in this Earth season (the launch day if none)."""
        d = self.launch
        for _ in range(700):
            if earth_season(d) == season:
                return d
            d += dt.timedelta(days=1)
        return self.launch

    def set_date(self, v):
        """Jump to a date ("2033-09-01") or a mission day (140); the season follows the date."""
        s = str(v).strip()
        self.date = self.launch + dt.timedelta(days=int(s) - 1) if s.isdigit() else dt.date.fromisoformat(s)
        self.follow_real = False
        self._last_h = None
        self.set_season(earth_season(self.date))

    def _new_day(self):
        before = earth_season(self.date)
        self.date += dt.timedelta(days=1)
        now = earth_season(self.date)
        if now != before and now in self.seasons:
            self.set_season(now)
            self.host.event({"type": "note", "text": f"day {self.mission_day()}: {now} begins"})

    def mission_day(self):
        return (self.date - self.launch).days + 1

    def set_speed(self, minutes):
        h = self.hour()
        self.day_minutes = max(0.0, float(minutes))
        self.offset_h = 0.0
        self._demo_t0, self._demo_h0 = time.monotonic(), h
        if self.day_minutes == 0:
            self.offset_h = (h - self._real_h()) % 24
            self.follow_real = True
        self._last_h = None

    # ---- GROUND --------------------------------------------------------------------------

    def day(self, h, season=None):
        """(level 0..1, colour temperature K, morning blue 0..1) at hour h.

        night ─ dawn simulation (30 min before wake) ─ post-sleep (first hour: light ramps up against
        sleep inertia) ─ blue-enriched morning ─ neutral day ─ the
        season's dusk (golden evening) ─ pre-sleep (3 h before bed: <= 2700 K, no blue) ─ night."""
        s = self.seasons[season or self.season]
        wake, dusk, sleep = s["dawn_h"], s["dusk_h"], self.sleep_h
        nl, peak, ev = s["night_level"], s["peak_level"], s.get("evening_level", 0.2)
        rise = smoothstep((h - (wake - 0.5)) / 1.5)          # dawn simulation → full light 1 h after waking
        sunset = smoothstep((h - (dusk - 1.0)) / 1.5)        # the season's dusk
        bed = smoothstep((h - (sleep - 1.0)) / 1.0)          # last hour before sleep → night
        span = max(1.0, dusk - 1.0 - 13.0)
        afternoon = smoothstep((h - 13.0) / span)            # the afternoon slowly warms and softens
        level = nl + (peak * (1 - 0.15 * afternoon) - nl) * rise
        level = level * (1 - sunset) + ev * sunset
        level = level * (1 - bed) + nl * bed
        k = 1800 + (s["peak_k"] - (s["peak_k"] - 4000) * afternoon - 1800) * rise
        k = k * (1 - sunset) + 2700 * sunset
        presleep = smoothstep((h - (sleep - 3.0)) / 0.75)    # from 3 h before bed: warm only
        k = min(k, 6500 - (6500 - 2700) * presleep)
        k = k * (1 - bed) + 1800 * bed
        blue = s.get("blue", 0.0) * rise * (1 - smoothstep((h - (wake + 3.0)) / 3.5)) * (1 - presleep)
        return level, k, blue

    def day_light(self, h):
        """(level 0..1, colour temperature K) at hour h for the current season."""
        level, k, _ = self.day(h)
        return level, k

    def _sound(self, kind, name):
        key = (kind, name)
        if key not in self.cache:
            f = self.stems / kind / f"{name}.wav"
            sr = self.audio.sr
            if f.exists():
                self.cache[key] = load_wav(f, sr)
            else:
                gen = (synth.BEDS if kind == "ground" else synth.ACCENTS).get(name)
                self.cache[key] = gen(sr) if gen else None
        return self.cache[key]

    def _update_beds(self, h, fade=6.0):
        s = self.seasons[self.season]
        day = s["dawn_h"] <= h < s["dusk_h"]   # bed switches with the season's light, not the clock
        want = (s["day_beds"] if day else s["night_beds"]) if self.ground_on else []
        gain = self.bed_gain * (self.top_level if self.top else 1.0)
        for name in list(self.beds):
            if name not in want:
                self.beds.pop(name).ramp(0.0, fade)
        for name in want:
            if name in self.beds:
                v = self.beds[name]
                if abs(v.target - gain) > 1e-3:
                    v.ramp(gain, fade / 2)
                continue
            buf = self._sound("ground", name)
            if buf is not None:
                v = self.beds[name] = self.audio.ambient_bed(buf, gain, fade)
                v.name = name
        self.bed_names = list(self.beds)

    def accent_loudness(self):
        """How loud the playing accent sounds are right now (0..1), for the accent light."""
        lv = 0.0
        for v in self.playing:
            if v.done or v.pos < 0:
                continue
            seg = v.buf[v.pos:v.pos + 960]
            if len(seg):
                lv = max(lv, float(np.abs(seg).mean()) * v.g)
        return min(1.0, lv * 6.0)

    # ---- MIDDLE --------------------------------------------------------------------------

    def accent(self, name=None):
        """Trigger a weather accent now (name None = a random one for the season)."""
        s = self.seasons[self.season]
        name = name or random.choice(s["accents"])
        a = ACCENTS.get(name)
        if not a:
            return None
        if a["light"]:
            mode, col, amp, sec, width = a["light"]
            rgb = hex_rgb(col) if col else np.zeros(3)
            if mode == "glow":
                rgb = rgb * max(0.4, self.level * 1.6)   # accents scale with the time of day
            self.light.accent(rgb, amp, sec, reverse=random.random() < 0.5, mode=mode, width=width or 0.12, name=name)
        if a["sound"]:
            sname, travel = a["sound"]
            buf = self._sound("accent", sname)
            if buf is not None:
                if travel and random.random() < 0.5:
                    travel = ">".join(reversed(travel.split(">")))
                for v in self.audio.ambient_shot(buf, self.accent_gain, travel, name=sname) or []:
                    v.name = name
                self.playing = [p for p in self.playing if not p.done] + \
                    [v for v in (self.audio.room.mixer.voices + self.audio.amb.voices) if v.name == name]
        self.last_accent = {"name": name, "at": time.time()}
        self.host.event({"type": "accent", "name": name})
        log.info("accent: %s", name)
        return name

    def _schedule(self):
        lo, hi = self.gap_demo if self.day_minutes > 0 else self.gap
        self.next_accent = time.monotonic() + random.uniform(lo, hi)

    # ---- control -------------------------------------------------------------------------

    def set_top(self, active, level=None):
        """A Top moment starts/ends: duck Ground (to level, default duck_level; 0 = silent and
        dark, for scenarios that bring their own atmosphere), pause Middle."""
        self.top = active
        self.top_level = self.duck_level if level is None else float(level)
        self.light.set_duck(self.top_level if active else 1.0, fade=2.0 if active else 4.0)
        if not active:
            self._schedule()
        self._update_beds(self.hour(), fade=3.0)

    def set_season(self, name):
        if name in self.seasons:
            self.season = name
            self._update_beds(self.hour(), fade=4.0)

    def tick(self):
        h = self.hour()
        if self.follow_real:                                        # real time: the real calendar
            d = self._mission_today()
            if d != self.date:
                self.date = d
                if earth_season(d) != self.season and earth_season(d) in self.seasons:
                    self.set_season(earth_season(d))
        elif self._last_h is not None and h < self._last_h - 12:   # simulated / set date: next day at midnight
            self._new_day()
        self._last_h = h
        self.level, self.k, self.blue = self.day(h)
        if self.accent_colour == "circadian":   # blue-tinted by day (alerting), orange in the evening (no blue)
            self.light.accent_tint = circadian_tint(self.k, self.blue)
        else:
            self.light.accent_tint = hex_rgb(SEASON_TINT.get(self.season, "#F2EAE3"))
        if self.ground_on:
            self.light.room_ground((cct_rgb(self.k) + MELANOPIC * self.blue) * self.level, fade=2.0)
        else:
            self.light.room_ground(np.zeros(3), fade=2.0)
        self._update_beds(h)
        if self.middle_on and not self.top and time.monotonic() >= self.next_accent:
            self.accent()
            self._schedule()

    def now(self):
        """Back to the real clock (speed: real time)."""
        self.set_speed(0)
        self.offset_h = 0.0
        self.follow_real = True
        self._last_h = None

    def sounds(self):
        """What GROUND and MIDDLE play right now: [{name, level}] (level = current gain)."""
        ground = [{"name": n, "level": round(v.g, 3)} for n, v in self.beds.items()]
        fading = [v for v in self.audio.room.mixer.voices
                  if v.loop and not v.done and v.name and v.name not in self.beds and v.g > 0.001
                  and v not in self.host.scenario_voices()]
        ground += [{"name": v.name, "level": round(v.g, 3), "fading": True} for v in fading]
        self.playing = [v for v in self.playing if not v.done]
        middle = {}
        for v in self.playing:
            pos = max(0, v.pos) / max(1, len(v.buf))
            middle[v.name] = {"name": v.name, "level": round(v.g, 3), "progress": round(min(1.0, pos), 3)}
        return {"ground": ground, "middle": list(middle.values())}

    def curve(self, n=96, season=None):
        """A season's day: n samples of [level 0..1, colour temperature K, morning blue 0..1] over 24 h."""
        out = []
        for i in range(n):
            lv, k, b = self.day(24 * i / n, season)
            out.append([round(lv, 3), int(k), round(b, 3)])
        return out

    def state(self):
        h = self.hour()
        s = self.seasons[self.season]
        return {
            "dawn_h": s["dawn_h"], "dusk_h": s["dusk_h"], "peak_k": s["peak_k"], "sleep_h": self.sleep_h,
            "curve": self.curve(), "blue": round(self.blue, 3),
            "date": self.date.isoformat(), "mission_day": self.mission_day(), "launch": self.launch.isoformat(),
            "date_real": self.follow_real,
            "real_hour": round(self._real_h(), 2),
            "season": self.season, "seasons": list(self.seasons),
            "season_info": {n: {"peak_k": v["peak_k"], "dawn_h": v["dawn_h"], "dusk_h": v["dusk_h"],
                                "day_beds": v["day_beds"], "night_beds": v["night_beds"], "accents": v["accents"]}
                            for n, v in self.seasons.items()},
            "hour": round(h, 2), "clock": f"{int(h):02d}:{int(h % 1 * 60):02d}",
            "day_minutes": self.day_minutes, "k": int(self.k), "level": round(self.level, 3),
            "ground": self.ground_on, "middle": self.middle_on, "top": self.top,
            "beds": self.bed_names,
            "accents": self.seasons[self.season]["accents"], "all_accents": list(ACCENTS),
            "next_accent_s": max(0, round(self.next_accent - time.monotonic())) if self.middle_on and not self.top else None,
            "last_accent": self.last_accent,
            "output": {"kind": self.audio.room.kind, "name": self.audio.room.name, "ok": self.audio.room.ok},
        }
