# Log: physical prototype

Every change with undo steps. Newest first.

## 20.10.2026 — S2 staging (Wizard of Oz) + 2-s empty rule
- New S2 buttons "Someone passes" (`spring_someone`: activation to full in ~1 s + next phase) and "No one there" (`spring_empty`: dark within ~1 s). Once either is pressed, the run is "staged": the radars are ignored until the next start; the hint shows "· staged".
- Sensor rule: `EMPTY_S` 5 → 2 s. A dropout under 2 s keeps the light; after 2 s with nobody the season goes dark within ~1 s, and the next person seen moves one phase on.
- Files: `host/scenarios/spring_cleaning.py`, `host/web/app.js` (buttons), cache `v=65`, new test `test_spring_staged_and_two_second_empty`. Tests 16 passed. Checked live: start winter (0.0) → empty → someone: spring·Beginning (0.9) → empty (0.0) → someone: spring·Middle (0.95).
- **Undo:** `git revert` this commit.

## 20.10.2026 — Real bee instead of the synthetic one
- The room accent `bee_pass` (summer/spring accents of the room program) had no recording and came from `core/synth.py`, which sounded computery. Now `Sounds/accent/bee_pass.wav`: 4 s cut from Flo's bee recording `s2/bees.mp3` (strongest 4 s from 18.2 s), swell in/out, drifting left → right, 48 kHz stereo. The room loads `accent/<name>.wav` before the synth, so no code change. Checked: host restarted, accent triggered from the page. Audio is not in git (.gitignore); source noted in `Sounds/SOURCES.md`.
- **Undo:** delete or rename `Sounds/accent/bee_pass.wav` → the synthetic bee comes back.

## 20.10.2026 — S1 always ends at 1:30
- `scenarios/morning_jam.py`: the jam ends 1:30 after the start (`end_s = 90` in `[morning_jam]`, counted from the start incl. the 6-s wake, the same as the page's timer); the piano outro starts at once (no waiting for the loop end). The idle end (`idle_timeout_s`) and `max_minutes` are gone; Stop still ends it at once.
- Checked live: wake 0 s → jam 6 s → outro 90.1 s (timer 90) → idle 97 s. Tests 15 passed.
- **Undo:** `git revert` this commit (or set the old keys back: `idle_timeout_s = 45`, `max_minutes = 2`).

## 19.10.2026 — Postcard lid: window skin 0.45 → 0.8 mm
- Flo's friend saw holes in the printed (PETG) lid. STLs were watertight; the only thin wall was the 0.45 mm break-out skin (one line standing up → slicer gaps). `make_postcard_case.py`: `SKIN = 0.8` (two lines). All 4 variants re-exported (normal, M, PETG, M PETG), `postcard_m_petg.zip` rebuilt, README updated.
- **Undo:** `SKIN = 0.45` and re-run the script with `""`, `--m`, `--petg`, `--m --petg`.

## 19.10.2026 — Prototype/Demo is now the git repo itself
- `Prototype/Demo` = local clone of https://github.com/Flo-Gruenewald/master-thesis (branch `main`, remote `origin`); commit `8557b67` moved `demo/*` to the repo root. README + `.gitignore` now live in this folder (`.gitignore` also keeps out `*.otf`/`*.ttf`: a PP Pangaia font had appeared in `host/web/fonts/`). Git identity set in the repo (Flo-Gruenewald, noreply mail).
- Workflow: after a tested change → `git status`, commit, `git push`; `git pull` before working (experiments from Claude Code on the web come as PRs). Noted in `00_Bots/Prototype/Prototype_Bot_Onboarding.md` (Rules). The export script → `00_Bots/Prototype/Tools/_Archive/`.
- **Undo:** delete the hidden `.git` folder in `Prototype/Demo` (the files stay); on GitHub revert `8557b67` to get `demo/` back.

## 19.10.2026 — Demo code on GitHub
- Pushed to https://github.com/Flo-Gruenewald/master-thesis (public), commit `0ec3a52` "Add the demo code": `demo/` = a filtered copy of `Prototype/Demo` (88 files, 3 MB) + root README (project, folder table, what is left out) + `.gitignore`.
- Left out on purpose: `esphome/secrets.yaml` and `.esphome/` (home Wi-Fi password in clear text), all audio (Beatles song, Pixabay licence, VR music, Lena's voice), PP Neue Montreal fonts (commercial), `host/traces/` (recorded table loops), WLED backups (home SSID), logs, caches, backup folders.
- Update later: `python 00_Bots/Prototype/Tools/export_demo_to_github.py Prototype/Demo <clone>/demo`, check `git status`, commit, push (GitHub sign-in via Git Credential Manager on the laptop).
- **Undo:** on GitHub revert commit `0ec3a52` (or delete `demo/`).
- Same day: `MorningJam_Progress.md` removed from the repo (commit `ae5c1d1`, Flo's OK); undo = revert that commit.

## 18.10.2026 — Scenario tab header: big day, plain title, small framing
- Order now: mission day big (30 px, Mars orange / the tab's colour) → story as the title (24 px, not italic) → framing small (11 px caps, grey). Days from the booklet: S1 "Day 140 · Wednesday morning", S2 "Day 445 · on the way home" (where S2 starts), S3 "Day 455 · Friday, late evening". Cache `v=64`. Checked on S3.
- **Undo:** as the entry below (`before_story_pulse/`).

## 18.10.2026 — Pollini's notes (16): table pulse in S3, framing + story on each scenario tab
- S3 (`scenarios/miss_you_sis.py`): while the postcard lies unread ("arrived"), the table edge pulses in Mars orange every 2.8 s (`light.accent` mode tint, name "postcard"); it stops once the card is picked up. Checked live: accent "postcard" during arrived, none after the (simulated) hold.
- Each scenario tab opens with Flo's framing (small caps) and a short story line (`STORY` in `web/app.js`, `.story` in `style.css`, only in the single-tab view):
  S1 "Table · Monotony · Moments of connection · Bottom-up" / "Day 182, breakfast. The same table, the same faces, the same morning. Then someone taps a rhythm."
  S2 "Corridor · Detachment & Confinement · Transition · Top-down" / "Day 445, on the way home. The corridor has been winter for weeks, until someone walks through it."
  S3 "Sleeping pod · Isolation & Connection to home · Bottom-up" / "Night in the sleeping pod. Earth is a pale dot behind the window. Then a postcard arrives."
- Cache `v=63`. Tests 15 passed. Not done (asked): two-way postcard (point 4).
- **Undo:** copy `miss_you_sis.py` (→ `scenarios/`), `app.js`, `style.css` (→ `web/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_story_pulse/`, restart the host.

## 18.10.2026 — Turn off: LEDs stay off when a unit reconnects
- "Turn off" already faded the room out and sent `{"on": false}` to every WLED. Gap: a unit that dropped off Wi-Fi and came back got `{"on": true}` from the host's watcher, so its LEDs lit up again while the room was off. Now a (re)connecting unit gets `on: false` while the room is off (`core/light.py` `_watch`). Tests 15 passed; not yet tried live.
- The ESPs themselves keep running (WLED has no remote shutdown). Flo's decision: no firmware change; he cuts the 5 V line with a switch / power strip after "Turn off".
- **Undo:** copy `light.py` back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_power_off_fix/` into `core/`.

## 18.10.2026 — Node drawing: wall and table as one exhibition piece; clock on the tablet
- The wall piece now stands right behind the table's back edge (its rail continues behind the table: one exhibition piece), the small wall unit/radar box on the cove is gone, the tablet on the ledge shows the room clock "16:53" (+ the season ring). Texts: wall = light row on a rail behind the table, tablet with the room clock, the wall unit inside carries the second radar; the table text no longer mentions the tablet. Generator `00_Bots/Prototype/Tools/node_wall_piece.py` (foot position `O`, hover area computed from the piece). Cache `v=62`.
- **Undo:** previous generator version is in the session only; restore the drawing from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_node_room/` (original or `_rail_only_rejected`), `app.js` texts from `before_node_room/app.js`.

## 18.10.2026 — Node drawing: wall piece drawn from the 3D model
- Flo: the wall piece must look like the model. Now drawn isometrically from `Prototype/Prints/renders/wall_unit_*`: one slotted rail on a foot, a wide panel of tiles (light washing the top row), the protruding cove lid with the LED line under it, the tablet ledge with the iPad (room clock), the wall unit with its radar on the cove. Rest of the drawing unchanged (no cube). Generator: `00_Bots/Prototype/Tools/node_wall_piece.py` (archived drawing → `web/node_mvp.svg`); viewBox raised a little; wall hover area fitted. Cache `v=61`.
- Previous rail-only version → `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_node_room/node_mvp_rail_only_rejected.svg`.
- **Undo:** copy that file (or the original `node_mvp.svg` from the same folder) to `web/node_mvp.svg`.

## 18.10.2026 — Node page: isometric drawing back (Flo), clean wall piece, no cube
- Flo rejected the new front-view drawing: the isometric MVP drawing (`web/node_mvp.svg`, booklet p. 42) is back, changed only a little: the wall piece redrawn as built (aluminium rail on a foot, 3D-printed housing on top with the wall unit + radar, curved light row; the old panel, embedded render and screen removed), the cube on the table removed (and its "sound" hotspot), a stray leader line removed.
- Kept from the previous entry: the hover fix (`node-st down` instead of `off`), short concept texts for Ground · Wall piece / Middle · Table edge (incl. mic + tablet) / Top · Ring lamp, online/offline as a small line only. Front view → `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_node_room/node_room_frontview_rejected.svg`. Cache `v=59`.
- Checked: hover on all three pieces, no overlay, status line shows (ring lamp offline at the time).
- **Undo:** copy `app.js`, `style.css`, `index.html`, `node_mvp.svg` back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_node_room/`, restart the host.

## 18.10.2026 — Node page: new drawing of the setup as built; S3 orange
- Bug: hovering an offline piece blacked out the page: the status line had the class `off`, which is also the full-screen "room off" overlay. Now `node-st down`.
- New drawing `web/node_room.svg` (own, simple, front view): wall piece (aluminium rail, 3D-printed housing, curved light row, wall unit with radar), table with LED edge + table unit, ring lamp on its tripod with the spotlight unit, tablet, postcard, host laptop (sound · Wi-Fi · page). The cube on the table is gone. Each piece is a hover/tap target; hover = dashed frame, the others dim. Right/below: what the piece does (concept, plain English); online/offline only as a small line, the drawing never changes with it.
- Code (`app.js` node block) reduced: NODE_PARTS (title, sub, text, device), nodeStatus, renderNode. Old `node_mvp.svg` → archive. Cache `v=58`.
- S3: main colour Mars orange (`.card.seasonal.postal`, postcard view uses `var(--top)`).
- **Undo:** copy `app.js`, `style.css`, `index.html` and `node_mvp.svg` back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_node_room/` into `web/`, delete `node_room.svg`, restart the host.

## 18.10.2026 — S2: autumn added, only spring has phases; S3: first postcard view
- S2 (`scenarios/spring_cleaning.py`): stages winter → spring Beginning/Middle/End → summer → autumn (spring is the highlight; the others one phase each: how it feels and sounds). Autumn: 4800 K, level 0.38, ground "Autumn wind" (`ground/wind.wav`), accent "Rain shower" (`accent/rain_pass.wav`). Mission days 445 · 474/488/502 · 528 · 555. "Next season" jumps to the next season's first phase; arrival after 5 s quiet = next step (unchanged). Flo steps it himself.
- S2 UI: four season cards (spring wider), phases only on spring; autumn colour #A14530; labels on page + iPad (`clock.html`).
- S3 UI (first draft, Flo will reiterate): postcard card with "Earth" stamp, status text (waiting / arrived / Rome / Lena / home), Rome intensity bar, "card held / lies on the table", step row Arrived · Rome · Lena · Home, buttons "Postcard from Earth", "Hold the card". Cache `v=56`.
- Checked: S2 winter → spring·Beginning → summer → autumn (days 445/474/528/555), autumn chips; S3 waiting → arrived. Tests 15 passed. Afterwards: room switched off, host stopped (energy).
- **Undo:** copy `spring_cleaning.py` (→ `scenarios/`), `app.js`, `style.css`, `clock.html` (→ `web/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_autumn_s3view/`, set `v=54`, restart the host.

## 18.10.2026 — S2: three phases per season; arrival after 5 s quiet = next phase; new season colours
- `scenarios/spring_cleaning.py`: 9 stages = winter/spring/summer × Beginning · Middle · End, each with light (K, level), beds and a mission day (430/445/462 · 474/488/502 · 514/528/542). The song comes in at "spring · End" (no longer needs a season jump). Steps: web buttons "Next phase" (`spring_pass`) and "Next season" (`spring_season`, to the next season's Beginning); automatically: someone is seen after nobody was seen for 5 s (`EMPTY_S`) → next phase. Closeness still sets the activation (0 nobody … 1 up close). "Skip days" button removed (command still exists).
- UI: each season card shows its three phases (current one filled); colours: winter Kolibri #76DBD8, spring orange-blue gradient (#76DBD8 → #E37156), summer Mars orange #E37156. Cache `v=54`.
- Checked: start → winter·Beginning (day 430), Next phase → winter·Middle (445), Next season → spring·Beginning (474), 2× Next phase → spring·End (502). Tests 15 passed. The 5-s arrival trigger is not yet tried with people.
- **Undo:** copy `spring_cleaning.py` (→ `scenarios/`), `app.js`, `style.css` (→ `web/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_s2_phases/`, set `v=53`, restart the host.

## 18.10.2026 — S2 season interface: one card per season with its sounds
- Flo: the sounds must stay settable on the page. The S2 tab now shows three cards (Winter · Spring · Summer), each with its Ground and Accent sounds as on/off buttons (`spring_sound`, same handler as before). The current season's card is bright with a border in its colour and glows with the activation (closeness); past seasons slightly dimmed, coming ones dimmer. Top line: hint + mission day + clock; bottom right: "Next season", "Skip days". Cache `v=53`.
- Checked: cards render, Frog toggled on and off from the card.
- **Undo:** see the entry below (archive `before_season_interface/`).

## 18.10.2026 — S2: closeness activates the season; season interface (stripped UI)
- Flo after testing with a friend: S2 did not work with the sensors (passes need a full crossing; the LD2450 sees walking people only ~1/3 of the time) and the UI was far too full.
- Logic (`scenarios/spring_cleaning.py`): no pass detection. Activation = closeness of the nearest fused person: 0 beyond 3 m / nobody (fades out in ~5 s), 1 at ≤ 0.6 m. Beds, light (ground + spotlight) and the season's accents scale with it (accents only above 0.2); standing still adds a little (linger). "Next season" (`spring_pass`) and "Skip days" (`spring_skip`) step by hand; no automatic fast-forward after a step; summer stays until Stop.
- UI (S2 tab, `web/app.js` `seasonView`, `style.css` `.si-*`, cache `v=52`): big season icon + name in its colour (winter #A9C7D8, spring #9CCB8C, summer #F2AD9D), three steps winter → spring → summer, one hint line, mission day + clock; glow and brightness follow the activation; a short flash on a season step. Removed from S2: radar map, circadian curve, booklet timeline, events, sound table (sounds stay on the iPad).
- Checked: S2 runs, activation 0.77 with someone near, "Next season" → spring, day 472. Tests 15 passed.
- **Undo:** copy `spring_cleaning.py` (→ `scenarios/`), `app.js`, `style.css`, `index.html` (→ `web/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_season_interface/`, restart the host.

## 18.10.2026 — Radar re-test with the filters (Flo + friend)
- Data: `00_Bots/Prototype/Tools/radar_data/radar_test_2026-10-18_1615_filtered.csv` (raw both radars + host's fused count). Seconds with someone counted, raw → host: P1 nobody 0 → 0 · P2 1 stands 30 → 30 (never 2) · P3 1 walks 8/10 → 11 · P4 2 stand → host sees 2 people 18 of 30 s (before: never) · P5 2 walk 15/26 → 21 (2 people 4 s) · P6 nobody: raw wall ghost 30 s → host 4 s (only the people walking out at the start; the frozen wall ghost is dropped after 3 s).
- Flo: "pretty good", two people still sometimes counted as one (LD2450 limit when they stand still / behind each other). No further change.

## 18.10.2026 — Radar page: both radars in one map; presence from the fused people
- Radar page (`web/radar.html`, cache `v=35`): one merged map in the spotlight radar's coordinates. Spotlight radar targets + trail in Mars orange `#E37156`, wall radar targets (moved by `wall_offset_mm`/`wall_rot_deg`) in Kolibri blue `#76DBD8`, white ring = a person the host counts (fused + filtered = the engine's input). Proximity preview now uses the host's people.
- Host: state `presence.wall_cal` = [offset x, offset y, rotation] for the page; `present` (and the presence start) = any filtered person on either radar (before: only the spotlight radar's ON/OFF).
- Live check 16:03: spotlight (34, 59) cm and wall → (46, 36) cm merged into one person.
- Timer test page (`00_Bots/Prototype/Tools/radar_test.py`) now also records the host's fused count.
- **Undo:** copy `main.py` and `radar.html` (→ `web/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_radar_merge_view/`, set `v=34` in `index.html`, restart the host.

## 18.10.2026 — Radars calibrated with a test (ghosts filtered, wall radar fused)
- Test with Flo + a friend (`00_Bots/Prototype/Tools/radar_test.py`, timer page :8098; data `Tools/radar_data/radar_test_2026-10-18_1550.csv`): P1 nobody 0/0 · P2 1 stands 30/30 both · P3 1 walks spot 5, wall 13 of 30 · P4 2 stand: both radars only ever 1 target · P5 2 walk: spot 2 targets once · P6 nobody: ghosts on BOTH 30/30.
- Findings: the ghosts were frozen tracks (identical x/y for ~25 s: spotlight at (−15, 25) cm next to the ring light, wall at (−114, 322) cm far left); real people always jitter. The first ghost (earlier today) sat < 50 cm in front of the ring light. The wall radar sees the same person ≈ (+905, −320) mm off the spotlight radar's coordinates (median error 14 cm). In P4 both radars locked onto the SAME person: two people standing still are a sensor limit of the LD2450 (it tracks movement; the stronger reflector wins).
- Host (`main.py`, `people`): frozen targets (moved < 10 mm for 3 s) are dropped; spotlight targets < 55 cm and wall targets < 30 cm or > 3 m are dropped; wall targets are moved into the spotlight radar's coordinates and merged (< 45 cm = same person), so two people count as two when each radar sees a different one. `present` (and the presence start) now needs a filtered person, not only the radar's own ON. Keys in `[presence]` (`room.toml`): `stale_s`, `stale_mm`, `spot_min_mm`, `wall_min_mm`, `wall_max_mm`, `wall_offset_mm`, `wall_rot_deg`, `ghost_merge_mm` 400 → 450.
- Replay of the test data: P6 ghosts drop from 30 s to 3 s (spotlight) / 0 s (wall with the 3 m limit); standing people are still counted 30/30. Tests: 15 passed (new: frozen ghost, near zone, wall fusion).
- **Undo:** copy `main.py`, `room.toml` back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_radar_calibration/`, revert `tests/test_host_core.py` (the three radar tests), restart the host.

## 18.10.2026 — Power dialog: "Restart all units"
- Power button (rail, bottom) → dialog has a new button "Restart all units": host command `restart_units` reboots every online WLED unit (table `strip1`, spotlight `top`, `wall`) via `POST /json/state {"rb":true}`; they come back after ~15 s and the host picks them up again. The postcard is not included (its firmware has no restart command).
- Code: `Light.restart_all()` (`core/light.py`), `restart_units` in `on_cmd` (`main.py`), button `#confirm-restart` (`web/index.html`, `app.js`), cache `?v=50`.
- Tested 15:33: all three rebooted (uptime 27 s afterwards) and are online again.
- **Undo:** copy `main.py`, `light.py` (→ `core/`), `index.html`, `app.js` (→ `web/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_restart_units/`, restart the host.

## 18.10.2026 — Wall unit brighter: WLED limit 2000 mA, host cap 1800 mA, gain 2.5
- Flo: new solid 5 V line (rating unknown) and OK for the change. WLED on the wall unit: max current 800 → 2000 mA (global + output, `/json/cfg`). Host: `host_max_ma` 580 → 1800, new key `gain = 2.5` (per-unit brightness factor before the cap, `Wled.gain` in `core/light.py`).
- Why the gain: at the old settings the wall drew only ~660 mA at its brightest, so the limit was not what kept it dark; the room program's level was. Now ~2.5× brighter; the cap keeps WLED's limiter out (no flicker).
- Checked: wall stays online (uptime counting, no resets), 521 mA at 14:23 (was 281 mA at 14:12 with the same program).
- **Undo:** WLED → Config → LED Preferences → max current 800 mA (or POST `{"hw":{"led":{"maxpwr":800}}}` incl. the output's `maxpwr`); in `room.toml` set `host_max_ma = 580`, delete `gain`; restart the host. If the ESP starts rebooting at bright scenes, the 5 V line is too weak → lower `gain` first.

## 18.10.2026 — Wall unit: host caps the current (white flickered)
- Cause: in white the wall reached ~660 of WLED's 800 mA limit; WLED's limiter then dims frame by frame → flicker. Now the host scales each DDP frame to stay under `host_max_ma = 580` (WLED's estimate: `ledma`/3 per channel, W counts too), so WLED's limiter does not step in. Full white (mostly the W LED) is now capped at ≈ 31 %; dimmer colours are untouched.
- Code: `Wled.cap_ma`/`cap_per_ch` + `limit_current()` in `Light.send()` (`core/light.py`); keys `host_max_ma`, `ledma` in the wall's `[[wled]]` block (`room.toml`). Other units unchanged (no key = no cap).
- Hardware still recommended (C3 drives the 5 V strip with 3.3 V data, no level shifter): 330 Ω in the data line, 1000 µF across 5 V/GND at the strip, short thick power wires.
- **Undo:** copy `room.toml` and `light.py` (→ `core/`) back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_wall_cap/`, restart the host.

## 18.10.2026 — Wall unit: passer-by blue tint removed; Wi-Fi check
- Removed the wall-radar "someone passes → wall turns Kolibri blue" effect: `[light.wall_pass]` in `room.toml`, its fields + blend in `core/light.py`, the trigger in `main.py` (`wall_seen` is still recorded, unused).
- Before: the wall unit dropped off Wi-Fi every 20–60 s from 12:10 (likely resets). After the host restart at 14:05: online at 192.168.137.126 (mDNS `wall-unit`), uptime counting up, RSSI −43 dBm, 281 mA of the 800 mA limit, MQTT on, 60 RGBW LEDs on GPIO5. Cause of the drops not confirmed (serial log needed if it comes back).
- Files: `host/room.toml`, `host/core/light.py`, `host/main.py`.
- **Undo:** copy the three files back from `Prototype/Archive/Demo_cleanup_2026-10-15/host/before_wall_pass_removal/` (light.py → `core/`), restart the host.

## 17.10.2026 — Wall C3: Wi-Fi loss = power supply (not radar, not code)
- Symptom: the wall radar reports a person right after boot, then goes silent; the LEDs flicker. Ping: 60–63 % loss at RSSI −46, TX power already 8.5 dBm, Wi-Fi patch from 08.10 already in the build (`wled/patch_wled.py`).
- Tests (Flo): power bank → connects, then unstable (throttles at low draw, same as the table C3 on 08.10). New USB cable/charger → never connects. Same cable **without the LED strip → connects** (ping 20 % loss).
- Cause: the supply/cable can't deliver the Wi-Fi current peaks plus the 60 LEDs.
- Fix (hardware, open): 5 V ≥ 2 A charger with a short, thick cable; LED strip 5 V straight from the supply (not via the C3's 5V pin); 470–1000 µF capacitor across 5V/GND at the C3. Stopgap (Flo's OK): wall C3 ABL `hw.led.maxpwr` 1800 → **800 mA** via `/json/cfg` (verified). **Undo:** POST `{"hw":{"led":{"maxpwr":1800}}}` to `http://192.168.137.15/json/cfg`.

## 17.10.2026 — Wall radar: someone passes → wall light turns Kolibri blue
- The host listens to `in/presence_wall/count` and `in/presence_wall/target/+/+` (LD2450 on the wall C3). A count > 0 or a target with a position counts as "someone there".
- While the wall radar sees someone (+3 s hold), the `wall` spot fades (0.6 s) to Kolibri blue `#76DBD8`, then fades back. Settings: `[light.wall_pass]` in `room.toml` (enabled, spot, color, hold_s, fade_s).
- Tested offline: wall pixels reach exactly (118, 219, 216) and return to the normal light.
- Files: `host/room.toml`, `host/core/light.py`, `host/main.py`. Backup: `host/_backup_wallpass_1710/`.
- Fix (same day): at full Kolibri blue the 60 LEDs drew ~2.5 A, the C3 browned out and rebooted (~70 s offline, radar silent). New `level = 0.3` in `[light.wall_pass]` dims the tint.
- **Undo:** set `enabled = false` in `[light.wall_pass]`, or copy the three files from `host/_backup_wallpass_1710/` back; restart the host.

## 16.10.2026 — S2: booklet mission timeline, transposed sound table, compact events
- Mission timeline = the booklet graphic (Mission · Adaptation · Habitat rows, no Earth/Mars), `web/mission_timeline.svg` made by `00_Bots/Prototype/Tools/make_web_timeline.py` from the Documentation bot's `build_mission_timeline.py`. Pointer + trail move with the mission day (`tlMove`, coordinates from the SVG's `data-x0/px/w`).
- Caption without the stage text ("Birds" etc.): "Mission … day N". Sound table: rows Winter/Spring/Summer, columns Ground | Accent (page + tablet `clock.html`). Events narrow and stacked; bigger table/caption fonts. S2 start button small (44 px) in the timeline bento corner. Cache `?v=49`.
- Incident: a too-wide cut in the edit script truncated `app.js` (~800 lines, page broken "route is not defined"). Restored from the browser's cached `?v=46`, edits reapplied with bounded cuts; checked: timeline, pointer, table, circadian curve, Node page.
- Files: `host/web/app.js`, `style.css`, `index.html`, `clock.html`, `mission_timeline.svg`.
- **Undo:** copy `Prototype/Archive/Demo_cleanup_2026-10-15/host/web/app_v46_before_s2_timeline.js` over `app.js`; in `style.css` revert the `.stable`/`.st-*`/`.sv-cap`/`.tl-*`/`.card.seasonal .card-top .play` rules; delete `mission_timeline.svg`; set `?v=46` in `index.html`.

## 16.10.2026 — Node page: MVP drawing with hover explanations
- Node page = booklet drawing (p. 42, `web/node_mvp.svg`, cropped, no text) left, explanation panel right: hover/tap wall piece, table edge, ring lamp or sound box; WLED status (`wall`, `strip1`, `top`) live from `S.devices`. Intro line + host/hotspot note when nothing is hovered.
- Removed the TOP/MIDDLE/GROUND level panels (markup, JS: fixtures, sound rows, accents, `drawStrip`/`avgPx`, CSS). `node.svg`, `crew.svg` moved to `Prototype/Archive/Demo_cleanup_2026-10-15/host/web/`. Cache `?v=46`.
- Rail: scenario tabs `#s1`-`#s3` show the text "S1", "S2", "S3" instead of icons.
- Files: `host/web/index.html`, `app.js`, `style.css`, `node_mvp.svg`.
- **Undo:** move `node.svg`/`crew.svg` back from the Archive folder; restore `index.html`, `app.js`, `style.css` from the previous version (no copy kept; the old Node page is the `?v=45` state); delete `node_mvp.svg`.

## 16.10.2026 — One tab per scenario; S2 = the four essentials (mission, circadian day, radar, customize)
- Flo: S2 shows the room's transition — it needs only the mission timeline, the circadian day, the radar (passing by) and the customization; each scenario its own tab with the whole screen; no phase bar on top (the timeline guides); minimal text; the radar a smaller square bento.
- `index.html`: rail "Scenarios" → three tabs `#s1` Morning Jam (note icon), `#s2` Spring Cleaning (sprout), `#s3` I Miss You, Sis (envelope). `app.js` `route()`: `SCEN_TAB` → the scenarios page with only that card (`#cards[data-only]`, `.card.sel`), page title = scenario name; the selected card's stage is drawn even when it isn't running; old `#scenarios` links go to S1. S2 captions shortened (stage · "Mission · day N" · "Circadian day" · "Radar" · "Events" · "Customize"), close/lingering bars removed from the events box. `style.css`: tab layout (card title/number/description hidden, play button top right), `.card.seasonal .phases` hidden, the old try/extra rows hidden for S2, first S2 row = circadian `1fr` + radar square (`aspect-ratio: 1`). index v=45. Checked: each tab shows exactly its card; S2 sizes (1400×1000): timeline 203 px, circadian + radar 384×384, events/customize 181 px, all inside the card.
- **Undo:** rail back to one `#scenarios` link; `PAGES`/`route()` as before (scenarios page with all cards); remove the `[data-only]`/`.sel` CSS block.

## 16.10.2026 — S2 interface: timeline without Earth/Mars, gliding pointer, bottom row 1:2
- Timeline rows: mission, adaptation, habitat only (more room for the curve and the radar). The timeline is drawn once; the pointer (`.tl-hereh`, 1 s CSS transition) and a trail from the scenario's start day (`start_day` 445 in `ui()`) move with the mission day (`tlMove()` in app.js). Bottom row 1:2 (events | sounds). index v=44. Checked in the browser: same pointer element across updates, day 445 → 486 over two passes + fast-forward.
- **Undo:** add the earth/mars rows back in `timeline()`; `.sv-row:last-child` rule out.

## 16.10.2026 — S2 interface: mission timeline, circadian day, radar, sound table; synced with the host clock
- Flo: S2 in our blue (Kolibri #76DBD8, top-down); phases only winter/spring/summer with the logo's season icons; the booklet's mission timeline at the top, placed in the **2nd vulnerability window**; the home page's circadian curve (it races during the fast-forward); a mini radar (prototype + sensors + people); sounds as a table (seasons × ground/accent); events on the left; no left "winter" box; the scenario runs on the host's clock (no second time).
- `scenarios/spring_cleaning.py`: STAGES carry a season (moments = winter/spring/summer; breath/birds are stages inside spring); `STAGE_DAY` winter 445 / breath 472 / birds 484 / spring 496 / summer 515 (habitat seasons inside the window 345–534, data from `00_Bots/Documentation/Tools/build_mission_timeline.py`): start sets the **room date** to day 445, each pass moves it forward; the fast-forward now runs the **host's room clock** (`set_hour` + `_new_day`, date/mission day count on: tested 185 → 187, 472 → 474, clock back to the same hour). Sounds: `SOUND_ROWS` winter (winter wind | wind gust), spring (rain, birds, bees, song | cat, frog), summer (crickets | bird call); accents only in their season. `ui()` adds season, curve (96 pts + dawn/dusk/sleep), mission day, room map, layers.
- `room.toml` new `[room_map]` (table, wall, wall radar position/facing, range) for the mini radar — adjust to the real setup.
- `web/app.js`: `curveMarkup()`/`curveLabels()` extracted from the home page's `drawCurve()` (home unchanged, checked), reused in S2; `timeline()`, `soundTable()`, `SEASON_ICON`; S2 stage = timeline (full width) → circadian | radar → events | sounds; try/extra rows hidden while S2 runs. `style.css`: `.card.seasonal` blue + layout. `clock.html`: tablet bar = the same table + "Skip days". index v=43.
- **Undo:** S2 file from the archive/earlier entries; remove `[room_map]`; app.js: drawCurve back to inline markup (curveMarkup/curveLabels can stay), remove timeline/soundTable/seasonView parts.

## 16.10.2026 — S3 rebuilt: hold the postcard → Lena's evening in Rome; postcard v4 (Wi-Fi/MQTT) built
- Flo: the postcard creates the ambience of somewhere else (not rain = our season) → a Roman piazza in the evening.
- `scenarios/miss_you_sis.py` rewritten (v1 archived as `Archive/Demo_cleanup_2026-10-15/host/scenarios/miss_you_sis_v1_rain_tap.py`): arrived (teal breathing, arrival sound, publishes `postcard/arrived` → the card buzzes twice) → **rome**: held, the piazza fades in with the card's intensity (piazza voices, fountain at the table, swallows in the room, a Vespa crossing now and then; golden light, teal fades) → **lena**: held fully → bells once, then `Sounds/s3/lena_rome.wav|mp3` if Flo adds it → letting go fades Rome in ~6 s; card still for `rest_s` (20 s) → **home** → end. Never picked up: a soft taste of Rome after `wait_s` (45 s). No microphone/tap.
- Host: listens to `easteregged/in/postcard/touch` `{"held":0|1,"i":0..1}`; cmd `postcard_hold` (web try-it "Hold the card (on/off)"); state `postcard {held, rome}`. `room.toml [miss_you_sis]`: wait_s, voice_gain, rest_s (cosy_s gone). index v=40.
- `postcard_fw` **v4** (v3 archived as `postcard_main_v3.cpp`): heartbeat unchanged + WiFiManager (no password in code; first start opens the AP "postcard-setup", Flo picks FLO-WORK there; non-blocking, the heartbeat keeps running) + MQTT (PubSubClient) to 192.168.137.1: publishes `in/postcard/touch` on change and every 0.5 s while held; subscribes `postcard/arrived` → two short buzzes. `lib_deps` WiFiManager 2.0.17, PubSubClient 2.8. Built in `C:\pc\postcard` (flash 64 %), **not flashed yet**.
- Tested with the web stand-in: arrived → hold → rome (fountain, piazza, swallows) → bells at 0.85 → release → fade → home → idle, no errors.
- **Undo:** copy the archived v1 scenario and v3 firmware back; remove the `postcard_hold`/`postcard` lines in main.py and the S3 sims in app.js.

## 16.10.2026 — S2 uses Flo's spring sounds; frog; Rome sounds for S3 downloaded
- Flo's files in `Sounds/s2/` renamed (originals listed in SOURCES.md): `frog`, `winter_wind`, `birds`, `rain`, `bees` (.mp3). `core/scenario.py` `sound()` loads `.wav`, else `.mp3`; new `has_sound()`.
- `scenarios/spring_cleaning.py`: beds winter/rain/birds/bees from `s2/*`, crickets = cicadas; bees as a bed in spring (0.16) and summer (0.06) instead of the synth `bee_pass`; new tablet sound **frog** (`CALLS`: cat and frog call now and then from stage spring on); defaults all on except the frog (demo: "instead of a cat I like a frog"). Labels in `app.js`/`clock.html`. Tested live: winter_wind → +rain → +birds → bees + here_comes_the_sun, cat off/frog on via command; 14 tests pass.
- S3 Rome: 5 CC0 sounds from Freesound (HQ previews) in `Sounds/s3/rome/` (piazza, fountain, bells, swallows, vespa; authors + links in SOURCES.md). Not used yet.
- **Undo:** S2 from the archived v1 or the backup in this log; delete `Sounds/s3/rome/`.

## 16.10.2026 — Wall unit: new ESP32-C3 with LEDs + second LD2450 radar (flashed)
- New C3 SuperMini on COM4 (MAC ac:eb:e6:4a:c3:ac), resoldered by Flo. Pin test firmware (`C:\pc\pintest`, flashed first): GPIO2 stuck at 3.3 V (bridge) → don't use 1/2; GPIO3↔4 bridge found, re-soldered, gone on the re-test; 8/9 = board pull-ups (LED, BOOT); free: 0, 3–7, 10, 20, 21.
- `wled/usermod_ld2450/usermod_ld2450.h`: ESP32-C3 support (`Serial1`, the C3 has no Serial2) and a topic part `LD2450_SOURCE` (default `presence`; the wall uses `presence_wall` → `easteregged/in/presence_wall/...`, `status/presence_wall`, so the two radars don't overwrite each other). Before: `Prototype/Archive/Demo_cleanup_2026-10-15/usermod_ld2450_before_wall.h`.
- New env `wall_c3_ld2450` in `platformio_override.ini`: WLED "Wall", mDNS `wall-unit` (the host's `[[wled]] wall` finds it), 60 RGBW on **GPIO5**, radar TX → **GPIO6**, ABL 1.8 A. Built in `C:\wb` (flash 75.6 %), **flashed over USB to COM4**. Next: Flo sets Wi-Fi via the WLED-AP (needs the hotspot FLO-WORK on). The host doesn't read `presence_wall` yet (fusion = later).
- Wiring: 5V (charger 5 V/3 A, one unit per charger) → strip 5V, radar VCC, C3 5V; GND common; strip DIN → GPIO5 (~330 Ω); radar TX → GPIO6.
- On the hotspot (Flo set Wi-Fi via WLED-AP): **192.168.137.197**. WLED name → `wall-unit` (`/json/cfg` id.name; mDNS already wall-unit). MQTT on: broker 192.168.137.1:1883, client id `wall-unit`, topics `wled/wall`, rebooted. Usermod config OK (rxPin 6). Radar still "no data" (wiring to check: radar TX → GPIO6, VCC 5V). Undo: WLED → Config → Sync → MQTT off; name back to "Wall".
- **Undo:** restore the archived usermod header, delete the `wall_c3_ld2450` env; the Gledopto stays configured as `wall-unit` in WLED and can take over again.

## 16.10.2026 — MorningJam_Progress.md archived
- Old checklist (early October) replaced by this log + the bot onboarding → moved to `Prototype/Archive/Demo_cleanup_2026-10-15/MorningJam_Progress.md`. References pointed to Log/onboarding in `host/README.md`, `Setup_Reference.md`, `host/core/synth.py`; old prompts/plans and Docu-bot tools only name it as text (no file reads), left as they are.
- **Undo:** move it back to `Prototype/Demo/`.

## 16.10.2026 — Sounds folder visible: host/stems → Demo/Sounds; song filed
- Flo couldn't find the sounds (hidden in `host/stems/`). Moved to **`Prototype/Demo/Sounds/`** (same sub folders: MJ stems, `ground/`, `accent/`, `s2/`, `s3/`, `SOURCES.md`). `room.toml` `stems_dir = "../Sounds"`; paths updated in `tests/test_host_core.py`, `tools/import_vr_sounds.py`, host README, Prototype bot onboarding.
- Flo's `Demo/690716c Here Comes The Sun (take 39).mp3` → `Sounds/s2/here_comes_the_sun.mp3` (listed in SOURCES.md). S2 loads it in the background at scenario start (0.8 s, no hiccup at pass 3). Tested: at stage "spring" `here_comes_the_sun` plays with the birds; 14 tests pass.
- **Undo:** move `Demo/Sounds` back to `Demo/host/stems`, `stems_dir = "stems"`, revert the path edits; the song back to `Demo/` under its old name.

## 16.10.2026 — S2 Spring Cleaning rebuilt: presence + transition (demo script)
- Flo: S1 = mic + LED reactive, S2 = presence and transition, no mic/tap, no cat. Demo: start in winter → walk past → "it breathes out" (rain) → days run fast on the LEDs → walk past → birds → days → walk past → full spring (bees, birds, "Here Comes the Sun" as invitation) → tablet: change sounds → walk past (song volume follows presence) → days → last pass → crickets, light summer → end.
- `scenarios/spring_cleaning.py` rewritten: stages winter/breath/birds/spring/summer (light K + level, beds); a **pass** = the nearest radar person crosses x < −350 mm ↔ > +350 mm within 8 s (`host.people`); **lingering** (moves < 250 mm for 3 s) → louder beds, brighter ground + spotlight; song gain follows closeness (0.6 m → full, 3 m → quiet); **day/night fast-forward** 3 s after each pass: 2 days in 10 s with `Room.day()` on the ground LEDs; bees = synth `bee_pass` accents (stage ≥ 3); cicadas = the crickets bed; after the 4th pass summer holds 15 s, room season → summer, release. Song file `stems/s2/here_comes_the_sun.wav|mp3` (Flo adds it; until then `s2/music.wav`). Old version archived: `Prototype/Archive/Demo_cleanup_2026-10-15/host/scenarios/spring_cleaning_v1_timer_tap.py`.
- Host: cmds `spring_sound {name, on}`, `spring_pass` (simulated pass), `spring_skip` (days now); state `spring` (sounds, stage, passes, near, linger).
- Web: S2 card shows a season view instead of the loop (stage, hint, passes, close/lingering bars); try-its "Someone passes", "Skip days"; sound toggles. Tablet `clock.html`: a "Spring" bar while S2 runs (sound chips + "Skip days"). index v=39.
- `RoomHost.ps1`: detects the host by port 8080 **or** UDP 7010 (a still-starting host was started twice); bug fixed (two equal PIDs were summed to a non-existing one); `host.log` now UTF-8.
- Tested with simulated passes: winter → breath → 2 days → birds → 2 days → spring → bees off (tablet) → summer → idle; page + tablet bar checked in the browser. **Not tested with the real radar yet** (spotlight was charging).
- **Undo:** copy the archived v1 back to `scenarios/spring_cleaning.py`; remove the `spring_*` lines in `main.py`, the season view/SPRING_LABEL/sims in `app.js` + `.season-view`/`.sv-*` CSS, the `#spring` bar in `clock.html`.

## 15.10.2026 — Host cleanup: one audio output, no Home Assistant
- Flo: cut what the laptop setup doesn't use (e.g. surround), keep the core working, don't overdo it.
- Removed: Home Assistant (`core/ha.py`, `core/ha_bridge.py`, room player, `[ha]` + `[ha.entities]` in room.toml, `devices.ha` in state); room stream for Music Assistant (`/room.wav|flac|mp3`, `Broadcast`, `wav_header`, `web/listen.html`); Pi wall node bed output (`_NodeBed`, `_node_beds`, `node_resend`, `node_send`); PipeWire/Bluetooth sink; separate accent speaker (`accent_output`, `acc_out`); `sync_test` and `room_latency` commands. `RoomOut` = "main" (default) or a second sound card; travelling accents pan left/right on one output (as before without a second speaker). `core/web.py` 177 → 84 lines; `core/ambient.py` −120 lines. `[room] room_output` comment updated. Tests: dropped the HA and WAV-header tests → 14 passed; `pyflakes` clean.
- Host logs to stdout now; `RoomHost.ps1` also writes the window's log to `host/host.log` (overwritten per start). README updated.
- Smoke test on the running host: accent `bird_cross`, Morning Jam idle → wake → jam → Stop → outro → idle, no errors.
- Moved (not deleted) to `Prototype/Archive/Demo_cleanup_2026-10-15/host/`: the removed files, old backups `_backup_copilot_0610`, `_backup_mj_1510`, and `_backup_cleanup_1510` (= all touched files before this cleanup).
- **Undo:** copy `_backup_cleanup_1510/*` back over `Demo/host/` (main.py, room.toml, core/, web/, tests/), move `ha.py`, `ha_bridge.py`, `listen.html`, the two tests back; restart the host.

## 15.10.2026 — Folder layout: Physical → Demo, Physical_v2 removed
- Flo: `Prototype/Physical/` renamed to **`Prototype/Demo/`** (code + app); 3D prints moved by Flo to `Prototype/Prints/`; old prototypes in `Prototype/Archive/`. `Prototype/Physical_v2/` (unused refactor copy from 09.10) moved to the **Windows Recycle Bin**.
- Updated paths (`Prototype/Physical/…` → `Prototype/Demo/…`, `Physical\prints\` → `Prototype\Prints\`) in 14 files: Prompts (incl. `NewChat_Postcard_Flash_Lenovo.md`), `Plan/Guide_Hardware_1_Presence.md`, `Plan/System_Diagram.svg`, `Setup_Log/Setup_Reference.md`, comment in `host/core/bus.py`. Older log entries below keep the old name. Desktop shortcut "Room Host" now points to `Demo\host\RoomHost.bat` (icon `Demo\host\web\icons\roomhost.ico`); tested: starts the host. Note: the running host window keeps `host\` open, so the folder can't be renamed while it runs.
- **Undo:** rename `Demo` back to `Physical`, restore `Physical_v2` from the Recycle Bin, replace `Prototype/Demo` → `Prototype/Physical` in the files above, point the shortcut back.

## 15.10.2026 — Desktop on/off for the host
- Flo heard the host still running in the background (started invisibly by Claude). New `host/RoomHost.ps1` + `host/RoomHost.bat` and a desktop shortcut "Room Host" (`C:\Users\flori\Desktop\Room Host.lnk`): double-click = toggle. Host not running → starts in its own PowerShell window with the live log (closing the window stops it); running (whoever listens on port 8080) → stopped. Tested both ways.
- **Undo:** delete the shortcut and the two files; start the host as before with `python main.py` in `host\`.
- Logo icons: `web/logo.svg` rendered with headless Edge → `web/icons/roomhost.ico` (16–256 px, transparent; set as the desktop shortcut's icon), `web/icons/apple-touch-icon.png` (180 px, on #171310) + `icon-512.png`. `clock.html` and `index.html` link the apple-touch-icon (clock.html also the SVG favicon). The iPad picks it up only when the home-screen link is added again. (Undo: delete `web/icons/`, the `<link>` lines, reset the shortcut icon.)

## 15.10.2026 — Morning Jam: no absence timeout
- Flo: not needed. Removed `absence_timeout_s` (room.toml, was temporarily 86400), the check in `scenarios/morning_jam.py _should_end()` and `Host.absent_for()` (main.py, only used there). The jam now ends by Stop, `idle_timeout_s` (45 s without a new row) or `max_minutes` (2).
- **Undo:** add `absence_timeout_s = 20` to `[morning_jam]`, `or self.host.absent_for() > c["absence_timeout_s"]` in `_should_end()`, and `absent_for()` (returns 0 while present / no presence source, else `time.monotonic() - self.absent_since`).

## 17.10.2026 — Wall C3: LEDs stay dark (debugging) · radar tab shows the wall radar
- `host/web/radar.html`: second canvas "Wall radar" fed by `in/presence_wall/...` (own targets, trails, count; proximity rings + host rings stay on the spotlight radar); log lines tagged top/wall. `index.html` iframe `v=34`. JS syntax-checked; not yet looked at in the browser. Before: scratchpad copy.
- LEDs dark: WLED runs (on, bri 255, DDP live from the host), estimates 770–950 mA for full red with `lor = 2` → firmware drives the output. Moved the data wire 5 → **10** (Flo) and set WLED LED pin `[5]` → **`[10]`** (`/json/cfg`, rebooted): still dark → not the pin. Remaining suspects: strip wired at DOUT instead of DIN, no 5 V at the strip, missing common GND, dead first pixel. Live override `lor = 2` (solid red) is still on for testing.
- **Undo:** LED pin back to 5 (`/json/cfg` hw.led.ins[0].pin = [5]) when the wire goes back; `lor` 0 to hand the LEDs back to the host; restore radar.html from the scratchpad copy.
- Follow-up: after Flo re-did the wiring the strip showed only 1–2 random pixels; the C3 kept dropping off the network. LED pin set back to **5** (saved, rebooted) → **the LEDs light up**. Cause of the dropouts: the **power bank switches itself off** (low-current auto-off) → C3 + strip lose power, open data line = random pixels. Fix: run the wall unit from the 5 V/3 A wall charger (as planned for the defence) or a power bank with an always-on/low-current mode. `lor` back to 0 (host drives the LEDs) once the C3 is online again.

## 17.10.2026 — Wall C3: radar RX wired, found on the hotspot
- Flo wired the radar's RX too (for later radar commands/updates): **radar TX → GPIO6** (C3 RX, read by the usermod), **radar RX ← GPIO7** (C3 TX, not used by the firmware yet – needs a TX pin in the usermod + re-flash, Prototype bot, ask first). Rest unchanged: strip DIN → GPIO5, 5 V and GND shared.
- Found: `wall-unit.local` = **192.168.137.15** now (was .197; MAC ac:eb:e6:4a:c3:ac, WLED 0.15.1, 60 LEDs, RSSI −44). Usermod LD2450 enabled, rxPin 6, reports **1 person** → radar data arrives now. But the usermod says **"mqtt off · sent 0"**: WLED MQTT is off → presence_wall doesn't reach the host (WLED → Config → Sync → MQTT, broker 192.168.137.1:1883 – not changed, ask Flo).
- Checked on Flo's request: MQTT on the C3 is already **on** with the right settings (broker 192.168.137.1:1883, cid wall-unit, topics wled/wall, wled/all) – nothing changed; rebooted via `/json/state {"rb":true}`. "mqtt off" = not connected: nothing listens on port 1883 on the laptop and no python runs → the room host (with its embedded broker) is not started. Once the host runs, the C3 connects by itself. → Flo started the host: broker listening, C3 usermod "mqtt on · sent 215" – presence_wall arrives at the host.

## 17.10.2026 — Postcard PETG versions (normal + M)
- Friend has PETG, no TPU → `make_postcard_case.py --petg` (`set_petg()`, combinable with `--m`): ring wall 2.5, groove 0.8 → hook 0.65 mm (45° flanks), 0.15 mm play, plates 2.5 mm, ring waves 0.3 mm (≥ 1.4 mm wall behind the groove). Files `postcard/postcard_petg_*`, `postcard/postcard_m_petg_*`; TPU files unchanged. Audit: all watertight, 1 body; backs no overhang, rings only the USB-slot top (14 mm bridge) + ≤ 0.8 mm spots, lids ≤ 2 mm ledges (skin carries the window). README updated.
- **Undo:** delete `set_petg()` + the `_petg` files.

## 17.10.2026 — Print audit of all parts (old printer, no supports)
- New audit (scratchpad `audit.py`): watertight / bodies / degenerate / tiny edges, overhang spots > 45° clustered with span × depth, bed contact and height/base ratio, fits 220 × 220 × 250. Results: all parts watertight, 1 body, no gaps (a few zero-area triangles in backs/lids, harmless). Rings: only the USB-slot top (14 mm bridge); belly + waves stay ≤ ~42° (0.3–0.4 mm deep spots). Backs: only ≤ 0.8 mm spots at the tongue. Lids: only 0.5–2 mm ledges (skin carries the window) — but standing 139/161 mm tall on ~1 cm² (ratio 13–17) = tippy in TPU. Table clip simple: rail recess's upper end now runs out at 45° (was a 1.5 mm ledge over 64 mm) → largest spot 5.9 mm (mic-recess roof), rest ≤ 3.5 mm hole roofs.
- Decision (Flo): the lid stays standing, printed with a big brim (8–10 mm) and slowly (~15–20 mm/s) — noted in `postcard/README.md`.

## 17.10.2026 — Postcard: ring with a gentle belly; XL archived
- Flo: ring a bit curved so it sits softer in the hand; overwrite M, archive XL. `make_postcard_case.py`: `RING_BULGE = 2.5` → the ring's side bulges out 2.5 mm at mid-height (sine, 0 at the rounded top and the chamfered bottom; max ~14° from vertical, prints lying without supports), waves ride on it. `finish()` only cuts the bed flat when `bed_cut` > 0 (it had sliced the new belly off the ring's +x end). Normal: 145 × 91 × 26; M: 167 × 91 × ~36 (power bank still fits, the inside is unchanged). All 6 parts watertight, 1 body. XL files + render → `_archive/postcard_old_2026-10-16/xl_2026-10-17/` (`set_xl()` stays, M builds on it). Render `renders/postcard_m.png`, README updated.
- **Undo:** `RING_BULGE = 0`; move the XL files back.

## 17.10.2026 — Postcard M variant (~35 mm with the 25 mm power bank) + waves on the ring
- Flo: a ~3.5 cm thick version where the thick power bank just fits; the wave pattern also on the ring (pressed inwards). `make_postcard_case.py --m` (`set_m()`): XL footprint 162 × 86, plates 2.5 mm (GD 1.2 → flanks > 45°), lip 0.6, back bulge 0.5, lid rim 1.6, cavity 25.3 mm → assembled 162 × 86 × 35.8 mm, power bank 150 × 65 × 25 fits (0.84 mm at the corners, 0.3 mm height). `RING_WAVE = 0.5`: the ring's outside carries whole Pulse waves (λ ≈ 3.6) pressed 0.5 mm in, in all three variants (min. 1.2 mm wall to the groove). Lid envelope rebuilt (wide sweep + core prism, rounding top 0.05 above the rim) → no glancing contact; the thin-rim lid had broken into 11 bodies before. All 9 parts (normal / xl / m × ring, back, lid) watertight, 1 body, no supports (lid with break-out skin). Render `renders/postcard_m.png`, README updated.
- Open: USB plug of the power bank (port on its long side, 7.5 mm side gap) – Flo is measuring.
- **Undo:** `RING_WAVE = 0`; delete `set_m()` and `postcard_m_*`.

## 17.10.2026 — Postcard XL variant for the 10,000 mAh power bank (trial)
- Flo: try fitting the 150 × 65 × 25 mm power bank into the postcard. `make_postcard_case.py --xl` (`set_xl()`): L 140 → 162, cavity 10.5 → 26 mm, dips/waves scaled with the length; outputs `postcard/postcard_xl_{ring,back,lid}.stl` (+ `_model/`), the normal postcard files untouched. Fit check: power bank inside the inner outline with ≥ 0.84 mm gap (corners), 1 mm in height. Assembled 162 × 86 × 42 mm. Printing as v5 (no supports, lid skin). Render `renders/postcard_xl.png`.
- Open: no room for the USB plug at the power bank's end (only ~3 mm) — needs ~20 mm more length if the plug sits at an end; electronics (C3 on edge, motor) fit in the 7.5 mm side gaps.

## 17.10.2026 — Postcard v5: break-out skin in the lid window
- Flo chose a thin skin instead of the 46 mm bridge. `lid()`: `SKIN = 0.45` mm wall closing the window on the photo side (window outline + 0.3 overlap) → the window's top edge is carried by the skin when printed standing; only a ~2–3 mm overhang over the rest of the frame thickness remains. Cut the skin out along the window edge after printing (README). All 3 parts watertight, no supports.
- **Undo:** remove the `skin` from the union in `lid()`.

## 17.10.2026 — Postcard v5: 3 parts, the back clicks in too
- Flo: split the postcard so the bottom also slots in; check printing (no supports). `scripts/make_postcard_case.py`: `shell()` → `ring()` + `back()`. Ring: 2 inner 45° V-grooves (back at z = 2, lid at z = 16.5), 1.2 mm lip below the back, rounded top edge, bottom edge arc-to-45° chamfer, USB slot; printed lying. Back: textured dome + finger ovals on a 4 mm rim with the same V-tongue as the lid (`slab(..., base=TL)` + `tongue(0)`), printed flat (inside on the bed, texture up). Lid unchanged, printed standing. Overhang check as printed: ring 42 mm² (USB-slot top, 14 mm bridge), back 16 mm², lid 196 mm² (window top edge ≈ 46 mm bridge). All watertight.
- Files: `postcard/postcard_{ring,back,lid}.stl` (print-ready), `postcard/_model/` (assembled positions); one-piece shell archived to `_archive/postcard_old_2026-10-16/v4_shell_onepiece/`. Render `renders/postcard_case_v5.png`. READMEs updated.
- **Undo:** restore `shell()` from the archive's v4 entry and the archived shell STLs.

## 16.10.2026 — Simple table clip: cable groove removed
- Flo: the cable groove (inner face of the strip + under the plate) can go. `plate_cuts(..., cable_groove=True)`; `build_simple()` passes `False`. The ideal `table_unit_clip.stl` keeps its groove. Simple clip watertight, 1 body, still no supports.
- **Undo:** `cable_groove=True` in `build_simple()`.

## 16.10.2026 — Simple table clip: wall behind the rail instead of the notch
- Flo: keep a wall so the rail is screwed through the plastic into the table (holds best). `build_simple()`: notch removed; the edge strip is a `PAD` wall in the middle (5 mm thick, 44 mm wide, 45° ends into the strip) with a 1.5 mm recess 36 mm wide for the rail's back (locates it sideways) and 2 Ø3.4 holes (`PAD_SCREW_Z` 9 / 22.5) → wood screws 4 × 30 through rail slot + wall into the table edge. Still printed standing, no supports (only ≤ 2 mm bridges). Watertight, 1 body. README + render updated.
- **Undo:** restore the notch cut (previous entry) instead of the pad.

## 16.10.2026 — Table clip: new SIMPLE version for an old printer (no supports, no rail holder)
- Fablab closed; Flo's friend prints on an old printer → simpler model, saved as a NEW file; the ideal version stays (`table_unit_clip.stl`, geometry unchanged: same volume/area/bounds).
- `make_table_unit.py`: new `build_simple()` → `table_unit/table_unit_clip_simple.stl`: the clip without the rail holder; a 55 mm notch (rail width + 0.5 each side) through strip, plate edge and floor lets the rail pass straight onto the table edge (screwed into the table through its own slots; the notch holds it sideways). Printed standing (y = 0 on the bed, 140 mm tall): teardrop corners at the bed end (`plan_rect_tear`), upper pocket side wall with a 45° underside (`ext_x_wedge_at_end`), notch roof 3 mm → **no supports** (overhang check: only ≤ 3 mm bridges). 66 × 64 × 140, 76 cm³, watertight, 1 body. Shared plate details moved into `plate_cuts()` (mic, grille, cable groove, 4 edge-strip holes). Render `renders/table_unit_clip_simple.png`; READMEs updated (simple = send now).
- **Undo:** delete `build_simple()` + its export and `table_unit_clip_simple.stl`.

## 16.10.2026 — Table clip v4: guides halved (20 mm up and down)
- Flo: halve the rail guide above and below. `GUIDE` 40 → 20, `GUIDE_DOWN` 40 → 20; `SCREW_Z` = 43 (guide up, M4), 22.5 / 9 (table edge, wood 4 × 30), −14 (pocket, M4), −41 (guide down, M4). Clip 77.5 × 140 × 103.6 mm, 141 cm³, watertight, 1 body. Guide top now 23 mm above the table top, bottom 81 mm below it (rail guided over 104 mm). READMEs + render updated.
- **Undo:** `GUIDE = GUIDE_DOWN = 40`, `SCREW_Z = (62, 47, 22.5, 9, −14, −46, −62)`.

## 16.10.2026 — Table clip v4: 140 mm wide instead of 220
- Flo: shorter along the table, just enough for the electronics and the rail (asked ~half). 110 mm leaves no room for side screws (the holder with its 45° wings is ~87 mm) → `WIDTH` 220 → **140**. Grille margin now derived (`_m0`) so a middle-row hole still sits on the centre (mic port); `EDGE_HOLES_Y` = 6 / 16 / 124 / 134 (2 screws each side); cable groove (y = 117) stays clear of wings (end 114) and holes. Pocket inside 134 × 60 × 28 mm. Clip 77.5 × 140 × 143.6, 168 cm³, watertight, 1 body. READMEs + render updated.
- **Undo:** `WIDTH = 220.0`, `EDGE_HOLES_Y = (15, 35, 55, 165, 185, 205)`, grille margin 19.7.

## 16.10.2026 — Postcard folder tidied: only the two print files on top
- `Prints/postcard/` now holds just `postcard_shell.stl` + `postcard_lid.stl` (current v4, print-ready standing; byte-identical to the former `case_v4/*_upright.stl`) and a README; lying model versions in `postcard/_model/`.
- Archived to `Prints/_archive/postcard_old_2026-10-16/`: `v2_shell_and_tests/` (v2 tray/lid, Pulse test, swatches), `v3_four_parts/` (4-part case + `make_postcard_case_v3.py`), `v4_folder/` (old case_v4 files). Script renamed `make_postcard_case_v4.py` → `scripts/make_postcard_case.py` (writes straight to `postcard/` and `postcard/_model/`); `render_postcard_exploded.py` now reads the v2 shell from the archive (booklet p. 67). `Prints/README.md` updated.
- **Undo:** move the archive folders back into `postcard/`, rename the script back.

## 16.10.2026 — Table clip v4: screw holes in the edge strip instead of tabs
- Flo meant holes in the outside of the edge strip (sketch), not tabs under the table. `make_table_unit.py`: `TABS` off (`y=()`), new `EDGE_HOLES_Y` = 15 / 35 / 55 and 165 / 185 / 205 mm: Ø3.4 horizontal holes through the strip at mid table-edge height → 6 × wood screw 4 × 20 into the table edge. Cable groove moved 5 mm (`GROOVE_DY` 52 → 47) so it stays clear of the holes and the holder wings. 78 × 220 × 144, 213 cm³, watertight, 1 body, 0 edges < 0.05 mm. READMEs + render updated.
- **Undo:** `EDGE_HOLES_Y = ()`, `TABS` y back to (25, 110, 195), `GROOVE_DY = 52`.

## 16.10.2026 — Table clip v4: guide also 40 mm below, screw tabs under the table
- Flo: the guide should also go below (chose +40 mm with supports); small holes at the top of the pocket to screw it to the table.
- `make_table_unit.py`: `GUIDE_DOWN = 40` → the holder (full profile, wall behind the rail's back too) runs from 40 mm below the pocket floor to 40 mm above the plate (144 mm guided); 2 more Ø3.4 holes in the lower guide (`SCREW_Z` −46 / −62). The part now stands on the lower holder end (607 mm²) → tree supports under the pocket floor and the plate, brim on. `TABS`: 3 tabs (y 25 / 110 / 195, 20 wide, 12 out, 4 thick, 45° underneath, top 0.05 mm below the wall top) on the outside of the pocket's back wall with vertical Ø3.4 holes → wood screws up into the table underside (reachable from below). Pocket-corner mask 0.5 mm wider (the back wall forms its own face), holder back face made exactly flat. Clip 90 × 220 × 144, 220 cm³, watertight, 1 body, 0 edges < 0.05 mm; fit test unchanged. READMEs, render, sections updated.
- **Undo:** `GUIDE_DOWN = 0`, `SCREW_Z` without −46/−62, `TABS = dict(y=(), …)`.

## 16.10.2026 — Table clip v4: round Ø3.4 screw holes
- Flo: smaller round holes so the screws grip. `make_table_unit.py`: the 6 × 11 slots → round **Ø3.4** holes (`SCREW_D`) at the same 5 heights; the 4 mm wood screws and M4 screws cut their own thread in the PLA (nut optional). Note: the holes must meet the rail's slots — slide the rail so a slot sits over each hole. Watertight, 1 body, 186 cm³. README + render updated.
- **Undo:** `SLOT = (6.0, 11.0)` and the stadium-slot loop (previous entry).

## 16.10.2026 — Table clip v4: 2 mm groove with bent corners, lead-ins, fit test piece
- Flo: 1.4 mm groove too tight → 2 mm slot, corners bent. `make_table_unit.py`: `RAIL["fit"]` 0.2 → **0.5** (2 mm slot for the 1 mm sheet), new `RAIL["bend"] = 2` + `rounded_path()`: the groove follows bent corners; it is the union of a sharp, the nominal (R 2) and a wide (R 3.5) bend → checked: rails with sheet 1.0–1.2 mm and any bend radius 0–3 mm fit with ≥ 0.4 mm play. `LEAD = 0.4` mm lead-in steps at both groove ends (bed: against the elephant foot). Final mesh `Manifold.simplify(0.02)`. Clip watertight, 1 body, 0 edges < 0.05 mm, 185 cm³.
- New `table_unit/rail_fit_test.stl` (`build_fit_test()`): only the holder cross-section, 15 mm tall, ~10 cm³ — print first, slide the rail through.
- Recommendations (README updated): print the fit test first; screws now 2 × 4 × 30 wood screws (table edge), 3 × M4 × 20 + nut; tree supports only under the plate.
- **Undo:** `fit=0.2`, groove from the plain polyline (`join_style=2`), `LEAD = 0`, drop the fit test.

## 16.10.2026 — Table clip v4: hat inside open to the back
- Flo: the hollow may break through to the outside so the screws hold well. `rail_outlines()`: `hollow` now runs out through the outer wall over its full height (vertical channel on the back); the screw heads sit directly on the 4 mm wall at the rail's back (wood screw 4 × 30 into the table edge is enough now; M4 × 20 + nut in guide/pocket). Watertight, 1 body, 185 cm³; sections + views re-rendered.
- **Undo:** in `rail_outlines()` drop the `.union(box(...))` that opens the hollow.

## 16.10.2026 — Table clip v4: 45° wings into the strip, hollow hat inside
- Flo: the holder should merge into the clip at 45° (integral structure); the inside of the hat may be hollow (screws pass through) / hug the profile.
- `make_table_unit.py`: in the strip zone the holder's outside is one shape (`wings`) that runs into the strip at 45° on both sides (no steps, no slits); the 45° line and the wing top end just inside the strip / 0.25 mm below the plate top (no coplanar faces). `rail_outlines()` returns `hollow` = hat interior minus 4 mm walls around the sheet → cut through the full height (open at both ends). Checked: watertight, 1 body, 0 edges < 0.05 mm, 195 cm³; only overhang = plate underside (supports). Sections + views re-rendered.
- **Undo:** remove the `wings` and `hollow` lines in `build()` (holder = body only, hat inside solid).

## 16.10.2026 — Table clip v4: brim 10 mm
- Flo: the brims (Krempe) are ~1 cm. `RAIL["brim"]` 4 → **10** → rail 54 mm wide over the brims; groove play 0.2–0.28 mm checked, walls 4 mm around. Clip 77 × 220 × 104, 193 cm³, watertight, 1 body, only overhang = plate underside (supports). Section + views re-rendered. Leg slant still 0 (upright legs).
- **Undo:** `brim=4.0`, rerun.

## 16.10.2026 — Table clip v4: rail holder rebuilt from scratch, printed lying
- Flo: new rail references (Hutprofil, 153 cm, back 35 mm with slots, legs ~10 mm, brim, ~1 mm sheet); old groove not good → redo from scratch.
- `Prints/scripts/make_table_unit.py` rewritten (v3 standing version archived: `Prints/_archive/table_unit_v3_standing_2026-10-16/`). Rail defined by its sheet centre line (`RAIL`: back 35, depth 10, brim 4, slant 0, sheet 1, fit 0.2) → groove = sheet + 0.2 mm per side (square caps: 0.2–0.28 mm play everywhere, checked), body = HW 4 mm around groove + solid hat inside. **Print orientation changed**: lying on the pocket floor, rail direction up → every layer is the exact profile, no reliefs; tree supports only under the table plate. Guide now 40 mm ABOVE the plate (wall behind the rail's back there, sitting on the plate); below/at the table the body stops inside the strip. Pocket side walls plain (12 mm). 5 slots: z 62/47 (M4 + nut, guide), 22.5/9 (4 × 50 wood screws, table edge), −14 (M4 + nut, pocket). Corner rounding without teardrops (not needed lying).
- Check: watertight, 1 body, 0 edges < 0.05 mm, 10k triangles, 77 × 220 × 104, 183 cm³; only overhang = plate underside (supports). Sections with the rail overlaid: `renders/table_unit_groove_section.png`; views `renders/table_unit_clip_views.png` (render uses the real rail profile now). README (supports note) + `Prints/README.md` updated.
- Open: brim width (4 mm) and leg slant (0) are read from Flo's sketch/photo — measure with the calliper, then change `RAIL["brim"]` / `RAIL["slant"]` and rerun.
- **Undo:** restore `_archive/table_unit_v3_standing_2026-10-16/` (script + STLs).

## 16.10.2026 — Table clip: groove = sheet-thin rail slot (hat inside solid), back wall joined
- Flo: the groove was still a big open cavity, not the rail's shape. `make_table_unit.py`: inside of the hat solid again, so the groove is only the 1.3 mm slot around the sheet (web, legs, flanges). Two printing reliefs stay (printed standing): 45° triangle under the core above the lower leg, 45° roof behind the upper flange (a block there would start in mid-air).
- Fixed a real printing fault found in the section (also in the earlier versions): below the pocket the wall behind the web was not connected to the holder (it would have started in mid-air) → web wall now reaches into the holder with 45° ends; holder walls end inside the strip (x = −0.3, not on its face); closed the small gap above the bottom chamfer. Sections at table edge / pocket / guide: one piece each, no stray voids (`renders/table_unit_groove_section.png`). Watertight, 1 body, 205 cm³.
- **Undo:** previous entry's state (hat inside open: `box(-dep - c, lo, -t - c, hi)` in the void instead of the core relief).

## 16.10.2026 — Postcard: round USB end, no inner wedge · Table clip: walls hug the groove, pocket side walls
- Postcard (`make_postcard_case_v4.py`): `TEAR = 0` → the +x (USB) corners are as round as the others; shell no longer cut flat at the bed end; the 45° wedge inside the shell's −x end removed (Flo). Consequence when printed standing: the shell's inner −x end wall prints as a ~50 mm bridge (inside only, TPU may sag a little). Lid keeps its 0.6 mm bed flat (106 mm² contact). Both watertight, 1 body.
- Table clip (`make_table_unit.py`): holder outline = convex hull of the groove grown by 4 mm (flat back, top follows the 45° roof) + 45° chamfer under the bottom → walls hug the groove (Flo's sketch); `LIP = 12` mm side walls at both open pocket ends (y = 0 straight on the bed, y = 220 with a 45° underside) so nothing slips out, cables pass above. 77 × 220 × 104, 179 cm³, watertight, overhangs unchanged. Upright STL + renders (`renders/table_unit_clip_views.png`, `renders/postcard_shell_inside.png`) rebuilt.
- **Undo:** postcard `TEAR = 1`, re-add the wedge + `finish(shell())`; table: previous `outer` polygon (v3.1) and remove the lip block in `build()`.

## 15.10.2026 — Table unit v3.1: rail holder integrated again (one part)
- Flo: the rail is part of the clip, going inside it, clean back; stable through thickness but not wasteful.
- `make_table_unit.py`: separate holder dropped (`make_rail_holder.py` + `rail_holder.stl` → `Prints/_archive/rail_holder_separate_2026-10-15/`). Back in the clip: channel with the rail's exact hat profile (0.15 mm play, web on the table edge), inside of the hat open, flat 4 mm back wall, 45° sides, 40 mm guide below the pocket with a 4 mm wall behind the web, 5 vertical slots (2 × 4 × 50 wood screws, 3 × M4 × 30 + nut). Holder walls are ~4 mm everywhere (≈ 526 mm² cross-section, ≈ 54 cm³; no room left for an inner chamber). Whole clip 77 × 220 × 104, 172 cm³, watertight, 1 body, overhangs only ≤ 1.3 mm ceilings. Upright STL + render rebuilt, README updated.
- **Undo:** restore the files from `_archive/rail_holder_separate_2026-10-15/` and the v3 notch (previous entry).

## 15.10.2026 — Table unit v3: separate rail holder that fits the rail exactly
- Flo: the holder must follow the metal rail's shape and fit exactly, not be a casing. Printed standing (like the clip) that shape can't be printed without supports → split into two parts.
- New `Prints/scripts/make_rail_holder.py` → `Prints/table_unit/rail_holder.stl` (18 × 63 × 121, already upright): rail hat profile grown by 4 mm (walls inside and outside the sheet, hat stays open), 0.15 mm play, from 40 mm below the pocket to 20 mm above the table top; back wall behind the web only below the table; vertical row of 5 slots 6 × 11 (2 × wood screws 4 × 50 into the table edge, 3 × M4 × 30 + nut). Printed on its lower end: every layer is the exact profile, no overhangs (check: watertight, 1 body, ~1k triangles).
- `make_table_unit.py`: housing/shaft/slots/guide removed, notch = holder outline + 0.3 mm through strip/plate/floor; dead code removed, docstring updated. Clip 66 × 220 × 64, watertight; upright STL rebuilt. `render_table_unit.py` shows clip + holder. `Prints/README.md` updated.
- **Undo:** v2.4 state = previous log entry (shaft inside the clip); delete `make_rail_holder.py` + `rail_holder.stl`.

## 15.10.2026 — Postcard v4.2 (soft edges, clean mesh) + table clip v2.4 (rail-shaped 4 mm housing, vertical screw row)
- Postcard (`Prints/scripts/make_postcard_case_v4.py`): ring outer edges rounded R 2 (top + bottom), lid frame edge half-round R 1, back slab now ends inside the ring wall (ring alone forms the edge). `finish()`: bed end (+x) cut 0.6 mm flat (rounding starts at 45°, lid stands on 121 mm²) + `Manifold.simplify(0.05)` → no slivers (shell 39k tris, lid 24k, was 341k / 231k). Lid plate end at the bed side bevelled 45° (no tongue there; it would have started in mid-air).
- Table clip (`Prints/scripts/make_table_unit.py`): housing follows the rail with `HW = 4` mm walls: hat inside open (no core), outer wall over the flanges, pillar behind the lower flange, 45° roof above the upper leg (a block there would start in mid-air when printed standing), block above it hollowed; 4 mm wall behind the web below the table (45° ends). Screws: the 4 side holes removed; **vertical row of 5 slots** 6 × 11 along the rail (`SCREW_Z` 22.5 / 9 → 4 × 50 wood screws into the table edge; −12 / −37 / −62 → M4 × 25 bolts + nuts through outer wall, web, back wall).
- Check (as printed, standing): all 3 parts watertight, 1 body, 2-manifold; overhangs only small ceilings (≤ 1.3 mm flange tips, hole roofs) + the lid window's top edge (≈ 46 mm bridge). Stale zips moved to `Prints/_archive/stale_zips_2026-10-15/` (Flo: no zips until sending).
- **Undo:** values in the entries below; postcard: `BED_CUT = 0`, drop `finish()`/bevel; table: restore `shaft_outlines()` from v2.3 entry and `EDGE_SCREWS`.

## 15.10.2026 — Postcard v4.1 + table clip v2.3 (exact rail profile)
- Postcard (`Prints/scripts/make_postcard_case_v4.py`): back = two big oval dips at the ends (28 × 44, no centre oval), front window back to a rounded rectangle (70 × 56 R5; its top edge is a ~46 mm bridge when printed standing), deeper snap: lid plate 4 mm, V-tongue 1.3 mm deep, ring wall 3 mm (shell 17 mm + dome). Zip `Prints/fablab/postcard_v4_tpu.zip` rebuilt.
- Table clip (Flo: rail wobbles inside the shaft): shaft = **exact hat profile** of the rail (web 35, legs 10, flanges 10, sheet 1, play 0.15 mm), solid core between the legs, pillars behind the flanges; 45° roofs over the two wide ceilings above the legs (printed standing), located by flange tips + web ends. Slots now go through outer wall + core (use 4 × 40 mm screws). STLs + `Prints/fablab/table_module.zip` + README rebuilt.
- **Undo:** table: restore the trapezoid `shaft_outlines()` (log entry v2 / `_archive/table_unit_v1_2026-10-15/` for v1); postcard: values in the v4 entry below.

## 15.10.2026 — Postcard v4 (2 prints) + table clip v2.2 (guide sleeve, more screws)
- Note: `prints/` now lives at `Prototype/Prints/` (moved by Flo). My Write recreated an empty `Physical/prints/scripts/make_postcard_case.py` (v4) there — the copy that counts is `Prints/scripts/make_postcard_case_v4.py`; the stray `Physical/prints/` can be deleted (moving/overwriting was blocked by the safety filter). `Prints/scripts/make_postcard_case.py` = v3 (unchanged).
- Postcard v4 (`make_postcard_case_v4.py` → `Prints/postcard/case_v4/`): **2 prints**: `shell` (ring + domed back in one, back = 2 end dips + central oval dip 24 × 48 for the four fingers, ripples flowing, dome 3 mm) and `lid` (inner plate with V-tongue + 0.5 mm photo gap open at −x + textured frame, thumb dips at both ends, octagonal window 70 × 56 with 45° ends). Both printed **standing on the +x end** (+x corners = 45° teardrops, 45° wedge inside the top end of the cavity, window ends 45°) → overhang check: shell 89 mm², lid 134 mm² (small faces). `*_upright.stl` = as printed. Zip `Prints/fablab/postcard_v4_tpu.zip`; render `renders/postcard_case_v4.png`.
- Table clip v2.2 (Flo: rail wobbles): shaft extended **40 mm below the pocket** as a guide sleeve, shaft play tightened (width 1.0 → 0.4, depth 0.3 → 0.2), **4 extra Ø4.5 screw holes** through the edge strip into the table edge (y = centre ± 45 / ± 85, mid-height). 76 × 220 × 104, watertight. STLs + `fablab/table_module.zip` rebuilt, render updated.
- **Undo:** table: `GUIDE = 0`, remove `EDGE_SCREWS` loop, `clear_w=1.0, clear_d=0.3`, rerun; postcard: use `fablab/postcard_case_v3_tpu.zip`.

## 15.10.2026 — Table holes all through; postcard v3 ripples flow, back domed
- Table module: all sound holes now go through (also over mic recess and cable groove; blind holes removed, `SKIN` gone). Mesh still clean (watertight, 9,314 triangles, 2 edges < 0.1 mm). `table_unit/table_unit_clip(_upright).stl` and `fablab/table_module.zip` rebuilt.
- Postcard v3 (`make_postcard_case.py`): ripple distance = smooth min of the dip distances (`FLOW = 18` mm, log-sum-exp) → the two ring systems flow into each other around a soft saddle instead of meeting in a hard line. Back plate: oval dome `BULGE = 3` mm (elliptic, (1−u)^1.5, flat into the rim) → 6.1 mm high in the middle. Zip `fablab/postcard_case_v3_tpu.zip` rebuilt; render `renders/postcard_case_v3.png`.
- **Undo:** table: restore the blind-hole branch (see entry "Table module v2.1"); postcard: `FLOW` back to `r_min = min(...)`, `BULGE = 0`, rerun.

## 15.10.2026 — Postcard v3: clip-together TPU case (fablab)
- Flo's sketch: Pulse ripples all over (irregular), dips at both ends front (thumbs) and back (fingertips), photo window in the middle, closed case that clicks together without screws, double front wall for a printed photo.
- New `scripts/make_postcard_case.py` → `postcard/case_v3/`: `ring` (140 × 86 × 19, wall 2.4, 3 inner 45° V-grooves, USB-C slot 14 × 6 at +x; built as a sweep, no booleans), `back_plate` (Pulse height field λ 3.6 / 0.9 mm with phase/amplitude drift + 2 fingertip dips), `front_plate` (plain, closes the 10.5 mm electronics cavity), `front_frame` (waves + 2 thumb dips + window 70 × 56 R5). Plate edges = 45° V-tongues, 0.1 radial / 0.05 per side play; photo (≤ 0.5 mm) lies between front_plate and frame. All watertight, printed flat textured side up, no supports. Render `renders/postcard_case_v3.png`. Zip `fablab/postcard_case_v3_tpu.zip` (4 STL + README).
- Not modelled yet: pockets for C3/LiPo/motor, pressure-strip slot (electronics lie loose in the cavity).
- **Undo:** delete `scripts/make_postcard_case.py`, `postcard/case_v3/`, `renders/postcard_case_v3.png`, `fablab/postcard_case_v3_tpu.zip`.

## 15.10.2026 — Table module v2.1 packed for the fablab
- Flo confirmed the rail size (55 over the flanges, 10 deep, web on the table). New `fablab/table_module.zip`: `table_unit_clip.stl` already **standing upright** (y → z, the end with the 45° chamfered corners on the bed, 76 × 64 × 220, watertight) + README (6 lines: 1×, as in the file, no supports, brim, PLA, don't scale). Same README in `table_unit/README.md`. `table_unit/table_unit_clip.stl` = v2.1 in model coordinates (lying, for Rhino/renders), `table_unit/table_unit_clip_upright.stl` = the same part upright as in the zip.
- **Undo:** move `_archive/fablab_table_module_v1/table_module.zip` back to `fablab/` (overwrites the new one); old README text is inside that zip.

## 15.10.2026 — Table module v2.1: slots for ties, complete hole pattern, last row removed
- Flo: bigger holes in the shaft (cable ties possible); gaps in the hole pattern look weird; last row before the plate's tip looks odd.
- `scripts/make_table_unit.py`: shaft holes Ø4.5 → stadium **slots 6 × 11 mm** (long side along the rail; 4 mm screw with washer, or a cable tie). Hole band: 7 rows instead of 8 (last row before the sloped tip gone, ~5 mm free edge); no more skipped holes: holes over the mic recess/cable-groove edges are now **blind holes from the top** (0.4 mm skin over the groove), holes fully over the recess stay open; the mic port sits exactly on a grid spot (middle row, margin 19.7). Mesh: watertight, 9,034 triangles, 2 edges < 0.1 mm. Render updated (`renders/table_unit_clip_views.png`, top-right = plate from above).
- **Undo:** in `make_table_unit.py` set `SLOT` back to round Ø4.5 holes (cylinder instead of `batch_hull`), `GRILLE` x1 = 33 / margin 22 and the old skip filter — or take the v2 state from this log's entry below (rebuild from `_archive/table_unit_v1_2026-10-15/` for v1).

## 15.10.2026 — Table module v2: rail through the clip, rounded corners, clean mesh
- Flo: the steel rail should go through the C-clip and lie on the table (max hold), screwed from outside; round the 90° corners lying on the table; the v1 mesh looked messy in Rhino.
- `scripts/make_table_unit.py` rewritten: vertical **rail shaft** in the middle of the edge strip (open top/bottom), side walls at 45° (shaft widens towards the table → no overhang standing), outer wall rests on the rail flanges; 2 × Ø4.5 screw holes through the outer wall (screw passes between the rail legs, through the web slot into the table edge). Assumed rail (as in `render_assembly.rail`): web 35 on the table, legs 10, flanges 10 each side → shaft 56 wide at the outer wall, 10.3 deep. Cable-tie slots and outer ridges removed; cable groove moved to 52 mm beside the centre (was inside the shaft).
- Corners on/under the table rounded in plan R 10 (bed end y = 0: teardrop, arc to 45° then chamfer), strip ends R 2. Sound holes now hexagons (Ø1.8 flat-to-flat), holes that would clip the mic recess/groove edges skipped.
- Mesh: built only from manifold3d 2D extrusions + manifold booleans, top/bottom made by one slab cut → watertight, 8,948 triangles (v1: 23,828), 2 edges < 0.1 mm (v1: 87 < 0.05 mm). Overhang check (print standing, y up): nothing steeper than 45° except groove/mic-recess roofs (≤ 2 mm) and the tiny hole roofs. Orca (Anycubic template, cropped to 200 mm): slices, 6 h 46, 84 g.
- New `scripts/render_table_unit.py` → `renders/table_unit_clip_views.png`. `fablab/table_module.zip` **not** updated yet (rail size to confirm).
- **Undo:** copy `_archive/table_unit_v1_2026-10-15/make_table_unit.py` → `scripts/`, `table_unit_clip.stl` → `table_unit/`; delete `scripts/render_table_unit.py` and `renders/table_unit_clip_views.png`.

## 15.10.2026 — prints/ tidied up (Model Bot)
- New layout: `scripts/` (all .py), `table_unit/` (clip STL from the root + README from `table_module.zip`), `spotlight/` (spotlight-case stl/3mf/3dm out of the waterproof-box download), `fablab/` (`fablab_2026-10-14/` + the 3 zips), `drawings/` (sketches + wall-unit elevations), `_sources/` (the 4 Thingiverse downloads). `modules/`, `postcard/`, `renders/` unchanged (booklet tools in `Design Dokuz/Tools` read them).
- Archived: table-case (Renkforce edit, 08.10.) → `_archive/table_case_2026-10-08/`; spotlight .3dmbak/.stlbak/gcode (+ duplicate gcode from the sci-fi folder) → `_archive/spotlight_case_2026-10-07/`; `sci-fi-wall_v1.gcode` → `_archive/old_gcode_2026-10-08/`; empty `sketch-wall-piece_v2.png` (0 bytes) → `_archive/empty_files/`. Every move listed in `_archive/cleanup_2026-10-15_moves.txt`.
- Scripts relinked: `HERE = Path(__file__).resolve().parents[1]` (= prints/) in make_postcard, make_print_project, make_table_unit, make_wall_modules, render_assembly, render_postcard_exploded; make_cove_groove rglob from prints/; wall_unit_elevation writes to `drawings/`. Tested: make_table_unit → identical clip (volume/extents), elevation → drawings/. Python packages (trimesh, manifold3d …) installed on this PC.
- New `prints/README.md`: folders + module table. Paths updated in `Prompts/Model_Bot_Onboarding.md`, `Prototype_Bot_Onboarding.md`, `NewChat_Postcard_Flash_Lenovo.md`, `Gemini_Setup_Photo.md`.
- **Undo:** move each line of `_archive/cleanup_2026-10-15_moves.txt` back (right side → left side), move `scripts/*.py` back to prints/ and set `HERE = pathlib.Path(__file__).parent` again (wall_unit_elevation: `pathlib.Path(__file__).with_name(...)`; make_cove_groove: `pathlib.Path(__file__).parent.rglob`), delete `prints/README.md` and `table_unit/README.md`, revert the prompt paths.

## 15.10.2026 — Postcard flashed (v2); host no longer crashes on a slow WLED
- Postcard C3 on the Lenovo's USB (COM3, MAC 88:56:a6:6d:0b:c4; the table unit is …02:cc). Build dir `C:\pc\postcard` with the PlatformIO of `C:\wb\venv` (no separate venv). Flashed 4× while tuning.
- Findings: wiring OK (3V3 → strip → GPIO1 + 10 kΩ → GND; polarity of the strip doesn't matter). Single ADC readings swing 0…4095 within 100 ms (mains hum on the long strip wires); at rest the strip reads ~2000 (≈9 kΩ), pressed 4095. Motor + PN2222 OK (felt at full duty), but PWM 110–120 doesn't start it.
- `postcard_fw/src/main.cpp` v2 (Flo: always a faint heartbeat, faster/stronger only when pressed): each reading = average over 20 ms (cancels 50 Hz); resting value = lowest reading at start; dead zone `DEAD = 600`; full press computed at start (`4095 − rest − DEAD`); always beating: `BPM_REST 60` → `BPM_MAX 130` with the charge, strength `PWM_REST 170` → `PWM_MAX 255` with the pressure; every lub/dub starts with a 25 ms full-duty kick; 2 test buzzes at start; log = min/avg/max per 100 ms. Old v1 kept as `postcard_fw/src/main_v1_backup.cpp.txt`.
- Host crash (15:2x): `core/light.py _watch()` — the `POST /json/state` to a WLED that answered slowly raised `TimeoutError`, which wasn't caught → the whole host stopped. Now caught (`aiohttp.ClientError, asyncio.TimeoutError`), and `_keep_watching()` restarts a WLED watcher after any error (logs a warning).
- **v3 (flashed, works):** Flo: no hardware change now, intensity from holding time instead of pressure. Held / not held with hysteresis (`HOLD_ON 0.5` / `HOLD_OFF 0.3` of rest → top); strength `PWM_REST 170` → 255 over `HOLD_S 4`, back within `RELEASE_S 1.5`; tempo 60 → 130 bpm (`CHARGE_UP 0.12` ≈ 8 s, `CHARGE_DOWN 0.04` ≈ 25 s back). Motor swapped by Flo; the readings of ~2000 at rest / 4095 when pressed came from a loose strip wire — after re-plugging: rest ~5, held 2000–3400 (real gradation). Test log: short hold → small rise, 10 s hold → full strength + 130 bpm, release → strength back in 1.5 s, tempo drains. Reset without replug: `python -m esptool --port COM3 --after hard_reset chip_id` (recalibrates the resting value).
- Open: motor sometimes stops until re-plugged (likely a loose contact; add a flyback diode 1N4148/1N4007 across the motor, cathode to 5V); finer pressure would need a 1–2.2 kΩ pull-down instead of 10 kΩ.
- **Undo:** postcard: copy `main_v1_backup.cpp.txt` back to `main.cpp`, build + upload from `C:\pc\postcard`; host: revert the two changes in `core/light.py` (`connect()` gathers `_watch` directly, `except aiohttp.ClientError`).

## 15.10.2026 — Morning Jam refactor: whole-loop rows, one mic control, live feedback
- Flo: rows must land where they were played (beat 2 and 6 → 2 and 6 next round), no "listen", one mic control that also shows the level, rows visible as waveforms one under the other, minimal code, feedback on the interaction.
- `core/netmic.py` RowRecorder: records the **whole loop** (8 beats) instead of a 4/4 bar tiled twice; no bleed learning (`learning`, `bleed`, `row_over_bleed`, `row_beats` removed); fixed `threshold` (RMS 20 ms), changed live from the web page. `core/audio.py`: `add_row(rec)` = the loop as recorded (no tiling), `waveform()` helper (160-point peak waveform `env`, kept through snapshots for Spring Cleaning).
- `scenarios/morning_jam.py` rewritten (123 → 87 lines): wake → jam → outro; no laptop-mic fallback (`on_sound`, `on_onset` muted); feedback: spotlight lifts live with the table mic (host loop: `light.mic`/`capture_tgt` from the table mic level over the threshold — before this came from the laptop mic, which made the spotlight blink when talking), new row = bone flash on spotlight + table edge, every row = soft peach pulse when it comes round. `core/scenario.py`: `on_bar` removed.
- `main.py`: cmd `mic_threshold` (raw RMS), state `mic_threshold`, meter `lvl`/`gate` (raw); removed the slider→threshold hack from earlier today. `room.toml [morning_jam]`: only `row_threshold = 0.002` + `row_gate` left.
- Web (`app.js`, `style.css`, `index.html` v=36): Morning Jam card = one "Table mic" bar: live level fill + draggable threshold line on one log scale (0.0003…0.1), glows when above; stage = rows as mirrored waveforms, newest at the bottom (new row glows peach), plus a live lane that draws what the mic hears in the current loop (grey under / orange over the line); sims Tap/Hum removed from Morning Jam.
- Backup of all touched files before the refactor: `host/_backup_mj_1510/`.
- Stop → outro: new hook `Scenario.wind_down()` (`core/scenario.py`, default False = cut as before); Morning Jam returns True during wake/jam → `ending`, the jam ends and the piano outro plays at once; a second Stop cuts. `main.py` cmd "stop" asks `wind_down()` first. Tested: Stop at 9 s → outro 0.5 s later → idle 7 s later. `max_minutes` 6 → **2**. Row waveforms smoother: `waveform()` = RMS per bin + [1 2 3 2 1] smoothing (was peak).
- Scenarios page: removed the "Presence starts the selected scenario" bar (index.html, its JS in `scenState()`, `.presence-bar` CSS); `auto_start = false` stays, all scenarios are started by hand. index v=38.
- Flo's browser kept the old page (cached `index.html`): `core/web.py` now sends `Cache-Control: no-cache` for `/` and `/static/*` (middleware `no_cache`). Morning Jam try-its: only "Clear rows" left; card text mentions talking. index v=37. (Undo: remove the middleware; SIMS back to arrive/leave/clear.)
- **Undo:** copy the files from `host/_backup_mj_1510/` back (`netmic.py`, `audio.py` → `core/`, `morning_jam.py` → `scenarios/`, `app.js`, `style.css`, `index.html` → `web/`, `main.py`, `room.toml` → `host/`), restore `on_bar` in `core/scenario.py`, restart the host.

## 15.10.2026 — Morning Jam: fixed row threshold, rows shown as waveforms
- Test with the table mic (after a loose mic wire was fixed; the loose wire had given a fake "bleed" of 0.1): beat bleed 0.001, taps 0.02–0.05 RMS, 7 rows in ~1 min. Flo: threshold felt too high, no calibration at scenario start.
- `room.toml [morning_jam]`: `row_threshold` 0.02 → **0.008**, new `row_calibrate = false` (true = old behaviour: learn bleed in "listen", threshold = bleed × `row_over_bleed`). `scenarios/morning_jam.py`: learns only when `row_calibrate`.
- Temporary: `absence_timeout_s` 20 → 86400 (spotlight/radar charging; the jam ended at once without presence). **Set back to 20** when the spotlight runs again.
- Row view: the web page placed table-mic rows at `slot/steps` = 150 %…1000 % (outside the loop) → invisible. `core/audio.py add_row()` stores a 160-point peak waveform per row (`v.env`), `main.py` sends it as `layers[].env`, `web/app.js` + `style.css`: in the scenario stage a "rows · table mic" lane, one mirrored waveform strip per row (tiled over the loop, last 12, fading with age); rows no longer drawn as markers in the small loops.
- **Undo:** `row_threshold = 0.02`, delete `row_calibrate` line and in `morning_jam.py` set `rows.learning = True`; `absence_timeout_s = 20`; remove the `env` lines in `audio.py`/`main.py`, the rows block in `stageState()` (app.js), the `.bl-lane.rows`/`.bl-row` CSS and the `.filter((l) => l.kind !== "row")` in the small-loop marks.

## 15.10.2026 — Lenovo laptop = presentation host on its hotspot FLO-WORK
- Hotspot FLO-WORK on (2.4 GHz, power saving off), laptop = 192.168.137.1 (checked). Host `python main.py` runs on the Lenovo (requirements installed; Python already allowed in the firewall for "public"). Audio out for now = MOMENTUM 4 headset (Windows default); the host also opens its mic → Bluetooth hands-free mode, sounds "electronic" (to fix: other input device).
- On the hotspot: table ESP (.137.242, no LED strip at the moment), spotlight-unit (.137.19), iPad (.137.181); both WLEDs found by mDNS. Wall unit / Gledopto ignored for now.
- Spotlight: WLED MQTT broker 192.168.137.200 → **192.168.137.1** (via `/json/cfg`, rebooted); connects to the host's embedded broker. room.toml comment updated.
- Table mic stream target 192.168.178.101 → **192.168.137.1** in `wled/usermod_audio_stream/usermod_audio_stream.h` (default) and `wled/platformio_override.ini` (`table_c3_stream`). Build dir on the Lenovo: `C:\wb` (WLED v0.15.1 clone + venv).
- Built `table_c3_stream` in `C:\wb` (needed Node.js → installed Node.js LTS 24.20 via winget, then `npm ci`): 1.55 MB, flash 76 %. **Flashed OTA** (curl → `http://192.168.137.242/update`, WLED "Table"; WLAN kept). WLED Info: "Mic stream: … packets → 192.168.137.1:7010"; host shows `mic: table mic (UDP 7010, 192.168.137.242)`. Radar data from the spotlight also reaches the host (`in/presence/*`). Host output now Realtek laptop speakers, MOMENTUM disconnected.
- **Undo:** spotlight WLED → Config → Sync → MQTT broker back to 192.168.137.200; table: OTA-flash a `table_c3` build (audioreactive) instead; stop the host (Ctrl+C / end the python process); stream target back to 192.168.178.101 in both files (or per device: WLED → Usermods → AudioStream).

## 15.10.2026 — Host on the laptop; table mic streamed; Morning Jam records bar rows
- Supervisor: all sound from the PC. New `host/machine.toml` (laptop): WASAPI, Windows default output, input "USB", room_output "main", embedded MQTT. The Pi deploy overwrites machine.toml on the Pi, so it never reaches dexy. Pi was off (checked); laptop = 192.168.178.101. Host runs: `python main.py` in `host\`.
- Flo: the table unit's INMP441 becomes the Morning Jam mic, raw audio, no sound detection: each 4/4 bar is recorded; if it was loud enough the whole bar becomes a row in the loop. New `host/core/netmic.py` (NetMic: UDP "NMIC"+seq+int16 16 kHz, capture clock = min-filtered arrival offset − latency; RowRecorder: bars of `row_beats`, threshold = max(row_threshold, learned beat bleed × row_over_bleed), gate, resample to 48 kHz), `AudioEngine.add_row()` (bar tiled to the loop, plays from the current loop), hooks `on_bar`/`on_row` in `core/scenario.py`, `main.py` wiring (`[netmic] enabled`), Morning Jam learns the bleed in "listen" and records rows in "jam" (falls back to the old tap detection without the net mic). `room.toml`: `[netmic]` + row settings in `[morning_jam]`. Simulated test (scratchpad `sim_tablemic.py`): bleed learned, 4 bars of claps → 4 rows accepted.
- Firmware: `wled/usermod_audio_stream/usermod_audio_stream.h` (I2S 48 kHz → 16 kHz mono, UDP to 192.168.178.101:7010, settings in WLED → Usermods → AudioStream), registered in `patch_wled.py`, new env `table_c3_stream` (no audioreactive), `build.sh` copies it. Built OK in `C:\Users\Florian\.wb` (1.44 MB). **Not flashed yet.**
- **Undo:** delete `host/machine.toml` (laptop) and set `[netmic] enabled = false`; firmware: keep flashing `table_c3` (audioreactive) as before.

## 14.10.2026 — Postcard: single "Pulse" TPU test piece
- Sampler looked pixelated (0.45 mm grid + hard-edged formulas); Flo: test only Nr. 1. `make_postcard.py --pulse` → `postcard/postcard_pulse_tpu.stl`: 90 × 90 mm, base 3 mm, smooth dip (Ø 22, 1.5 deep) + soft cosine waves (λ 3.6, 0.9 high) fading out at r 30–40, 0.2 mm height grid; `heightfield_solid()` bottom now a centre fan (smaller STL, 20 MB). Orca: no warnings, ~1 h 32 (PLA profile). `prints/postcard_pulse_tpu.zip` (STL + README); sampler (4 fields, 0.25 mm) → `_archive/`.

## 14.10.2026 — Postcard: one-piece TPU sampler (after the failed TPU print)
- Swatch print on the fablab's Bambu X1 failed (pillowing + strings). Likely causes: my 3MF carried the Anycubic process (2 % infill, 0.3 mm), features too fine for TPU (0.4 mm ridges, many islands), TPU settings (AMS, speed, moisture). From now on fablab gets **STL only**.
- `make_postcard.py --sampler` → `postcard/postcard_sampler_tpu.stl`: one 170 × 110 mm plate (base 3 mm), smooth height field (no thin ridges): 1 Pulse, 2 Pebble, 3 Heartbeat (6 lub-dub domes), 4 Terrain (soft terraces), 5 Fingerprint (bold loop ridges, λ 3.6 mm, amp 0.9 mm), fields fade into flat gutters. `heightfield_solid()` builds the closed mesh. Orca: no warnings. `prints/postcard_sampler_tpu.zip` (STL + 4-line README with Bambu TPU notes); old swatch zip → `_archive/`.

## 14.10.2026 — Postcard swatches: Pebble fixed, 3 = Heartbeat rosette
- Pebble back to the earlier version, a little more irregular (outline noise 0.22, rings 1.5–2.3 mm apart, no gaps/stretch); its dip is now 6 stacked outline slices (no crease from deforming a sphere). Swatch 3 = Heartbeat rosette: 6 pairs of soft raised petals (big + small = lub-dub) around the dip; circling at ~3 cm/s (preferred C-tactile speed) ≈ 90 bpm. Orca: no warnings. `prints/postcard_swatches_5.zip` rebuilt.

## 14.10.2026 — Postcard swatches: Pebble more irregular, 3 = Mandala (wrap-up)
- `swatch_pebble`: stronger outline noise (0.30), dip elongated 1.25 × 0.85 and rotated 28°, rings with uneven spacing (1.2–3.2 mm) and eroded gaps. `swatch_spiral` → Mandala: scalloped ring (12 lobes), 12 petals, ring of 36 dots, outer wave ring (24 arcs). Plate 2 h 42 (PLA profile), no Orca warnings, all tiles closed underneath. `prints/postcard_swatches_5.zip` rebuilt (legend updated).
- State of the postcard: shell v2 (`postcard_tpu_2026-10-14.zip`: plain tray + lid with Pulse texture) and the 5 swatches; the winning texture goes into the lid next.

## 14.10.2026 — Postcard: 5 experimental haptic swatches
- `make_postcard.py --swatches` → `postcard/postcard_swatches_5` (STL + 3MF, plate 179 × 117 mm, five 55 mm tiles marked 1–5 dots): 1 Pulse (round dip + even ripples), 2 Pebble (irregular off-centre dip + growth rings following its outline), 3 Spiral (one spiral ridge with a "lub" every fifth of a turn), 4 Terrain (procedural height map, 7 terraces × 0.3 mm), 5 Fingerprint (procedural loop pattern, 1.6 mm ridges). New `ext_robust()` (manifold3d CrossSection extrusion) for complex outlines. Render `postcard/postcard_swatches_view.png`; zip `prints/postcard_swatches_5.zip` (replaces the 3-pitch test, moved to `_archive/`).
- **Undo:** delete the swatch files/zip; restore `_archive/postcard_texture_test.*`.

## 14.10.2026 — Postcard: haptic test swatches
- `make_postcard.py --test` → `postcard/postcard_texture_test` (3 tiles 55 × 55 × 2.4, each = the lid's grip zone: thumb dip + ripples; pitch 1.2 / 1.8 / 2.6 mm, marked 1/2/3 dots). Orca (PLA profile) 1 h 31 for all three, no warnings. `prints/postcard_texture_test.zip`.
- **Undo:** delete the test files/zip; the `--test` branch in `make_postcard.py` is optional.

## 14.10.2026 — Tactile postcard v2: plain tray, textured lid
- Flo: tray simpler (parts fitted freely); lid with a haptic pattern that invites stroking (research: C-tactile afferents like slow stroking 1–10 cm/s at skin temperature; low-effusivity materials feel warm; dense/tall spikes feel unpleasant). `make_postcard.py` v2: tray = floor + walls, 1.2 mm grip floors, one USB-C opening 14 × 6, top rebate (1.0 × 2.4) for the lid; lid = flat plate printed texture up: thumb dip per grip (Ø 26, 1.2 deep, 1.2 left for touch) + ripples spreading out (0.4 high, 0.8 wide, pitch 1.8 growing), perforated stamp in the middle. 15 mm thick in total. Orca (PLA profile): tray 1 h 41, lid 1 h 49, no warnings. Renders `postcard/postcard_view.png`, `postcard_lid_top.png`; zip rebuilt.
- **Undo:** previous geometry is in git-less history only → rerun from the v1 description in the entry below (frames + push-in lid).

## 14.10.2026 — Tactile postcard: first TPU shell
- New `prints/make_postcard.py` → `prints/postcard/postcard_tray` + `postcard_lid` (STL + 3MF, 140 × 86 × 15 mm, rounded "Switch"-like slab, push-in lid with 1.2 mm rim, 0.15 mm clearance). Inside: frames for LiPo 102535, ESP32-C3 SuperMini and TP4056 (both USB-C through the +x wall), coin-motor ring in the left grip; floor and lid 1.2 mm thin under both grips for copper-foil touch electrodes; perforated "stamp" recess on the lid. Orca (PLA profile): tray 1 h 53, lid 1 h 17, no warnings. `prints/postcard_tpu_2026-10-14.zip` with a 4-line README (TPU 95A).
- **Undo:** delete `make_postcard.py`, `postcard/`, the zip.

## 14.10.2026 — Fablab rev. 10: clip mesh repaired
- Orca: 48 non-manifold edges in `clips_12_plate` (4 per clip; the extruded 2D dog-bone had near-duplicate points where arcs meet the neck). `clip_part()` now = manifold union of two cylinders + neck box → 0 non-manifold edges, watertight. Checked the other package files: top module, wall tile, end caps 0 non-manifold edges. `fablab_2026-10-14_rev10.zip`; rev. 9 zip → `_archive/`.
- **Undo:** `_archive/fablab_2026-10-14_rev9.zip` (broken clips).

## 14.10.2026 — Fablab rev. 9: clips as a ready plate
- Duplicated clips sat too close → warning. New `clips_12_plate` (12 clips, 3 × 4, 10 mm gaps, 140 × 78 mm, 54 min, Orca: no warning) replaces `clip_dogbone_x12` (→ `_archive/fablab_rev6_files/`). README: 6 lines. `fablab_2026-10-14_rev9.zip`; rev. 8 zip → `_archive/`.
- **Undo:** use `_archive/fablab_2026-10-14_rev8.zip`.

## 14.10.2026 — Fablab rev. 8: max 3 mm walls also on the tiles
- Flo: keep max 3 mm walls everywhere, the fablab sets infill. `TILE_SOLID = False`, new `TILE_SHELL = 3.0` (hollow tiles, used in `hollow_tile`), tiles upright with external clip sockets; top modules unchanged (2.4 mm). All three tiles = tablet tile with ledge (`wall_tile_x3`).
- Times: tile 11 h 33 (5 %) / 12 h 59 (15 %) / 18 h 20 (100 %); total ≈ 69 h / 76 h / 98 h. Tiles keep the non-critical Orca note (relief ≤ 1.3 mm). README rev. 8, `fablab_2026-10-14_rev8.zip`; rev. 7 zip → `_archive/`.
- **Undo:** `TILE_SOLID = True` + export tiles `--back-down` (rev. 7); or `_archive/fablab_2026-10-14_rev7.zip`.

## 14.10.2026 — Fablab rev. 7: 4 files only
- Flo: all wall tiles with the ledge, keep it simple. Fablab folder now: `top_module_x3`, `wall_tile_x3` (= tablet tile incl. pilot holes; flat on the back), `end_caps_left_right` (both caps on one plate, 131 × 200, print orientation), `clip_dogbone_x12`, README. Old separate tile/cap files → `_archive/fablab_rev6_files/`. Total ≈ 63 h (5 %) / ≈ 75 h (15 %).
- `fablab_2026-10-14_rev7.zip`; rev. 6 zip → `_archive/`.
- **Undo:** restore the files from `_archive/fablab_rev6_files/` or use `_archive/fablab_2026-10-14_rev6.zip`.

## 14.10.2026 — Fablab rev. 6: planned for 5–15 % infill, solid flat tiles
- Flo: assume ≤ 15 % infill, maybe 5 %. Orca comparison: top module identical with/without channel (the foot is gone); wall tiles solid + flat on the back are faster than hollow upright ones at 5 % (side 8 h 01 vs 9 h 54, tablet 9 h 32 vs 11 h 41), equal at 15 %, no Orca warning, relief faces up. `TILE_SOLID = True`: tiles without channel, clip pockets in the back (3.3 mm deep), printed `--back-down`. Top modules unchanged (external sockets, 2.4 mm).
- Total ≈ 60 h / 1.1 kg at 5 %, ≈ 71 h / 1.3 kg at 15 %. No Orca warnings on any part. README rewritten (rev. 6), `fablab_2026-10-14_rev6.zip`; rev. 5 zip → `_archive/`.
- **Undo:** `TILE_SOLID = False` (hollow upright tiles, rev. 5) and export tiles without `--back-down`; or `_archive/fablab_2026-10-14_rev5.zip`.

## 14.10.2026 — Fablab rev. 5: external clip sockets, 2.4 mm walls
- Fablab suggestion: clips outside. `make_wall_modules.py`: `EXTERNAL_CLIPS = True` → no pockets; `clip_socket()` adds half a dog-bone rim (1.6 mm wide, clip thickness + 0.3 high) on the back face (sticks out 3.3 mm behind, at the module edges, away from the rail) and on the top face of the top modules; tiles get them on the back. Clips 3.0 mm again. `BACK_SKIN`, `TOP_SKIN`, `SHELL` → 2.4. End-cap outline clipped to the body (no sockets). Pi pocket unchanged in size (slightly larger).
- Times (15 % / 100 %): top 10 h 45 / 12 h 52, tablet tile 12 h 47 / 16 h 42, side tile 10 h 46 / 13 h 43, end cap 1 h 51. Total ≈ 71 h / ≈ 88 h (rev. 1 at 100 %: ≈ 175 h). Tiles keep the non-critical Orca note.
- `fablab_2026-10-14_rev5.zip`; rev. 4 zip → `_archive/`.
- **Undo:** `EXTERNAL_CLIPS = False`, skins/SHELL back to 3, clips 2.0; or `_archive/fablab_2026-10-14_rev4.zip`.

## 14.10.2026 — Fablab rev. 4: 3 mm walls, less Pi slack
- Tested in Orca (15 % infill): 3 mm walls −3…4 %, depth 35 vs 40 −2 %; geometry is now wall/layer-bound (600 layers per top module), further thinning gains little. Applied: `SHELL`, `BACK_SKIN`, `TOP_SKIN` 4 → 3, clips 2.8 → 2.0 mm (pockets 2.3 deep), `DEPTH_ADD` 40 → 35. Pi pocket still takes an upright 42 × 84 mm box beside the screw column.
- Times per part (15 % / 100 % infill): top 11 h 33 / 14 h 42, end cap 1 h 51, tablet tile 13 h 00 / 18 h 14, side tile 11 h 00 / 15 h 15. Total ≈ 74 h (15 %) / ≈ 97 h (100 %; rev. 1 ≈ 175 h). Tiles keep the non-critical Orca note (relief ≤ 1.3 mm).
- `fablab_2026-10-14_rev4.zip`; rev. 3 zip → `_archive/`.
- **Undo:** values back to 4 / 4 / 4, clips 2.8, `DEPTH_ADD = 40`; or `_archive/fablab_2026-10-14_rev3.zip`.

## 14.10.2026 — Fablab rev. 3: flat bottom, Pi pocket, 40 mm deeper
- Flo (photos): the Pi in its case stands upright at the back and was stuck at the stepped foot/floor. Pi 5 drawing (official, RP-008347): board 85 × 56, holes 58 × 49, parts up to 18.4 mm above the PCB; Flo's case ≈ 80 × 40 mm cross-section (from the photo).
- `make_wall_modules.py`: `FLAT_BOTTOM = True` (flat 4 mm bottom block from the back to the cove start replaces the tile foot; cavity pocket down to z = 4), `DEPTH_ADD` 30 → 40. Cavity: x 4…134, z 4…92. Upright box up to 45 × 86 mm fits in every module, also beside the screw column (mid: up to ~47 mm deep, outer: ~62 mm). Modules now 136 × 180 × 96.
- Re-exported top modules + end caps (modules/ and fablab/), Orca: no warnings; 15 % infill 12 h 00 / 205 g, 100 % 18 h 41 / 329 g per module. `fablab_2026-10-14_rev3.zip`; rev. 2 zip → `_archive/`.
- **Undo:** `FLAT_BOTTOM = False`, `DEPTH_ADD = 30.0`; or `_archive/fablab_2026-10-14_rev2.zip`.

## 14.10.2026 — Fablab rev. 2: max ~4 mm solid sections
- Fablab feedback: max 3–4 mm thickness. `make_wall_modules.py`: `SHELL = 4`, `BACK_SKIN`/`TOP_SKIN` 7 → 4 (`ROOF_THIN` off), clips 4.6 → 2.8 mm (pockets 3.1 deep), screw column 12 → 8 mm wide; `hollow_profile()` = channels along y in the top modules where the profile is thicker than 8 mm (wall foot); `hollow_tile()` = channel inside the wall tiles following the relief (front wall ≥ 4 mm behind the deepest groove, 45° transitions, closed bottom, open top, solid seam strip 12 mm + edges). Tiles now print **upright**; plate↔panel bond fixed (the tile's foot was lifted ~0.4 mm, only ~100 mm² contact); groove top between panel rows chamfered 45°.
- Times (Orca, i3 Mega, 0.3 mm): at 2–15 % infill rev. 2 ≈ same time as rev. 1 (−4…−8 % PLA); at 100 % infill −24 % (top module 24 h 23 → 18 h 30) to −43 % (side tile 34 h → 19 h 24). Remaining Orca note on the tiles = relief ledges ≤ 1.3 mm (non-critical).
- `fablab_2026-10-14/` updated + `fablab_2026-10-14_rev2.zip`; rev. 1 zip → `_archive/`. Renders not updated.
- **Undo:** `SHELL = None`, `BACK_SKIN = TOP_SKIN = 7`, `ROOF_THIN = (4.0, 22.0)`, `CLIP t/depth 4.6/5.0`, `boss_d 12`, remove the groove wedge + bond blocks in `wall_tile`; or use `_archive/fablab_2026-10-14_rev1.zip`.

## 14.10.2026 — Print files cleaned up for the fablab
- New send folder `prints/fablab_2026-10-14/` (+ `.zip`): current parts with quantity in the name (`top_module_x3`, `end_cap_left_x1`, `end_cap_right_x1`, `wall_tile_tablet_x1`, `wall_tile_side_x2` = flat variant, `clip_dogbone_x12`), STL + freshly oriented 3MF, `README.md` (orientation, settings, times ≈ 57 h / ≈ 1 kg).
- `modules/` keeps only current generator outputs. Moved (not deleted) to `prints/_archive/`: `wood_beam_backup/`, Flo's old G-codes (`old_gcode_2026-10-08/`), the shelf variant of the side tiles (`shelf_side_tiles/`), all preview/section PNGs (`previews/`).
- **Undo:** move the folders back from `_archive/`; delete the fablab folder/zip.

## 13.10.2026 — Wall unit: top modules 30 mm deeper + thinner roof (Pi 5 fits)
- Flo: the Pi in its case almost fit the printed mid module. `make_wall_modules.py`: `DEPTH_ADD = 30` (cove + LED slot 30 mm further into the room, flat floor in between, slab lengthened), `ROOF_THIN = (4, 22)` (roof 4 mm instead of 7 between y 22…158, ends sloped 45°). Cavity now x 7…124, z 19…92 (middle). Official Pi 5 case (98.5 × 70.3 × 33, retailer spec) fits **standing on its long edge** (≈1.5 mm play) in every module, in the mid module beside the screw column; lying flat it does not (LED slot).
- Modules now 126 × 180 × 96 mm (side print footprint 126 × 96). All three top modules + both end caps re-exported (STL + 3MF). Orca CLI: no warnings. Top module 9 h 12 / 157 g each, end cap 1 h 38 / 30 g. The printed mid module (old profile) no longer matches the new ones → reprint all three for a continuous cove.
- Renders in `prints/renders/` deliberately NOT updated (Flo); re-running `render_assembly.py` would pick up the new STLs.
- **Undo:** `DEPTH_ADD = 0.0`, `ROOF_THIN = None`, rerun + re-export.

## 13.10.2026 — Page 63: one setup photo instead of three scenario images
- Gemini redesigned the scene from photo + renders (ring lamp on the floor, wall unit too small/low, invented person). New approach: true-scale photomontage, Gemini only blends. `prints/composite_setup.py` (wall unit front render + kiosk screen, light row top 2.0 m, rail hidden behind ring lamp/box via wall-colour mask) → `prints/renders/setup_montage.png`; `render_assembly.py` keeps the object mask (`LAST_ALPHA`).
- New `Prompts/Gemini_Setup_Photo.md` (one-turn prompt, step-by-step fallback, crop advice, draft card texts for scenarios 1–3 from the scenario code). `Gemini_Scenario_Photos.md` superseded.
- **Undo:** delete `composite_setup.py`, `setup_montage.png`, the prompt file.

## 13.10.2026 — Kiosk clock screenshot on the iPad renders
- Silent laptop host (scratchpad `test_room.toml`: volume 0, all hosts 127.0.0.9, mDNS names dummied, ports 8090/1893) → headless Edge screenshot of `/static/clock.html` at iPad mini 6 landscape (1133 × 744 pt @2x) → `prints/renders/ipad_clock_screen.png`. Host stopped afterwards; Pis not touched.
- `render_assembly.py`: `paste_screen()` maps the screenshot onto the iPad screen (LED-on renders). Gemini prompt: screenshot as 4th reference image.
- **Undo:** delete `ipad_clock_screen.png` (renders then show a blank screen) and re-run `render_assembly.py`.

## 13.10.2026 — Wall unit: flat side-tile variant
- `wall_tile(..., ledge=False)` → `wall_tile_side_flat_x2` (same bottom line as the tablet tile, no shelf; 7 h 54 / 136 g, Orca: no warnings). Both side variants kept until Flo picks. `render_assembly.py --flat` renders the flat version (`*_flat_sides.png`); Gemini prompt covers both.
- **Undo:** delete `wall_tile_side_flat_x2.*` and `renders/*_flat_sides.png`.

## 13.10.2026 — Wall unit: side tiles get the ledge too
- Flo: the row looked incomplete under the tablet. `wall_tile(tablet, rail)`: side tiles = tablet tile without seam fill / pilot holes → continuous 54 cm ledge and one bottom line. New `wall_tile_side_x2` (print twice, 9 h 22 / 159 g, Orca: no warnings); old `wall_tile_x2.*` → Recycle Bin. Renders and Gemini prompt updated.
- **Undo:** restore `wall_tile_x2.*`; `__main__` back to `wall_tile()`.

## 13.10.2026 — Wall unit: assembly renders + Gemini prompt for documentation photos
- New `prints/render_assembly.py` (numpy z-buffer renderer, no Blender): assembles the real STLs (3 top modules, end caps, 2 wall tiles, tablet tile, steel rail, stand-in iPad) → `prints/renders/wall_unit_{threequarter,front}_{led_off,led_on}.png`.
- New `Prompts/Gemini_WallUnit_Photo.md`: prompt A (unit alone, style of the table / ring-light photos), prompt B (with the folding table).
- **Undo:** delete `render_assembly.py`, `prints/renders/`, the prompt file.

## 09.10.2026 — Wall unit: wall tiles + tablet tile
- `make_wall_modules.py`: new `wall_tile(tablet)` = panel section of the tile wall (z 0..114, 180 wide, 18 mm, flat back), side clip pockets. Tablet version: plate 50 mm lower, ledge (channel 35 mm for a ≈15 mm case, 12 mm lip with 45° inner face) → iPad mini 6 in hardshell case leans ≈ 8° on the panel, top ≈ 16 mm under the light row; seam filled at y = 90, 3 pilot holes for the steel rail (no recess: printed on the back it tripped "floating cantilever"; wall row ≈ 1 mm proud of the light row). `IPAD`, `LEDGE`, `TILE_H` parameters. `make_print_project.py`: `--back-down`.
- Exported STL + 3MF (back on the bed): `wall_tile_x2` (print twice) **5 h 34 / 94 g**, `wall_tile_tablet` **9 h 19 / 158 g**. Orca CLI: no warnings.
- **Undo:** delete the two files; remove the `wall_tile` entries in `__main__`.

## 09.10.2026 — Wall unit: all top modules hollow + removable end caps
- Flo: edges like the middle (hollow, rail groove may stay unused), outer sides closed by a wall that opens. `make_wall_modules.py`: left/mid/right now the same body (`top_module(beam_y=W/2)`, both ends open); new `end_cap(side, module)`: 2.4 mm plate with the module outline (slot + clip-pocket notches covered) + 1.6 mm friction rim 8 mm into the cavity (0.3 mm clearance), lever notch at the back edge. `CAP` dict for the values.
- Exported STL + 3MF: `top_left_light_storage`, `top_mid_light_storage_steel`, `top_right_light_storage` (all side, 7 h 54 / 134 g each), `end_cap_left` / `end_cap_right` (plate on the bed, 1 h 13 / 22 g each). Orca CLI: no warnings. Old solid `top_left_light.*` and an old section PNG → Recycle Bin.
- **Undo:** restore `top_left_light.*` from the Recycle Bin; `__main__` back to the solid left / end-closed right modules.

## 09.10.2026 (night) — Physical_v2 built (code only, not deployed); open checks from the hotspot migration
- **To check (Flo, 09.10):** Nextcloud may not have synced (or logged) the very last changes of 08.10 evening. Whoever continues: compare `Physical/host` (and `pi/kellerkind/`) with dexy's `~/easteregged/host` / kellerkind's `~/easteregged` before relying on either copy — dexy is the source of truth.
- **kellerkind FLO-WORK step unverified:** the `sudo nmcli … FLO-WORK … && sudo reboot` command was handed over 08.10 ~22:15; at ~03:00 kellerkind still answered on G (192.168.178.59) while the hotspot was off. Check `nmcli connection show` on kellerkind.
- **Hotspot was off at ~03:00** (dexy and the WLED units unreachable) — check Windows' Mobile hotspot power saving is off before the exhibition.
- **Physical_v2:** leaner copy of the code (same setup, dexy stays host), dead weight removed, verified on the laptop (tests, byte-identical light frames old vs new, silent full-host run). Nothing deployed, `Physical/` code unchanged. Details, deploy steps and proposals: `Physical_v2/REFACTOR_REPORT.md`. The old Copilot plan that was in `Physical_v2/` is now in `Physical_v2/_old_copilot_plan_0710/`.
- **Undo:** delete `Physical_v2/` contents except `_old_copilot_plan_0710/` (Flo deletes).

## 08.10.2026 (22:10) — Hotspot migration, step 5: kellerkind scripts use dexy.local
- Laptop SSH key installed on kellerkind by Flo (still on G, 192.168.178.59).
- `pi/kellerkind/run_node.sh`, `kiosk.sh`, `ground_player.py`, `cue_player.py`: hard-coded `192.168.178.158` → **`dexy.local`** (kellerkind resolves mDNS: nsswitch `mdns4_minimal`, avahi active; dexy announces 192.168.137.200 on FLO-WORK). kellerkind's copies were identical to the pre-edit laptop copies; deployed. Backup on kellerkind `~/easteregged/scripts_backup_0810_prehotspot.tgz`; laptop pre-edit copies in scratchpad `kellerkind_before_0810/`.
- Next: FLO-WORK connection on kellerkind (Flo, sudo) + reboot.
- **Undo:** on kellerkind `cd ~/easteregged && tar xzf scripts_backup_0810_prehotspot.tgz && ./run_node.sh`; locally `sed -i 's/dexy\.local/192.168.178.158/g'` on the four files.

## 08.10.2026 (21:58) — Hotspot migration, step 4: Gledopto renamed "wall-unit", on FLO-WORK
- WLED via `/json/cfg` (on G): mDNS `easteregged-wall` → **`wall-unit`**, name "Wall unit", MQTT broker → 192.168.137.200 (MQTT stays disabled). Flo replaced G with FLO-WORK → **192.168.137.93** (DHCP), RSSI −46.
- `host/room.toml` `[[wled]] wall`: `mdns = "wall-unit"` (local + dexy; dexy backup `room.toml.before-wall-0810`). Host restarted 21:57: wall online at .137.93, strip1 at .137.47.
- Spotlight unit: lost 21:45 (RSSI −79), then unplugged by Flo — re-check signal when it's back.
- **Undo:** WLED POST `{"id":{"mdns":"easteregged-wall","name":"Wall · ground"}}` to `/json/cfg` + Wi-Fi back to G (old config: scratchpad `wall_cfg_before_0810.json`); dexy: `cp ~/easteregged/host/room.toml.before-wall-0810 ~/easteregged/host/room.toml` + `run.sh`.

## 08.10.2026 (21:45) — Hotspot migration, step 3: TOP renamed "spotlight-unit", on FLO-WORK
- WLED via `/json/cfg` (while still on G): mDNS `easteregged-top` → **`spotlight-unit`**, name "Spotlight unit", MQTT broker 192.168.178.158 → **192.168.137.200**, client id → `spotlight-unit` (port 1883, topics `wled/top`, radar prefix `easteregged` unchanged). Flo then replaced G with FLO-WORK (TX power unchanged). Now **192.168.137.132** (DHCP), RSSI −79 (weak — keep it closer to the laptop or check at the venue).
- `host/room.toml` `[[wled]] top`: `mdns = "spotlight-unit"` (local + dexy, they were identical before; dexy backup `room.toml.before-spotlight-0810`). Host restarted 21:40: "WLED top online at 192.168.137.132" (21:41:50).
- Radar check: Mosquitto "client connected from 192.168.137.132 as spotlight-unit"; `easteregged/in/presence/state ON`, `count 1`, `target/1/x|y` flowing (8 s sample).
- At host restart: Marsboy + JBL not connected → USB speaker fallback (as before).
- **Undo:** WLED: POST `{"id":{"mdns":"easteregged-top","name":"TOP spotlight"},"if":{"mqtt":{"broker":"192.168.178.158","cid":"easteregged-top"}}}` to `/json/cfg`, Wi-Fi back to G (old config: scratchpad `top_cfg_before_0810.json`); dexy: `cp ~/easteregged/host/room.toml.before-spotlight-0810 ~/easteregged/host/room.toml` + `run.sh`.

## 08.10.2026 (21:36) — Hotspot migration, step 2: table unit on FLO-WORK
- WLED 0.15.1 stores **only one network** → Flo replaced G with FLO-WORK (Config → WiFi Setup; TX power kept 8.5 dBm). Table unit now **192.168.137.47** (DHCP), mDNS `table-unit`, RSSI −51, channel 1. Host: "WLED strip1 online at 192.168.137.47" at 21:34:28 (found by mDNS, `room.toml` unchanged), `live` from 192.168.137.200.
- Consequence: the table unit works only while the laptop hotspot is on (at home too). Hotspot off / wrong password → it opens WLED-AP (`wled1234`, 4.3.2.1).
- Windows' hotspot client list shows only DHCP clients → dexy (fixed IP) is not listed there, but is connected.
- **Undo:** in its WLED page set the network back to G (pre-change config: scratchpad `table_cfg_before_0810.json`).

## 08.10.2026 (21:30) — Hotspot migration, step 1: laptop access + dexy on FLO-WORK
- **Laptop** (Windows Mobile Hotspot **FLO-WORK**, 2.4 GHz, WPA2, laptop = 192.168.137.1): new SSH key `~/.ssh/id_ed25519` ("flo-laptop") installed on dexy by Flo → `ssh pi@192.168.137.200` / `pi@192.168.178.158` without password. **Hotspot "power saving" must be off** (Settings → Mobile hotspot), otherwise Windows turns the hotspot off after a few minutes without clients (happened once).
- **Backup before change** on dexy: `~/easteregged/host_backup_0810_prehotspot.tgz` (host without stems/traces, run.sh, presence.py) + `net_before_hotspot_0810.txt`.
- **dexy:** new NetworkManager connection `FLO-WORK` (Flo, sudo): fixed **192.168.137.200/24**, gw + DNS 192.168.137.1, IPv6 ignored, autoconnect priority **10** (G stays, priority 0; old unused profile `netplan-wlan0-FLO-LAPTOP` left alone). First switch failed with WRONG_KEY (password re-entered via `nmcli connection edit`), second failed because the hotspot had switched itself off; third: **dexy on FLO-WORK since 21:28**, host running, web `http://192.168.137.200:8080` answers.
- Note: while the laptop is also on G, its hotspot NATs 137.x → G, so dexy still reaches G devices (table unit .173) — this will not exist at the exhibition.
- **Undo:** `ssh -t pi@192.168.137.200 "sudo nmcli connection delete FLO-WORK"` (dexy falls back to G); key: remove the "flo-laptop" line from dexy's `~/.ssh/authorized_keys`.

## 08.10.2026 (20:25) — dexy drives the table unit; host files merged; Copilot accent "expand" live
- **Found:** Copilot's 06.10 accent work (light.py, room.py, room.toml, main.py, web.py, tests) was built on an **older local copy** — locally my 06.10 evening changes were gone (wall/Gledopto entry, accent on SPI1, `http_port`, accent_base/boost/tint keys, mic gate + Bluetooth sync in main.py, cmd logging in web.py). dexy had the right state.
- **Merge:** dexy's light.py/room.py/main.py/web.py/room.toml taken as base locally; Copilot's `accent_from_ground()` + `accent_colour = "expand"` ported into light.py (glow = expand colour × max(ground level × `accent_over_ground` 1.25, `accent_floor`), accent sounds/duck/weather accents as before; mic gate stays in main.py). Copilot's versions kept in `host/_backup_copilot_0610/` (Flo may delete). Copilot's clock-drag fix (web/app.js, index.html v34) kept. Test adapted (mic gate lives in main.py). `pytest`: 17 passed, 1 skipped; silent laptop run OK.
- **room.toml:** `accent_colour = "expand"` + keys; **strip1 = table unit** (`host = "192.168.178.173"`, `mdns = "table-unit"`, WLED/DDP instead of `kind = "spi"`).
- **Wi-Fi patches** for the C3 now in `Prototype/Physical/wled/patch_wled.py` (tested on clean WLED files, applies once); `build.sh` takes the env as 2nd argument.
- **Deployed** to dexy (room.toml, core/light.py, core/room.py, tests, web/app.js, web/index.html), restarted: "WLED strip1 online at 192.168.178.173 (89 LEDs, RGBW)", table unit `live` = DDP from .158. Note at restart: Marsboy and JBL Bluetooth not connected → fallback to the USB speaker.
- **Mic decision (Flo, 08.10):** keep as is — the USB mic on dexy stays the Morning Jam mic (records taps/hums as layers). The C3 mic sends only levels/16 bands via WLED sound sync (no audio); host does not read it yet. Option for later: stream raw 16 kHz audio from the C3 over UDP (needs timestamps/jitter buffer for the bleed profile, ~½ day).
- **Undo:** on dexy `cd ~/easteregged/host && tar xzf ~/easteregged/host_backup_0810_table.tgz && ~/easteregged/run.sh`; locally copy back from `_backup_copilot_0610/` (only if the Copilot base is wanted).

## 08.10.2026 — Table unit = ESP32-C3 SuperMini (WLED + INMP441 mic); clock page full-screen on the iPad
(Re-added 20:10: Log.md had been overwritten from an older copy by another session; earlier 08.10 entries — also the wall unit's "steel rail" and "wood beam" — are in Nextcloud's version history.)
- **Board:** ESP32-C3 SuperMini, MAC 88:56:a6:6d:02:cc, 4 MB (laptop COM9). **Mic** INMP441: SD→4, WS→5, SCK→6, L/R→G, VDD→3.3, GND→G. The mic board's outer ring is **not** ground → GND wire on the GND pad (that was why it stayed silent). Raw I2S test recorder in `C:\Users\Florian\.wb\mictest` (48 kHz): voice/clap clean.
- **Firmware:** WLED 0.15.1 env `table_c3` (`Prototype/Physical/wled/platformio_override.ini`, built in `C:\Users\Florian\.wb\src`, from PowerShell — Git Bash breaks Espressif's installer): audioreactive on (I2S 4/5/6), 89 × SK6812 RGBW on GPIO 7, ABL 1800 mA, name "Table". First flash boot-looped: WLED + audioreactive = 1.59 MB > default 1.5 MB slot → `board_build.partitions = ${esp32.big_partitions}`, erased + reflashed. Now on `table_c3_debug` (+ `WLED_DEBUG`, and a local patch in `wled00/wled.cpp` printing `STA disconnect reason: N`).
- **Wi-Fi (Flo via WLED-AP):** G, TX power 8.5 dBm (SuperMini antenna fix; higher = no connection), mDNS `table-unit` → **192.168.178.173**, RSSI −61…−68. Still intermittent: some boots loop "Connecting to G… disconnected" and fall back to the AP, the next boot connects at once; on the power bank it was not reachable.
- **Tests over Wi-Fi (on PC USB):** red/green/blue via `/json/state` accepted (89 LEDs). Mic: **sound sync set to send** (`um.AudioReactive.sync.mode = 1`, UDP multicast 239.0.0.1:11988, ~30 packets/s); PC received level 0 (quiet) … 255 (clap) → what dexy will read.
- **Wi-Fi fix (20:30):** debug log showed `STA disconnect reason: 202` (AUTH_FAIL) / 2 on most boots although the password is right. Two local patches in `C:\Users\Florian\.wb\src\wled00\wled.cpp` `initConnection()` before `WiFi.begin`: set TX power first (WLED did it after begin → first auth frames at 19.5 dBm), and `setScanMethod(WIFI_ALL_CHANNEL_SCAN)` + `setSortMethod(WIFI_CONNECT_AP_BY_SIGNAL)` (G is a mesh: join the strongest AP, not the first found). Result 4/4 boots connected in 9–15 s (one 202, then OK), BSSID 80:23:95:86:67:03, −62 dBm. Re-test: R/G/B/W + mic level 0…252, 472 sync packets in 15 s. Ring left on Mars rust. TODO: move both patches into `Prototype/Physical/wled/patch_wled.py`.
- **Power:** strip 5V/GND from power-bank port 2, C3 via USB-C from port 1, extra GND wire strip ↔ C3 G (not from the C3's 5V pin).
- **Not yet:** dexy `room.toml` still drives the accent strip via SPI1 (`strip1`).
- **Clock page:** `host/web/clock.html` got iOS web-app meta tags (full-screen via Share → Add to Home Screen); only this file copied to dexy (Copilot's app.js/index.html v34 still not deployed).
- PlatformIO Core reinstalled by Flo; its incomplete `framework-arduinoespressif32-libs` moved to `~/.platformio/libs_incomplete_backup` (Flo may delete). C: drive had been full.
- **Undo:** other firmware via `pio run -e <env> -t upload`; remove `[env:table_c3]` / `[env:table_c3_debug]`; sync off: POST `{"um":{"AudioReactive":{"sync":{"mode":0}}}}` to `/json/cfg`; clock: on dexy `cp ~/easteregged/host/web/clock.html.bak-0810 ~/easteregged/host/web/clock.html`.

## 08.10.2026 — Wall unit: rail recess was the "floating cantilever"
- Orca CLI (`--debug 3`) prints the same warning as the GUI → bisected on the middle module: recess off → warning gone (max cantilever 6.4 → 3.2 mm); pilot holes / column irrelevant. Fix: recess ends sloped 45° in `rail_mount()`. All three modules now slice in Orca **without warnings**; mid, left, right STL + 3MF re-exported (mid 8 h 05). No G-code in the project.
- **Undo:** recess back to `cube(-1.0, RAIL["recess"], yc - g, yc + g, ...)`.

## 06.10.2026 (21:09) — Copilot: GROUND-expanding accent + clock drag

- Local-only implementation and verification details, measured LED acceptance values, and undo steps: `Setup_Log/Log_Copilot.md`. No deployment or Pi access.

## 06.10.2026 (21:07) — Copilot: accent light expands GROUND

- Local only: added `accent_from_ground()` and `[light] accent_colour = "expand"`; accent RGB derives from the current wall GROUND colour, brightness follows the actual `Room.day()` level × 1.25 with floor/duck, playing accent sounds add a smoothed lift, and microphone lift is gated to a running Morning Jam. Legacy circadian/season accent paths retain the previous base-glow behavior. Acceptance RGBs and test result are in `Setup_Log/Log_Copilot.md`.
- **No deployment or Pi access** per the task prompt.
- **Undo:** revert only `host/core/light.py`, `host/core/room.py`, `host/room.toml` `[light]` additions, and the two accent tests; details in `Log_Copilot.md`.

## 06.10.2026 (21:00) — Copilot prompt: accent light that expands the ground light

- New `Prompts/Copilot_Accent_Light.md`: Task A — accent colour derived from the GROUND colour (bluish white → clear blue, evening → sunset red-orange; RGBW rule: warm accents keep blue ≈ 0), brightness = ground level × 1.25 (`accent_colour = "expand"`, `accent_over_ground`), acceptance table + tests; Task B (optional) — the Home page's clock drag sends a stream of `clock` values. Rules: no deploy, no Pis, laptop test config, logs in `Log_Copilot.md` + a line here.
- **Undo:** delete the file.

## 06.10.2026 (20:50) — Accent glow follows the ground light; clock "reset" traced; end of day

- `room.toml [light]`: `accent_level` 0.6 → **0** (follow the day), `accent_base` 1.3, `accent_floor` 0.12, `accent_tint_mix` 0.35 → the table glow = the GROUND colour and level with a light circadian tint (Flo: "an accent to the general light, not extreme"). `core/room.py`: evening LED colour Mars Rust (1, .30, .08) instead of orange, night rust (.80, .20, .06). Live 20:45: wall #322111, table #422310. Tests 13 passed, deployed.
- "Clock jumps back when I set 9:00": the room never resets by itself. `core/web.py` now logs every web command with the sender's IP (`cmd from … :`). Test: after `clock 9.0`, the laptop (192.168.178.101) sent `clock` 15.87 → 15.82 → 16.63 → 19.95 → 20.82 → 21.36 within 5 s = a drag on the Home page's curve/event axis (4 page connections from the laptop). Next: check the curve drag (pointer capture / several open tabs).
- **Undo:** room.toml / core/room.py from the scratchpad copies; web.py: remove the `cmd from` log line.

## 06.10.2026 (20:42) — Wall on the Gledopto live; table glow in LED colours (orange, rust, amber, morning blue)

- Gledopto (192.168.178.171) powers + drives the 60-LED wall strip; host: "WLED wall online at 192.168.178.171 (60 LEDs, RGBW)". WLED via API: LED length 89 → **60**, current limit 500 → **1200 mA**, name "Wall · ground", mDNS `easteregged-wall` (also in `room.toml`). Live: evening light #322111, ~160 mA.
- Table glow looked pink: the screen colours (#E37156 …) on an RGBW strip get a white-chip share → salmon/pink. `core/room.py` `circadian_tint(k, blue)` now in LED terms with blue ≈ 0 for warm colours: day amber (1, .55, .06), orange from the golden evening (≤ 3500 K → pre-sleep 2700 K (1, .36, .02)), night rust (.85, .18, .01); during the blue morning it leans to blue (.18, .62, 1) in proportion to the room's `blue` (× 1.4). Live 20:40 pre-sleep → table #C54703 (orange). Tests 13 passed. Deployed (Pi backup `core/room.py.before-ledcolours`).
- **Undo:** restore `core/room.py` from scratchpad `room.before-ledcolours.py` / the Pi backup; WLED length/limit via its page.

## 06.10.2026 (20:40) — Wall light moves to the Gledopto; kellerkind undervoltage + 3.3 V finding; clock page v4

- "kellerkind doesn't change the general light": the chain host → DDP → led_node worked (node live, pwr followed the room: 400 mA morning → 74 mA pre-sleep). Root causes: (1) **kellerkind permanent undervoltage** (`throttled` bit 0 set, also with the strip at 97 mA) — the Pi also powers the WaveShare screen + mouse + keyboard + the strip on pin 4; (2) after moving the strip to its own power bank (5V from the bank, GND to the strip + Pi pin 6, data pin 38), undervoltage gone, but the strip shows **full white + flashing** (power-bank overload) = it no longer accepts the Pi's **3.3 V data at a full 5 V supply** (common ground confirmed by Flo). Explains the morning's ESP8266 result for the same strip.
- Decision (Flo): **wall strip on the Gledopto** (built-in level shifter; already set to 60 LEDs / 500 mA as the test bench), powered from the same power bank. `host/room.toml`: `[[wled]] id = "wall"` → host 192.168.178.171, mDNS `easteregged-bench`, http 80. `pi/kellerkind/run_node.sh`: led_node loop commented out (ground_player stays). Deployed; host waits for the Gledopto.
- Open: 74AHCT125 level shifter (to use the Pi pin again); kellerkind supply/cable (screen on its USB); Gledopto current limit for normal use.
- Clock page (`host/web/clock.html`) iterations with Flo: time 43 vh; the circadian glow tried as an edge strip (CSS breathing = 124 % CPU on the Pi 3B), a blurred SVG halo around the wheel (151 %), a baked canvas image with 7 fps opacity breathing (91 %) → now **a static image on the right edge, carved by a soft circle so it hugs the wheel** (wide at top/bottom), redrawn only when the light colour/level changes; tap the edge → day curve. Wheel: season icons back, touch a segment → exhibition card: Earth seasons (why: tilt 23.4°, day length; what the room borrows: K, dawn/dusk, sounds; mood · host from booklet p. 39), Mars seasons (northern: lengths 194/178/142/154 sols, aphelion clouds, dust storm season in northern autumn/winter near perihelion; "outside the window only"). `core/room.py` state: `season_info` for all seasons. Previous versions in scratchpad `clock_v2.html`, `clock_v3.html`.
- **Undo:** room.toml from scratchpad `room.before-wallgledopto.toml` (wall → kellerkind :8081) + uncomment the led_node loop.

## 06.10.2026 (18:55) — Room clock page for kellerkind's screen

- Screen (kellerkind HDMI-A-1, "RTK WSQLED"): **1280×720, 16:9, landscape, no rotation**; EDID claims 70×39 cm (often generic on cheap panels — real diagonal to confirm). Touch works (Flo).
- New `host/web/clock.html` (`/static/clock.html`): a home object — time (Pangaia, 36 vh), date + mission day, the seasons wheel (same geometry as the Home page, display only: the room's Earth segment + Mars season lit, "you are here" line, season name), the circadian light as a soft glow on the left edge (room colour, stronger by day); tap the glow → the day curve (now, K, %, dawn, dusk), tap again or 30 s → back. No animations, only the `state` topic, redraws only on change → Chromium ~8 % CPU on the Pi 3B. Checked in the browser at 1280×720.
- `pi/kellerkind/kiosk.sh`: URL → `http://192.168.178.158:8080/static/clock.html` (the main page stays at `/?kiosk=1#home`). Deployed (dexy web, kellerkind kiosk restarted).
- **Undo:** kiosk.sh URL back to `…/?kiosk=1#home`; delete clock.html.

## 06.10.2026 (18:45) — Ground sound from kellerkind's own files; table glow circadian + reacts only to accents

- **Soundscape without a stream (Flo's idea):** `host/machine.pi.toml` `room_output = "node:kellerkind"` (`room_latency_ms` 300). `core/ambient.py`: RoomOut kind `node`. `core/room.py`: `_update_beds` → `_node_beds` publishes the wanted beds **retained** on `easteregged/node/kellerkind/beds` {"beds": {name: gain}, "fade", "master"} (only on change; stand-in `_NodeBed` objects for the UI), `node_resend()` after a volume change. `core/audio.py`: travelling accents send their wall half as a cue `node/kellerkind/play` {"sound": "accent/<name>", "gain", "env": in|out}; standing accents stay at the table; `ambient_shot(…, name=)`. `main.py`: `audio.node_send` = bus.publish.
- kellerkind: new `pi/kellerkind/ground_player.py` (replaces the stream + `cue_player.py`): loads stems/ground + stems/accent (all 48 kHz s16 stereo; copied, 37 MB), loops beds with fades, cues on top (env in/out, acks), one pw-cat to the AUX sink (300 ms buffer). `run_node.sh` rewritten (led_node + ground_player; `SPI_BUS=1` for pin 38). Check: beds {"wind": 0.15} received, PipeWire stream active, ~0 % CPU. **Flo: soundscape plays without stutter.** LED node waits for SPI1 (`/dev/spidev1.0` missing → sudo `dtoverlay=spi1-1cs`, Flo).
- **Table (ACCENT) glow:** mic reactivity only while Morning Jam runs (`main.py`: `light.mic` = 0 otherwise); new `light.accent_audio` = loudness of the playing accent sounds (`room.accent_loudness()`, includes the JBL mixer) → accent spots brighten with them (`[light] accent_react = 1.2`, fast attack / slow release). Colour: `accent_colour = "circadian"` → `circadian_tint(k)`: blue #5FC8E0 at ≥ 3650 K, orange #E37156 at ≤ 3550 K (narrow crossover, no grey-pink middle), rust #A14530 towards 2000 K; `accent_tint_mix` 1.0, `accent_level` 0.8 → 0.6. Live: 18:37 autumn, 3508 K → orange #C5624A; bird accent brightened the glow and fell back.
- Tests 13 passed. Deployed (backups `~/easteregged/host.bak-2026-10-06-node.tgz`, `…-react.tgz`). dexy 70.8 °C, `throttled=0xe0000` (no current throttling).
- **Undo:** dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-06-node.tgz && ~/easteregged/run.sh` (back to the stream: also restore run_node.sh on kellerkind from scratchpad `run_node.before-groundplayer.sh`); accent colour back: `accent_colour = "season"`, `accent_react = 0`.

## 06.10.2026 (17:50) — kellerkind: stream stutter fixed (kiosk CPU), LED wire on the wrong pin, undervoltage

- Flo: Marsboy stuttered ("digital rain"); local files played via `pw-play` were clean → the stream starved: Chromium kiosk used ~180–250 % CPU (load ~3), plus **kellerkind had undervoltage** (`throttled=0x50000`).
- `host/web/app.js`: `?kiosk=1` → skips the `meter` / `light` streams and adds class `kiosk`; `style.css`: `.kiosk` turns off all animations/transitions + hides the cursor; `?v=33`. `pi/kellerkind/kiosk.sh` URL `…/?kiosk=1#home`; `run_node.sh`: stream buffer `--latency` 200 → 1000 ms, `MAX_MA` 600 → **400** (strip powered from kellerkind's pin 4 while its supply is weak). Deployed (dexy web only, kellerkind restarted) → Chromium ~30 % CPU, load falling.
- Touch works (Flo).
- Wall LEDs dark: Flo wired DIN to **pin 38** (as on dexy) — led_node uses SPI0 = **pin 19**. Fix: move the data wire to pin 19 (or sudo `dtoverlay=spi1-1cs` + `SPI_BUS=1`). Power: 5V pin 4, GND pin 6.
- **Undo:** web from scratchpad `web_v31/`; kiosk URL without `?kiosk=1`; run_node.sh latency/MAX_MA back.

## 06.10.2026 (17:30) — kellerkind = complete GROUND unit: circadian light, soundscape on AUX, kiosk; checks

- **Sound routing changed:** `host/machine.pi.toml` (= machine.toml on dexy) `room_output = "stream"` (was "main") → the GROUND soundscape (beds) goes out as `/room.wav` (endless WAV, 48 kHz s16 stereo, 192 kB/s); `room_latency_ms = 400` (only for travelling accents when no JBL is connected). The table speaker keeps the scenario sound; accents stay on the JBL (`accent_output`, currently not connected → they travel table ↔ wall).
- `pi/kellerkind/run_node.sh`: + ground stream loop `curl -sN …/room.wav | tail -c +45 | pw-cat --playback --raw --format s16 --rate 48000 --channels 2 --target alsa_output.platform-3f00b840.mailbox.stereo-fallback` (AUX jack in PipeWire, log `ground_stream.log`), `XDG_RUNTIME_DIR=/run/user/1000`, exact pkill patterns. `cue_player.py`: plays via `pw-play --target <AUX sink>` (mixed with the stream), publishes an ack on `easteregged/node/kellerkind/ack` {"sound","ok"}.
- Checks: wall LEDs = host GROUND layer exactly (#624f40, 4038 K, level 0.385, autumn, 17:24), node live (1674 frames, ~181 mA); stream active in PipeWire on "bcm2835 Headphones"; room bed "wind"; cue → ack round trip ok (`accent/cat_meow`). Kiosk Chromium running (Home page). Desktop autologin on (`raspi-config get_autologin` = 0, desktop boot) → kiosk + PipeWire come back after reboot; crontab starts the node programs.
- **Touch: no touch input device found** — only "USB Optical Mouse" and "HID 04f3:0103" keyboard; display HDMI-A-1 "RTK WSQLED" 1280×720, transform normal. The screen's USB touch cable is probably not connected.
- dexy during the change: 68.6 °C, `throttled=0xe0000` (no current throttling; earlier events only).
- Open (Flo): connect the touch USB cable; tap test (watch `easteregged/cmd`); power-cycle kellerkind for the reboot test; judge the Marsboy level (PipeWire sink volume 40 %, `soundscape_gain` 0.15).
- **Undo:** dexy machine.toml `room_output = "main"` (backup `machine.toml.before-groundstream`), `run.sh`; kellerkind: previous run_node.sh / cue_player.py from scratchpad `before_groundsound/`, `setsid ~/easteregged/run_node.sh`.

## 06.10.2026 (17:05) — kellerkind (GROUND wall) set up: LED node, cue player, kiosk; status of all Pis

- **kellerkind** = Raspberry Pi 3B Rev 1.2, fresh SD (Raspberry Pi OS Trixie, desktop, 64-bit), IP **192.168.178.59** (MAC b8:27:eb:39:37:d2), Wi-Fi "G" 2.4 GHz −25 dBm. Imager settings had not been applied (card came up as `raspberrypi`, SSH off) → Flo: hostname kellerkind + SSH via raspi-config, laptop key added (old host key for .59 removed, backup `~/.ssh/known_hosts.old`). Flo (sudo): SPI on (`raspi-config nonint do_spi 0`), Wi-Fi power save off (`nmcli connection modify G … powersave 2`), reboot.
- New `pi/kellerkind/`: `led_node.py` (looks like a WLED to the host: DDP UDP 4048 → SPI0 / pin 19, 60 SK6812 RGBW, software cap 600 mA, GET /json/info + POST /json/state on **HTTP 8081**, dark after 10 s without frames), `cue_player.py` (MQTT `easteregged/node/kellerkind/play` → `aplay`/`pw-play` on the headphone jack = Marsboy; status `easteregged/status/kellerkind` online/offline; sounds in `~/easteregged/stems/accent/`), `run_node.sh` (restart loops; first versions killed their own SSH session via pkill/pgrep patterns — now exact), `kiosk.sh` (waits for the host, then Chromium `--ozone-platform=wayland --kiosk http://192.168.178.158:8080/#home`). On kellerkind: `~/easteregged/` + `venv` (system site packages + paho-mqtt), crontab `@reboot sleep 15 && …/run_node.sh`, `~/.config/labwc/autostart` (copy of the system file + `kiosk.sh &`).
- Self-tests: direct SPI colour test (red/green/blue/white/blocks) and AUX test (Front_Center.wav + 440 Hz, PCM 78 %) sent — **visual/acoustic confirmation by Flo pending**; DDP test from the laptop → node "live", 120 frames, ~427 mA estimated; cue player played `test` + `accent/bird_cross` (0.8).
- Host (dexy): `core/light.py` `http_port` per light subnode (default 80); `core/audio.py` loop layers only go to spots that have speaker channels (a spot with `channels = []` made layers silent); `room.toml`: `[[wled]] id = "wall"` (192.168.178.59, http_port 8081, 60 LEDs RGBW) + spot `wall` `level = "ground"`. Tests 13 passed. Deployed (backup `~/easteregged/host.bak-2026-10-06-wall.tgz`), restarted: "WLED wall online at 192.168.178.59 (60 LEDs, RGBW)", node receiving frames.
- Status 17:05: dexy reachable (SSH ok, ping blocked by Windows), up 3 h 40 min, host 1×, web :8080 / HA :8123 / MA :8095 / ESPHome :6052 → 200, containers music-assistant, esphome (healthy), homeassistant, mosquitto up 4 h. **Dexy runs hot: 85 °C and throttled (`0xe0006`, temperature, no undervoltage) at ~1.3 load; later 75.7 °C (`0xe0000`)** → needs a cooler/fan. Dexy Wi-Fi back on 5 GHz −71 dBm (band lock still open). TOP DevKit (.170) "not found" (off?) → radar offline; JBL not connected → accents on the table speaker. Old errors in host.log: MQTT reconnects during the restarts only.
- **Undo:** on kellerkind `pkill -f run_node.sh; pkill -f led_node.py; pkill -f cue_player.py; pkill chromium`, remove the crontab line and the kiosk line in `~/.config/labwc/autostart`; on dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-06-wall.tgz && ~/easteregged/run.sh`.

## 06.10.2026 (13:25) — Dexy outages analysed; power + Wi-Fi recorder

- Host log timeline (system journal keeps only the current boot): **unclean restarts at ~12:19 and ~12:55** (host start without a prior "shutting down"; the second 5 min after raising the strip to 1200 mA) → brownout/crash on the power bank; 12:19–12:37 no entries at all; **12:58–13:09 host running but dexy unreachable** → Wi-Fi lost while alive. 13:19 disconnect = Flo's power-save change (locally generated), reconnected in 3 s.
- Flo: Wi-Fi trouble also happened without the strip. Recorder shows dexy (on mains) **switching bands**: 13:15 2.4 GHz −52 dBm, 13:24 5 GHz (5520 MHz, DFS ch 104) −76/−77 dBm. → two separate problems: weak 5 GHz through the wall (band steering) + power-bank brownouts.
- New `~/easteregged/netmon.sh` on dexy (not in Nextcloud; source in this entry's chat): every 10 s → `~/easteregged/netmon.log`: date/time, EXT5V voltage, `get_throttled`, Wi-Fi freq/signal/bitrate, ping to the FritzBox, JBL connected; crontab `@reboot sleep 15 && …/netmon.sh`. Stop: `pkill -f netmon.sh`.
- Proposed (sudo, Flo): pin dexy to 2.4 GHz (`nmcli … 802-11-wireless.band bg`), persistent journal (`Storage=persistent`); better: LAN cable. Power: separate power bank for the strip; dexy on mains at the defence if possible.
- **Undo:** `pkill -f netmon.sh`, remove the crontab line, delete the script/log.

## 06.10.2026 (13:00) — Accent glow: more season colour (70 %) — local, not deployed yet

- `room.toml [light] accent_tint_mix` 0.45 → 0.7 (Flo: "always add a bit of colour"). Direction kept: autumn/winter warm (rust, deep rust), spring cool (Kolibri blue), summer peach — booklet palette + hue-heat idea (warm light feels warmer; evidence mixed). The circadian "cooler/bluer in winter" belongs to the wall's morning curve, already in `core/room.py`.
- **Not deployed:** dexy dropped off the Wi-Fi again during the copy (third time today; 5 GHz, −71 dBm through a wall). Deploy = copy room.toml + `run.sh`.
- **Undo:** `accent_tint_mix = 0.45`.

## 06.10.2026 (12:50) — Accent glow fixed at 80 %, current cap 1200 mA

- `core/light.py`: `[light] accent_level` (>0 = fixed glow, LED output share; the colour is normalised, frames are squared before sending). `room.toml`: `accent_level = 0.8`, `strip1 max_ma` 800 → **1200** (80 % on 89 LEDs needs ~1.0–1.4 A depending on the colour; at 800 mA it would reach only 45–62 %). Tests 13 passed. Deployed, restarted: "SPI strip … max 1200 mA"; table strip max 228/255 ≈ 80 %. Dexy supply over 30 s: 5.12–5.14 V, `throttled=0x0`.
- Wi-Fi power save: Flo changed it in NetworkManager, but `iw dev wlan0 get power_save` still says **on** (takes effect after the connection is re-activated or a reboot).
- **Undo:** `accent_level = 0` (back to the day-following glow), `max_ma = 800`, deploy, `run.sh`.

## 06.10.2026 (12:48) — Accent light brighter + coloured; dexy Wi-Fi drops

- `core/light.py`: accent spots get `accent_floor` (minimum glow, also at night), `accent_tint_mix` (season colour mixed into the glow) and `accent_boost` (weather accents × factor); `accent_tint` is set by the room each tick. `core/room.py`: `SEASON_TINT` (summer #F2AD9D, autumn #E37156, winter #A14530, spring #76DBD8); accent colours: cat_meow now a coral glow (#EB8F7A), wind_gust a cool blue-grey glow (#9FB8C4) instead of a shade, rain_pass a stronger blue tint (#5A86B0). `room.toml [light]`: accent_base 0.15 → **1.4**, accent_floor 0.3, accent_tint_mix 0.45, accent_boost 2.0 → table strip ~35–38 % LED output by day (was ~4 %), ~16 % at night. Tests 13 passed. Deployed (backup `~/easteregged/host.bak-2026-10-06-accentlight.tgz`); live check: strip max 151/255 ≈ 35 %.
- Dexy dropped off the network twice (no ping/SSH/web; Flo: "it fails in the room next door"). Found after a power cycle: Wi-Fi "G" on **5 GHz ch 104 (DFS), −71 dBm**, **power save on**; journal not persistent (no log of the drop). Causes: weak 5 GHz through a wall + power save (+ possibly Bluetooth coexistence, DFS switches). Proposed: power save off (sudo nmcli, Flo), better a LAN cable.
- JBL after the reboot: trusted, reconnected with `bluetoothctl connect`; the host must start after the JBL's sink exists, otherwise accents fall back to the table speaker until the next restart (to improve: retry the accent output).
- **Undo:** on dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-06-accentlight.tgz && ~/easteregged/run.sh`.

## 06.10.2026 (12:17) — JBL paired; table = soundscape, JBL = travelling accents, synced by ear

- JBL GO Essential (F8:5C:7E:C0:2C:8D) paired, trusted, connected from dexy (`bluetoothctl`, no sudo); PipeWire sink `bluez_output.F8_5C_7E_C0_2C_8D.1`. Other Bluetooth devices nearby (incl. the parents' Pioneer) left alone.
- Fixes in `core/ambient.py`: `pw-cat --raw` (it read "-" as a sound file and stopped at once); buffer configurable (`*_buffer_ms`, 350 ms; was ~150 → stutter on Bluetooth). `core/audio.py`: optional **`accent_output`** (own RoomOut + `accent_latency_ms`), `_far()` = accent output, else room output; standing accents (cat, rain, thunder) play on the accent speaker (else the table); travelling accents (bird, bee, gust) move table ↔ JBL with the table part delayed; `sync_test()` = 4 clicks meant to coincide. `main.py`: cmds `sync_test`, `room_latency` (live; sets the accent latency when an accent output exists); `ambient_volume` also sets the accent mixer.
- `machine.pi.toml` (= machine.toml on dexy): `room_output = "main"` (soundscape on the table speaker), `accent_output = "pw:JBL"`, `accent_buffer_ms = 350`, **`accent_latency_ms = 990`** (tuned with Flo: 900 / 950 table first, 1050 / 1200 JBL first). Stutter gone (Flo). Tests 13 passed. Backups on dexy: `host.bak-2026-10-06-jbl.tgz`, `core/ambient.py.before-raw`, `machine.toml.before-jbl`.
- **Undo:** on dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-06-jbl.tgz && ~/easteregged/run.sh`; or in machine.toml remove `accent_output` (accents back on the table / room output).

## 06.10.2026 (12:00) — ACCENT strip runs straight from dexy (SPI1, pin 38)

- 89-LED strip retested on the test Gledopto (colours, blocks, rainbow) ✓ — survived the short; its loose extra power leads insulated by Flo.
- Flo: `sudo systemctl disable --now dexy` + `dtoverlay=spi1-1cs` in `/boot/firmware/config.txt`, reboot → `/dev/spidev1.0`, old Dexy service disabled/inactive. Wiring: pin 2 = 5V, pin 6 = GND, pin 38 (GPIO20, SPI1 MOSI) = DIN. Dexy boots normally, 5.13 V.
- `host/room.toml`: `strip1` `kind = "spi"`, **`spi_bus = 1`** (pin 38); deployed with `core/light.py` (SPI output, 800 mA cap) + tests (13 passed). Direct test on dexy (host stopped 20 s): red/green/blue/white chip/blocks, ~409 mA estimated, `throttled=0x0`. Host restarted: "SPI strip strip1 on /dev/spidev1.0 (89 LEDs, max 800 mA)", 1 host.
- The Joy-IT ESP8266 entry is gone from use (`strip1` = SPI now).
- **Undo:** on dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-06-spi.tgz && ~/easteregged/run.sh`; SPI1: remove the `dtoverlay=spi1-1cs` line (sudo); old service: `sudo systemctl enable --now dexy`.

## 06.10.2026 — Test bench: spare ESP8266 flashed; Gledopto back to plain WLED

- Cause of yesterday's short (Flo): the 89-LED strip has extra red/white power leads at its input end with bare ends — they probably touched (+5V–GND). To cut short + insulate before reuse.
- Spare ESP8266 (CH340, COM5, MAC 5c:cf:7f:20:6d:c3): flash erased, **WLED 0.15.1** (`nodemcuv2`, built locally in `C:\Users\Florian\.wb`, MQTT patch included) flashed over USB; Flo joined it to Wi-Fi "G" → **192.168.178.172**, name "Test ESP", mDNS `easteregged-test`, 60 × SK6812 RGBW on GPIO2/D4, 500 mA. The 60-LED wall strip stayed dark on it (ESP stable, no restarts; VIN/VU and power checked by Flo) → likely the 3.3 V data level without a level shifter for this strip.
- Gledopto (.171): it still had MQTT on (not connected) + the LD2450 test usermod → both off, then **plain WLED 0.15.1** (`esp32dev`, no usermod) uploaded over Wi-Fi, settings kept; renamed "Test Gledopto", mDNS `easteregged-bench`, 60 LEDs, 500 mA. The 60-LED wall strip lights up on it ✓ → the Gledopto is the test bench for strips.
- dexy not reachable over SSH at the time (switched off?).
- **Undo:** Gledopto: LED length 77 / 850 mA; the ESP8266 can be reflashed any time.

## 05.10.2026 (19:00) — End of day: summary + checklists

- Dexy checked after the short: boots normally, 5.14 V, `throttled=0x0`, host + web ok. Still open on dexy: `dexy.service` enabled/active, SPI1 overlay not set (sudo, Flo).
- `MorningJam_Progress.md` §7 rewritten (three subnodes by level, done list, next list); `Plan/Guide_Presentation_Setup.md` state note + ticks (C done via WLED usermod, B1 done, new B3 pins, kellerkind note); `Setup_Reference.md` state block on top.
- **Undo:** previous versions in the scratchpad (`MorningJam_Progress.before-wrapup.md`, `Guide.before-wrapup.md`) and Nextcloud's version history.

## 05.10.2026 (18:40) — Short on the accent strip wiring: dexy wouldn't boot, Joy-IT ESP8266 burned

- Flo wired the 89-LED ACCENT strip to dexy (5V pin 2, DIN pin 38 = SPI1 MOSI planned, GND pin 6). Dexy then only blinked red (power chip shutting down → 5 V shorted/overloaded). The SPI1 sudo step (`dtoverlay=spi1-1cs`) is not confirmed. Reconnected to the Joy-IT ESP8266 → brief smoke; the ESP shows no LED and its USB chip (CP2102, was COM4) no longer enumerates → **ESP8266 "easter-egged" (.169) dead**, do not reuse. Most likely a +5V–GND contact at the strip's connection end / wiring, created while rewiring (the strip worked on the ESP earlier the same day).
- Open: measure the strip (+5V–GND), inspect the first pads; check dexy boots without header wires; until then the strip stays disconnected. `strip1` in `room.toml` on dexy still points to .169 (offline now); locally it is already `kind = "spi"` (not deployed).
- Remaining spare boards: healthy ESP8266 (CH340, MAC 5c:cf:7f:20:6d:c3), Gledopto (test firmware), 3× ESP32-C3 SuperMini (untested), "maybe" ESP32-D.

## 05.10.2026 (18:10) — Wall strip (GROUND) tested and counted: 60 LEDs; SPI output for dexy prepared

- Wall strip tested on the Joy-IT ESP8266 (.169) with WLED live override (`lor:2`): first nothing lit and the ESP's 5V sagged (LEDs dimmed); +5V–GND ≈ 6 kΩ (no short) → a bad solder joint, re-soldered by Flo → all LEDs work. Counted with 10-LED colour blocks: **60 LEDs**. Wiring direction checked from a photo: wires on GND · DIN ▲ · +5V, correct. Live override ended (`lor:0`), host drives the ESP again.
- `host/core/light.py` (+ test): light subnode `kind = "spi"` — a strip on the host Pi's own SPI pin (GPIO10/MOSI, /dev/spidev0.0, 2.4 MHz, 3-bit encoding as in the old Dexy project), software current cap `max_ma` (no WLED limiter), black frame on "off". `room.toml`: `strip1` (ACCENT, table) switched to `kind = "spi"`, `max_ma = 800` — **local only, not deployed**: waits for Flo to disable the old `dexy` service (it drives GPIO10 too) and to wire the strip to dexy (pins 2/4, 6, 19). Tests 13 passed; silent laptop start ok.
- Strips: TOP ring 77 (ESP32 DevKit), ACCENT table 89 (→ dexy SPI), GROUND wall 60 (→ kellerkind, not online yet).
- **Undo (local):** scratchpad `host_before_spi/` (room.toml, light.py, test).

## 05.10.2026 (17:24) — One level per spot: table = accent, spotlight = the moment (one lamp)

- `core/light.py`: spots get `level = "ground" | "accent" | "top"` (`spot_level`, `normalize_spots`; old flag configs still work as before). ground = circadian light; accent = weather accents over a faint day glow (`[light] accent_base = 0.15`); top = one evenly lit lamp: the scenario's spotlight colour/level × beat breath + the listening glow + tap/layer pulses (all pulses now go to the TOP spot), proximity rust when no scenario runs. Replaces Copilot's static "rust while any scenario runs".
- `main.py`: `normalize_spots` at start (scenarios read `moment` = the TOP spot).
- `room.toml`: table spot `level = "accent"` (name "Table · accent"); `top_spotlight` `level = "top"` and **`channels = [0, 1]`** — it had `[]`, so the audio round-robin sent about half of the Morning Jam layers to no speaker (silent).
- Tests: two light tests updated/replaced (legacy spots keep full ground; new test: off/proximity/accents only on accent/scenario spotlight evenly/pulses to TOP) → 12 passed, 1 skipped. Silent laptop run (volume 0, dummy hosts, ports 8090/1893): Morning Jam starts, spotlight sunrise evenly over the ring, no errors. Deployed (backup `~/easteregged/host.bak-2026-10-05-levels.tgz`), restarted: 1 host, top + strip1 online.
- Note: a scenario's own room light (`light.ground`, e.g. the Morning Jam sunrise) still shows on the table strip too; once the wall (ground) exists it can be limited to ground spots.
- **Undo:** on dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-05-levels.tgz && ~/easteregged/run.sh`; locally scratchpad `host_before_levels/`.

## 05.10.2026 (17:18) — New table strip: 89 LEDs

- Flo's new strip on the Joy-IT ESP8266 (`strip1`, .169, WLED 16.0.1): colour test via the WLED API (live override `lor:2`: red, green, blue, white chip, RGB white, rainbow) — all fine; the strip has 89 LEDs, not 77.
- WLED LED output 0: `len` 77 → 89 (other LED settings unchanged: GPIO2, SK6812 RGBW, GRB, 850 mA), rebooted (ends the live override). `host/room.toml`: `strip1 led_count = 89`, spot `table` `leds = [0, 89]`. Tests 12 passed. Deployed (Pi backup `room.toml.before-89`), restarted: "WLED strip1 online … (89 LEDs, RGBW)", 1 host.
- **Undo:** WLED → Config → LED Preferences: length 77; on dexy `cp ~/easteregged/host/room.toml.before-89 ~/easteregged/host/room.toml && ~/easteregged/run.sh`.

## 05.10.2026 (17:05) — Radar page in the main interface

- `web/`: new rail entry **Radar** (`#radar`) → `page-radar` embeds `radar.html?embed=1` (header hidden in embed mode, dark scrollbar); the frame only loads while the page is open (its own WebSocket closes when you leave). `?v=31` everywhere. Deployed to dexy (web only), checked in the browser.
- **Undo:** copy scratchpad `web_v29/` back to `host/web/` (and to the Pi).

## 05.10.2026 (17:00) — Proximity light on the TOP spotlight; radar ghost filter; live radar page

- `core/light.py`: `set_proximity(distance_mm)`; while no scenario runs the TOP spotlight = proximity level (off when nobody, `soft_level` at ≥ `soft_m`, eased up to 100 % at ≤ `full_m`, fades at `fade_s`); a running scenario still sets `top_spotlight_active`. `room.toml`: `[light.proximity]` (enabled, full_m 0.6, soft_m 4.0, soft_level 0.10, fade_s 1.5); `top_spotlight_idle` 0.02 → 0.0.
- `main.py`: ghost filter in `people` — a target counts after `ghost_confirm_s` (1.0) of steady sightings; targets within `ghost_merge_mm` (400) of a counted one are merged; each person gets `d` (mm from the sensor). The loop feeds the nearest `d` to the light at 2 Hz. `room.toml [presence]`: the two keys.
- `web/radar.html` (new, `/static/radar.html`): live radar map (raw targets + trails, host-counted people as white rings), counts, messages/s, raw log, proximity preview with editable numbers, the spotlight's current colour.
- Tests: presence test updated (`d`, confirm 0), new tests for the ghost filter and the proximity light → 12 passed, 1 skipped. Deployed to dexy (backup `~/easteregged/host.bak-2026-10-05-proximity.tgz`), restarted: 1 host; live: 2.2 m → 31 %, 1.1 m → 75 %.
- Open (next wave, Flo): mount the radar rigidly under the ring light, then calibrate (numbers in `[light.proximity]`, spot `pos`).
- **Undo:** on dexy `cd ~/easteregged/host && tar xzf ../host.bak-2026-10-05-proximity.tgz && ~/easteregged/run.sh`; locally restore from scratchpad `host_before_proximity/`; or just set `[light.proximity] enabled = false`.

## 05.10.2026 (16:55) — Radar live; ultrasonic sensor switched off (switchable)

- TOP DevKit wired by Flo (LEDs GPIO4, LD2450 TX → GPIO16): radar messages reach Mosquitto on dexy (state ON, count 1, target x/y updating); host state shows `src: radar`, people with x/y. LEDs: WLED boot colour, then the host's DDP (idle = 2 % rust, looks off).
- `pi/run.sh`: `presence.py` (HC-SR04) only starts if `~/easteregged/use_ultrasonic` exists. Deployed (Pi backup `run.sh.before-radar`), restarted: 1 host, no presence.py.
- **Undo:** `touch ~/easteregged/use_ultrasonic && ~/easteregged/run.sh` (both sensors then fight), or restore `run.sh.before-radar`.

## 05.10.2026 (16:40) — TOP subnode = ESP32 DevKit (WLED + radar on one board); Gledopto out

- Decision (Flo): the Gledopto leaves the setup (glued into its housing); the **ESP32 DevKit V1** (MAC 44:1d:64:fb:4a:f0, the old wall board) drives the TOP spotlight LEDs **and** reads the LD2450.
- Flashed over USB (esptool, bootloader dio 40m + partitions + boot_app0 + app): **WLED 0.15.1 + LD2450 usermod** (`wled/`, env `top_ld2450`, radar RX = GPIO16) + a patch for WLED's double MQTT connect (`wled/patch_wled.py`; the first try on the Gledopto showed "session taken over" and lost all radar messages). Wi-Fi survived; IP stays **192.168.178.170**. Set via API: mDNS `easteregged-top`, name "TOP spotlight", MQTT → 192.168.178.158:1883, client id `easteregged-top`. LED settings kept: GPIO4, 77 × SK6812 RGBW, 850 mA. Checked: one MQTT session, usermod publishing (no radar wired yet → "nobody").
- `host/room.toml`: `[[wled]] id = "gledopto"` (.171) → `id = "top"` (.170, `easteregged-top`), spot `top_spotlight` → `light = "top"`. Deployed (room.toml only; Pi backup `room.toml.before-top-devkit`), host restarted: "WLED top online at 192.168.178.170", 1 host.
- Gledopto: MQTT switched off via API was not confirmed (it no longer answered, probably unplugged). It still runs the test firmware (WLED 0.15.1 + usermod on IO13). If it is used again: flash stock WLED or turn its MQTT off first, or it competes with the TOP radar.
- `esphome/`: Flo's Wi-Fi details were in `secrets.example.yaml` → moved to `secrets.yaml`, fresh template written. ESPHome itself won't build here (spaces in the path, MSYS) — not needed now.
- Open: `presence.py` (HC-SR04) still runs on dexy; stop it once the radar is wired, or both sources fight over presence. Table ESP8266 (`strip1`, .169) offline since it was unplugged for the chip check.
- **Undo:** on dexy `cp ~/easteregged/host/room.toml.before-top-devkit ~/easteregged/host/room.toml && ~/easteregged/run.sh` (laptop copy in the scratchpad); DevKit back to WLED 16 via install.wled.me.

## 05.10.2026 (16:00) — Radar on the Gledopto: WLED build with an LD2450 usermod (not flashed yet)

- The Gledopto has a free screw terminal **IO13 · GND** (unused in its WLED config: buttons 17/0, relay 18, LEDs 16). Plan: LD2450 TX → IO13, GND → GND, 5V → the V terminal of the unused GPIO2 output (= the Gledopto's input voltage, so only while it runs on 5 V). Radar RX stays unconnected.
- New `wled/`: `usermod_ld2450/usermod_ld2450.h` (reads the radar frames, publishes `easteregged/in/presence/state|count|target/n/x|y` + `status/presence` over WLED's MQTT — same topics as the ESPHome config, host unchanged), `platformio_override.ini`, `build.sh`. Built WLED 0.15.1 + usermod (env `gledopto_ld2450`, flash 86 %) in `C:\Users\Florian\.wb` (short path: the scratchpad path broke the Windows path limit). Firmware: `C:\Users\Florian\.wb\src\.pio\build\gledopto_ld2450\firmware.bin`.
- Backup of the Gledopto's settings before any change: `wled/backup_gledopto_2026-10-05/` (cfg.json, presets.json; Wi-Fi password is masked by WLED).
- **Undo** (after flashing): upload the stock WLED 0.15.1 ESP32 .bin from the WLED releases page via Config → Security & Updates → Manual OTA; restore settings from the backup if needed.

## 05.10.2026 (15:20, Copilot; logged afterwards by Claude) — Gledopto as the TOP spotlight

- `host/core/light.py`: spots can be `top_spotlight = true`; such a spot shows one fixed colour (`[light] top_spotlight_color`, #E37156) at `top_spotlight_idle` (0.02) while no scenario runs and `top_spotlight_active` (1.0) while any scenario runs (`set_scenario_running`, called from `main.py` start/finally). It gets no ground, no accents, no pulses, no beat — it is a static cue, not the responsive light. `main.py`: the two calls. `room.toml`: `[[wled]] id = "gledopto"` (192.168.178.171, mDNS `wled-6b0744`, 77 RGBW), spot `top_spotlight`; **the wall ESP32 (`.170`) and the `wall` spot were removed** (MIDDLE accents now fall back to the table strip); `max_brightness` 0.7 → 1.0. Test `test_top_spotlight_has_idle_and_running_levels…` added. Docs: README, Setup_Reference (Gledopto section), MorningJam_Progress, Guide_Hardware_1. Deployed: dexy runs these exact files (checked 05.10 ~15:40).
- Note: the Gledopto section in Setup_Reference ends with the ESP32 wiring text (D4/GPIO4, 330 Ω) copied from the old wall node — wrong for the Gledopto (data GPIO16, built-in level shifter).
- **Undo:** restore `core/light.py`, `main.py`, `room.toml` from Nextcloud's version history (before 05.10 15:14), redeploy, restart.

## 05.10.2026 — Hands-on guide for the presentation setup

- New `Plan/Guide_Presentation_Setup.md`: A wall Pi 3B (fresh SD, SPI, LED strip, Marsboy, screen) → B table Pi 5 (disable old dexy service, SPI, ring) → C spotlight ESP32 (radar firmware, secrets, cone LEDs, wiring, ESPHome) → D room + venue; troubleshooting.
- **Undo:** delete the file.

## 05.10.2026 — Spotlight as its own unit; booklet pages 5.3 (49–53)

- Decision (Flo's sketch, `Plan/Sketch_Presentation_Setup_2026-10-05.jpg`): three units + JBL. **Table** = Pi 5 host (table LED ring Accent, USB mic, USB speaker Moment, Bluetooth JBL General). **Wall** = Pi 3B (LED strip on a wall shelf General, HDMI room screen General = Home view in kiosk mode, Marsboy on AUX Accent). **Spotlight** = ESP32 DevKit with ESPHome: LED ring in the foil cone (Moment) + LD2450 radar in the same housing, own small power bank; light frames over sACN/E1.31 (host needs an E1.31 sender — new work), so a real DMX spot could replace the cone later. The wall unit no longer has the funnel or the radar.
- `Plan/Wiring_Presentation_Setup.svg` is now **out of date** (funnel on the wall Pi, radar via USB-serial); booklet page 51 shows the current wiring. Update the plan SVG when the build starts.
- Booklet pages built: `Design Dokuz/Exports/SVG/Filled/49–53_5-3_*.svg/.png` (script `Design Dokuz/Tools/build_physical_pages.py`).
- **Undo:** delete the five pages, the script and the sketch copy; the decision itself is noted in `MorningJam_Progress.md` §7.

## 04.10.2026 — Wiring diagram for the Pi-based presentation setup (draft)

- New `Plan/Wiring_Presentation_Setup.svg`: wall unit = Pi 3B (LED ring GROUND + funnel TOP on GPIO10/SPI, LD2450 via USB-serial, 3.5 mm → PAM8403 → wall speaker MIDDLE), power bank A; table unit = Pi 5 (table ring MIDDLE on GPIO10, USB mic, USB sound card → PAM8403 → moment speaker TOP, Bluetooth → JBL GROUND), power bank B (+ travel router); legend, power budget, wiring rules. Direction discussed in chat: Pis replace the ESPs (ESPs stay as plan B). Not decided/built yet.
- Revised (Flo: no sound card): table = the existing USB speaker straight into the Pi 5 (TOP); USB sound card, table PAM8403, moment speaker and the amp power branch removed; notes + power budget updated.
- Revised again (Flo: keep it simple): wall amp + 3.5 mm + passive speaker → a 2nd USB speaker on the Pi 3B; audio legend entry removed; subtitle states the rule (per unit one Pi, one power bank, one LED data wire, everything else USB).
- Wall speaker = Flo's **Marsboy** speaker (AUX in, own battery) on the Pi 3B's 3.5 mm jack instead of a 2nd USB speaker → nothing to buy for sound. Speakers now: USB speaker (table, TOP), Marsboy (wall, MIDDLE), JBL optional (GROUND).
- **Undo:** delete the file.

## 04.10.2026 — Prompt for the presentation-setup chat

- New `Prompts/NewChat_Presentation_Setup.md`: context, read-first files, the agreed two-subnode setup (wall: DevKit ring + funnel + C3 radar; table: Pi 5, mic, USB sound card + stereo amp L=moment / R=accent, ESP8266 ring; JBL over Bluetooth behind the commission; travel router), hardware, shopping list, software tasks, working style and rules.
- **Undo:** delete the file.

## 02.10.2026 (17:15) — Home re-laid: clock + seasons left, curve + events right

- `web/` (`?v=29`): left column = clock tile (date, clock in the same size, "Back to now", small Speed control) above the seasons wheel; right = circadian curve (full height) over the events. The "Light now" tile is gone: the value (e.g. "4068 K · 39 %") sits at the room dot on the curve, the phase + colour dot in the curve's header. Hovering the white "you are here" line on the wheel shows "You are here · Day 171 · date · season". `.seg` styles restored (speed buttons were unstyled).
- Deployed to dexy (web only). Then the Pi was shut down at Flo's request.
- **Undo:** copy scratchpad `web_v8` back to `host/web/` (and the Pi).

## 02.10.2026 — Seasons wheel "you are here"; sound-only highlight on Node

- Seasons wheel: a bone-white line (with dot) across both rings at the room's date — inside its Earth segment, proportional between the season's start and end (mission end ~6 Dec 2034, day ~600); tooltip "Day N · date". In real time the date always picks the segment (a remembered click is cleared).
- Node: hovering the Sound variance tile highlights only the sound in the drawing (dotted path + the two upper speakers, a passive highlight) and only that tile; hovering the top band in the drawing still describes light + sound.
- `?v=27`, deployed to dexy (web only).
- **Undo:** remove `dateAngle`/`MISSION_END`/the `w-here` group and its update block, the `sndvar` entry (and set `ASSOC_KEY["mid-sound"]` back to `"variance"`) in app.js; the `#w-here` CSS lines.

## 02.10.2026 — Real time = today's date in the mission

- `core/room.py`: in real time the room's date is today's day/month in the mission year (2 Oct 2026 → 2 Oct 2033, day 171; before 15 Apr → 2034) and the season follows it — also after a restart. A date picked on the wheel (or `[room] date`) holds until "Back to now" or the Real speed button; simulated speeds run on from the current date. State `date_real`; the clock tile says "date set by hand" when it isn't today. `room.toml`: comment on `date`. Page `?v=25`. Deployed to dexy, host restarted.
- **Undo:** restore `core/room.py`, `room.toml`, `web/` from scratchpad `web_v7` (that is before the date feature too), or revert the `follow_real` lines; restart.

## 02.10.2026 — Fix: "Turn off events" covered the whole page

- The events track got the class `off` when hidden, which is also the full-screen "room is off" overlay style. Renamed to `ev-hidden` (app.js, style.css), `?v=24`, deployed to dexy.
- **Undo:** not needed (bug fix).

## 02.10.2026 — The room's mission date

- `core/room.py`: mission calendar — `[room] mission_launch = "2033-04-15"` (day 1; fits the scenario captions: d96 summer, d213 autumn, d412 spring), `date` (start; empty = first mission day of `season`). The date advances when the room's clock passes midnight (also at 8/2 min per day); entering a new Earth season (20/21 Mar, Jun, Sep, Dec) turns the room's season (event "day N: spring begins"). New command `date` (ISO date or mission day). State: `date`, `mission_day`, `launch`. Note: the date restarts from `date`/season when the host restarts.
- `main.py`: `cmd date`. `room.toml`: the two keys.
- Page (`?v=23`): "Day 340 · Mon, 20 March 2034" in the clock tile; Earth wheel segments jump to their season's first mission day (the date sets the season), the wheel marks the segment holding the date; edge labels on the events timeline grow inwards.
- Deployed to dexy, host restarted. Tests 9 passed, 1 skipped.
- **Undo:** restore `core/room.py`, `main.py`, `room.toml`, `web/` from scratchpad `web_v7` (and on the Pi), restart.

## 02.10.2026 — Found ESP32 board tested (read-only)

- "ESP32-D" board on COM5 (CH340): boots its old program once, then no download mode with BOOT and a reset loop (RTCWDT) → likely power (cable/port or regulator). Nothing written to it. Noted in `Setup_Reference.md` spare hardware ("maybe pile"). The radar stays on the ESP32 DevKit (guide step 1: wall strip → Gledopto).
- **Undo:** remove the row from `Setup_Reference.md`.
- Second found "ESP32-D" board: VIN ≈ 2.6 V, 3V3 ≈ 1.4 V on USB, ESP32 silent → noted as broken in `Setup_Reference.md` (Undo: remove that row too).
- "Maybe" ESP32-D remeasured: 5V pin ≈ 3.8 V, 3V3 ≈ 2.8 V; boots fully now but auto-reset into download mode doesn't work (manual BOOT needed); stays "maybe".
- Found ESP8266 (COM6): healthy (ESP8266EX, 4 MB), old firmware kept, noted as spare WLED node. 3× ESP32-C3 SuperMini noted, not tested. (Undo: remove the rows.)

## 02.10.2026 — Hardware guide 1: presence sensor

- New `Plan/Guide_Hardware_1_Presence.md`: step-by-step LD2450 radar on the ESP32 DevKit with ESPHome (wall strip first moves to the Gledopto to free the ESP32), firmware check, wiring, secrets, flashing, MQTT check, switching the host from `presence.py` to the radar, mounting + `pos` calibration, troubleshooting. No device changed yet.
- **Undo:** delete the file.

## 02.10.2026 — Scenarios: stage view with the loop

- `main.py` state: each scenario lists its `moments` (the keys of its `hints`). Host restarted on dexy.
- `host/web/` (`?v=21`): playing a scenario turns its card into a stage (¾ width, the other two step aside into a narrow column, animated): moments track with the current one lit + elapsed time, the big loop (8-beat grid, taps and hums as they join and fade, glowing playhead) when a loop runs, BPM/layers/listening, what plays; Try it + the scenario's extras below. Fixed: all `?v=` tags now change together (app.js had stayed at v=15).
- Not done: "Turn off" also shutting the Pi down (needs a sudo rule for shutdown — Flo's decision, see the chat).
- **Undo:** copy scratchpad `web_v6` back to `host/web/` (and the Pi); remove `"moments": list(v.hints)` from the scenarios line in `main.py`, restart.

## 02.10.2026 — Events on the day axis, big Pangaia clock, larger type

- `main.py` `event()`: every event also carries `h` = the room's hour (shifted/simulated clock). Host restarted on dexy.
- `host/web/` (`?v=19`): Home grid = clock · curve · seasons / speed · curve · seasons / light now · events · seasons. Events tile is as wide as the curve and uses the same 0–24 h axis (room time); labels alternate above/below, crowded ones become dots with a tooltip; one room line runs from the curve down through the events (drag on either to move the clock); toggle "Turn off events" hides them (remembered per browser). Clock in Pangaia, sized to its tile. Type larger everywhere (titles much more: page 38 px, tiles 26 px, level tiles 22 px, scenario titles 34 px).
- **Undo:** copy scratchpad `web_v5` back to `host/web/` (and the Pi); remove the 3 `room`/`payload["h"]` lines from `event()` in `main.py`, restart.

## 02.10.2026 — Node drawing: cleaner, crew lights up with the table

- `web/node.svg` regenerated (scratchpad `make_node_svg.py`): also drops element 143 (inner dotted soundscape circle) and 169 (stray label dot). New `web/crew.svg` = the three crew icons in Sapienza red, laid over the drawing; lit (with a soft glow) when the table is hovered/tapped; hovering a crew member counts as the table. Fixed: in narrow windows/phones the drawing collapsed to 0 px height (`.diagram { flex: none; height: 60vh }`). `?v=15`, deployed to dexy.
- **Undo:** run `make_node_svg.py` without 143/169 in `DROP`; remove the `#crew` img (index.html), `.crew` rules (style.css) and the three `crew-hs` rects + `$("crew")` line (app.js).

## 02.10.2026 — Events "now" marker; surface stay as its own piece

- `host/web/` (`?v=13`): the events timeline ends in a "now" marker (full-height line + dot + current time), like the room marker on the curve. Seasons wheel: the surface-stay pill is its own element (not part of the Mars-winter segment); it lifts off the ring when the wheel spreads, springs further out with a glow on hover/click and shows "Surface stay". Deployed to dexy.
- **Undo:** copy scratchpad `web_v4` back (pre-v5 state), or revert the `.tl-now` block (index.html, style.css, `tl-now` line in app.js) and move the stay path back into the Mars winter group in `buildWheel`.

## 02.10.2026 — Seasons wheel: dark season ticks

- `host/web/app.js` (`?v=10`): the lines between the seasons on the Home wheel are page-dark (#171310, 3 px) instead of bone. Deployed to dexy.
- **Undo:** in `buildWheel`, set the tick `stroke` back to `"#F2EAE3"` and `stroke-width` to 2.

## 02.10.2026 (12:40) — Interface v5: palette colours, post-sleep, wheel notes, calmer Node

- `host/web/` (`?v=9`): curve and "Light now" drawn in Mars Rust variations (deep rust → sand → peach → bone; morning blue = Kolibri blue → #3F7573; pre-sleep rust band, new post-sleep band = first hour after waking, peach); dawn + dusk in the wheel text, curve marker "dawn". Wheel: Earth/Mars dots and the surface-stay piece show their own text on click (no season change). Node: device chips and fixture status dots removed; top band of the drawing = weather light + sound variance (both tiles light up); accent buttons moved to Sound variance; sound rows/meters updated in place (fixes the flickering main sound). Scenarios: presence bar back under the cards ("Presence starts the selected scenario"). Rail: Node icon = folded map. `core/room.py`: docstring names the post-sleep hour (no behaviour change).
- Deployed web + room.py to dexy (no restart).
- **Undo:** copy scratchpad `web_v4` back to `host/web/` (and to the Pi).

## 02.10.2026 (11:45) — Interface v4: bento home, seasons wheel, interactive node; research-based circadian day; real blue on RGBW

- **Circadian day** (`core/room.py` `day()`, seasons in `room.toml`): anchored to crew wake (`dawn_h` 6.5 in every season) and `[room] sleep_h = 22.5`; dawn simulation 30 min before waking; blue-enriched morning (`blue` per season, strongest in winter, gone by ~13:00); neutral day; the season's dusk = golden evening; pre-sleep from sleep − 3 h (≤ 2700 K, no blue); night 1800 K. Seasons now change dusk, peak level/K, `evening_level`, `blue` — no longer dawn. Sources: Brown et al. 2022 (PLOS Biol), ISS SSLA modes (Brainard), Najjar et al. 2014 (Concordia), Thompson et al. 2014 (dawn simulation), Wehr 2001 (photoperiod). State: `curve` = [level, K, blue], `blue`, `sleep_h`.
- **RGBW** (`core/light.py`): `cct_rgb` moved here (room.py re-exports it); new `[[wled]] white_k = 4000` — the white LED carries what it can, R/G/B add the rest, so cool/morning light now gets real blue (before: W = min(R,G,B) sent ~everything to the white LED). Check the strip's white type (WW/NW/CW) and set `white_k`.
- **Web** (`host/web/`, cache-busted `?v=5`): Home bento (clock · speed · circadian curve with blue + pre-sleep · seasons wheel · events timeline left→right · light now); seasons wheel = the Habitat Halo logo (inner Earth seasons, outer Mars seasons, launch Apr 2033; click a segment sets the room's season); Node: booklet drawing without labels (`web/node.svg`, made by scratchpad `make_node_svg.py`) + hover/tap hotspots → label in the drawing, technical info, matching tile highlighted; level tiles list their fixtures (“Table spotlight”, “Wall weather light”, …) with strip + current colour; pill sliders. Scenarios: big start button top right, Tempora/Memoria removed, each card has its own “Try it” simulations. Titles in PP Pangaia (`web/fonts/PPPangaia-Medium.otf`).
- Tests: 9 passed, 1 skipped. Deployed to dexy (backup `~/easteregged/host.bak-2026-10-02.tgz`), restarted via `run.sh`.
- **Undo:** on dexy `cd ~/easteregged && ./stop.sh && rm -rf host && tar xzf host.bak-2026-10-02.tgz && ./run.sh`; locally restore `core/room.py`, `core/light.py`, `room.toml` and `web/` from scratchpad `web_v2` (Nextcloud version history also has them).

## 02.10.2026 — Interface v3 after Flo's review (one screen, booklet diagram, logo)

- `host/web/`: every page fits one screen (laptop/desktop; phone and narrow windows still scroll).
  - Rail: Habitat Halo logo (`web/logo.svg`, cropped from `Design Dokuz/habitat-halo_logo_v4.svg`) instead of the circle; also favicon and on the "room is off" screen.
  - Home: curve smaller; Light tile removed; event timeline larger (up to 40 events, in columns, 24 h times).
  - Node: the booklet's node drawing (`web/node.svg` = `Plan/node-diagram.svg` cropped to the room) instead of the code-drawn diagram; device list → status chips under it (details on hover); right side = booklet bento (TOP/MIDDLE/GROUND × Light/Sound) with live strips, sounds, toggles and the speaker / brightness / room-sound sliders.
  - Scenarios: neutral buttons; only a running card uses orange (border, number, Stop). Presence toggle + simulator moved into one bar at the bottom. Mic sensitivity slider on the Morning Jam card.
- Deployed to dexy (`~/easteregged/host/web`), no restart needed.
- **Undo:** copy back the previous web folder (scratchpad `web_v2`, also in Nextcloud's version history) to `host/web/` and to the Pi; delete `web/logo.svg` and `web/node.svg`.

## 01.10.2026 (23:30) — Night task: interface v2, Copilot merged, deployed

- Interface v2 (`host/web/`: Home · Node · Scenarios · Turn off) + backend (`recent` events, `power` on/off with fade, day curve in state). Checked in the browser: postcard, Turn off/on, phone view, no console errors. HA device dot is grey when HA is off.
- Copilot C1–C3 merged: `main.py` imports `start_bridge` and appends its task; room stream URL uses `[ha] room_stream_format`; `room.toml` gets `room_stream_format = "wav"` and a commented `[ha.entities]` block; README text added. The xfail test replaced (6500 K is daylight white, not blue); the two Host stubs in the tests gained `power = True`. `pytest`: 9 passed, 1 skipped (ffmpeg missing on the laptop).
- Deployed to dexy (tar over ssh, `machine.pi.toml` → `machine.toml`), restarted via `run.sh`: 19 HA entities, page on :8080.
- **Undo:** on dexy `cd ~/easteregged && ./stop.sh && rm -rf host && tar xzf host.bak-2026-10-01.tgz && ./run.sh`; locally restore `web_v1` (scratchpad) and remove the merge lines above from main.py / room.toml / README.

## 01.10.2026 (22:10) — Normal mode again; diagram link colours; docs reviewed

- Pi: stream test ended (`machine.toml.before-stream` restored → `room_output = "main"`), host restarted (1 instance, Mosquitto, wall WLED online, /room.wav off).
- `Plan/System_Diagram.svg/.png`: links coloured by the level they carry (table strip + USB speaker/mic = TOP sand, wall strip/Gledopto = MIDDLE blue, light trunk / room stream / Sendspin / JBL = white); infrastructure grey; legend note.
- Copilot C1–C3 reported done; Claude ran the suite: 8 passed, 1 skipped (no ffmpeg on the laptop), 1 xfail (test expects 6500 K bluish — wrong expectation). Merge into main.py/room.toml/README stays in tonight's task 5.
- Docs reviewed and updated: `MorningJam_Progress.md` (state line, decisions, done items, stale/duplicate items, phase B), `Plan/Plan_Physical_Prototype.md` (paths, status, messaging/device layer, hardware inventory, Copilot role, assets, level colours), `Plan/Plan_Interface_v2.md` (state before tonight), `Plan/Migration_HA.md` (status), `Plan/ESPHome_Evaluation.md` (status), `Setup_Log/Setup_Reference.md` (HA/MA status, spare hardware).
- **Undo:** previous versions via Nextcloud's version history; stream test again: see the 21:45 entry.

## 01.10.2026 (22:15) — System diagram v3: technical

- `Plan/System_Diagram.svg/.png` rebuilt as a technical diagram (Flo: no design-level "character" box; show protocols and where Docker/HA live): Pi split into NATIVE (host main.py with its parts, presence.py) and DOCKER (homeassistant :8123, music-assistant :8095, mosquitto :1883, esphome :6052); every link labelled with its protocol (DDP/UDP 4048, MQTT 1883, REST, HTTP, WS, Sendspin, API·OTA, USB, GPIO 23/24, Bluetooth, SSH 22); protocol legend; level colours only as tags on output devices; planned parts dashed.
- **Undo:** previous version via Nextcloud's version history.

## 01.10.2026 (22:00) — System diagram redesigned; level colours fixed

- `Plan/System_Diagram.svg/.png` rebuilt for readability (Flo: too small/too much text): fewer, larger elements; level lanes TOP / MIDDLE / GROUND on the right; colours as in the booklet node diagram: **TOP sand, MIDDLE blue (#76DBD8), GROUND white**.
- `Plan/Plan_Interface_v2.md`: colour roles changed to the same (was MIDDLE rust, GROUND neutral); postcard colour noted as open question.
- **Undo:** previous diagram via Nextcloud's version history; revert the colour row in the plan.

## 01.10.2026 (21:45) — System diagram; room stream test

- New `Plan/System_Diagram.svg` (+ `System_Diagram.png`, 2×): network, PC, Pi (experience layer: room program, scenarios, web page, audio, mic, light engine; device layer: Mosquitto, HA, Music Assistant, ESPHome; attached USB speaker/mic, HC-SR04), WLED subnodes, planned devices (Gledopto, LD2450, Sendspin speakers, JBL/INMP441), protocols, level colours. Mars Rust.
- Room stream test: Pi temporarily on `room_output = "stream"` (Pi's machine.toml; backup `machine.toml.before-stream`). Test 1 ok: `/static/listen.html` (new `host/web/listen.html`) plays the room sound in the browser (Flo heard it). Plain `/room.wav` in the address bar = endless download (browser behaviour). Browsers reconnect on the endless WAV → MP3/FLAC (Copilot C2) is the robust format for Music Assistant. While the test runs, GROUND/MIDDLE don't play on the Pi speaker.
- **Undo:** delete the diagram files; on the Pi `cp ~/easteregged/host/machine.toml.before-stream ~/easteregged/host/machine.toml && ~/easteregged/run.sh`.

## 01.10.2026 (21:30) — Network decision documented

- Setup_Reference "Network" rewritten: current setup = home FritzBox network (PC on LAN cable .101, Pi on Wi-Fi .158, WLEDs .169/.170, ~7 ms PC→Pi); recommendation to fix the IPs; foreign devices (Pioneer, LG) stay untouched, MA providers stay on for now (Flo); later own local network for the thesis — list of what changes then.
- **Undo:** restore the previous Network section from Nextcloud's version history.

## 01.10.2026 (21:20) — The room is in Home Assistant

- Flo added the MQTT integration (127.0.0.1:1883). HA created the device "Easter-egged room" with all 19 entities (ids `*.easter_egged_room_*`, e.g. `select.easter_egged_room_scenario`, `button.easter_egged_room_weather_accent`), live states ok.
- Round trip tested: `button.press` on the weather-accent button via the HA API → host played `bird_cross`.
- Open: Music Assistant integration, disabling WLED/Cast in HA (Flo).

## 01.10.2026 (21:25) — Pioneer receiver off limits

- Setup_Reference: the auto-discovered Pioneer VSX-832 belongs to Flo's parents — never use it; stream tests with Music Assistant's web player.
- **Undo:** remove the line.

## 01.10.2026 (21:20) — Fix: run.sh started several hosts; HA token verified

- Bug: each `run.sh` call started new restart loops without ending the old ones (autostart + manual restarts → 2–3 hosts at once, kicking each other off Mosquitto every second, "session taken over"; they would also fight over audio and LEDs).
- `pi/stop.sh`: now also ends every run.sh loop (matches only `bash ./run.sh` / `bash /home/pi/easteregged/run.sh` processes, skips its caller). `pi/run.sh`: calls stop.sh first, so a second call is a clean restart. Note: a first version had a literal NUL byte instead of `\000` (shell escaping) — file rewritten directly.
- Tested on the Pi: two consecutive starts → 1 host, 2 loops (host + presence), 0 takeovers.
- HA token (`easteregged-host`, in `~/.easteregged_ha_token`) verified: API answers; the room isn't in HA yet (MQTT integration missing). HA also found a Pioneer VSX-832 receiver (media player) and the WLED strip.
- **Undo:** restore the previous run.sh/stop.sh from Nextcloud's version history (not recommended).

## 01.10.2026 (21:15) — HA token stored outside the synced files

- `pi/run.sh`: exports `HA_TOKEN` from `~/.easteregged_ha_token` (on the Pi only, chmod 600) — survives deploys, never synced. `host/machine.pi.toml`: `[ha] url = "http://127.0.0.1:8123"`, comment for `room_player`. Both copied to the Pi (machine.toml refreshed).
- HA state seen on the Pi: onboarding done, dashboards music-assistant / esphome-builder / room-host, WLED integration auto-discovered (recommend disabling — the host owns the strips), MQTT not yet added, Music Assistant admin created.
- **Undo:** remove the HA_TOKEN line from run.sh and the url line; `rm ~/.easteregged_ha_token`.

## 01.10.2026 (20:50) — Idle room by default; HA stack running on dexy

- `host/room.toml`: `auto_start = false` → after boot the room is idle with only GROUND + MIDDLE; TOP moments start from the page (or switch "Presence starts it" on). Copied to the Pi (only this file and machine.pi.toml — Copilot works on other host files in parallel).
- `host/machine.pi.toml` (+ the Pi's machine.toml): `[mqtt] mode = "external"` (127.0.0.1:1883), `[ha] discovery = true`.
- Pi: `~/ha/` stack copied (+ `~/ha/esphome/` configs), images pulled (~5.5 GB), `docker compose up -d`: homeassistant :8123, music-assistant :8095, esphome :6052, mosquitto :1883. Host restarted on Mosquitto: connected, 19 discovery entities retained, state idle (auto off, ground + middle on, bed crickets); presence script publishes to Mosquitto (status online). The host was stopped ~15 min during the image pull.
- Open: HA + MA onboarding (Flo), MQTT integration, WLED strips were offline at the check.
- **Undo:** `cd ~/ha && docker compose down`; in `~/easteregged/host/machine.toml` remove `[mqtt]`/`[ha]`; `auto_start = true` in room.toml; restart the host (`~/easteregged/run.sh`).

## 01.10.2026 (20:45) — Copilot and Claude in parallel: file ownership

- `Prompts/Copilot_HA_Tasks.md`: Copilot runs now, in parallel with the interface night; strict file ownership (Copilot: ha_bridge.py, web.py new routes, tests/, requirements-dev.txt, Migration_HA.md, Log_Copilot.md, integration notes); hooks/config/README text for Claude's files go into the new `Prompts/Copilot_Integration_Notes.md`.
- `Plan/Plan_Interface_v2.md`: ownership table, new task 5 "merge Copilot's work" before deploying; night prompt updated (order 1–3, 5, 4).
- **Undo:** revert the three prompt/plan files from Nextcloud's version history; delete the integration notes.

## 01.10.2026 (20:25) — Pi updated, Copilot hand-off

- Silent smoke test of the level backend (light `px/g/m/t/acc`, `sounds`, meters, cmd `now`): ok, no errors. Deployed the whole host (HA prep + level backend) to dexy, restarted (it was running); the kept jam trace on the Pi was not touched.
- New `Prompts/Copilot_HA_Tasks.md` (Copilot: C3 tests, C1 HA entity bridge, C2 FLAC/MP3 room stream; division of the HA list). Progress: phase B split into numbered sub-steps with owners.
- **Undo:** redeploy the previous host from Nextcloud's version history; delete the prompt; revert the progress sub-steps.

## 01.10.2026 (late) — Decision: HA stack in Docker on dexy (option A)

- Recorded in `Plan/Migration_HA.md`; phase B broken into sub-steps in the progress file.
- **Undo:** remove the decision line and the sub-steps.

## 01.10.2026 (late) — New-chat prompt rewritten, ESPHome Device Builder in the HA stack

- `Prompts/NewChat_Prompt.md`: full context for a new chat/agent (thesis, levels, prototype, current work, next steps, read-first list, rules).
- `pi/ha/docker-compose.yml`: + `esphome` service (ESPHome Device Builder, port 6052, configs in `~/ha/esphome/`); `Plan/Migration_HA.md` step 7b.
- **Undo:** remove the `esphome` service block and step 7b; the old prompt text is in Nextcloud's version history.

## 01.10.2026 (evening) — Folder cleanup, interface v2 plan revised

- Folders: `Plan/` (Plan_Physical_Prototype, Plan_Interface_v2, ESPHome_Evaluation, Migration_HA, node-diagram.svg), `Setup_Log/` (Setup_Reference, this Log), `Prompts/` (NewChat_Prompt — moved out of the progress file —, Night_2026-10-01_Interface_v2, Old_Handoff_MorningJam_Physical from `_archive/`, which is gone). `MorningJam_Progress.md` stays at the top. References updated in the live docs, README, room.toml, bus.py, docker-compose; older Log entries keep their original paths.
- `Plan/Plan_Interface_v2.md` rewritten for Flo's structure: left rail with Home (light, clock + circadian curve, event bar), Node (diagram, devices, levels), Scenarios (3 cards) and Turn off; Mars Rust, minimal; backend additions (curve, recent events, power).
- **Undo:** move the files back to `Prototype/Physical/` (and the handoff back to `_archive/`), restore the prompt section at the end of the progress file from `Prompts/NewChat_Prompt.md`.

## 01.10.2026 (evening) — Interface v2: backend patched, plan written

- Backend for the level view patched on the laptop, **untested, not deployed**: light previews per level (`light.py` `vg/vm/vt`, `preview()` → `{px,g,m,t,acc}`), named voices (`ambient.py`, `audio.py`, `room.py`, `scenario.py`), `room.sounds()` / `now()`, `main.py` `level_sounds()`, state `sounds`, meter `out/room`, cmd `now`. The current page still works with it.
- New `Plan_Interface_v2.md`: Flo's brief, target layout (node diagram, full-width day bar with Now, TOP/MIDDLE/GROUND rows with own light strip + sound list, output row), tasks, acceptance — to be done in the night.
- **Undo:** restore light.py, ambient.py, audio.py, room.py, scenario.py, main.py from Nextcloud's version history (state of 01.10 ~20:00); delete the plan.

## 01.10.2026 (night) — Prepared for Home Assistant + ESPHome + Sendspin

- `host\core\bus.py`: `[mqtt] mode` embedded/external, host/port/username/password, async connect + reconnect, on-connect hooks, `publish_raw`.
- **New** `host\core\ha.py`: HA MQTT discovery (19 entities, commands on our `easteregged/cmd`), `play_url` via the HA REST API (token only in the Pi's machine.toml or env `HA_TOKEN`).
- `host\core\ambient.py`: `room_output = "stream"` → `Broadcast` + endless WAV at `/room.wav`; `host\core\web.py`: `/room.wav`, `/stems/` routes.
- `host\main.py`: external broker, HA discovery after every connect, room stream task + `start_room_player`, LD2450 inputs (`in/presence/state|count|target/n/x|y`), `people` + `nearest_spot` (spots `pos`), state: presence count/people, devices ha/mqtt.
- `room.toml`: `[mqtt]`, `[ha]`, `room_output` "stream" documented, commented `pos` per spot. Web: radar map of people, MQTT/HA status lines.
- **New** `esphome\presence_ld2450.yaml`, `esphome\sendspin_speaker.yaml` (both pass `esphome config`, ESPHome 2026.6.5; speaker option `channel: mono`), `esphome\secrets.example.yaml`; `pi\ha\docker-compose.yml` + `mosquitto\mosquitto.conf`; `Migration_HA.md`.
- Tested silently on the laptop with a fake HA: discovery, radar → people → spots, HA command format, `/room.wav` (valid WAV, 192 kB/s), play call with token. Embedded mode unchanged.
- **Undo:** delete core\ha.py, esphome\, pi\ha\, Migration_HA.md; restore bus.py, ambient.py, web.py, main.py, room.toml, web\* from Nextcloud's version history.

## 01.10.2026 (night) — Evaluation update: Home Assistant, Sendspin, LD2450

- `ESPHome_Evaluation.md`: new section (HA as device layer, Music Assistant + Sendspin for synced speakers, Bluetooth limits, LD2450 position tracking), hybrid architecture, effort, phased recommendation.
- **Undo:** remove the section "Update 01.10 (night)".

## 01.10.2026 (night) — ESPHome evaluation

- New `ESPHome_Evaluation.md`: what ESPHome would change per part (lights no, presence moderately, mmWave LD2410 yes, audio later), effort, recommendation, two ready YAML configs (HC-SR04 / LD2410C on an ESP32) matching the host's MQTT topics.
- `MorningJam_Progress.md` §6: option added.
- **Undo:** delete the file and the progress line.

## 01.10.2026 (night) — Scenarios 2 + 3, real sounds, scenario switch

- **New** `host\scenarios\spring_cleaning.py` (S2) and `host\scenarios\miss_you_sis.py` (S3); `host\tools\import_vr_sounds.py` → `host\stems\ground|accent|s2|s3\` + `stems\SOURCES.md` (real CC0 recordings + Lena L01 from `E:\UE\Tools\transit_src\`, cut to 30 s loops / one-shots, ~99 MB).
- `core\scenario.py`: `order`, `hints`, `room_duck`, `starts_on_presence`; helpers `sound()`, `bed()`, `move()`, `cleanup()`, `wait_tap()` (tap = mic onset ≥ `tap_min_strength`).
- `core\audio.py`: `ambient_bed(where=table|room)`, `move_bed`, `snapshot_layers` / `restore_layers` (traces). `core\room.py`: `set_top(active, level)`. `core\synth.py`: fallbacks for `birds`/`winter`.
- `main.py`: loads every scenario in `scenarios\`, `select()`, `postcard()` (+ MQTT `in/postcard`, cmd `scenario`/`postcard`), traces kept in `host\traces\*.pkl`, hints in the state, no "not listening" events outside the jam. Morning Jam keeps its layers as trace `jam` at the outro.
- `room.toml`: real bed names per season, `soundscape_gain 0.15`, `accent_gain 0.5`, `tap_min_strength`, `[spring_cleaning]`, `[miss_you_sis]`. Web: scenario buttons, "Postcard from Earth", hint line.
- Tested silently on the laptop (all three scenarios end to end, trace → rewind, season switch to spring, postcard flow); started on the Pi for 15 s (no errors, ~150 MB RAM, 17 % CPU) and stopped again.
- **Undo:** delete the two scenario files, `host\tools\`, `host\stems\ground|accent|s2|s3\`, `host\traces\`; restore the other files from Nextcloud's version history; redeploy.

## 01.10.2026 (evening) — Room levels GROUND + MIDDLE, clean stop, docs

- **New** `host\core\room.py` (room program: circadian day per season, soundscape beds, weather accents, ducking during TOP), `core\ambient.py` (ambient mixer + room output: main / sound card / PipeWire sink via pw-cat), `core\synth.py` (placeholder sounds).
- `core\light.py`: room ground layer + scenario override (`ground`/`release`), `set_duck`, accent modes glow/shade/tint/flash on `middle` spots, "listening" core while capturing.
- `core\audio.py`: ambient mixed into the Top speaker or sent to the room output; `ambient_bed`, `ambient_shot` (travelling).
- `main.py`: room tick (2 Hz); commands season / day_minutes / clock / ground / middle / accent / ambient_volume; presence median; meter `cap`; clean SIGTERM/SIGINT shutdown (3 s per step). `core\web.py`: closes websockets on stop.
- Scenarios: `idle()` and the Morning Jam outro hand the light back to the room instead of a fixed glow.
- `room.toml`: `[[wled]] wall` (192.168.178.170); spots table = strip1 LEDs 0–76, wall = wall LEDs 0–76; `[room]`, `[seasons.*]`; presence `median_of = 5`, `confirm_readings = 3`. `machine.pi.toml`: `[room] room_output`.
- Web page: Ground + Middle tiles, level tags, room-sound slider, "● recording".
- `pi\`: `run.sh` (TERM-based restart), new `stop.sh`, `bt_pair.sh`. Deployed to dexy. Tested: silent laptop test (seasons, accents, ducking, jam), SIGTERM stop on the Pi (~1 s, WLED off), PipeWire sink lookup. Host on dexy left **stopped** (starts at the next boot).
- Docs: `host\README.md` (new: files, levels, MQTT topics, adding subnodes/scenarios), `Plan_Physical_Prototype.md` §4 rewritten, `Setup_Reference.md`, `MorningJam_Progress.md` (ticked + next-session checklist).
- **Undo:** restore the previous versions from Nextcloud's version history (light.py, audio.py, main.py, web\*, room.toml, scenario files); delete room.py, ambient.py, synth.py, host\README.md, pi\stop.sh, pi\bt_pair.sh; redeploy to the Pi.

## 01.10.2026 — Light subnode 2 (ESP32) set up

- ESP32 DevKit V1 USB-C checked with esptool (ESP32-D0WD-V3 rev 3.1, flash OK, old "FLO-PHONE" sketch on it); auto-download unreliable → hold BOOT. Flo flashed WLED 16.0.1.
- Set via the WLED API on 192.168.178.170: mDNS `easter-egged-wall`, LED output GPIO4 (board label D4), 77 × SK6812 RGBW, 850 mA. First save was lost because of an immediate reboot → wait ~4 s after `/json/cfg` before rebooting. Colour test passed; strip switched off afterwards.
- ESP8266: Wi-Fi sleep disabled via the API.
- Pi: host/presence stopped; Flo shuts it down with `sudo poweroff`. Found: the host ignores SIGINT when started in the background (run.sh) → needs a SIGTERM handler for a clean stop (WLED off).
- Docs: `Setup_Reference.md` subnode 2 filled in (IP, chip, GPIO4, wiring); `MorningJam_Progress.md` §5a steps 1, 3, 4 ticked.
- **Undo:** WLED settings can be changed back on `http://192.168.178.170` (Config → LED Preferences / WiFi Setup).

## 01.10.2026 — Autostart on the Pi, setup reference rewritten

- dexy: crontab of user pi `@reboot sleep 20 && /home/pi/easteregged/run.sh` (host + presence start at boot). Checked on the big power bank: 4.98 V, no throttling.
- ESP8266 now standalone on the mini power bank; WLED current limit 850 mA (set by Flo).
- `Setup_Reference.md` rewritten: overview diagram (controller + subnodes), Pi section (devices, folders, autostart, logs), sensor wiring diagram, both light subnodes with wiring, network, operating commands, assets.
- **Undo:** on dexy `crontab -l | grep -v easteregged | crontab -`; the old reference text is in the Nextcloud version history.

## 01.10.2026 — Host on the Pi, progress: sensorial levels

- Host now runs on dexy (192.168.178.158) with its own USB mic + speaker: `~/easteregged/host/` + `machine.toml` (from `host\machine.pi.toml`), started by `~/easteregged/run.sh` (source `pi\run.sh`, restarts on crash; no autostart yet). Laptop host stopped. Stems copied into `host\stems\` (`stems_dir = "stems"`); `main.py` merges an optional `machine.toml`; stale sensor readings (>5 s) count as "nobody".
- `MorningJam_Progress.md`: §4 ticked (mic layers, reactive light, web page, host on Pi) + test notes; new §5 sensorial levels with step-by-step 5a MIDDLE (2nd ESP + wall strip, JBL via Bluetooth on dexy, ElevenLabs accent sound list), 5b GROUND, 5c TOP polish.
- **Undo:** on dexy `pkill -f easteregged` and `rm -rf ~/easteregged/host ~/easteregged/run.sh`; restore `stems_dir = "E:/UE/Tools/transit_src/audio/S1v2"`, delete `host\stems\`, `host\machine.pi.toml` and the merge block in `main.py`; revert §4/§5 of the progress file.

## 01.10.2026 — Host v0.1, Pi presence subnode, naming

- **New `host\`** (Python, one command `run.bat` / `python main.py`): embedded MQTT broker (amqtt, broker option B), audio engine (beds, layers snapped to 16ths/beats, one-shots, routing to spot channels), mic detection (hit / hum, learned speaker-bleed profile), light engine (WLED subnodes over DDP, GROUND / MIDDLE / TOP levels), web page on :8080 (Mars Rust, simulator), scenario `scenarios\morning_jam.py`, config `room.toml`. Packages installed globally on the laptop: sounddevice, soundfile, paho-mqtt, amqtt, zeroconf.
- Tested 01.10 with the simulator: speaker, mic, WLED online; wake → listen → jam, layers and host shaker work. Open: mic level very low (~ -67 dB).
- **Naming** (matches the booklet's node diagram): node = room/controller, subnode = network device, spot = speaker channels + light zone. In `room.toml`: `[[spots]]`, `[[wled]]`.
- **New `pi\presence.py`**: HC-SR04 → MQTT `easteregged/in/presence` `{"distance_cm": x}`, LWT `easteregged/status/presence`. Installed on dexy (192.168.178.158) in `~/easteregged/` with a venv. SSH key from the laptop added to dexy (`~/.ssh/authorized_keys`).
- `Setup_Reference.md`: Pi section filled (dexy, login, venv, Dexy service).
- **Undo:** delete `host\` and `pi\`; `pip uninstall sounddevice soundfile paho-mqtt amqtt zeroconf`; on dexy `rm -rf ~/easteregged` and remove the laptop key line from `~/.ssh/authorized_keys`; revert the Pi section in `Setup_Reference.md`.

## 01.10.2026 — Setup reference file

- New `Setup_Reference.md`: network, WLED node (values read from the device: 16.0.1, 192.168.178.169, mDNS `easter-egged`, 77 LEDs SK6812 RGBW GRB, GPIO2, 2500 mA), wiring, power, audio, Pi presence.
- `MorningJam_Progress.md` §2b: WLED item ticked, IP and settings noted. Header links to the new file. `Plan_Physical_Prototype.md` line 3 links to it.
- **Undo:** delete `Setup_Reference.md` and the two link sentences; untick the WLED item and remove its note.

## 01.10.2026 — Bench work adjusted to the actual kit

Flo's inventory (Progress §1): ESP8266 instead of ESP32, 5 V 3 A USB power bank instead of a 4 A supply, USB stand mic, USB speaker, Pi 5, phone hotspot.

- `MorningJam_Progress.md` §2 rewritten as 2a quick checks (speaker/mic show up in Windows, ESP8266 board + USB driver, hotspot on 2.4 GHz, a way to get 5 V out of the power bank), 2b LEDs (WLED ESP8266 build, GPIO2/D4, power-bank wiring with common ground, current limiter 2500 mA, mDNS `mj-light`), 2c presence (HC-SR04 pinout on the Pi 5, `gpiozero` not `RPi.GPIO`, Windows firewall). Prompt: "ESP32" → "ESP8266".
- `Plan_Physical_Prototype.md` §5: "Have" list, LEDs, sound, mic, power, network lines updated to the real kit; the "To get for milestone 1" list removed (everything is there).
- **Undo:** restore the previous §2 (5 lines: flash, wire, settings, wire HC-SR04, Pi script) and "ESP32" in the prompt; in the plan, restore the old §5 "Have", "Sound", "Mic" lines and the "To get for milestone 1" list. Old wording: Have = "laptop with mic, stand mic, ESP32, Raspberry Pis (2x), 2 speakers (Bluetooth, maybe aux), LED strip (maybe a second one), fablab with a 3D printer"; LEDs = "the ESP32 runs WLED … drives one or two strips"; Sound = "one speaker on aux … stereo-to-2×mono splitter"; Mic = "laptop mic or stand mic, XLR needs an interface"; To get = HC-SR04 + 1k/2k, 5 V 4 A supply (~40 % brightness), 330 Ω + 1000 µF + jumpers, 3.5 mm splitter + aux.

## 01.10.2026 — Prompt file → progress checklist

- Renamed `MorningJam_Prompt.md` → `MorningJam_Progress.md` and rewrote it: tickable prep checklist (check, buy, bench work, broker decision, software, later) + the updated new-chat prompt at the bottom (now also points to the progress file and the "any environment" rule).
- `Plan_Physical_Prototype.md`: two references updated to the new file name (line 3 and the "Who does what" table).
- **Undo:** rename back to `MorningJam_Prompt.md`, keep only the prompt block, and revert the two references in the plan.

## 01.10.2026 — Plan: environment-agnostic, PIR and piezo dropped

- `Plan_Physical_Prototype.md`:
  - §1: added the principle "works in any environment" (portable kit, mic-only input, no furniture sensors).
  - §2: scenario 2 row no longer mentions moving an object.
  - §5 "Later": removed piezo tap pads and reed switch; scenario 3 trigger marked as open (must stay portable); added a "Dropped" note.
- `_archive\Handoff_MorningJam_Physical.md`: added an "archived, superseded" banner at the top.
- **Undo:** delete the added lines/banner and restore the two removed bullets in §5 ("Piezo tap pads on a 2nd ESP32", "Reed switch + magnet for the message object") and "maybe move an object" in §2.
