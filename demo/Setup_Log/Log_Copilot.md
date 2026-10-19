# Copilot task log

## 2026-10-06 21:09 — Accent expansion and clock drag (Tasks A+B)
- Files: `host/core/light.py`, `host/core/room.py`, `host/room.toml`, `host/tests/test_host_core.py`, `host/web/app.js`, `host/web/index.html`.
- Task A: added LED-safe ground-derived expand colors and 1.25× ground brightness with floor, duck, sound lift and Morning-Jam-only mic lift; kept `circadian`/`season` fallback behavior. Task B: curve drag previews locally and sends one final clock value on pointer release; adds pointer-capture cleanup and a cross-tab local-storage lease. All `?v=` asset tags bumped to 34.
- Tested: `python -m pytest tests -q` → 17 passed, 1 skipped; Python compile check passed; `node --check host/web/app.js` passed; all four asset tags verified at `v=34`. No server was launched, no hardware tested, and no Pi contacted.
- Undo: remove `accent_from_ground`/expand handling and the Room tick data feeds, remove the added `[light]` keys and two accent tests; restore the former `curveInput()` and change `?v=34` back to `?v=33` in `index.html`.

## 2026-10-06 21:07 — Accent light expands GROUND (Task A)
- Files: `host/core/light.py`, `host/core/room.py`, `host/room.toml`, `host/tests/test_host_core.py`.
- Changed: LED-safe `accent_from_ground`; `expand` is the room default and follows scalar `Room.day()` ground level at 1.25× with floor, duck, smooth sound-reactive lift, and Morning-Jam-only mic lift. Legacy circadian/season render paths retain the old base-glow behavior.
- Tested: full suite `17 passed, 1 skipped`; compile checks pass. Acceptance RGB outputs: morning `(0.122, 0.554, 1.000)`, neutral `(1.000, 0.562, 0.035)`, golden `(1.000, 0.402, 0.020)`, pre-sleep `(1.000, 0.324, 0.017)`, dim night `(0.850, 0.180, 0.030)`; brightness ratio `1.25`.
- Undo: remove `accent_from_ground` and expand fields/branch from `host/core/light.py`; revert `host/core/room.py` accent mode/audio/mic gating; remove the added `[light]` keys from room.toml; remove the two expand tests. No deployment performed.

## 2026-10-01 — C2 compressed room streams
- Files: `host/core/web.py`, `host/tests/test_room_stream.py`, `Plan/Migration_HA.md`, `Prompts/Copilot_Integration_Notes.md`.
- Tested: Python syntax check passed; `/room.flac` missing-ffmpeg response test passed directly. FLAC/MP3 stream test skipped because ffmpeg is unavailable locally.
- Undo: remove the two compressed route registrations and `_room_compressed` / `_feed_ffmpeg` from `host/core/web.py`; remove `host/tests/test_room_stream.py`; revert C2 migration, integration-note, and log entries.

## 2026-10-01 — C1 Home Assistant entity bridge
- Files: `host/core/ha_bridge.py`, `host/tests/test_ha_bridge.py`, `Plan/Migration_HA.md`, `Prompts/Copilot_Integration_Notes.md`.
- Tested: bridge syntax check passed; fake aiohttp HA WebSocket test passed when invoked directly (pytest is unavailable in the terminal executable; see C3 entry).
- Undo: remove `host/core/ha_bridge.py` and `host/tests/test_ha_bridge.py`; revert the C1 sections in migration, integration notes, and this log.

## 2026-10-01 — C3 host test suite
- Files: `host/tests/test_host_core.py`, `host/requirements-dev.txt`, `Prompts/Copilot_Integration_Notes.md`.
- Tested: direct invocation of all non-xfailed C3 behavior test functions passed; the 6500 K blue-dominance test reproduces its expected failure. `host/main.py --list-devices` passed (imports and device enumeration only). `python -m pytest tests -q` could not start: terminal interpreter reports `No module named pytest`, despite the environment package inventory and installer reporting pytest 9.1.1.
- Known issue: `host/core/room.py:62` normalizes 6500 K RGB with red and blue tied at 1.0; documented and xfailed in the test suite per file ownership rules.
- Undo: remove `host/tests/test_host_core.py` and `host/requirements-dev.txt`; revert the C3 entry in integration notes and remove this log entry.

Summary: Added `accent_colour = "expand"` and the optional one-command-per-drag clock update.
Tests: 17 passed, 1 skipped; JS syntax, Python compilation and HTML cache tags passed.
Acceptance RGB (linear LED values): morning `(0.122, 0.554, 1.000)`; neutral `(1.000, 0.562, 0.035)`; golden `(1.000, 0.402, 0.020)`.
Acceptance RGB continued: pre-sleep `(1.000, 0.324, 0.017)`; dim night `(0.850, 0.180, 0.030)`; brightness ratio `1.25`.
Claude real-strip check: verify blue morning and low-blue warm evenings on SK6812 RGBW, confirm current stays within PSU limit, confirm weather/sound lift and only Morning Jam mic response.