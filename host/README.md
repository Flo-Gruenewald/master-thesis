# Host: the room's controller

Runs one room ("node"): the MQTT broker, audio (Top beat + layers, room soundscape and accents), light (WLED subnodes), the web page and the scenario. Runs on the Raspberry Pi "dexy" (autostart) or on the laptop.

- Devices, IPs, wiring, operating commands: `..\Setup_Log\Setup_Reference.md`
- What's done / next: `..\Setup_Log\Log.md` (newest first) and `00_Bots/Prototype/Prototype_Bot_Onboarding.md` (open points)
- Change history: `..\Setup_Log\Log.md`

## Run

| Where | How |
|---|---|
| Pi (normal) | starts at boot (`~/easteregged/run.sh` via crontab). Manually: `~/easteregged/run.sh`, stop: `~/easteregged/stop.sh` |
| Laptop | `run.bat` (installs the packages once). Stop the Pi's host first: two hosts would fight over the LEDs |
| Test without hardware | `python main.py --config <copy of room.toml with master_volume = 0 and dummy WLED hosts>` |
| Audio devices | `python main.py --list-devices` |

Web page: `http://<host-ip>:8080` (Pi: http://192.168.178.158:8080).

## Files

| File | What |
|---|---|
| `main.py` | starts everything; `Host` = presence, commands, state, the output loop |
| `room.toml` | **the room**: spots, WLED subnodes, tempo, mic, presence, room program, seasons, colours |
| `machine.toml` | per machine, merged over `room.toml` (audio device names). On the Pi: copy of `machine.pi.toml` |
| `core/bus.py` | MQTT: embedded broker (amqtt) or an external one, + the host's client |
| `core/audio.py` | transport (beat), beds, layers, one-shots, routing to spot channels |
| `core/mic.py` | hit / hum detection with a learned speaker-bleed profile |
| `core/ambient.py` | room sound: mixer + room output (the main output, or a second sound card) |
| `core/room.py` | **room program**: GROUND (circadian day, season, soundscape) and MIDDLE (weather accents) |
| `core/synth.py` | placeholder sounds until real files exist in `../Sounds/ground/` and `../Sounds/accent/` |
| `core/light.py` | WLED subnodes over DDP; GROUND / MIDDLE / TOP rendering |
| `core/web.py` | web page + WebSocket bridge to MQTT |
| `core/scenario.py` | base class for scenarios |
| `scenarios/morning_jam.py` | Scenario 1 · Morning Jam (TOP, active: the jam) |
| `scenarios/spring_cleaning.py` | Scenario 2 · Spring Cleaning (passive: the season turns; tap = rewind of the last jam) |
| `scenarios/miss_you_sis.py` | Scenario 3 · I Miss You, Sis (a postcard from Earth; tap = open; the rain travels) |
| `traces/` | kept jams (`jam.pkl`) for Spring Cleaning's rewind; survives restarts |
| `tools/import_vr_sounds.py` | copies the real recordings from the VR prototype into `../Sounds/` (once, on the laptop) |
| `../Sounds/` | all sounds (moved out of host/ 16.10): Morning Jam stems; `ground/`, `accent/` (room), `s2/`, `s3/` (scenarios); sources + licences in `Sounds/SOURCES.md` |

## Levels (booklet node diagram)

| Level | Owner | Light | Sound |
|---|---|---|---|
| GROUND | room program (always) | circadian day per season on all spots (colour temperature + level) | soundscape beds on the room output |
| MIDDLE | room program (every 1.5–4 min, paused during a moment) | accents on `middle` spots: glow, shade (cloud), tint (rain), flash (lightning) | accents that travel Top speaker ↔ room speaker |
| TOP | scenario | table spotlight/pulses on ordinary `moment` spots; the dedicated Gledopto TOP spotlight shows dim warm-rust while idle and bright warm-rust while any scenario runs | beat, layers, one-shots on the configured audio spots |

While a TOP moment runs, GROUND dims to `duck_level` and MIDDLE pauses. A scenario may take over the ground light of spots (`light.ground`) and gives it back with `light.release`.

The TOP spotlight cue is not a MIDDLE accent: its WLED output is configured as `top_spotlight = true`, `moment = true`, `middle = false`. It is a lighting-only warm-rust indicator for scenario activity/location; its fixed color is not changed by table spotlight or sound-pulse rendering. Dexy (Pi 5) remains the host/controller and sends DDP to the online Gledopto at `192.168.178.171`. The separate Pi 3B named Kellerkind is currently offline and is not this WLED output.

## MQTT

Broker: the host itself, port **1883**, no login. Prefix: `easteregged` (`room.toml` → `topic_prefix`). All payloads JSON.

### Inputs (subnodes → host)

| Topic | Payload | From |
|---|---|---|
| `easteregged/in/presence` | `{"distance_cm": 82.4, "src": "pi"}` (5×/s) — or `{"present": true, "src": "sim"}` | presence subnode (Pi script, later an ESP), simulator |
| `easteregged/in/presence/distance` | a bare number (cm) | e.g. ESPHome `state_topic` |
| `easteregged/in/presence/state` | `ON` / `OFF` | ESPHome binary sensor (LD2450 `has_target`) |
| `easteregged/in/presence/count` | number of people | LD2450 `target_count` |
| `easteregged/in/presence/target/<1-3>/<x|y>` | mm (x left/right, y away from the sensor) | LD2450 targets → people → nearest spot (`pos` in `room.toml`) |
| `easteregged/status/presence` | `"online"` / `"offline"` (retained; set "offline" as the MQTT last will) | presence subnode |
| `easteregged/in/sound` | `{"kind": "hit"}` or `{"kind": "hum"}` | simulator (the mic is read by the host directly) |
| `easteregged/in/postcard` | anything | "a postcard from Earth arrives" → Scenario 3 starts (later: a phone, an Earth-side app) |

The host decides presence: median of the last `median_of` distances, closer than `near_cm` for `confirm_readings` readings = someone is here. A sensor that stops sending counts as "nobody" after 5 s.

### Commands (anyone → host): `easteregged/cmd`

`{"cmd": "<name>", "value": ...}`

| cmd | value | Effect |
|---|---|---|
| `start` / `stop` | — | start the selected scenario / quiet: fade out, no auto-start for `quiet_after_stop_s` |
| `scenario` | `morning_jam` `spring_cleaning` `miss_you_sis` | select (a running one stops gently) |
| `postcard` | — | a postcard from Earth arrives → Scenario 3 |
| `clear_layers` | — | fade all loop layers |
| `auto` | bool | presence starts the scenario |
| `volume`, `ambient_volume`, `brightness`, `sensitivity` | 0..1 | master volume, room sound, light, mic |
| `season` | `summer` `autumn` `winter` `spring` | room season |
| `day_minutes` | 0 = real clock, e.g. 8 | length of a room day |
| `clock` | 0..24 | jump the room's clock |
| `ground`, `middle` | bool | switch the levels |
| `accent` | name or null | trigger a weather accent now (`sun_ray`, `cloud`, `bird_cross`, `bee_pass`, `cat_meow`, `wind_gust`, `rain_pass`, `thunder_far`) |

### Outputs (host → anyone)

| Topic | Payload | Rate |
|---|---|---|
| `easteregged/state` (retained) | scenario, moment, presence, layers, spots, room (season, clock, K, beds, accents), devices, levels | 2×/s + on change |
| `easteregged/meter` | `{"mic", "thr", "pos", "beat", "cap"}` | 20×/s |
| `easteregged/light` | `{"px": "<hex RGB of the virtual strip>"}` | 15×/s |
| `easteregged/event` | `{"type": "hit"/"hum"/"presence"/"moment"/"start"/"stop"/"accent", ...}` | on event |
| `easteregged/status/host` (retained) | `"online"` / `"offline"` | — |

Fast light does **not** go over MQTT: the host sends frames straight to each WLED over DDP (UDP 4048, 40 fps).

## Tests and start

**Start/stop:** desktop icon "Room Host" (`RoomHost.bat` → `RoomHost.ps1`): toggles the host; it runs in its own window and logs to `host.log`.

**Tests:** `pip install -r requirements-dev.txt`, then `python -m pytest tests` from `host/`.

## A new subnode

- **Light:** flash WLED, add a `[[wled]]` block (id, host IP, mdns, led_count, rgbw) and a `[[spots]]` entry (`light = "<id>"`, `leds = [first, count]`, `moment`/`middle`).
- **Sensor:** publish to `easteregged/in/...` on the host's broker; add a handler in `main.py` (`bus.on(...)`).
- **Room speaker on a second sound card:** in `machine.toml`: `[room] room_output = "<part of its name>"`, `room_latency_ms` if it lags.

## A new scenario

Copy a file in `scenarios/` (it appears on the web page automatically), set `name`/`title`/`order`/`hints`, `room_duck` (Ground level meanwhile, 0 = silent), `starts_on_presence`; write `run()`. Helpers: `self.bed()`/`self.move()` (scenario sounds, faded out automatically), `self.sound("s3/lena_01")`, `await self.wait_tap(seconds)` (a tap on the table), `self.host.traces`/`keep_trace`. Use `self.light` (spotlight, pulse, ground/release, accent), `self.audio` (start_bed, oneshot, add_layer, ambient_shot), `self.host.room` (season, accent).

Removed 15.10.2026 (Home Assistant bridge, room stream for Music Assistant, Pi wall node / PipeWire / accent speaker output, sync test): archived in `Prototype/Archive/Demo_cleanup_2026-10-15/`.
