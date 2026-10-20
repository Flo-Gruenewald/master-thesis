import sys
import time
import tomllib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

HOST_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOST_DIR))

from core.ambient import AVoice, Mixer
from core.light import Light, accent_from_ground
from core.room import Room, cct_rgb
from main import Host


@pytest.fixture(scope="module")
def config():
    with (HOST_DIR / "room.toml").open("rb") as stream:
        return tomllib.load(stream)


def test_cct_rgb_is_normalized_and_warm_at_2200k():
    warm = cct_rgb(2200)
    cool = cct_rgb(6500)

    assert warm.min() >= 0 and warm.max() == pytest.approx(1)
    assert cool.min() >= 0 and cool.max() == pytest.approx(1)
    assert warm[0] > warm[2]


def test_cct_rgb_warm_to_daylight():
    # 6500 K is daylight white (about neutral), not blue; blue only wins above it
    warm, day, cold = cct_rgb(2700), cct_rgb(6500), cct_rgb(9000)
    assert warm[0] > warm[2]
    assert abs(day[0] - day[2]) < 0.05
    assert cold[2] > cold[0]


def test_day_light_seasons_and_dawn_dusk(config):
    class AudioStub:
        sr = 48000

    host_stub = SimpleNamespace(
        audio=AudioStub(), light=object(), cfg={"audio": {"stems_dir": str(HOST_DIR.parent / "Sounds")},
                                                "room": config["room"], "seasons": config["seasons"]}
    )
    room = Room(host_stub)

    for season, settings in config["seasons"].items():
        room.season = season
        night, _ = room.day_light(2)
        noon, _ = room.day_light(12)
        assert night == pytest.approx(settings["night_level"])
        assert noon == pytest.approx(settings["peak_level"], abs=0.02)

        dawn = settings["dawn_h"]
        dusk = settings["dusk_h"]
        assert room.day_light(dawn - 0.5)[0] <= room.day_light(dawn)[0] <= room.day_light(dawn + 0.5)[0]
        assert room.day_light(dusk - 0.5)[0] >= room.day_light(dusk)[0] >= room.day_light(dusk + 0.5)[0]


def make_light():
    cfg = {
        "light": {"fps": 40, "max_brightness": 1},
        "wled": [{"id": "w", "led_count": 4}],
    }
    spots = [
        {"id": "moment", "light": "w", "leds": [0, 2], "moment": True},
        {"id": "middle", "light": "w", "leds": [2, 2], "middle": True},
    ]
    return Light(cfg, spots)


def test_light_ground_middle_and_top_layers_are_spatially_scoped():
    light = make_light()
    try:
        ground = np.array([0.2, 0.3, 0.4])
        light.room_ground(ground, fade=0.001)
        light.render(1)
        assert np.allclose(light.vpx[:2], light.vg[:2])
        assert np.allclose(light.vg[:2], ground)
        assert np.allclose(light.vg[2:], ground)

        light.accent([1, 0, 0], amp=1, seconds=2, mode="glow", width=1)
        light.render(0.5)
        light.render(0.5)
        assert np.any(light.vm[2:] > 0)
        assert np.allclose(light.vm[:2], 0)

        light.spotlight([0, 1, 0], 1, width=1, fade=0.001)
        light.render(1)
        assert np.any(light.vt[:2] > 0)
        assert np.allclose(light.vt[2:], 0)

        preview = light.preview()
        for key in ("px", "g", "m", "t"):
            assert len(preview[key]) == light.vn * 6
            assert all(char in "0123456789abcdef" for char in preview[key])
    finally:
        light.sock.close()


def test_accent_from_ground_led_color_acceptance():
    samples = [
        ("morning", (0.82, 0.90, 1.0)),
        ("neutral", (1.0, 0.93, 0.85)),
        ("golden", (1.0, 0.75, 0.50)),
        ("presleep", (1.0, 0.65, 0.35)),
        ("night", tuple(cct_rgb(1800) * 0.04)),
    ]
    result = {name: accent_from_ground(rgb) for name, rgb in samples}

    morning = result["morning"]
    assert morning[2] == pytest.approx(1.0)
    assert morning[0] <= 0.3
    assert 0.5 <= morning[1] <= 0.7

    neutral = result["neutral"]
    assert neutral[0] == pytest.approx(1.0)
    assert neutral[2] <= 0.35
    assert neutral[1] < 0.8

    golden = result["golden"]
    assert golden[0] == pytest.approx(1.0)
    assert 0.3 <= golden[1] <= 0.45
    assert golden[2] <= 0.05

    presleep = result["presleep"]
    assert presleep[0] == pytest.approx(1.0)
    assert 0.25 <= presleep[1] <= 0.35
    assert presleep[2] <= 0.04

    night = result["night"]
    assert night[0] == pytest.approx(0.85, abs=0.02)
    assert night[1] <= 0.2
    assert night[2] <= 0.03


def test_expand_accent_tracks_ground_brightness_audio_and_duck():
    cfg = {
        "light": {"fps": 40, "max_brightness": 1, "accent_colour": "expand",
                  "accent_over_ground": 1.25, "accent_floor": 0.12, "accent_saturation": 1.0,
                  "accent_warm_push": 0.85, "accent_cool_push": 0.9, "accent_react": 1.2},
        "wled": [{"id": "strip", "led_count": 2}],
    }
    spots = [{"id": "wall", "light": "strip", "leds": [0, 1], "level": "ground"},
             {"id": "table", "light": "strip", "leds": [1, 1], "level": "accent"}]
    light = Light(cfg, spots)
    try:
        ground = np.array([0.4, 0.4, 0.4])
        light.ground_level = 0.4
        light.room_cur["wall"] = ground.copy()
        light.room_cur["table"] = ground.copy()
        light.room_tgt["wall"] = ground.copy()
        light.room_tgt["table"] = ground.copy()
        light.room_rate["wall"] = light.room_rate["table"] = 0.0
        light.render(0.01)
        assert np.max(light.vpx[1]) == pytest.approx(0.4 * 1.25)

        light.set_duck(0.6, fade=0.001)
        light.render(0.01)
        assert np.max(light.vpx[1]) == pytest.approx(0.4 * 1.25 * 0.6)

        dim_level = np.max(light.vpx[1])
        light.accent_audio = 0.2
        light.render(0.05)
        assert dim_level < np.max(light.vpx[1]) <= 0.6

        # the mic lifts the light; main.py sets light.mic only while Morning Jam runs (0 otherwise)
        light.accent_audio = 0.0
        light.mic = 0.0
        light._acc_env = 0.0
        light.render(0.01)
        mic_off = np.max(light.vpx[1])
        light.mic = 1.0
        light.render(0.01)
        assert np.max(light.vpx[1]) > mic_off
    finally:
        light.sock.close()


@pytest.mark.parametrize("mode", ["circadian", "season"])
def test_legacy_accent_modes_keep_their_base_ground_glow(mode):
    ground = np.array([0.4, 0.3, 0.2])
    cfg = {"light": {"fps": 40, "max_brightness": 1, "accent_colour": mode, "accent_base": 0.15},
           "wled": [{"id": "strip", "led_count": 1}]}
    spots = [{"id": "table", "light": "strip", "leds": [0, 1], "level": "accent"}]
    light = Light(cfg, spots)
    try:
        light.room_cur["table"] = ground.copy()
        light.room_tgt["table"] = ground.copy()
        light.room_rate["table"] = 0.0
        light.render(0.01)
        assert np.allclose(light.vpx[0], ground * 0.15)
    finally:
        light.sock.close()


def test_top_spotlight_is_one_lamp_for_the_moment_and_proximity_when_idle():
    rust = np.array([227, 113, 86], dtype=float) / 255
    cfg = {
        "light": {"fps": 40, "max_brightness": 1, "top_spotlight_color": "#E37156", "top_spotlight_idle": 0.0,
                  "accent_base": 0.15, "proximity": {"enabled": True, "full_m": 0.6, "soft_m": 4.0,
                                                     "soft_level": 0.1, "fade_s": 0.01}},
        "wled": [{"id": "top", "led_count": 3}, {"id": "table", "led_count": 4}],
    }
    spots = [{"id": "top_spotlight", "light": "top", "leds": [0, 3], "level": "top"},
             {"id": "table", "light": "table", "leds": [0, 4], "level": "accent"}]
    light = Light(cfg, spots)
    try:
        top, acc = slice(0, 3), slice(3, 7)
        light.room_ground(np.array([0.4, 0.4, 0.4]), fade=0.001)
        light.render(1)
        assert np.allclose(light.vpx[top], 0)                       # nobody, no scenario: off
        assert np.allclose(light.vg[acc], 0.4 * 0.15)               # accent: faint day colour only
        light.set_proximity(10000)
        light.render(1)
        assert np.allclose(light.vt[top], rust * 0.1)               # someone far away: soft, evenly
        light.accent([0, 1, 0], amp=1, seconds=2, mode="glow", width=1)
        light.render(0.5)
        light.render(0.5)
        assert np.any(light.vm[acc] > 0) and np.allclose(light.vm[top], 0)   # accents only on accent spots

        light.set_scenario_running(True)
        light.spotlight([0, 0, 1], 0.5, fade=0.001)
        light.render(1)
        assert np.allclose(light.vt[top], [0, 0, 0.5])              # the scenario's spotlight, whole lamp
        light.pulse("table", [1, 0, 0], amp=1)                       # a tap: goes to the TOP lamp
        assert [p["spot"] for p in light.pulses] == ["top_spotlight"]
        light.render(0.001)
        assert light.vt[0, 0] > 0.5 and np.allclose(light.vt[top][:, 0], light.vt[0, 0])
    finally:
        light.sock.close()


class BusStub:
    prefix = "easteregged"

    def __init__(self):
        self.messages = []

    def publish_raw(self, topic, payload, retain=False):
        self.messages.append((topic, payload, retain))


def test_presence_median_confirmation_targets_and_expiry(monkeypatch):
    host = Host.__new__(Host)
    host.power = True
    host.cfg = {"host": {"cooldown_s": 0}}
    host.pcfg = {"near_cm": 100, "hysteresis_cm": 20, "confirm_readings": 3, "median_of": 3,
                 "ghost_confirm_s": 0.0, "ghost_merge_mm": 400}
    host.present = False
    host.distance = None
    host.pres_src = None
    host.pres_t = 0
    host.absent_since = time.monotonic()
    host._streak = 0
    from collections import deque
    host._dist = deque(maxlen=3)
    host.dirty = False
    host.auto = False
    host.scenario = SimpleNamespace(starts_on_presence=False)
    host.running = False
    host.quiet_until = host.cooldown_until = 0
    host.spots = [{"id": "left", "pos": [-100, 1000]}, {"id": "right", "pos": [100, 1000]}]
    host.targets = {}
    host.wtargets = {}
    host.radar_count = None
    host.radar_t = 0
    events = []
    host.event = events.append

    host.on_presence("in/presence", {"distance_cm": 150})
    host.on_presence("in/presence", {"distance_cm": 30})
    host.on_presence("in/presence", {"distance_cm": 30})
    assert host.distance == 30
    assert not host.present
    host.on_presence("in/presence", {"distance_cm": 30})
    assert host.present

    host.on_presence_state("in/presence/state", "OFF")
    assert not host.present
    host.on_presence_state("in/presence/state", "ON")         # radar ON without a (filtered) person = ghost
    assert not host.present
    host.on_target("in/presence/target/1/x", "-90")
    host.on_target("in/presence/target/1/y", "1000")
    host.on_presence_state("in/presence/state", "ON")
    assert host.present
    host.on_presence_state("in/presence/state", "unavailable")
    assert host.present

    host.on_presence_count("in/presence/count", "2")
    assert host.radar_count == 2
    host.on_target("in/presence/target/1/x", "-90")
    host.on_target("in/presence/target/1/y", "1000")
    assert host.people == [{"n": 1, "x": -90, "y": 1000, "d": 1004, "spot": "left", "src": "spot"}]

    host.targets[2] = {"x": 0, "y": 1000, "t": time.monotonic() - 4}
    assert len(host.people) == 1
    assert events


def test_ambient_voices():
    samples = np.arange(8, dtype=np.float32).reshape(4, 2)
    loop = AVoice(samples, 1, 0, 4, loop=True)
    loop.g = loop.target = 1
    first = loop.render(6)
    assert first.shape == (6, 2)
    assert np.array_equal(first[4:], samples[:2])

    one_shot = AVoice(samples, 1, 0, 4)
    assert one_shot.render(4).shape == (4, 2)
    assert one_shot.render(1) is None
    assert one_shot.done

    ramp = AVoice(samples, 0, 0, 4, loop=True)
    ramp.ramp(1, 1)
    ramp.render(4)
    assert ramp.g == pytest.approx(1)
    mixer = Mixer(4)
    mixer.add(ramp)
    assert mixer.mix(2).shape == (2, 2)

def test_radar_ghost_filter_confirms_and_merges():
    host = Host.__new__(Host)
    host.pcfg = {"ghost_confirm_s": 1.0, "ghost_merge_mm": 400}
    host.spots = []
    host.targets = {}
    host.wtargets = {}
    host.radar_t = 0
    host.on_target("in/presence/target/1/x", "0")
    host.on_target("in/presence/target/1/y", "2000")
    assert host.people == []                                   # not yet seen for 1 s
    now = time.monotonic()
    host.targets[1]["first"] = now - 2                         # person 1: seen steadily for 2 s
    host.targets[2] = {"x": 150, "y": 2100, "t": now, "first": now - 2}   # reflection 18 cm away
    host.targets[3] = {"x": -1500, "y": 2500, "t": now, "first": now - 0.3}  # brief ghost
    ppl = host.people
    assert [p["n"] for p in ppl] == [1]
    assert ppl[0]["d"] == 2000


def test_proximity_light_off_soft_and_bright(config):
    light = Light(config, config["spots"])
    if not light.prox_on:
        return
    top = next(k for k, s in light.spots.items() if s["top_spotlight"])
    s = light.spots[top]

    def level(d):
        light.set_proximity(d)
        for _ in range(400):
            light.render(1 / 40)
        return light.vt[s["v"]:s["v"] + s["n"]].max() / max(light.top_spotlight_rgb)

    assert level(None) == 0
    assert abs(level(10000) - light.prox_soft_level) < 0.01
    assert level(2000) < level(1000) < level(300)
    assert abs(level(300) - 1.0) < 0.01


def test_spi_strip_encoding_and_current_limit():
    from core.light import spi_frame, limit_current, _SPI_LUT
    assert list(_SPI_LUT[0]) == [0b10010010, 0b01001001, 0b00100100]     # 0 → 100 100 100 …
    assert list(_SPI_LUT[255]) == [0b11011011, 0b01101101, 0b10110110]   # 1 → 110 110 110 …
    b = np.array([[255, 0, 0, 0], [0, 0, 0, 255]], dtype=np.uint8)
    f = spi_frame(b)
    assert len(f) == 2 * 4 * 3 + 64 and not f[-64:].any()
    full = np.ones((89, 4))
    x, ma = limit_current(full, 800)
    assert ma == 800 and float(x.sum()) * 12 + 89 < 801
    x, ma = limit_current(np.full((89, 4), 0.01), 800)
    assert ma < 800 and np.allclose(x, 0.01)


def test_radar_frozen_ghosts_near_zone_and_wall_fusion():
    host = Host.__new__(Host)
    host.pcfg = {"ghost_confirm_s": 1.0, "ghost_merge_mm": 450, "stale_s": 3.0, "spot_min_mm": 550,
                 "wall_offset_mm": [905, -320], "wall_max_mm": 3000}
    host.spots = []
    host.targets = {}
    host.wtargets = {}
    now = time.monotonic()
    host.targets[1] = {"x": 500, "y": 1000, "t": now, "first": now - 5, "moved": now - 0.5}    # person (jitters)
    host.targets[2] = {"x": -147, "y": 249, "t": now, "first": now - 9, "moved": now - 0.5}    # at the lamp
    host.targets[3] = {"x": 900, "y": 1800, "t": now, "first": now - 9, "moved": now - 8}      # frozen ghost
    host.wtargets[1] = {"x": -400, "y": 1350, "t": now, "first": now - 5, "moved": now - 0.5}  # same person
    host.wtargets[2] = {"x": -1500, "y": 2400, "t": now, "first": now - 5, "moved": now - 0.5}  # 2nd person
    host.wtargets[3] = {"x": -1200, "y": 3200, "t": now, "first": now - 5, "moved": now - 0.5}  # too far
    ppl = host.people
    assert [(p["src"], p["n"]) for p in ppl] == [("spot", 1), ("wall", 12)]
    assert (ppl[1]["x"], ppl[1]["y"]) == (-595, 2080)


def test_spring_staged_and_two_second_empty():
    from scenarios import spring_cleaning as sc
    s = sc.Scenario.__new__(sc.Scenario)
    s.host = SimpleNamespace(people=[{"x": 0, "y": 900, "d": 900}])
    s.flags, s.trail, s.linger, s.near, s.empty_since, s.staged = set(), [], 0.0, 0.8, None, None
    t = 100.0
    assert s._watch(t) is False                       # someone there: no pass
    lit = s.near
    s.host.people = []
    s._watch(t + 1.0)
    assert s.near == lit                              # 1 s empty: still lit (radar dropouts)
    s._watch(t + 3.5)
    assert s.near < lit                               # > 2 s empty: fading to dark
    s.host.people = [{"x": 0, "y": 900, "d": 900}]
    assert s._watch(t + 4.0) is True                  # the next person = next phase
    s.command("spring_empty", None)
    assert s._watch(t + 5.0) is False and s.near < lit   # staged empty ignores the radar
    s.command("spring_someone", None)
    assert s._watch(t + 6.0) is True                  # staged pass = next phase
