"""Easter-egged host: the room's controller.

One command starts the MQTT broker, audio (beat, layers, mic), light (WLED subnodes),
the web page and the scenario. Run:  python main.py   (or run.bat)
"""
import argparse
import asyncio
import collections
import importlib
import logging
import math
import pickle
import signal
import statistics
import socket
import sys
import time
import tomllib
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.audio import AudioEngine  # noqa: E402
from core.netmic import NetMic, RowRecorder  # noqa: E402
from core.bus import Bus, start_broker  # noqa: E402
from core.light import Light, normalize_spots  # noqa: E402
from core.room import Room  # noqa: E402
from core.web import Web  # noqa: E402

log = logging.getLogger("host")


def db01(x):
    """RMS → 0..1 for meters (-60..0 dBFS)."""
    return max(0.0, min(1.0, (20 * math.log10(x + 1e-9) + 60) / 60))


class Host:
    def __init__(self, cfg, bus, audio, light):
        self.cfg = cfg
        self.bus = bus
        self.audio = audio
        self.light = light
        self.netmic = self.rows = None      # table mic + its loop recorder (set in main() when [netmic] is on)
        self.spots = cfg["spots"]
        h = cfg["host"]
        self.auto = bool(h["auto_start"])
        self.pcfg = cfg["presence"]
        self.present = False
        self.distance = None
        self.pres_src = None
        self.pres_t = 0.0
        self.absent_since = time.monotonic()
        self._streak = 0
        self._dist = collections.deque(maxlen=int(self.pcfg.get("median_of", 5)))
        self.pi_status = "unknown"
        self.moment = "idle"
        self.running = False
        self.task = None
        self._stopping = False
        self.started = 0.0
        self.quiet_until = 0.0
        self.cooldown_until = 0.0
        self.dirty = True
        # all scenarios in scenarios/; the selected one runs on Start / presence
        self.scenarios = {}
        for f in sorted((ROOT / "scenarios").glob("*.py")):
            if f.stem != "__init__":
                sc = importlib.import_module(f"scenarios.{f.stem}").Scenario(self)
                self.scenarios[sc.name] = sc
        self.scenarios = dict(sorted(self.scenarios.items(), key=lambda kv: kv[1].order))
        self.scenario = self.scenarios[h["scenario"]]
        self.traces = {}
        self._trace_dir = ROOT / "traces"
        for f in self._trace_dir.glob("*.pkl"):
            try:
                self.traces[f.stem] = pickle.loads(f.read_bytes())
            except Exception as e:
                log.warning("trace %s unreadable: %s", f.name, e)
        bus.on("cmd", self.on_cmd)
        bus.on("in/presence", self.on_presence)
        bus.on("in/presence/distance", self.on_presence)
        bus.on("in/presence/state", self.on_presence_state)     # ESPHome binary sensor: ON / OFF
        bus.on("in/presence/count", self.on_presence_count)
        bus.on("in/presence/target/+/+", self.on_target)          # LD2450: target/<1..3>/<x|y> in mm
        bus.on("in/presence_wall/count", self.on_wall_count)      # second LD2450 on the wall unit
        bus.on("in/presence_wall/target/+/+", self.on_wall_target)
        self.wall_seen = -1e9                                      # last time the wall radar saw someone
        self.targets = {}           # n → {"x", "y", "t"}
        self.wtargets = {}          # wall radar, same shape (its own coordinates)
        self.radar_count = None
        self.radar_t = 0.0
        bus.on("in/sound", self.on_sim_sound)
        bus.on("in/postcard", lambda sub, p: self.postcard())
        bus.on("status/presence", self.on_presence_status)
        self.room = Room(self)
        self.recent = collections.deque(maxlen=12)    # for the event bar after a page reload
        self.power = True                             # False = the room is turned off (page: Turn off)
        self._saved = None                            # (master volume, brightness) while off
        self._off_sent = True

    # ---- scenario control ----------------------------------------------------------------

    def set_moment(self, name):
        self.moment = name
        self.dirty = True
        self.event({"type": "moment", "moment": name})

    def start(self, reason="manual"):
        if self.running:
            return
        self.running = True
        self.started = time.monotonic()
        self.quiet_until = 0.0
        self.light.set_scenario_running(True)
        self.room.set_top(True, self.scenario.room_duck)
        self.task = asyncio.create_task(self._run(reason))

    async def _run(self, reason):
        self.event({"type": "start", "reason": reason})
        try:
            await self.scenario.run()
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("scenario crashed")
        finally:
            self.scenario.cleanup(3.0)
            self.audio.mic.capture = False
            self.light.set_scenario_running(False)
            self.running = False
            self.task = None
            if not self._stopping:
                self.cooldown_until = time.monotonic() + self.cfg["host"]["cooldown_s"]
                self.scenario.idle()
            self._stopping = False
            self.room.set_top(False)
            self.set_moment("idle")

    def stop(self):
        """Quiet: everything fades within 2 s; presence won't restart it for a while."""
        self.quiet_until = time.monotonic() + self.cfg["host"]["quiet_after_stop_s"]
        self.audio.fade_all(2.0)
        self.audio.mic.capture = False
        self.scenario.cleanup(2.0)
        self.scenario.idle(fade=2.0)
        if self.task:
            self._stopping = True
            self.task.cancel()
        self.event({"type": "stop"})
        self.dirty = True

    def select(self, name):
        """Switch the scenario (a running one is stopped gently first)."""
        if name not in self.scenarios or name == self.scenario.name:
            return
        if self.running:
            self.stop()
            self.quiet_until = 0.0
        self.scenario = self.scenarios[name]
        self.event({"type": "scenario", "name": name})
        self.dirty = True

    def postcard(self):
        """A postcard from Earth arrives (Scenario 3). In the concept they are uplinked in batches
        and released in off-duty hours; here the web page or MQTT in/postcard releases one."""
        if "miss_you_sis" not in self.scenarios or not self.power:
            return
        if self.running and self.scenario.name == "miss_you_sis":
            return
        self.select("miss_you_sis")
        asyncio.get_running_loop().call_later(2.5 if self.running else 0.0, self.start, "postcard")

    def scenario_voices(self):
        return [v for sc in self.scenarios.values() for v in sc._voices]

    def level_sounds(self):
        """Sound per level for the web page."""
        a = self.audio
        top = [{"name": b.name, "level": round(b.g, 3), "where": "table"} for b in a.beds if b.g > 0.001]
        top += [{"name": s.name, "level": round(s.g, 3), "where": "table"} for s in a.shots
                if not s.silent and a.frame <= s.start + len(s.buf)]
        top += [{"name": v.name, "level": round(v.g, 3), "where": getattr(v, "where", "room")}
                for v in self.scenario.__dict__.get("_voices", []) if not v.done and v.g > 0.001]
        live = [ly for ly in a.layers if ly.target > 0]
        if live:
            top.append({"name": f"{len(live)} layers", "level": round(a.layer_gain, 3), "where": "table"})
        room = self.room.sounds()
        return {"top": top, **room}

    def keep_trace(self, name, snap):
        """Keep what a scenario made (e.g. the jam's layers) for a later rewind; survives restarts."""
        if not snap:
            return
        self.traces[name] = snap
        try:
            self._trace_dir.mkdir(exist_ok=True)
            (self._trace_dir / f"{name}.pkl").write_bytes(pickle.dumps(snap))
        except OSError as e:
            log.warning("could not save trace: %s", e)
        self.event({"type": "trace", "name": name, "layers": len(snap)})

    # ---- inputs --------------------------------------------------------------------------

    def on_cmd(self, sub, p):
        if not isinstance(p, dict):
            return
        c, v = p.get("cmd"), p.get("value")
        clamp = lambda x: max(0.0, min(1.0, float(x)))  # noqa: E731
        if c == "power":
            self.set_power(bool(v))
            return
        if c == "restart_units":                         # power menu: reboot all WLED units (wall, table, spotlight)
            ids = self.light.restart_all()
            self.event({"type": "note", "text": f"restarting {', '.join(ids)} (back in ~15 s)" if ids else "no unit online to restart"})
            return
        if not self.power and c in ("start", "postcard"):
            self.event({"type": "note", "text": "the room is off — turn it on first"})
            return
        if not self.power and c in ("volume", "brightness") and self._saved:
            vol, bri = self._saved
            self._saved = (clamp(v), bri) if c == "volume" else (vol, clamp(v))
            self.dirty = True
            return
        if c == "start":
            self.start("manual")
        elif c == "scenario":
            self.select(str(v))
        elif c == "postcard":
            self.postcard()
        elif c == "stop":
            if self.running and self.scenario.wind_down():   # first Stop: the scenario ends itself (e.g. outro)
                self.quiet_until = time.monotonic() + self.cfg["host"]["quiet_after_stop_s"]
                self.event({"type": "note", "text": "winding down — press Stop again to cut"})
            else:
                self.stop()
        elif c.startswith("spring_") and "spring_cleaning" in self.scenarios:   # S2: sounds, pass, skip days
            self.scenarios["spring_cleaning"].command(c, v)
        elif c == "postcard_hold" and "miss_you_sis" in self.scenarios:       # S3: stand-in for holding the card
            self.scenarios["miss_you_sis"].command(c, v)
        elif c == "clear_layers":
            self.audio.clear_layers()
        elif c == "volume":
            self.audio.master = clamp(v)
        elif c == "brightness":
            self.light.maxb = clamp(v)
        elif c == "sensitivity":
            self.audio.mic.sensitivity = clamp(v)
        elif c == "mic_threshold" and self.rows is not None:     # table mic: louder than this joins the loop
            self.rows.threshold = max(1e-4, min(0.2, float(v)))
        elif c == "auto":
            self.auto = bool(v)
        elif c == "season":
            self.room.set_season(str(v))
        elif c == "day_minutes":
            self.room.set_speed(float(v))
        elif c == "clock":
            self.room.set_hour(float(v))
        elif c == "date":
            self.room.set_date(v)
        elif c == "now":
            self.room.now()
        elif c == "ground":
            self.room.ground_on = bool(v)
        elif c == "middle":
            self.room.middle_on = bool(v)
            self.room._schedule()
        elif c == "accent":
            self.room.accent(v or None)
        elif c == "ambient_volume":
            self.audio.amb.gain = self.audio.room.mixer.gain = clamp(v)
        self.dirty = True

    def on_presence(self, sub, p):
        """{"present": bool} (simulator) or {"distance_cm": x} / a bare number (sensor subnode)."""
        if isinstance(p, (int, float)):
            p = {"distance_cm": float(p)}
        if not isinstance(p, dict):
            return
        self.pres_src = p.get("src", "sensor")
        self.pres_t = time.monotonic()
        if "present" in p:
            self._streak = 0
            self._set_present(bool(p["present"]))
            return
        d = p.get("distance_cm")
        if d is None:
            return
        self._dist.append(float(d))
        d = self.distance = statistics.median(self._dist)   # ignores single stray echoes
        th = self.pcfg["near_cm"] + (self.pcfg["hysteresis_cm"] if self.present else 0)
        near = d is not None and 0 < float(d) < th
        self._streak = self._streak + 1 if near != self.present else 0
        if self._streak >= self.pcfg["confirm_readings"]:
            self._streak = 0
            self._set_present(near)

    def on_presence_state(self, sub, p):
        v = str(p).strip().upper()
        if v not in ("ON", "OFF"):
            return
        self.pres_src, self.pres_t = "radar", time.monotonic()
        self._streak = 0
        # the radar's own ON/OFF only times the check: someone is here if a filtered person is left on EITHER radar
        # (its ON also counts frozen ghosts, its OFF misses people only the wall radar sees)
        self._set_present(bool(self.people))

    def on_presence_count(self, sub, p):
        try:
            self.radar_count = int(float(p))
        except (TypeError, ValueError):
            return
        self.radar_t = time.monotonic()
        self.dirty = True

    def on_wall_count(self, sub, p):
        try:
            if int(float(p)) > 0:
                self.wall_seen = time.monotonic()
        except (TypeError, ValueError):
            pass

    def on_wall_target(self, sub, p):
        if self._track(self.wtargets, sub, p):
            self.wall_seen = time.monotonic()

    def on_target(self, sub, p):
        if self._track(self.targets, sub, p):
            self.radar_t = time.monotonic()

    def _track(self, store, sub, p):
        """One LD2450 coordinate: in/<radar>/target/<n>/<x|y> in mm. Keeps when it last really moved."""
        parts = sub.split("/")
        try:
            n, axis, val = int(parts[3]), parts[4], float(p)
        except (IndexError, TypeError, ValueError):
            return False
        if axis not in ("x", "y"):
            return False
        now = time.monotonic()
        t = store.setdefault(n, {"x": 0.0, "y": 0.0, "t": 0.0, "first": now, "moved": now})
        if now - t["t"] > 1.5:          # target (re)appears: its "seen steadily" clock starts again
            t["first"] = t["moved"] = now
        if abs(val - t[axis]) > float(self.pcfg.get("stale_mm", 10)):
            t["moved"] = now
        t[axis] = val
        t["t"] = now
        return True

    @property
    def people(self):
        """Tracked people, both LD2450s fused: [{"n", "x", "y", "d" (mm, from the spotlight radar), "spot", "src"}].
        Filters (calibrated with the radar test of 18.10.2026, see the log):
        - a target counts only after it was seen steadily for ghost_confirm_s;
        - frozen targets (moved less than stale_mm for stale_s) are ghosts: real people always jitter;
        - targets closer than spot_min_mm / wall_min_mm to their radar are the lamp or the radar's own housing;
        - wall targets are moved into the spotlight radar's coordinates (wall_offset_mm, wall_rot_deg); targets
          closer than ghost_merge_mm to an already counted one are the same person (other radar, reflections)."""
        now, out = time.monotonic(), []
        c = self.pcfg
        confirm, merge = float(c.get("ghost_confirm_s", 1.0)), float(c.get("ghost_merge_mm", 400))
        stale = float(c.get("stale_s", 3.0))
        ox, oy = (float(v) for v in c.get("wall_offset_mm", [0, 0]))
        a = math.radians(float(c.get("wall_rot_deg", 0)))
        cand = []
        for src, store, dmin, dmax in (
                ("spot", self.targets, float(c.get("spot_min_mm", 0)), float(c.get("spot_max_mm", 1e9))),
                ("wall", getattr(self, "wtargets", {}), float(c.get("wall_min_mm", 0)), float(c.get("wall_max_mm", 1e9)))):
            for n, t in store.items():
                if now - t["t"] > 1.5 or (t["x"] == 0 and t["y"] == 0) or now - t.get("first", now) < confirm:
                    continue
                if now - t.get("moved", now) > stale or not dmin <= math.hypot(t["x"], t["y"]) <= dmax:
                    continue
                x, y = t["x"], t["y"]
                if src == "wall":
                    x, y = x * math.cos(a) - y * math.sin(a) + ox, x * math.sin(a) + y * math.cos(a) + oy
                cand.append((now - t.get("first", now), src, n, x, y))
        for _age, src, n, x, y in sorted(cand, key=lambda q: (q[1] != "spot", -q[0])):   # spotlight first, oldest first
            if any(math.hypot(x - p["x"], y - p["y"]) < merge for p in out):
                continue
            out.append({"n": n if src == "spot" else 10 + n, "x": round(x), "y": round(y), "d": round(math.hypot(x, y)),
                        "spot": self.nearest_spot(x, y), "src": src})
        return sorted(out, key=lambda p: p["n"])

    def nearest_spot(self, x, y):
        """The spot closest to a position (spots need pos = [x_mm, y_mm] in room.toml)."""
        best, bd = None, None
        for s in self.spots:
            if "pos" in s:
                d = (s["pos"][0] - x) ** 2 + (s["pos"][1] - y) ** 2
                if bd is None or d < bd:
                    best, bd = s["id"], d
        return best

    def _set_present(self, v):
        if v == self.present:
            return
        self.present = v
        if not v:
            self.absent_since = time.monotonic()
        self.event({"type": "presence", "present": v, "distance_cm": self.distance, "src": self.pres_src})
        self.dirty = True
        now = time.monotonic()
        if (v and self.power and self.auto and self.scenario.starts_on_presence and not self.running
                and now >= self.quiet_until and now >= self.cooldown_until):
            self.start("presence")

    def on_presence_status(self, sub, p):
        self.pi_status = str(p)
        self.dirty = True

    def on_audio_event(self, ev):
        """From the audio thread (via call_soon_threadsafe)."""
        if ev["type"] == "onset":
            self.scenario.on_onset(ev)
        elif ev["type"] == "sound":
            self.handle_sound(ev)

    def on_row_event(self, ev):
        """From the table mic's loop recorder: a loop became a row."""
        res = self.scenario.on_row(ev) or {"accepted": False, "reason": "ignored"}
        if res.get("accepted"):
            self.event({"type": "row", "src": "table mic", "row": ev["row"],
                        "strength": round(min(1.0, ev["level"] / max(self.rows.threshold, 1e-6) / 4), 2), **res})
            self.dirty = True

    def on_sim_sound(self, sub, p):
        kind = p.get("kind", "hit") if isinstance(p, dict) else "hit"
        if kind not in ("hit", "hum"):
            return
        self.scenario.on_onset({"strength": 0.8})
        self.handle_sound({"kind": kind, "t": time.perf_counter(), "buf": self.audio.sim_sound(kind),
                           "src": "sim", "strength": 0.8})

    def handle_sound(self, ev):
        res = self.scenario.on_sound(ev) or {"accepted": False, "reason": "ignored"}
        if res.get("reason") == "not listening" and not self.audio.mic.capture:
            return                                   # outside the jam: taps are handled as onsets only
        self.event({"type": ev["kind"], "src": ev.get("src", "mic"),
                    "strength": round(float(ev.get("strength", 0)), 2), **res})
        self.dirty = True

    def event(self, payload):
        payload["at"] = round(time.time(), 2)
        room = getattr(self, "room", None)
        if room is not None:
            payload["h"] = round(room.hour(), 3)          # room clock (may be shifted / simulated)
        self.recent.append(payload)
        self.bus.publish("event", payload)

    def set_power(self, on):
        """Turn the whole room off (quiet stop, sound and light fade out, WLEDs off) or back on."""
        if on == self.power:
            return
        if not on:
            if self.running:
                self.stop()
            self._saved = (self.audio.master, self.light.maxb)
            self._off_sent = False
            self.power = False
        else:
            self.power = True
            self.light.enabled = True
            master, maxb = self._saved or (self.audio.master, self.light.maxb)
            self.audio.master, self.light.maxb = master, maxb
            self.quiet_until = self.cooldown_until = 0.0
            asyncio.get_running_loop().run_in_executor(None, self.light.set_on, True)
        self.event({"type": "power", "on": on})
        self.dirty = True

    def _power_fade(self, dt):
        """While off: fade sound and light to zero over ~2 s, then switch the WLEDs off once."""
        if self.power or self._saved is None:
            return
        master0, maxb0 = self._saved
        self.audio.master = max(0.0, self.audio.master - master0 * dt / 2)
        self.light.maxb = max(0.0, self.light.maxb - maxb0 * dt / 2)
        if not self._off_sent and self.audio.master == 0.0 and self.light.maxb == 0.0:
            self._off_sent = True
            self.light.enabled = False
            asyncio.get_running_loop().run_in_executor(None, self.light.set_on, False)

    # ---- output loop ---------------------------------------------------------------------

    async def loop(self):
        dt = 1 / self.light.fps
        nxt = time.perf_counter()
        t_meter = t_light = t_state = t_room = 0.0
        while True:
            now = time.perf_counter()
            for t, spot, kind in self.audio.take_triggers(now):
                self.scenario.on_layer_play(t, spot, kind)
            if self.rows is not None:
                self.rows.tick(now)
            # the table mic moves the light only during Morning Jam; otherwise the room is idle
            jam = self.running and getattr(self.scenario, "name", "") == "morning_jam"
            over = self.netmic.level / self.rows.threshold if jam and self.rows is not None and self.netmic.ok else 0.0
            self.light.mic = min(1.0, math.log10(over)) if over > 1 else 0.0
            self.light.accent_audio = self.room.accent_loudness()
            self.light.capture_tgt = 1.0 if over > 1 or self.audio.mic.cap is not None else 0.0
            if now - t_room >= 0.5:
                t_room = now
                self.room.tick()
            self._power_fade(dt)
            if now - t_room < dt:       # 2 Hz is plenty for proximity; the light fades smoothly in between
                ppl = self.people
                self.light.set_proximity(min(p["d"] for p in ppl) if ppl else None)
            self.light.render(dt, self.audio.beat(now))
            self.light.send()
            if now - t_meter >= 0.05:
                t_meter = now
                self.bus.publish("meter", self.meter(now))
            if now - t_light >= 0.066:
                t_light = now
                self.bus.publish("light", self.light.preview())
            if now - t_state >= 0.5 or self.dirty:
                t_state = now
                self.dirty = False
                self.audio.housekeeping()
                if self.present and self.pres_src not in (None, "sim") and time.monotonic() - self.pres_t > 5:
                    self._set_present(False)  # sensor went quiet: don't keep a stale "someone is here"
                self.bus.publish("state", self.state(), retain=True)
            nxt += dt
            delay = nxt - time.perf_counter()
            if delay < -0.2:
                nxt = time.perf_counter()
            await asyncio.sleep(max(0.0, delay))

    def meter(self, now):
        m, b = self.audio.mic, self.audio.beat(now)
        frac = self.audio.loop_frac(now)
        nm, rows = self.netmic, self.rows
        if nm is not None and nm.ok:            # lvl / gate: raw RMS of the table mic and the row threshold
            return {"mic": round(db01(nm.level), 3), "thr": round(db01(rows.threshold), 3),
                    "lvl": round(nm.level, 5), "gate": round(rows.threshold, 5),
                    "pos": None if frac is None else round(frac, 4), "beat": None if b is None else b[0],
                    "cap": bool(rows.active), "out": round(db01(self.audio.out_level), 3),
                    "room": round(db01(self.audio.room.mixer.level / 3), 3)}
        return {"mic": round(db01(m.level), 3), "thr": round(db01(m.thr), 3),
                "pos": None if frac is None else round(frac, 4), "beat": None if b is None else b[0],
                "cap": m.cap is not None, "out": round(db01(self.audio.out_level), 3),
                "room": round(db01(self.audio.room.mixer.level / 3), 3)}

    def state(self):
        a, now = self.audio, time.monotonic()
        L = a.L
        return {
            "scenario": self.scenario.name, "title": self.scenario.title,
            "scenarios": [{"name": k, "title": v.title, "moments": list(v.hints)} for k, v in self.scenarios.items()],
            "traces": {k: len(v) for k, v in self.traces.items()},
            "moment": self.moment, "running": self.running,
            "power": self.power,
            "recent": list(self.recent),
            "hint": self.scenario.hints.get(self.moment, "") if self.running else "",
            "elapsed": round(now - self.started) if self.running else 0,
            "auto": self.auto,
            "quiet_s": max(0, round(self.quiet_until - now)),
            "presence": {"present": self.present, "distance_cm": self.distance, "src": self.pres_src,
                         "count": (self.radar_count if self.radar_count is not None and now - self.radar_t < 5
                                   else len(self.people) if self.people else int(self.present)),
                         "people": self.people,
                         "wall_cal": [*(float(v) for v in self.pcfg.get("wall_offset_mm", [0, 0])),
                                      float(self.pcfg.get("wall_rot_deg", 0))],
                         "age_s": round(now - self.pres_t, 1) if self.pres_src else None,
                         "sensor": self.pi_status},
            "volume": round(self._saved[0] if not self.power and self._saved else a.master, 2),
            "brightness": round(self._saved[1] if not self.power and self._saved else self.light.maxb, 2),
            "sensitivity": round(a.mic.sensitivity, 2), "capture": a.mic.capture,
            "mic_threshold": None if self.rows is None else self.rows.threshold,
            "spring": self.scenarios["spring_cleaning"].ui() if "spring_cleaning" in self.scenarios else None,
            "postcard": self.scenarios["miss_you_sis"].ui() if "miss_you_sis" in self.scenarios else None,
            "bpm": a.bpm, "beats": a.beats, "steps_per_beat": a.steps_per_beat,
            "beds": [b.name for b in a.beds if b.target > 0],
            "layers": [{"id": ly.id, "kind": ly.kind, "slot": ly.slot, "steps": ly.steps, "spot": ly.spot,
                        "len": round(len(ly.buf) / L, 4), "age": int(a.layer_age(ly)), "life": a.layer_loops,
                        "fading": ly.target == 0, "env": getattr(ly, "env", None)} for ly in a.layers],
            "spots": [{"id": s["id"], "name": s["name"], "a": int(s["leds"][0]), "n": int(s["leds"][1]), "moment": s.get("moment", False),
                       "pos": s.get("pos"),
                       "middle": self.light.spots[s["id"]]["middle"], "light": s["light"],
                       "channels": s["channels"]} for s in self.spots],
            "room": self.room.state(),
            "sounds": self.level_sounds(),
            "ambient_volume": round(self.audio.room.mixer.gain, 2),
            "devices": {"audio_out": a.out_name or "none (silent clock)",
                        "mic": (f"table mic (UDP {self.netmic.port}, {self.netmic.peer})" if self.netmic is not None and self.netmic.ok
                                else a.mic.ok and a.in_name or "none"),
                        "wled": [d.status for d in self.light.devices.values()],
                        "mqtt": f"{self.bus.host}:{self.bus.port}" + ("" if self.bus.connected else " (connecting)")},
        }


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "localhost"


async def main(args):
    cfg = tomllib.loads((ROOT / args.config).read_text(encoding="utf-8"))
    machine = ROOT / "machine.toml"
    if machine.exists():
        for section, values in tomllib.loads(machine.read_text(encoding="utf-8")).items():
            cfg.setdefault(section, {}).update(values)
        log.info("machine.toml merged")
    cfg["audio"]["stems_dir"] = str(ROOT / cfg["audio"]["stems_dir"])
    h = cfg["host"]
    loop = asyncio.get_running_loop()
    mq = cfg.get("mqtt", {})
    external = mq.get("mode", "embedded") == "external"
    broker = None if external else await start_broker(h["mqtt_port"])
    bus = Bus(h["topic_prefix"], int(mq.get("port", 1883)) if external else int(h["mqtt_port"]), loop,
              host=mq.get("host", "127.0.0.1") if external else "127.0.0.1",
              username=mq.get("username"), password=mq.get("password"))
    holder = {}
    normalize_spots(cfg["spots"])
    audio = AudioEngine(cfg, cfg["spots"], lambda ev: loop.call_soon_threadsafe(holder["host"].on_audio_event, ev))
    light = Light(cfg, cfg["spots"])
    host = holder["host"] = Host(cfg, bus, audio, light)
    host.netmic = host.rows = None
    if cfg.get("netmic", {}).get("enabled"):     # table unit streams its mic → loop rows for Morning Jam
        host.netmic = NetMic(cfg["netmic"])
        await host.netmic.start()
        host.rows = RowRecorder(cfg.get("morning_jam", {}), audio, host.netmic, host.on_row_event)
    web = Web(bus, h["web_port"], ROOT / "web")
    bus.start()
    await web.start()
    audio.start()
    host.scenario.idle()
    tasks = [asyncio.create_task(host.loop()), asyncio.create_task(light.connect())]
    me = asyncio.current_task()

    def _stop(*_):
        loop.call_soon_threadsafe(me.cancel)

    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _stop)
    url = f"http://localhost:{h['web_port']}"
    log.info("ready. Web page: %s  (phone on the same Wi-Fi: http://%s:%d)", url, lan_ip(), h["web_port"])
    if h.get("open_browser") and not args.no_browser:
        webbrowser.open(url)
    try:
        await asyncio.gather(*tasks)
    finally:
        log.info("shutting down")
        for t in tasks:
            t.cancel()
        steps = [("light", light.off), ("audio", audio.stop), ("bus", bus.stop),
                 ("web", web.stop)] + ([("broker", broker.shutdown)] if broker else [])
        for name, fn in steps:            # each step gets 3 s, so a stuck device can't block the exit
            t0 = time.monotonic()
            try:
                res = asyncio.to_thread(fn) if not asyncio.iscoroutinefunction(fn) else fn()
                await asyncio.wait_for(res, 3.0)
            except Exception as e:
                log.warning("shutdown %s: %s", name, e or type(e).__name__)
            if time.monotonic() - t0 > 1:
                log.info("shutdown %s took %.1f s", name, time.monotonic() - t0)
        log.info("stopped")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Easter-egged host (room controller)")
    ap.add_argument("--config", default="room.toml")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--list-devices", action="store_true", help="print audio devices and exit")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-6s %(message)s", datefmt="%H:%M:%S",
                        stream=sys.stdout)            # stdout: the RoomHost window logs it cleanly to host.log
    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        sys.exit(0)
    try:
        asyncio.run(main(args))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
