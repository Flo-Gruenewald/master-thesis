"""Copies the real sounds from the VR prototype into Prototype/Demo/Sounds/ (48 kHz, 16-bit).

Beds are cut to ~30 s seamless loops (equal-power crossfade of the tail into the head);
accents are short cuts with fades. Sources: E:/UE/Tools/transit_src/ (CC0 Freesound previews,
see Soundscapes/MANIFEST.md there; Lena's voice: ElevenLabs take from the VR prototype).
Run once on the laptop:  python tools/import_vr_sounds.py
"""
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SRC = Path("E:/UE/Tools/transit_src")
SC = SRC / "audio" / "Soundscapes"
OUT = Path(__file__).resolve().parents[2] / "Sounds"
SR = 48000


def load(path):
    x, sr = sf.read(str(path), dtype="float32", always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = x[:, :2]
    if sr != SR:
        g = gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    return x


def loudest(x, sec):
    """Start index of the loudest window of length sec (for picking a good cut)."""
    n = int(sec * SR)
    if len(x) <= n:
        return 0
    e = np.convolve((x ** 2).mean(axis=1), np.ones(SR // 10), "same")
    best = np.argmax(np.convolve(e, np.ones(n // (SR // 10) or 1), "valid")[: len(x) - n])
    return int(best)


def loop(x, sec=30.0, xf=3.0, start=5.0):
    a = int(start * SR)
    n, f = int(sec * SR), int(xf * SR)
    seg = x[a:a + n + f]
    if len(seg) < n + f:
        seg = x[: n + f]
    t = np.linspace(0, np.pi / 2, f, dtype=np.float32)[:, None]
    head = seg[:f] * np.sin(t) + seg[n:n + f] * np.cos(t)
    return np.concatenate([head, seg[f:n]])


def cut(x, sec, fade_in=0.3, fade_out=1.0, start=None):
    a = loudest(x, sec) if start is None else int(start * SR)
    y = x[a:a + int(sec * SR)].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    y[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]
    y[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
    return y


def save(rel, x, peak=0.7):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    m = float(np.abs(x).max()) + 1e-9
    sf.write(str(p), np.clip(x * (peak / m), -1, 1), SR, subtype="PCM_16")
    print(f"{rel:32s} {len(x) / SR:5.1f} s")


def main():
    # GROUND beds (names used in room.toml [seasons.*])
    save("ground/rain.wav", loop(load(SC / "SEASON_Spring_Rain.wav")))
    save("ground/birds.wav", loop(load(SC / "SEASON_Spring_Birds.wav")))
    save("ground/crickets.wav", loop(load(SC / "SEASON_Summer.wav")))
    save("ground/wind.wav", loop(load(SC / "SEASON_Autumn.wav")))
    save("ground/winter.wav", loop(load(SC / "SEASON_Winter.wav")))
    save("ground/room_tone.wav", loop(load(SC / "AMB_ShipHum.wav")), peak=0.5)
    # MIDDLE accents
    save("accent/cat_meow.wav", load(SC / "SFX_CatMeow.wav"))
    save("accent/bird_cross.wav", cut(load(SC / "SEASON_Spring_Birds.wav"), 4.0, 0.2, 0.8))
    save("accent/rain_pass.wav", cut(load(SC / "SEASON_Spring_Rain.wav"), 10.0, 3.0, 3.0, start=20))
    save("accent/wind_gust.wav", cut(load(SC / "SEASON_Autumn.wav"), 6.0, 1.5, 2.0))
    # Scenario 2 · Spring Cleaning
    save("s2/cat_meow_2.wav", load(SC / "SFX_CatMeow_02.wav"))
    save("s2/cat_purr.wav", loop(load(SC / "SFX_CatPurr.wav"), 15.0, 2.0, 3.0), peak=0.5)
    save("s2/rewind.wav", load(SC / "SFX_Rewind_Card.wav"))
    save("s2/trace.wav", load(SC / "SFX_Trace_Forming.wav"))
    save("s2/chime.wav", load(SC / "SFX_UI_Soft_Chime.wav"))
    save("s2/music.wav", load(SRC / "audio" / "MUS_SpringCleaning.wav"))
    # Scenario 3 · I Miss You, Sis
    save("s3/lena_01.wav", load(SRC / "audio" / "VO" / "VO_L01.wav"), peak=0.8)
    save("s3/rain_window.wav", loop(load(SC / "AMB_Rain_Window.wav")))
    save("s3/rain_soft.wav", loop(load(SC / "SFX_Rain_Soft_Loop.wav")))
    save("s3/movie_room.wav", loop(load(SC / "SFX_Movie_Room.wav")), peak=0.5)
    save("s3/invite.wav", load(SC / "SFX_Invite_Chime.wav"))
    save("s3/screen_wake.wav", load(SC / "SFX_Screen_Wake.wav"))
    save("s3/arrive.wav", load(SC / "SFX_UI_Soft_Chime.wav"))
    save("s3/music.wav", load(SRC / "audio" / "MUS_IMissYouSis.wav"))
    (OUT / "SOURCES.md").write_text(
        "# Sound sources\n\n"
        "- `MJ_*`, `SFX_Tap_Player`, `SFX_Tablet_Offer`: generated for the VR prototype (`E:/UE/Tools/make_s1_stems_v2.py`).\n"
        "- `ground/`, `accent/`, `s2/`, `s3/` (except music and voice): CC0 recordings from Freesound (HQ previews), "
        "collected for the VR prototype; per-file source, author and licence: `E:/UE/Tools/transit_src/audio/Soundscapes/MANIFEST.md`. "
        "Imported with `tools/import_vr_sounds.py` (cut to loops/one-shots, 48 kHz 16-bit).\n"
        "- `s2/music.wav`, `s3/music.wav`: the VR prototype's scenario music (`MUS_SpringCleaning`, `MUS_IMissYouSis`).\n"
        "- `s3/lena_01.wav`: Lena's voice (ElevenLabs, VR prototype take VO_L01).\n"
        "- `ground/fire.wav` and `accent/bee_pass`, `thunder_far`: none yet → generated placeholders (`core/synth.py`).\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
