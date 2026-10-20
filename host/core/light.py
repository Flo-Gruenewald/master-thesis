"""Light engine: spots on one or more WLED subnodes, rendered in three sensorial levels.

GROUND  base light of every spot. The room program sets it (circadian day, season); a scenario can
        take it over for a while (ground -> release); Top moments dim it (duck)
MIDDLE  weather accents travelling along the middle spots: glow, shade (cloud), tint (rain), flash
TOP     the moment: a spotlight at the moment spot(s), pulses on hits, a listening core

Frames go to each WLED over DDP (UDP 4048), which is fast enough for beat-synced light. A strip wired
straight to the host's Pi (`kind = "spi"`) gets its frames over SPI instead (GPIO10 / MOSI, see SpiStrip).

Each spot has one level (room.toml `level`): "ground" (circadian light only), "accent" (weather accents
over a faint glow of the day's colour) or "top" (the moment: scenario spotlight, pulses, listening glow,
proximity when idle, rendered evenly as one lamp). Older configs with moment/middle/top_spotlight flags
still work (see spot_level).
"""
import asyncio
import json
import logging
import math
import socket
import urllib.request

import aiohttp
import numpy as np

log = logging.getLogger("light")


def cct_rgb(k):
    """Colour temperature (K) → normalised RGB (Tanner Helland's approximation)."""
    t = k / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    rgb = np.clip(np.array([r, g, b]) / 255.0, 0, 1)
    return rgb / rgb.max()


def spot_level(s):
    """The level of a spot: `level` if set, else derived from the older flags."""
    lv = s.get("level")
    if lv in ("ground", "accent", "top"):
        return lv
    if s.get("top_spotlight"):
        return "top"
    if s.get("moment"):
        return "moment"                       # legacy: ground light + the moment on one strip
    return "mixed"                            # legacy: ground light + accents (if middle, the default)


def normalize_spots(spots):
    """Give every spot the flags the rest of the host reads (moment = this is where the moment is)."""
    for s in spots:
        lv = spot_level(s)
        s["moment"] = lv in ("top", "moment")
        s["middle"] = lv == "accent" or (lv == "moment" and bool(s.get("middle", False)))             or (lv == "mixed" and bool(s.get("middle", True)))
        s["top_spotlight"] = lv == "top"
    return spots


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


# SK6812/WS2812 over SPI: 2.4 MHz, every LED bit = 3 SPI bits (0 → 100, 1 → 110). Same method as the old
# Dexy project on this Pi. Lookup table: byte value → its 3 SPI bytes.
_SPI_LUT = np.zeros((256, 3), dtype=np.uint8)
for _v in range(256):
    _bits = 0
    for _i in range(7, -1, -1):
        _bits = (_bits << 3) | (0b110 if (_v >> _i) & 1 else 0b100)
    _SPI_LUT[_v] = [(_bits >> 16) & 0xFF, (_bits >> 8) & 0xFF, _bits & 0xFF]
SPI_HZ = 2_400_000


def spi_frame(px_bytes):
    """uint8 array (n, channels) in wire order (G, R, B[, W]) → SPI bytes incl. the reset gap."""
    return np.concatenate([_SPI_LUT[px_bytes.reshape(-1)].reshape(-1), np.zeros(64, dtype=np.uint8)])


def limit_current(x, max_ma, ma_per_channel=12.0, idle_ma=1.0):
    """Scale a frame (values 0..1, any channel count) so the strip stays under max_ma (estimate:
    ~12 mA per fully lit channel + ~1 mA per LED for the chip). Returns the scaled frame and the estimate."""
    n = x.shape[0]
    est = float(x.sum()) * ma_per_channel + n * idle_ma
    if max_ma and est > max_ma:
        k = max(0.0, (max_ma - n * idle_ma) / max(est - n * idle_ma, 1e-6))
        return x * k, max_ma
    return x, est


def accent_from_ground(rgb, saturation=1.0, warm_push=0.85, cool_push=0.9):
    """The accent "expands" the GROUND light (Copilot, 06.10): same hue, far more saturated — sky blue when the
    ground is cool, sunset red-orange when it is warm, deep red at night. LED values; warm tones keep blue ≈ 0
    (on the RGBW strip a blue share next to strong red turns pink)."""
    ground = np.clip(np.asarray(rgb, dtype=float), 0.0, 1.0)
    peak = float(ground.max())
    if peak <= 1e-9:
        return np.array([1.0, 0.30, 0.02])
    ground /= peak
    white = float(ground.min())
    accent = np.clip(ground - saturation * white, 0.0, 1.0)
    accent_peak = float(accent.max())
    if accent_peak <= 1e-9:
        accent = ground.copy()
    else:
        accent /= accent_peak

    red, green, blue = ground
    if blue >= red:
        coolness = min(1.0, max(0.0, (blue - red) / 0.2))
        push = min(1.0, max(0.0, cool_push)) * coolness
        target = np.array([0.15, 0.58, 1.0])
    else:
        warmth = min(1.0, max(0.0, (red - blue) / 0.65))
        push = min(1.0, max(0.0, warm_push)) * warmth
        if peak < 0.12:
            target = np.array([0.85, 0.18, 0.03])
            push = 1.0
        elif green <= 0.68:
            target = np.array([1.0, 0.30, 0.02])
        elif green <= 0.8:
            target = np.array([1.0, 0.35, 0.03])
        else:
            target = np.array([1.0, 0.68, 0.18])
    return np.clip(accent * (1 - push) + target * push, 0.0, 1.0)


class Wled:
    """One light subnode (a WLED over the network, or kind = "spi": a strip on the host's own SPI pin)."""

    def __init__(self, c):
        self.id = c["id"]
        self.kind = c.get("kind", "wled")
        self.spi_bus = int(c.get("spi_bus", 0))
        self.spi_dev = int(c.get("spi_device", 0))
        self.max_ma = float(c.get("max_ma", 800))
        # WLED over the network: the host keeps the frame under WLED's own current limit, so WLED's limiter
        # never has to step in (it dims frame by frame and makes white flicker). WLED estimates ledma per LED
        # for R+G+B at full, i.e. ledma/3 per channel (W counts like a colour); 0 = no host cap.
        self.cap_ma = float(c.get("host_max_ma", 0))
        self.cap_per_ch = float(c.get("ledma", 55)) / 3
        self.gain = float(c.get("gain", 1.0))                # brightness factor for this unit (before the cap)
        self.http_port = int(c.get("http_port", 80))       # 8081 for a Pi LED node (pi/kellerkind/led_node.py)
        self.spi = None
        self.ma = 0.0
        self.host = c.get("host")
        self.mdns = c.get("mdns")
        self.n = int(c["led_count"])
        self.rgbw = bool(c.get("rgbw", False))
        # colour of the strip's own white LED (SK6812 RGBW: warm ~3000 K, neutral ~4000-4500 K, cold ~6000 K).
        # The white LED carries what it can of each colour, R/G/B add the rest — so a cool target gets real blue.
        self.white = cct_rgb(float(c["white_k"])) if c.get("white_k") else np.ones(3)
        self.px = np.zeros((self.n, 3))
        self.addr = None
        self.seq = 0
        self.status = {"id": self.id, "ok": False, "ip": None, "leds": self.n, "note": "searching"}


class Light:
    def __init__(self, cfg, spots):
        c = cfg["light"]
        self.fps = int(c["fps"])
        self.maxb = float(c["max_brightness"])
        self.top_spotlight_rgb = hex_rgb(c["top_spotlight_color"]) if c.get("top_spotlight_color") else None
        self.top_spotlight_idle = float(c.get("top_spotlight_idle", 0.0))
        self.top_spotlight_active = float(c.get("top_spotlight_active", 1.0))
        self.accent_base = float(c.get("accent_base", 0.15))   # accent spots: share of the day's colour
        self.accent_floor = float(c.get("accent_floor", 0.0))  # accent spots: minimum glow (also at night)
        self.accent_tint_mix = float(c.get("accent_tint_mix", 0.0))  # how much of the season colour
        self.accent_boost = float(c.get("accent_boost", 1.0))  # weather accents: amplitude factor
        self.accent_level = float(c.get("accent_level", 0.0))  # >0: fixed glow (LED output share, e.g. 0.8)
        self.accent_tint = np.ones(3)                           # glow colour, set by the room (circadian or season)
        self.middle_tint = None       # a scenario may give the table (MIDDLE) its own base colour; release() clears it
        self.accent_react = float(c.get("accent_react", 0.0))  # accent spots follow the accent sounds' loudness
        self.accent_audio = 0.0                                 # current loudness of the playing accent sounds (0..1)
        self.accent_colour = str(c.get("accent_colour", "circadian"))   # "expand": colour from the ground light
        self.accent_over_ground = float(c.get("accent_over_ground", 1.25))  # expand: glow = ground level × this
        self.accent_saturation = float(c.get("accent_saturation", 1.0))
        self.accent_warm_push = float(c.get("accent_warm_push", 0.85))
        self.accent_cool_push = float(c.get("accent_cool_push", 0.9))
        self._acc_env = 0.0
        # Proximity (TOP spotlight while no scenario runs): off when nobody is there, soft when someone
        # enters, brighter the closer they come. Distance = nearest person seen by the radar.
        p = c.get("proximity", {})
        self.prox_on = bool(p.get("enabled", False))
        self.prox_full = float(p.get("full_m", 0.6)) * 1000
        self.prox_soft = float(p.get("soft_m", 4.0)) * 1000
        self.prox_soft_level = float(p.get("soft_level", 0.10))
        self.prox_rate = 1.0 / max(float(p.get("fade_s", 1.5)), 0.05)
        self.prox_tgt = 0.0
        self.prox_cur = 0.0
        self.scenario_running = False
        self.devices = {w["id"]: Wled(w) for w in cfg["wled"]}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        # spots → (device, first LED, count); the virtual strip is all spots in config order
        self.spots = {}
        start = 0
        for s in spots:
            dev = self.devices[s["light"]]
            a, n = int(s["leds"][0]), int(s["leds"][1])
            if a + n > dev.n:
                raise ValueError(f"spot {s['id']}: LEDs {a}..{a + n - 1} exceed {dev.id} ({dev.n} LEDs)")
            lv = spot_level(s)
            self.spots[s["id"]] = {"dev": dev, "a": a, "n": n, "v": start, "level": lv,
                                   "moment": lv in ("top", "moment"),
                                   "middle": (lv == "accent" or (lv == "moment" and bool(s.get("middle", False)))
                                              or (lv == "mixed" and bool(s.get("middle", True)))),
                                   "top_spotlight": lv == "top"}
            start += n
        self.vn = start
        self.vpx = np.zeros((self.vn, 3))
        self.vg = np.zeros((self.vn, 3))      # per-level previews for the web page
        self.vm = np.zeros((self.vn, 3))
        self.vt = np.zeros((self.vn, 3))
        self.active = []                      # names of the accents running now
        regular_spots = [s for s in self.spots.values() if not s["top_spotlight"]]
        self.vidx = (np.concatenate([np.arange(s["v"], s["v"] + s["n"]) for s in regular_spots])
                     if regular_spots else np.array([], dtype=int))
        # middle accents travel along these virtual indices (the middle spots, or all if none)
        mids = [s for s in self.spots.values() if s["middle"] and not s["top_spotlight"]]
        if not mids:
            mids = [s for s in self.spots.values() if not s["top_spotlight"]]
        self.mid_idx = (np.concatenate([np.arange(s["v"], s["v"] + s["n"]) for s in mids])
                        if mids else np.array([], dtype=int))
        self.room_cur = {k: np.zeros(3) for k in self.spots}
        self.room_tgt = {k: np.zeros(3) for k in self.spots}
        self.room_rate = {k: 1.0 for k in self.spots}
        self.cur = {k: np.zeros(3) for k in self.spots}
        self.tgt = {k: np.zeros(3) for k in self.spots}
        self.rate = {k: 1.0 for k in self.spots}
        self.w = {k: 0.0 for k in self.spots}           # scenario override weight per spot
        self.wtgt = {k: 0.0 for k in self.spots}
        self.wrate = {k: 1.0 for k in self.spots}
        self.duck = 1.0
        self.duck_tgt = 1.0
        self._duck_rate = 1.0
        self.breath = 0.0
        self.top = {"rgb": np.zeros(3), "level": 0.0, "tgt": 0.0, "width": 1.0, "wtgt": 1.0, "speed": 1.0}
        self.pulses = []
        self.accents = []
        self.mic = 0.0
        self.enabled = True           # False = the room is turned off: no frames are sent
        self.capture = 0.0
        self.capture_tgt = 0.0
        self.capture_rgb = np.array([1.0, 0.92, 0.86])

    # ---- GROUND --------------------------------------------------------------------------

    def room_ground(self, rgb, fade=2.0, spots=None):
        """The room program's base light (circadian day, season). rgb already includes the level."""
        for k in spots or self.spots:
            self.room_tgt[k] = np.asarray(rgb, float)
            self.room_rate[k] = np.max(np.abs(self.room_tgt[k] - self.room_cur[k])) / max(fade, 1e-3) + 1e-6

    def ground(self, rgb, level, fade=1.0, breath=None, spots=None):
        """A scenario takes over the base light of spots (fades in over the room's ground)."""
        for k in spots or self.spots:
            self.tgt[k] = np.asarray(rgb, float) * level
            self.rate[k] = np.max(np.abs(self.tgt[k] - self.cur[k])) / max(fade, 1e-3) + 1e-6
            self.wtgt[k] = 1.0
            self.wrate[k] = abs(1.0 - self.w[k]) / max(fade, 1e-3) + 1e-6
        if breath is not None:
            self.breath = breath

    def release(self, fade=3.0, spots=None):
        """Give the base light back to the room program."""
        self.middle_tint = None
        for k in spots or self.spots:
            self.wtgt[k] = 0.0
            self.wrate[k] = abs(self.w[k]) / max(fade, 1e-3) + 1e-6
        self.breath = 0.0

    def set_duck(self, level, fade=2.0):
        """Dim the room's ground while a Top moment runs (attention goes to the moment)."""
        self.duck_tgt = float(level)
        self._duck_rate = abs(self.duck_tgt - self.duck) / max(fade, 1e-3) + 1e-6

    def set_proximity(self, distance_mm):
        """Nearest person in mm (None = nobody). Sets the TOP spotlight's idle target level."""
        if distance_mm is None:
            self.prox_tgt = 0.0
        elif distance_mm >= self.prox_soft:
            self.prox_tgt = self.prox_soft_level
        elif distance_mm <= self.prox_full:
            self.prox_tgt = 1.0
        else:
            x = (self.prox_soft - distance_mm) / (self.prox_soft - self.prox_full)   # 0 far … 1 near
            self.prox_tgt = self.prox_soft_level + (1 - self.prox_soft_level) * x * x  # soft at the door

    def set_scenario_running(self, running):
        """Show the separate warm-rust marker while a scenario runs."""
        self.scenario_running = bool(running)

    # ---- MIDDLE --------------------------------------------------------------------------

    def accent(self, rgb, amp=0.6, seconds=3.0, reverse=False, mode="glow", width=0.12, middle=True, name=""):
        """A weather accent travelling along the middle spots (middle=False: along all spots).
        mode: glow (light passes by), shade (a cloud: darker passes by), tint (the whole area
        washes towards rgb and back), flash (lightning: a quick bright double flash)."""
        idx = self.mid_idx if middle else self.vidx
        amp = min(1.0, amp * self.accent_boost)
        self.accents.append({"rgb": np.asarray(rgb, float), "amp": amp, "dur": seconds, "age": 0.0,
                             "rev": reverse, "mode": mode, "width": width, "idx": idx, "name": name or mode})

    # ---- TOP -----------------------------------------------------------------------------

    def spotlight(self, rgb, level, width=0.35, fade=1.5):
        """A spotlight on the moment spot(s). width = fraction of the spot that is lit."""
        t = self.top
        t["rgb"] = np.asarray(rgb, float)
        t["tgt"], t["wtgt"] = level, width
        t["speed"] = 1.0 / max(fade, 1e-3)

    def pulse(self, spot, rgb, amp=1.0, decay=2.5):
        """A ripple at one spot (None = every moment spot)."""
        tops = [k for k, s in self.spots.items() if s["top_spotlight"]]
        if tops:
            keys = tops                       # the moment's feedback belongs to the TOP spotlight
        elif spot in self.spots:
            keys = [spot]
        else:
            keys = [k for k, s in self.spots.items() if s["moment"]] or list(self.spots)
        for k in keys:
            self.pulses.append({"spot": k, "rgb": np.asarray(rgb, float), "amp": amp, "decay": decay, "age": 0.0})

    # ---- render --------------------------------------------------------------------------

    @staticmethod
    def _approach(cur, tgt, step):
        d = tgt - cur
        return tgt if np.max(np.abs(d)) <= step else cur + np.clip(d, -step, step)

    @staticmethod
    def _step(cur, tgt, step):
        return tgt if abs(tgt - cur) <= step else cur + (step if tgt > cur else -step)

    def render(self, dt, beat=None):
        v, vg, vm, vt = self.vpx, self.vg, self.vm, self.vt
        v[:] = 0
        vm[:] = 0
        vt[:] = 0
        b = 1.0
        if beat is not None and self.breath:
            b = 1 - self.breath + self.breath * np.exp(-beat[1] * 4)
        lift = 1 + 0.8 * self.mic                # self.mic is only non-zero while Morning Jam runs (host)
        a = self.accent_audio                    # accent sounds: fast attack, slow release
        self._acc_env += (a - self._acc_env) * min(1.0, dt * (25 if a > self._acc_env else 2.5))
        self.duck = self._step(self.duck, self.duck_tgt, self._duck_rate * dt)
        for k, s in self.spots.items():
            self.room_cur[k] = self._approach(self.room_cur[k], self.room_tgt[k], self.room_rate[k] * dt)
            self.cur[k] = self._approach(self.cur[k], self.tgt[k], self.rate[k] * dt)
            w = self.w[k] = self._step(self.w[k], self.wtgt[k], self.wrate[k] * dt)
            lv = s["level"]
            if lv == "top":                    # only what a scenario gives it (ground/release on this spot)
                base = self.cur[k] * b * w
            elif lv == "accent":               # a glow of the day's colour, tinted by the season, under the accents
                rc = self.room_cur[k]
                hue = rc / max(float(rc.max()), 1e-6) if rc.max() > 1e-6 else self.accent_tint
                col = hue * (1 - self.accent_tint_mix) + self.accent_tint * self.accent_tint_mix
                if self.accent_colour == "expand":   # ground hue, saturated, a bit brighter than the ground
                    col = accent_from_ground(rc, self.accent_saturation, self.accent_warm_push, self.accent_cool_push)
                    glow = col * min(1.0, max(float(rc.max()) * self.accent_over_ground, self.accent_floor))
                elif self.accent_level > 0:    # fixed output share (frames are squared before sending)
                    col = col / max(float(col.max()), 1e-6)
                    glow = col * self.accent_level ** 0.5
                else:
                    glow = col * max(float(rc.max()), self.accent_floor) * self.accent_base
                base = glow * self.duck * (1 + self.accent_react * self._acc_env) * (1 - w) + self.cur[k] * b * w
                if self.middle_tint is not None:   # e.g. S2 winter: an orange ember instead of the cool ground hue
                    base = self.middle_tint * float(base.max())
            else:
                base = self.room_cur[k] * self.duck * (1 - w) + self.cur[k] * b * w
            vg[s["v"]:s["v"] + s["n"]] = base
            v[s["v"]:s["v"] + s["n"]] = base * lift

        keep = []
        for a in self.accents:
            x = min(1.0, a["age"] / a["dur"])
            env = np.sin(np.pi * x)
            idx = a["idx"]
            m = len(idx)
            if a["mode"] in ("glow", "shade"):
                c = (1 - x if a["rev"] else x) * (m - 1)
                shape = np.exp(-((np.arange(m) - c) / max(1.0, m * a["width"])) ** 2) * a["amp"] * env
                if a["mode"] == "glow":
                    v[idx] += np.outer(shape, a["rgb"])
                    vm[idx] += np.outer(shape, a["rgb"])
                else:                                       # a cloud: darker here; shown blue-grey in the preview
                    v[idx] *= (1 - np.clip(shape, 0, 0.95))[:, None]
                    vm[idx] += np.outer(shape, [0.30, 0.36, 0.45])
            elif a["mode"] == "tint":
                k = a["amp"] * env
                v[idx] = v[idx] * (1 - k) + a["rgb"] * k
                vm[idx] += a["rgb"] * k
            elif a["mode"] == "flash":
                t = a["age"]
                k = a["amp"] * (np.exp(-t * 9) + (0.6 * np.exp(-(t - 0.18) * 9) if t > 0.18 else 0.0))
                v[idx] += a["rgb"] * k
                vm[idx] += a["rgb"] * k
            a["age"] += dt
            if a["age"] < a["dur"]:
                keep.append(a)
        self.accents = keep[-8:]
        self.active = sorted({a["name"] for a in self.accents})

        t = self.top
        sp = t["speed"] * dt
        t["level"] += float(np.clip(t["tgt"] - t["level"], -sp, sp))
        t["width"] += float(np.clip(t["wtgt"] - t["width"], -sp, sp))
        self.capture += (self.capture_tgt - self.capture) * min(1.0, dt * 12)
        self.prox_cur = self._step(self.prox_cur, self.prox_tgt if self.prox_on else 0.0, self.prox_rate * dt)
        for s in self.spots.values():
            if not s["moment"]:
                continue
            if s["top_spotlight"]:             # one lamp: everything evenly over the whole ring
                sl = slice(s["v"], s["v"] + s["n"])
                if self.scenario_running:
                    vt[sl] += t["rgb"] * t["level"] * b
                    if self.capture > 0.01:    # "I'm listening"
                        vt[sl] += self.capture_rgb * 0.35 * self.capture
                elif self.top_spotlight_rgb is not None:
                    vt[sl] += self.top_spotlight_rgb * max(self.top_spotlight_idle, self.prox_cur)
                continue
            if t["level"] > 0.001:
                self._bump(vt, s, t["rgb"] * t["level"] * b, max(t["width"], 0.05) * s["n"] / 2)
            if self.capture > 0.01:     # "I'm listening": a soft bright core while a sound is captured
                self._bump(vt, s, self.capture_rgb * 0.45 * self.capture, s["n"] * 0.12)

        keep = []
        for p in self.pulses:
            s = self.spots[p["spot"]]
            if s["top_spotlight"]:
                vt[s["v"]:s["v"] + s["n"]] += p["rgb"] * p["amp"] * 0.7      # a flash of the whole lamp
            else:
                self._bump(vt, s, p["rgb"] * p["amp"], s["n"] * (0.08 + 0.4 * min(1.0, p["age"] * 1.5)))
            p["amp"] *= np.exp(-p["decay"] * dt)
            p["age"] += dt
            if p["amp"] > 0.02:
                keep.append(p)
        self.pulses = keep[-24:]

        v += vt
        for arr in (v, vg, vm, vt):
            np.clip(arr, 0, 1, out=arr)
        for s in self.spots.values():
            s["dev"].px[s["a"]:s["a"] + s["n"]] = v[s["v"]:s["v"] + s["n"]]

    def _bump(self, v, s, rgb, width):
        idx = np.arange(s["n"])
        w = np.exp(-((idx - (s["n"] - 1) / 2) / max(width, 0.5)) ** 2)
        v[s["v"]:s["v"] + s["n"]] += np.outer(w, rgb)

    def preview(self):
        """For the web page: the composite (what the LEDs show) and each level on its own, as hex RGB."""
        hx = lambda a: (np.clip(a * 255, 0, 255)).astype(np.uint8).tobytes().hex()  # noqa: E731
        return {"px": hx(self.vpx), "g": hx(self.vg), "m": hx(self.vm), "t": hx(self.vt), "acc": self.active}

    def restart_all(self):
        """Reboot every WLED unit that is online (power menu → "Restart all units"). Returns their ids.
        The units come back by themselves after ~10 s and are picked up again like after a power cut."""
        import threading
        ids = []
        for d in self.devices.values():
            if d.kind != "wled" or not d.addr:
                continue
            url = f"http://{d.addr[0]}:{d.http_port}/json/state"

            def go(url=url, did=d.id):
                try:
                    req = urllib.request.Request(url, data=b'{"rb":true}', headers={"Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=3).read()
                except OSError as e:
                    log.warning("restart %s: %s", did, e)
            threading.Thread(target=go, daemon=True).start()
            ids.append(d.id)
        log.info("restart requested: %s", ", ".join(ids) or "no unit online")
        return ids

    # ---- output --------------------------------------------------------------------------

    def send(self):
        if not self.enabled:
            return
        for d in self.devices.values():
            if d.kind == "spi":
                if d.spi is not None:
                    self._send_spi(d)
                continue
            if not d.addr:
                continue
            x = np.clip((d.px ** 2.0) * self.maxb * d.gain, 0, 1)
            if d.rgbw:
                w = np.clip((x / d.white).min(axis=1), 0, 1)
                x = np.column_stack([np.clip(x - w[:, None] * d.white, 0, 1), w])
            if d.cap_ma:
                x, d.ma = limit_current(x, d.cap_ma, d.cap_per_ch)
            data = (x * 255 + 0.5).astype(np.uint8).tobytes()
            d.seq = d.seq % 15 + 1
            hdr = bytes([0x41, d.seq, 0x1B if d.rgbw else 0x0B, 0x01, 0, 0, 0, 0]) + len(data).to_bytes(2, "big")
            try:
                self.sock.sendto(hdr + data, d.addr)
            except OSError:
                pass

    def _send_spi(self, d, black=False):
        x = np.zeros((d.n, 3)) if black else (d.px ** 2.0) * self.maxb
        if d.rgbw:
            w = np.clip((x / d.white).min(axis=1), 0, 1)
            x = np.column_stack([np.clip(x - w[:, None] * d.white, 0, 1), w])
        x, d.ma = limit_current(x, d.max_ma)               # no WLED in between: the host caps the current
        b = (x * 255 + 0.5).astype(np.uint8)
        b[:, [0, 1]] = b[:, [1, 0]]                          # R G B (W) → G R B (W), the strip's wire order
        try:
            d.spi.writebytes2(spi_frame(b))
        except OSError as e:
            log.warning("SPI strip %s: %s", d.id, e)
            d.spi = None
            d.status.update(ok=False, note=f"SPI error: {e}")

    def _open_spi(self, d):
        try:
            import spidev
        except ImportError:
            d.status.update(ok=False, note="spidev missing (only on the Pi)")
            return
        try:
            spi = spidev.SpiDev()
            spi.open(d.spi_bus, d.spi_dev)
            spi.max_speed_hz = SPI_HZ
            spi.mode = 0
            d.spi = spi
            d.status.update(ok=True, ip=f"SPI {d.spi_bus}.{d.spi_dev}", note=f"GPIO10 · max {d.max_ma:.0f} mA")
            log.info("SPI strip %s on /dev/spidev%d.%d (%d LEDs, max %d mA)", d.id, d.spi_bus, d.spi_dev,
                     d.n, d.max_ma)
        except OSError as e:
            d.status.update(ok=False, note=f"SPI not available: {e}")

    async def connect(self):
        for d in self.devices.values():
            if d.kind == "spi":
                self._open_spi(d)
        await asyncio.gather(*(self._keep_watching(d) for d in self.devices.values() if d.kind != "spi"))

    async def _keep_watching(self, d):
        """_watch, restarted after any error: one misbehaving WLED must never bring the host down."""
        while True:
            try:
                await self._watch(d)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("WLED %s watch error (%s: %s), retrying", d.id, type(e).__name__, e)
                d.status.update(ok=False, note="error, retrying")
                await asyncio.sleep(5)

    async def _watch(self, d):
        """Find the WLED (mDNS first, then the configured IP), then check on it every 15 s."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as http:
            while True:
                ip = d.status["ip"] if d.status["ok"] else None
                if not ip:
                    ip = await asyncio.to_thread(self._mdns, d.mdns) or d.host
                info = await self._get(http, f"http://{ip}:{d.http_port}/json/info") if ip else None
                if info:
                    leds = info.get("leds", {})
                    if not d.status["ok"]:
                        log.info("WLED %s online at %s (%s LEDs, %s)", d.id, ip, leds.get("count"),
                                 "RGBW" if leds.get("rgbw") else "RGB")
                        try:                                # a unit that (re)connects follows the room: off stays off
                            await http.post(f"http://{ip}:{d.http_port}/json/state",
                                            json={"on": True, "bri": 255} if self.enabled else {"on": False})
                        except (aiohttp.ClientError, asyncio.TimeoutError):   # a slow unit must never stop the host
                            pass
                    if leds.get("count") and leds["count"] != d.n:
                        log.warning("WLED %s reports %s LEDs, config says %d", d.id, leds["count"], d.n)
                    d.addr = (ip, 4048)
                    d.status.update(ok=True, ip=ip, note=f"WLED {info.get('ver', '')}")
                    await asyncio.sleep(15)
                else:
                    if d.status["ok"]:
                        log.warning("WLED %s lost", d.id)
                    d.status.update(ok=False, note="not found, retrying")
                    await asyncio.sleep(5)

    @staticmethod
    async def _get(http, url):
        try:
            async with http.get(url) as r:
                return await r.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return None

    @staticmethod
    def _mdns(name):
        if not name:
            return None
        try:
            from zeroconf import Zeroconf
            zc = Zeroconf()
            try:
                info = zc.get_service_info("_wled._tcp.local.", f"{name}._wled._tcp.local.", timeout=2500)
                if info and info.parsed_addresses():
                    return info.parsed_addresses()[0]
            finally:
                zc.close()
        except Exception as e:
            log.debug("mDNS lookup failed: %s", e)
        return None

    def set_on(self, on):
        """Switch every reachable WLED on (full brightness, the host dims) or off. Blocking (short timeouts)."""
        payload = {"on": True, "bri": 255} if on else {"on": False}
        for d in self.devices.values():
            if d.kind == "spi":
                if not on and d.spi is not None:
                    self._send_spi(d, black=True)            # a strip on the Pi keeps its last frame otherwise
                continue
            if d.status["ok"]:
                try:
                    req = urllib.request.Request(f"http://{d.status['ip']}:{d.http_port}/json/state", data=json.dumps(payload).encode(),
                                                 headers={"Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=1)
                except OSError:
                    pass

    def off(self):
        """On exit: switch the WLEDs off (they would fall back to their own effect otherwise)."""
        self.set_on(False)
