"""Scenario 2 · Spring Cleaning (presence). Day 410, housekeeping Sunday. No microphone here.

The season turns as people pass (booklet 4.2): every pass across the radar's view moves the room one step
from winter towards summer; a few seconds after a pass the days run fast (day/night on the LEDs).
Standing still = lingering: the season grows around the person (spotlight, louder sounds, brighter light).
The tablet switches the spring's sounds on/off (default: all on except the frog — demo: "instead of a cat I like a frog").

winter → breath (it breathes out, rain) → birds → spring (bees, birds, the song as an invitation, cat or frog now and then; its volume
follows how close people are) → summer (crickets, warm light) → end
Song file: Prototype/Demo/Sounds/s2/here_comes_the_sun.mp3 (or .wav; without it: s2/music.wav).
"""
import asyncio
import random
import time

from core.audio import load_wav
from core.room import cct_rgb
from core.scenario import Scenario as Base

# 18.10.2026 (Flo): spring is the highlight with three phases (Beginning · Middle · End); winter, summer and autumn
# show one phase each (how it feels and sounds). "Next phase" / "Next season" on the web page, or someone arriving
# after nobody was seen for EMPTY_S, moves on one step.
PHASES = {"spring": ["Beginning", "Middle", "End"]}
STAGES = [   # stage, season (= the moment on the web page), light (colour temperature K, level), sounds {name: gain}
    ("winter", "winter", 9000, 0.22, {"winter": 0.18}),
    ("spring_begin", "spring", 6500, 0.30, {"winter": 0.04, "rain": 0.14}),
    ("spring_middle", "spring", 5000, 0.40, {"rain": 0.05, "birds": 0.20, "bees": 0.10}),
    ("spring_end", "spring", 4200, 0.52, {"birds": 0.26, "bees": 0.16, "song": 0.32}),
    ("summer", "summer", 3500, 0.62, {"birds": 0.05, "crickets": 0.22}),
    ("autumn", "autumn", 4800, 0.38, {"wind": 0.16}),
]
BEDS = {"winter": "s2/winter_wind", "rain": "s2/rain", "birds": "s2/birds", "bees": "s2/bees",
        "crickets": "ground/crickets", "wind": "ground/wind"}                     # Flo's spring sounds (Sounds/s2), crickets = cicadas
# Where S2 sits in the mission (booklet p. 36, data: 00_Bots/Documentation/Tools/build_mission_timeline.py):
# the 2nd vulnerability window (days 345–534, way home), habitat winter 425–470 → spring 470–510 → summer 510–548.
# The scenario sets the host's room date to these mission days, so the whole room shows one time.
STAGE_DAY = {"winter": 445, "spring_begin": 474, "spring_middle": 488, "spring_end": 502, "summer": 528, "autumn": 555}
EMPTY_S = 5.0          # nobody seen this long → the next person who comes by moves the season one phase on

SOUND_ROWS = [   # the tablet's switches: season, general (beds), accents (calls now and then, only in that season)
    ("winter", ["winter"], ["gust"]),
    ("spring", ["rain", "birds", "bees", "song"], ["cat", "frog"]),
    ("summer", ["crickets"], ["birdcall"]),
    ("autumn", ["wind"], ["shower"]),
]
SOUNDS = [n for _, g, acc in SOUND_ROWS for n in g + acc]
CALLS = {"gust": ("accent/wind_gust", 0.4, (8, 14)), "cat": ("accent/cat_meow", 0.5, (12, 20)),
         "frog": ("s2/frog", 0.45, (8, 14)), "birdcall": ("accent/bird_cross", 0.4, (8, 14)),
         "shower": ("accent/rain_pass", 0.4, (10, 16))}
CALL_SEASON = {acc: season for season, _, accs in SOUND_ROWS for acc in accs}
# 18.10.2026 (Flo, after testing with two people): no pass detection. The season is OFF while nobody is near,
# it switches on as someone comes closer (3 m → 0.6 m) and is fully on up close; "Next season" and "Skip days"
# on the web page step the season and the days by hand.
FAR_MM, FULL_MM = 3000, 600
LINGER_S, LINGER_MM = 3.0, 250   # moving less than LINGER_MM for LINGER_S = lingering
SIM_DAYS, SIM_S = 2, 10.0
END_HOLD_S = 15.0      # (unused since 18.10: summer stays until Stop)


class Scenario(Base):
    name = "spring_cleaning"
    title = "Spring Cleaning"
    order = 2
    hints = {"winter": "Winter. Come closer: it wakes up", "spring": "Spring: come closer", "summer": "Summer",
             "autumn": "Autumn"}
    stage_hints = {"winter": "Winter: cold and quiet", "spring_begin": "Spring begins: it breathes out",
                   "spring_middle": "Spring: birds and bees", "spring_end": "Spring in full: the song",
                   "summer": "Summer: warm evenings", "autumn": "Autumn: the wind returns"}
    room_duck = 0.0          # the scenario brings its own season; the room's ground goes quiet

    def __init__(self, host):
        super().__init__(host)
        self.sounds = {s: s != "frog" for s in SOUNDS}  # the tablet's choice, kept between runs (demo: cat → frog)
        self.rows = [{"season": se, "general": g, "accent": a} for se, g, a in SOUND_ROWS]
        self.stage = self.passes = 0
        self.flags = set()                               # "pass" / "skip" from the web page

    def ui(self):
        stage, season = STAGES[self.stage][:2]
        sim = getattr(self, "sim_h", None)                     # set while the days run fast
        room = self.host.room
        if getattr(self, "_curve_for", None) != season:          # the day curve of the season shown (cached)
            se = room.seasons[season]
            self._curve_for = season
            self._curve = {"curve": room.curve(96, season), "dawn_h": se["dawn_h"], "dusk_h": se["dusk_h"],
                           "sleep_h": room.sleep_h}
        _, _, k, level, _ = STAGES[self.stage]
        g = cct_rgb(k) * min(1.0, level * (1.0 + 0.3 * getattr(self, "linger", 0.0))) * 255
        return {"sounds": self.sounds, "rows": self.rows, "stage": stage, "phases": PHASES,
                "phase": [n for n, st in enumerate(STAGES) if st[1] == season].index(self.stage),
                "mission_day": room.mission_day(), "start_day": STAGE_DAY["winter"],
                "ground": "#%02x%02x%02x" % tuple(int(min(255, v)) for v in g),
                "spot": round(0.08 + 0.6 * getattr(self, "linger", 0.0), 2),
                "layers": self._layers(), "season": season, "hint": self.stage_hints[stage],
                "passes": self.passes, "near": round(getattr(self, "near", 0.0), 2),
                "linger": round(getattr(self, "linger", 0.0), 2), "curve": self._curve,
                "h": round(room.hour(), 2), "sim": sim is not None, "day": room.mission_day(),
                "map": self.host.cfg.get("room_map", {})}

    def command(self, c, v):
        if c == "spring_sound" and isinstance(v, dict) and v.get("name") in self.sounds:
            self.sounds[v["name"]] = bool(v.get("on"))
        elif c == "spring_pass":                        # next phase
            self.flags.add("pass")
        elif c == "spring_season":                      # next season (its beginning)
            self.flags.add("season")
        elif c == "spring_skip":
            self.flags.add("skip")

    async def run(self):
        self.stage = self.passes = 0
        self.sim_h = None
        self.flags.clear()
        asyncio.get_running_loop().run_in_executor(None, self._song)   # load the song now (~1 s), not at pass 3
        self.voices, self.linger, self.near = {}, 0.0, 0.0
        self.trail = []
        self.empty_since = None                          # set when nobody is seen; an arrival after EMPTY_S = next phase
        next_call = {k: time.monotonic() + 4.0 for k in CALLS}
        self._to_day(STAGE_DAY["winter"], force=True)            # every demo starts at the window's winter
        self.moment(STAGES[0][1])
        self._mix(fade=4.0)
        while True:
            await self.sleep(0.1)
            now = time.monotonic()
            step = self._watch(now)
            if "season" in self.flags:
                self.flags.discard("season")
                season = STAGES[self.stage][1]                    # to the next season's (first) phase
                step = next((n - self.stage for n in range(self.stage + 1, len(STAGES)) if STAGES[n][1] != season), 0)
            if step and self.stage < len(STAGES) - 1:
                self.stage = min(len(STAGES) - 1, self.stage + int(step))
                self.passes += 1
                self._to_day(STAGE_DAY[STAGES[self.stage][0]])
                if STAGES[self.stage][1] != self.host.moment:
                    self.moment(STAGES[self.stage][1])
                self.host.event({"type": "note", "text": self.stage_hints[STAGES[self.stage][0]]})
                self._mix(fade=5.0)
            if "skip" in self.flags:
                self.flags.discard("skip")
                await self._simulate()
            self._mix(fade=0.6)
            for k, (rel, gain, gap) in CALLS.items():   # the season's accents, now and then
                if CALL_SEASON[k] == STAGES[self.stage][1] and now >= next_call[k] and self.sounds[k]:
                    if self.near > 0.2:                     # accents only while someone is near
                        self.audio.ambient_shot(self.sound(rel), gain * self.near)
                    next_call[k] = now + random.uniform(*gap)
        t_end = time.monotonic() + END_HOLD_S           # summer: stay a while, then hand back to the room
        while time.monotonic() < t_end:
            await self.sleep(0.2)
            self._watch(time.monotonic())
            self._mix(fade=0.6)
        for v in self.voices.values():
            v.ramp(0.0, 6.0)
        self.light.spotlight(self.color("warm"), 0.0, fade=3.0)
        self.host.room.set_season("summer")
        self.light.release(fade=8.0)
        await self.sleep(8.0)

    def _layers(self):
        """What plays on which level now (web page): general = beds, accent = the season's calls, moment = the song."""
        _, season, _, _, beds = STAGES[self.stage]
        on = lambda n: self.sounds.get(n, True)                                    # noqa: E731
        return {"general": [n for n in beds if n != "song" and on(n)],
                "accent": [n for n, se in CALL_SEASON.items() if se == season and on(n)],
                "moment": ["song"] if "song" in beds and on("song") else []}

    def _to_day(self, day, force=False):
        """Move the host's room date to this mission day (forward only, unless force); the hour stays."""
        room = self.host.room
        if force or room.mission_day() < day:
            h = room.hour()
            room.set_date(day)
            room.set_hour(h)

    # ---- presence ------------------------------------------------------------------------

    def _watch(self, now):
        """Track the nearest person: True on a pass; updates lingering (0..1) and closeness (0..1)."""
        passed = "pass" in self.flags
        self.flags.discard("pass")
        people = self.host.people
        p = min(people, key=lambda q: q["d"]) if people else None
        if p is None:                                   # nobody: the season fades out (~5 s)
            self.trail.clear()
            self.linger = max(0.0, self.linger - 0.03)
            self.near = max(0.0, self.near - 0.02)
            if self.empty_since is None:
                self.empty_since = now
            return passed
        if self.empty_since is not None and now - self.empty_since >= EMPTY_S:
            passed = True                               # someone comes by after a quiet while: next phase
        self.empty_since = None
        self.trail = [q for q in self.trail if now - q[0] < LINGER_S] + [(now, p["x"], p["y"])]
        span = max(max(abs(a[1] - b[1]), abs(a[2] - b[2])) for a in self.trail for b in self.trail)
        still = now - self.trail[0][0] > LINGER_S * 0.9 and span < LINGER_MM
        self.linger += ((1.0 if still else 0.0) - self.linger) * 0.05
        near = min(1.0, max(0.0, (FAR_MM - p["d"]) / (FAR_MM - FULL_MM)))   # 3 m → 0, 0.6 m → 1
        self.near += (near - self.near) * 0.1
        return passed

    # ---- sound + light -------------------------------------------------------------------

    def _mix(self, fade):
        _, _, k, level, beds = STAGES[self.stage]
        act = self.near                                   # activation: 0 nobody near … 1 right in front
        boost = act * (1.0 + 0.4 * self.linger)
        for name in set(beds) | set(self.voices):
            gain = beds.get(name, 0.0) * boost if self.sounds.get(name, True) else 0.0
            v = self.voices.get(name)
            if v is None:
                if gain <= 0:
                    continue
                v = self.voices[name] = self.bed(self._song() if name == "song" else BEDS[name], 0.0, fade=0.1,
                                                 where="table" if name == "rain" else "room")
            if abs(v.target - gain) > 1e-3:
                v.ramp(gain, fade)
        self.light.ground(cct_rgb(k), min(1.0, level * act * (1.0 + 0.3 * self.linger)), fade=fade, breath=0.0)
        self.light.spotlight(self.color("peach"), 0.7 * act * (0.6 + 0.4 * self.linger), width=0.5, fade=fade)

    def _song(self):
        """'Here Comes the Sun' if its file is there (wav or mp3), else the season's music."""
        rel = "s2/here_comes_the_sun"
        if rel not in self.audio.samples:
            for ext in ("wav", "mp3"):
                f = self.stems / f"{rel}.{ext}"
                if f.exists():
                    self.audio.samples[rel] = load_wav(f, self.audio.sr)
                    return rel
            return "s2/music"
        return rel

    async def _simulate(self):
        """Days run fast: SIM_DAYS day/night cycles in SIM_S seconds. It is the host's own room clock that runs
        (date + mission day count on), so the tablet, the home page and this scenario always show one time."""
        room = self.host.room
        season = STAGES[self.stage][1]                                # same season as the curve on the web page
        self.host.event({"type": "note", "text": f"{SIM_DAYS} days pass"})
        room.follow_real = False                                      # from now on the date counts on by itself
        h0, t0, days = room.hour(), time.monotonic(), 0
        self.sim_h = h0
        while (el := time.monotonic() - t0) < SIM_S:
            h = h0 + el / SIM_S * SIM_DAYS * 24
            while days < int(h // 24):                                # midnight passed: the next mission day
                days += 1
                room._new_day()
            room.set_hour(h % 24)
            level, k, _ = room.day(h % 24, season)
            self.light.ground(cct_rgb(k), level, fade=0.1, breath=0.0)
            await asyncio.sleep(0.05)
        while days < SIM_DAYS:
            days += 1
            room._new_day()
        room.set_hour(h0)                                             # same hour, SIM_DAYS later
        self.sim_h = None
        self._mix(fade=2.0)

    def on_onset(self, ev):
        pass                            # no microphone in this scenario
