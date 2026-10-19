# Migration: Home Assistant + ESPHome + Sendspin

Prepared 01.10.2026. The host is ready for it; nothing has to be rewritten. Background and reasoning: `ESPHome_Evaluation.md`.

**Status 01.10, 22:00:** Docker, stack running, host on Mosquitto with discovery, HA onboarding, MQTT integration (device "Easter-egged room", 19 entities, round trip tested), Music Assistant + its HA integration, HA token for the host — all done. Open: room stream on Music Assistant (needs the MP3/FLAC stream from Copilot C2, merged tonight), Sendspin speakers (hardware), optional HA entity bridge (C1, merged tonight).

**Decision 01.10 (Flo): option A — the HA stack runs in Docker on dexy next to our host** (no new hardware). HA OS on a dedicated device only if the installation becomes permanent.

## Target picture

```
 EXPERIENCE LAYER  our host on dexy (unchanged role): scenarios, live loop + mic, light rendering (DDP), room program
        │  MQTT — Mosquitto (HA stack) instead of the host's embedded broker
 DEVICE LAYER      Home Assistant + ESPHome + Music Assistant (Docker on dexy)
        ├ ESPHome presence subnode: LD2450 → easteregged/in/presence/... (and HA native API)
        ├ ESPHome Sendspin speakers (ESP32-S3 + MAX98357A) → Music Assistant group "Room speakers"
        │     plays the host's room sound stream http://dexy:8080/room.wav in sync on every speaker
        └ the host appears in HA as the device "Easter-egged room" (scenario, season, start/stop, volumes …)
 LIGHT             WLED subnodes, unchanged (the host streams DDP)
```

TOP (Morning Jam's live loop, beat-synced light) stays in the host: Home Assistant can't do sample-accurate audio or 40 fps light.

## What is already prepared (switches, all off by default)

| Switch (`room.toml`, override per machine in `machine.toml`) | Does |
|---|---|
| `[mqtt] mode = "external"`, `host`, `port` (+ `username`/`password` in machine.toml) | the host uses another broker (HA's Mosquitto) instead of starting its own |
| `[ha] discovery = true` | the host announces 19 entities to HA (MQTT discovery): scenario/season selects, start/stop/postcard/accent buttons, auto/ground/middle switches, volume/brightness/sensitivity/day-length numbers, moment/clock/K/people sensors, occupancy |
| `[room] room_output = "stream"` | the room's ambient sound (Ground beds, Middle accents, scenario room sounds) becomes an endless WAV stream at `/room.wav` (48 kHz, 16-bit stereo) |
| `[ha] url`, `room_player` (+ `token` in machine.toml or env `HA_TOKEN`) | the host asks HA to play `/room.wav` on that player (a Music Assistant/Sendspin group), retrying until it works |
| `[ha] room_stream_format = "wav"` (`wav` / `flac` / `mp3`) | selects the room player's stream URL; FLAC/MP3 require `ffmpeg` on the host and fall back to a clear HTTP 503 if it is unavailable |
| `[[spots]] pos = [x_mm, y_mm]` | with the LD2450 the host maps each person to the nearest spot (web page: radar map) |
| MQTT inputs | `in/presence/state` (ON/OFF), `in/presence/count`, `in/presence/target/<1-3>/<x|y>` (mm) — what the ESPHome LD2450 config publishes |
| `/stems/...` over HTTP | every sound file is reachable for HA/Music Assistant if needed |

Tested 01.10 on the laptop (silent, with a fake HA): discovery (19 entities), radar → people → spots, HA command format, room stream (valid WAV, 192 kB/s), HA play call with token.

Ready files: `esphome/presence_ld2450.yaml`, `esphome/sendspin_speaker.yaml` (both validated with ESPHome 2026.6.5), `esphome/secrets.example.yaml`, `pi/ha/docker-compose.yml`, `pi/ha/mosquitto/mosquitto.conf`.

## Shopping list

| For | Part | ~€ |
|---|---|---|
| Presence (per sensor) | **HLK-LD2450** radar + ESP32 DevKit (WROOM-32 is fine) + jumper wires | 8 + 8 |
| Room speaker (per speaker) | **ESP32-S3 DevKitC-1 N16R8** (needs PSRAM — the ESP32 DevKit V1 is not enough) + **MAX98357A** I2S amp + 3–5 W 4 Ω speaker + USB-C power | 10 + 4 + 5 |

## Phase A — LD2450 presence (no Home Assistant needed; before the defence)

1. **Flo:** wire the LD2450 to an ESP32 (see the header of `esphome/presence_ld2450.yaml`).
2. **Flo:** `esphome/secrets.yaml` from `secrets.example.yaml` (Wi-Fi; MQTT user empty for now).
3. Flash: on the laptop `pip install esphome` (in a venv) → `esphome run esphome/presence_ld2450.yaml` (USB the first time; hold BOOT if it won't connect). Or Claude does it with the board on USB.
4. Place the sensor, measure the spots' positions from it, set `pos = [x, y]` for each spot in `room.toml`.
5. Open the web page: the Presence tile shows people as dots; the event log shows "presence arrived (radar)".
6. Turn the old Pi sensor off (or keep both; the last reading wins).

## Phase B — Home Assistant + Music Assistant on dexy (after the defence, or as a half-day spike)

Commands marked **sudo** ask for the Pi's password — Flo runs them.

1. **sudo** — Docker: `sudo apt update && sudo apt install -y docker.io docker-compose` then `sudo usermod -aG docker pi`, log out and in.
2. Copy the stack: from the laptop `scp -r pi/ha pi@192.168.178.158:~/` (Claude can do this).
3. Stop our host (`~/easteregged/stop.sh`), then switch it to the external broker in `~/easteregged/host/machine.toml`:
   ```toml
   [mqtt]
   mode = "external"
   host = "127.0.0.1"
   port = 1883
   ```
   (Port 1883 is taken by Mosquitto now; the host must not start its own broker.)
4. `cd ~/ha && docker compose up -d`, then `~/easteregged/run.sh`.
5. **Flo** — Home Assistant onboarding at `http://192.168.178.158:8123` (create the HA user).
6. HA → Settings → Devices → Add integration **MQTT** → broker `127.0.0.1`, port 1883. Then set `[ha] discovery = true` in machine.toml and restart the host: the device **"Easter-egged room"** appears.
7. ESPHome nodes (presence, speakers) are discovered by HA automatically (Settings → Devices) — accept them.
7b. **ESPHome Device Builder** at `http://192.168.178.158:6052`: copy our `esphome/*.yaml` + your `secrets.yaml` into `~/ha/esphome/` (Claude can do that). New devices: "+ New device" → paste/adapt a config → **Install**. First install over USB: download the firmware there and flash it with web.esphome.io from the laptop (USB in the browser needs https, which the Pi page doesn't have); every later update goes over Wi-Fi with one click.
8. **Music Assistant** at `http://192.168.178.158:8095`: connect it to HA; the Sendspin provider is on by default; the ESPHome Sendspin speakers show up as players. Create a **sync group** "Room speakers". In HA it becomes e.g. `media_player.room_speakers`.
9. **Flo** — HA profile → Security → **Long-lived access token**. Put it into the Pi's `machine.toml` only. Keep `room_stream_format = "wav"` by default; after confirming ffmpeg is installed on dexy, optionally choose `"flac"` or `"mp3"` if Music Assistant does not accept the endless WAV:
   ```toml
   [ha]
   discovery = true
   url = "http://127.0.0.1:8123"
   room_player = "media_player.room_speakers"
   room_stream_format = "wav"  # wav | flac | mp3; compressed formats require ffmpeg on dexy
   token = "…"

   [room]
   room_output = "stream"
   room_latency_ms = 2000      # Music Assistant buffers; keeps travelling sounds together — tune by ear
   ```
10. Restart the host: Ground/Middle and the scenarios' room sounds now play on all Sendspin speakers in sync. The table speaker (USB, TOP) stays on the Pi.

**Rollback** at any step: `[mqtt] mode = "embedded"`, `room_output = "main"` (or delete the lines from machine.toml), `cd ~/ha && docker compose down`, restart the host.

## Open points / risks

### Optional: native HA entity inputs

After HA onboarding and ESPHome entity discovery, configure `[ha].url`, a token in machine.toml or `HA_TOKEN`, and the desired `[ha.entities]` mappings in room.toml. Presence, people count, LD2450 target coordinates, postcard and start inputs then reach the host's existing handlers over the HA WebSocket API. This is optional and independent of MQTT discovery; leaving the URL or entity mappings empty keeps it off. See `Prompts/Copilot_Integration_Notes.md` for the exact config block and host hook.

- Sendspin is a release candidate (RC1); ESPHome's Sendspin components are new — expect updates.
- The room stream adds Music Assistant's buffer (~1–3 s): fine for ambient sound, which is why TOP stays on the wired speaker.
- Bluetooth speakers can't join a synced group reliably (variable delay). The JBL can stay a single "pw:JBL" room speaker, or later become a Sendspin client via a Linux player (`sendspin` CLI) — untested.
- The Pi 5 (8 GB) runs host + HA + MA comfortably; SD-card wear from HA's database → move `ha-config` to a USB SSD if it becomes permanent.
- Security: Mosquitto without login on a private Wi-Fi (like today). For anything shared, switch on the password file (see `mosquitto.conf`).
