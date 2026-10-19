"""Procedural placeholder sounds for the room (Ground beds, Middle accents).

Used only when no recorded file exists in stems/ground/ or stems/accent/ (e.g. the ElevenLabs
sounds that have no file in Sounds/ yet). All return float32 stereo arrays at the given rate.
"""
import numpy as np
from scipy.signal import butter, lfilter

RNG = np.random.default_rng(7)


def _lp(x, hz, sr, order=2):
    b, a = butter(order, hz / (sr / 2), "low")
    return lfilter(b, a, x, axis=0)


def _bp(x, lo, hi, sr, order=2):
    b, a = butter(order, [lo / (sr / 2), hi / (sr / 2)], "band")
    return lfilter(b, a, x, axis=0)


def _stereo(x, width=0.0):
    """Mono → stereo; width > 0 decorrelates the channels a little."""
    if width <= 0:
        return np.column_stack([x, x]).astype(np.float32)
    d = int(len(x) * 0.0007) + 1
    return np.column_stack([x, np.roll(x, d) * (1 - width) + x * width]).astype(np.float32)


def _norm(x, peak=0.5):
    m = float(np.max(np.abs(x))) + 1e-9
    return (x * (peak / m)).astype(np.float32)


def _loopable(x, sr, xf=0.5):
    """Crossfade the tail into the head so the buffer loops without a click."""
    n = int(xf * sr)
    if len(x) <= 2 * n:
        return x
    ramp = np.linspace(0, 1, n, dtype=np.float32)
    if x.ndim == 2:
        ramp = ramp[:, None]
    head = x[:n] * ramp + x[-n:] * (1 - ramp)
    return np.concatenate([head, x[n:-n]])


def _env(n, sr, a=0.02, r=0.2):
    e = np.ones(n, np.float32)
    na, nr = max(1, int(a * sr)), max(1, int(r * sr))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


# ---- Ground beds (loop) ------------------------------------------------------------------

def rain(sr, sec=12.0):
    n = int(sec * sr)
    x = _lp(RNG.standard_normal(n), 3500, sr) * 0.5
    x += _bp(RNG.standard_normal(n), 1500, 6000, sr) * 0.25
    drops = np.zeros(n)
    idx = RNG.integers(0, n, int(sec * 60))
    drops[idx] = RNG.uniform(0.3, 1.0, len(idx))
    x += _bp(drops, 2000, 7000, sr) * 2.0
    return _loopable(_stereo(_norm(x, 0.4), 0.6), sr)


def wind(sr, sec=14.0):
    n = int(sec * sr)
    t = np.arange(n) / sr
    x = np.cumsum(RNG.standard_normal(n))
    x -= _lp(x, 0.5, sr)
    x = _bp(x, 80, 900, sr)
    sweep = 0.55 + 0.45 * np.sin(2 * np.pi * t / sec + 0.3 * np.sin(2 * np.pi * 3 * t / sec))
    return _loopable(_stereo(_norm(x * sweep, 0.4), 0.5), sr, 1.0)


def crickets(sr, sec=10.0):
    n = int(sec * sr)
    t = np.arange(n) / sr
    x = np.zeros(n)
    for f0, rate, ph in ((4300, 2.1, 0.0), (4700, 1.7, 0.4), (3900, 2.6, 0.8)):
        gate = (np.sin(2 * np.pi * rate * t + ph) > 0.55).astype(float)
        trill = (np.sin(2 * np.pi * 28 * t) > 0).astype(float)
        x += np.sin(2 * np.pi * f0 * t) * _lp(gate * trill, 300, sr) * RNG.uniform(0.4, 0.8)
    x += _bp(RNG.standard_normal(n), 200, 1200, sr) * 0.05
    return _loopable(_stereo(_norm(x, 0.25), 0.7), sr)


def fire(sr, sec=10.0):
    n = int(sec * sr)
    x = _lp(np.cumsum(RNG.standard_normal(n)) * 0.002, 400, sr)
    x -= _lp(x, 2, sr)
    pops = np.zeros(n)
    idx = RNG.integers(0, n, int(sec * 14))
    pops[idx] = RNG.uniform(0.2, 1.0, len(idx)) * RNG.choice([1, -1], len(idx))
    x = x * 4 + _bp(pops, 800, 6000, sr) * 3
    return _loopable(_stereo(_norm(x, 0.35), 0.4), sr)


def room_tone(sr, sec=10.0):
    n = int(sec * sr)
    t = np.arange(n) / sr
    x = _lp(RNG.standard_normal(n), 250, sr) * 0.6 + 0.08 * np.sin(2 * np.pi * 50 * t)
    return _loopable(_stereo(_norm(x, 0.12), 0.3), sr)


# ---- Middle accents (one-shots) ----------------------------------------------------------

def bird_cross(sr):
    out = []
    for _ in range(RNG.integers(3, 6)):
        d = RNG.uniform(0.08, 0.18)
        n = int(d * sr)
        t = np.arange(n) / sr
        f = RNG.uniform(2800, 4200) + RNG.uniform(-1500, 1500) * t / d
        f = f * (1 + 0.04 * np.sin(2 * np.pi * RNG.uniform(30, 60) * t))
        chirp = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.sin(np.pi * t / d) ** 2
        out += [chirp, np.zeros(int(RNG.uniform(0.04, 0.2) * sr))]
    x = np.concatenate(out)
    return _stereo(_norm(x, 0.5))


def bee_pass(sr, sec=3.0):
    n = int(sec * sr)
    t = np.arange(n) / sr
    f = 210 * (1 + 0.06 * np.sin(2 * np.pi * 11 * t)) * (1.08 - 0.16 * t / sec)  # passing by: pitch drops
    ph = 2 * np.pi * np.cumsum(f) / sr
    x = sum(np.sin(k * ph) / k for k in range(1, 8))
    x *= 0.5 + 0.5 * np.sin(2 * np.pi * 23 * t) ** 2
    x *= np.sin(np.pi * t / sec) ** 2
    return _stereo(_norm(_lp(x, 3000, sr), 0.4))


def cat_meow(sr, sec=0.9):
    n = int(sec * sr)
    t = np.arange(n) / sr
    f = 520 + 260 * np.sin(np.pi * t / sec) - 120 * t / sec
    ph = 2 * np.pi * np.cumsum(f) / sr
    x = sum(np.sin(k * ph) * (0.7 ** k) for k in range(1, 9))
    x = _bp(x, 400, 3500, sr) * np.sin(np.pi * t / sec) ** 1.5
    return _stereo(_norm(x, 0.45))


def wind_gust(sr, sec=6.0):
    x = wind(sr, sec)[:, 0]
    return _stereo(_norm(x * np.sin(np.pi * np.arange(len(x)) / len(x)) ** 2, 0.5), 0.5)


def rain_pass(sr, sec=10.0):
    x = rain(sr, sec + 1)[: int(sec * sr)]
    e = np.sin(np.pi * np.arange(len(x)) / len(x)) ** 1.5
    return (x * e[:, None] * 1.2).astype(np.float32)


def thunder_far(sr, sec=6.0):
    n = int(sec * sr)
    t = np.arange(n) / sr
    x = _lp(RNG.standard_normal(n), 140, sr, 3)
    e = np.exp(-t / 1.6) * (1 - np.exp(-t / 0.15)) * (1 + 0.5 * np.sin(2 * np.pi * 1.3 * t) ** 2)
    return _stereo(_norm(x * e, 0.55), 0.4)


BEDS = {"rain": rain, "wind": wind, "crickets": crickets, "fire": fire, "room_tone": room_tone,
        "winter": wind, "birds": crickets}
ACCENTS = {"bird_cross": bird_cross, "bee_pass": bee_pass, "cat_meow": cat_meow, "wind_gust": wind_gust,
           "rain_pass": rain_pass, "thunder_far": thunder_far}
