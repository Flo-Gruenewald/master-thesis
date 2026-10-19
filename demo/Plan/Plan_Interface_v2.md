# Plan: web interface v2 (night of 01.→02.10.2026)

Work order for Claude, done without Flo. Prompt to start it: `Prompts/Night_2026-10-01_Interface_v2.md`. Tick the boxes here as you go; log every change with undo steps in `Setup_Log/Log.md`.

## Flo's brief (01.10, after the first room test)

- "Really good progress, the sounds are immersive and the lights are (mostly) nice. Fine tuning another day."
- One whole light strip is confusing → **separate strips per level**; same for **sound** (a Ground bed like rain, accents that come periodically).
- See **where** things happen: **subnodes as in the node diagram** (booklet p. 42, `Plan/node-diagram.svg`), then the **experience levels from Top to Ground**.
- The **time of day** control is excellent → make it wide, with a **"Now"** button.
- **Structure (final):** a **sidebar on the left** (like the reference dashboard Flo shared: icon rail, rounded tiles, big numbers, toggles):
  1. **Home** — the light, the clock and the circadian rhythm, the event bar.
  2. **Node** — the node diagram, the devices list, the experiential levels.
  3. **Scenarios** — the 3 scenarios.
  - At the bottom of the sidebar: **Turn off**.
- **Don't copy the reference**: merge the Mars Rust design system with its layout idea. **KEEP IT MINIMAL.** It's Flo's own control machine (operator view), not a visitor screen.

## State before tonight

- **Backend for the level view is patched on the laptop (01.10 ~20:30), not tested, not deployed:** per-level light previews (`light` topic → `{px, g, m, t, acc}`), named voices, `room.sounds()`, `room.now()`, `main.py` `level_sounds()` → state `sounds: {top, middle, ground}`, meter `out` (Top speaker) / `room` (room output), cmd `now`. The old page still works with it.
- **Update 01.10, 22:00:** the level backend is tested (smoke test ok) and deployed; the Pi runs it with the HA stack (host on Mosquitto, `[mqtt] mode = "external"`), idle room by default (`auto_start = false`). Copilot has **finished C1–C3** (tests: 8 passed, 1 skipped, 1 xfail — the xfail expects 6500 K to be bluish; it's daylight white → fix the test in task 5). `core/web.py` now contains Copilot's `/room.flac` / `/room.mp3` routes. Deploy everything at the end.
- Folder cleaned up on 01.10: `Plan/`, `Setup_Log/`, `Prompts/`; the progress file stays at the top.

## Working in parallel with GitHub Copilot (tonight)

Copilot works on the Home Assistant tasks C1–C3 at the same time (`Prompts/Copilot_HA_Tasks.md`). To avoid clashes, **file ownership** is fixed:

| Claude (this plan) | Copilot — don't edit these tonight |
|---|---|
| `host/main.py`, `host/web/*`, `host/core/room.py`, `light.py`, `audio.py`, `ambient.py`, `scenario.py`, `host/scenarios/*`, `host/room.toml`, `host/README.md`, `Setup_Log/Log.md`, `MorningJam_Progress.md`, this plan | `host/core/ha_bridge.py`, `host/core/web.py`, `host/tests/*`, `host/requirements-dev.txt`, `Plan/Migration_HA.md`, `Setup_Log/Log_Copilot.md`, `Prompts/Copilot_Integration_Notes.md` |

If the interface needs a change in `core/web.py` (e.g. a new route): put it into `main.py` or note it for the morning instead — don't edit `web.py` while Copilot works on it. Copilot writes everything it needs in Claude's files into `Prompts/Copilot_Integration_Notes.md`; Claude merges it in task 5.

## Design: Mars Rust × the reference layout

| Element | Decision |
|---|---|
| Base | dark warm: background `#171310`, tiles `#211C17`, 1 px border `#3A2C24`; no glass blur, no shadows; a soft glow only where light is really on |
| Shape | tiles radius 20, inner elements radius 12, gap 12; generous padding; few, large elements per page |
| Type | PP Neue Montreal (Light for big numbers — copy `PPNeueMontreal-Light.woff2` from `Design Dokuz/Mars Rust/mars-rust-design-system/fonts/PP Neue Montreal/…`; Regular/Medium for text). Big numerals like the reference's "23°" for the clock |
| Colour roles | as in the booklet node diagram (Flo, 01.10): **TOP = sand `#E37156`, MIDDLE = blue `#76DBD8`, GROUND = white `#F2EAE3`**; off/alert = `#D0273F`. The postcard (Earth) also uses the blue — open question for Flo whether it needs its own colour |
| Controls | pill toggles (sand when on), segmented buttons, one primary button per tile at most |
| Icons | inline SVG, 1.5 px strokes, no icon library: home, node (three linked dots), scenarios (play/sparkle), power |
| Sidebar | 72 px icon rail, active item = tile colour + sand dot; tooltips with the page name; power at the bottom |
| Header per page | page title left (like "Living Room"), right: connection dot, current moment chip, room clock small |
| Phone | the rail becomes a bottom bar (Home · Node · Scenarios · Off); tiles stack in one column |

## Pages

### Home — "the room at a glance"
- **Clock + circadian rhythm (wide tile):** big room clock, season, K, light %. Below it the **day curve** for the current season (light level over 24 h as an SVG path, like the reference's temperature curve), coloured by colour temperature; a marker at the room's time and a faint marker at the real time. The curve **is** the time control: drag/click to jump (cmd `clock`). **Now** button (cmd `now`). Season segment, day-speed segment (Real · 8 min · 2 min).
- **Light tile:** what the LEDs show now — one composite strip per light subnode (device name, online dot), master brightness slider, Ground on/off toggle.
- **Event bar (full width, bottom):** the last ~8 events as a calm horizontal feed (time · icon/level colour · text), newest left; accents, moments, presence, scenario start/stop, taps.

### Node — "where things happen"
- **Node diagram (large tile):** the room from above, generated from the config (no hard-coded names): moment spots → the table in the centre with its LED pixels as a ring; other spots → along the walls as pixel lines; colours from the composite. Table speaker next to the table, pulsing with `meter.out`; room speaker in a corner pulsing with `meter.room` (dimmed with "shared" if `room.output.kind == "main"`); mic on the table (level ring, red dot while recording); presence sensor at the bottom wall with its cone and people dots (LD2450 `people`, or one dot at `distance_cm` for the ultrasonic); the Pi as controller with thin lines to every subnode; a status dot on each.
- **Devices list:** every subnode with role, address, status, a small live level (speaker, mic, room output) and its control: Top speaker volume (`volume`), room sound (`ambient_volume`), mic sensitivity, light brightness. Home Assistant / MQTT lines when configured.
- **Experiential levels:** three rows TOP / MIDDLE / GROUND, each: label + status (TOP: moment + hint; MIDDLE: next accent in N s + toggle; GROUND: K, light %, "dimmed for the moment" when ducked + toggle) · **its own light strip** (`t` / `m` / `g`, spots separated and labelled) · **its own sound list** with level bars (`state.sounds`; readable labels, e.g. crickets → Crickets, rain_window → Rain on the window, lena_01 → Lena (Earth), MJ_BeatLoop → Beat). MIDDLE row: accent buttons (season's ones highlighted), the playing accent with a progress bar, light-only accents from `light.acc`.

### Scenarios — "the moments"
- **Three cards** (order 1–3): title, value (Tempora / Memoria / –), one-line description, status (idle / running: moment + hint + elapsed), one primary action (Start / Stop).
  - **Morning Jam:** mini loop (playhead + layer marks), mic meter with "● recording", Clear layers.
  - **Spring Cleaning:** "kept jam: N layers" (or "no jam kept yet").
  - **I Miss You, Sis:** **Postcard from Earth** (teal).
- Above the cards: "Presence starts: <selected scenario>" toggle + quiet countdown after a stop.
- **Simulator** (small tile, collapsible): someone arrives / leaves, tap, hum — same messages as the hardware.

### Turn off (sidebar bottom)
- Click → small confirm sheet: "Turn the room off?" → cmd `power` false: the running scenario stops quietly, all sound fades out, the lights fade to black and WLEDs switch off, presence no longer starts anything. The page shows a calm "The room is off" overlay with **Turn on** (cmd `power` true → everything back as before).
- The Pi itself stays on (shutting it down needs sudo — out of scope; Flo uses `sudo poweroff`).

## Tasks

### 1. Backend
- [ ] Silent laptop test of the 01.10 patch (scratchpad `test_room.toml` recipe: master volume 0, dummy WLED hosts, ports 8090/1893): `light` has `px/g/m/t/acc`; `state.sounds` correct during an accent, a season change (old bed fading), Morning Jam, S2, S3; meter `out/room`; cmd `now`.
- [ ] `Room.state()`: add the current season's `dawn_h`, `dusk_h`, `peak_k`, and a 24 h `curve` (e.g. 96 samples of level + K) for the Home curve.
- [ ] State `recent`: the last 12 events (deque in `Host.event`), so the event bar is filled after a reload.
- [ ] cmd `power` (bool) + state `power`: off = stop scenario, fade audio (master → 0 over 2 s), light to black + WLED `{"on": false}`, auto-start ignored; on = restore master/brightness, WLED on, room program resumes. Keep it in `Host` (no scenario changes).
- [ ] README: light topic, state `sounds/recent/power`, meter, cmds `now`/`power`.

### 2. Frontend (rewrite `host/web/`: index.html, app.js, style.css; keep it one page with hash routing `#home` `#node` `#scenarios`, one WebSocket)
- [ ] Shell: sidebar rail + page header + three page containers; phone bottom bar.
- [ ] Home: clock + curve (drag = `clock`, Now, season, speed), light tile, event bar.
- [ ] Node: node diagram SVG, devices list with controls, three level rows.
- [ ] Scenarios: three cards with their specifics, presence toggle, simulator.
- [ ] Turn off: confirm sheet, off overlay, Turn on.
- [ ] Performance: build strips/diagram once, update colours only (~15 fps); lists via `setHTML` (only when changed).

### 3. Check
- [ ] Browser pane at 1280 px and 390 px, all three pages, no console errors; walk through: accent → visible in Node/MIDDLE and Home events; postcard → Scenarios card + Node TOP; power off/on.
- [ ] Screenshots of the three pages (desktop) + one phone view → SendUserFile (`display: render`) in the morning message.

### 5. Merge Copilot's work (before deploying)
- [ ] Read `Prompts/Copilot_Integration_Notes.md` and `Setup_Log/Log_Copilot.md`. Only merge tasks marked done.
- [ ] Run `python -m pytest host/tests` (if it exists) and the silent smoke test. Copilot files that break the host or the tests are **not** hooked in (leave them in place, note it for Flo).
- [ ] Apply the integration notes to `main.py` / `room.toml` / `README.md` (hooks, config sections, README text), re-run tests + smoke test, tick "Merge by Claude" in the notes.
- [ ] Copy Copilot's log entries into `Setup_Log/Log.md` (one combined entry "Copilot C1–C3", with their undo steps), keep `Log_Copilot.md` as the source.

### 4. Deploy + docs
- [ ] Only after task 5 passed. If dexy is reachable: deploy the whole host (tar over ssh, incl. stems; see `Setup_Log/Setup_Reference.md`), restart with `~/easteregged/run.sh` **only if it was running**, otherwise leave it stopped; open `http://192.168.178.158:8080`.
- [ ] `MorningJam_Progress.md` (tick), `Setup_Log/Log.md` (entry + undo), this plan (tick), `host/README.md`.
- [ ] Morning message for Flo: what changed, screenshots, open questions.

## Acceptance

1. Three pages behind a left rail (Home, Node, Scenarios) + Turn off; minimal, Mars Rust, nothing crowded.
2. Home: the time of day as a wide curve with Now; the lights; the event bar.
3. Node: where light and sound happen (diagram, live); devices; TOP/MIDDLE/GROUND each with its own light strip and sound list.
4. Scenarios: the three scenarios start/stop from their cards; postcard; the jam's loop and mic.
5. Nothing of today's functionality lost.

## Out of scope tonight

Light/sound fine tuning, Home Assistant phase B, LD2450 hardware, shutting down the Pi from the page.
