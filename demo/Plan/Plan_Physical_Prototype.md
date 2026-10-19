# Plan: physical prototype (context for all sessions)

Updated 01.10.2026 (22:00). This is the full context. Progress checklist: `../MorningJam_Progress.md`. Devices, settings, wiring, IPs: `../Setup_Log/Setup_Reference.md`. System diagram: `System_Diagram.svg`. Prompts (new chat, night work, Copilot, the old handoff): `../Prompts/`.

## 1. Why a physical prototype

- **Thesis:** a Mars-mission habitat that acts as a "host". It makes small ambient light and sound offers to break monotony.
- **Concept values:** Distributed but coherent; Convivial but considerate; Attentive but discreet; Ephemeral but steady.
- **Defence:** 21 Oct 2026.
- **Supervisor feedback 01.10** (`Notes\12_Thesis-Talk_Pollini.md`):
  - Ambient light and sound are the strong part.
  - The VR prototype feels detached and too sci-fi, and there is little real interaction with objects.
  - He wants spotlight moments coordinated across several nodes by a script, and a small physical-computing prototype (a corner or small room, LED strips, speakers behind, sensors).
- **Decision:** build an **experiential installation** that the commission and other students can try themselves.
  - The VR prototype (`Prototype\VR\`, finished for now) stays as a context film.
  - Crew characters such as Alice and Bob are not needed.
- **Principle: works in any environment.** The kit is portable and room-agnostic: laptop, mic, speakers, LED strips, one presence sensor. No sensors built into furniture (no piezo tap pads, no PIR, no switches under coasters). Anything people do with the room (tap a table, ding a cup, hum) reaches the host through the mic. Set-up in a new room = place nodes, edit the room config, done.

## 2. The installation and its three scenarios

One table corner, two to four nodes (node = one speaker plus one light zone), the same hardware for all scenarios.

| Scenario | Visitors do | The host does |
|---|---|---|
| **1 Morning Jam** (active, built first) | Tap the table, ding cups, hum into the mic | A beat loop runs; their sounds are added onto the loop; the light reacts to the sound |
| 2 Spring Cleaning (passive, built 01.10) | Just be in the room; tap the table to rewind | Sound layers and light build and shift slowly across the nodes; the orchestration carries the feel |
| 3 I Miss You Sis (passive, emotional, built 01.10) | A postcard arrives (web page / MQTT); tap the table to open it | Rain starts, the light turns blue, the message from home plays, then a warm invitation light; carries over from scenario 2 |

## 3. Milestone 1: Morning Jam basics (target ~08.10)

1. **Presence:** someone comes near → the ultrasonic sensor starts the scenario.
2. **Backbone loop:** a beat loop starts (the S1v2 chill stems, 84 BPM).
3. **Adding sounds:** sounds picked up by the mic (taps, cups, humming) are captured, snapped to the beat and **added onto the loop as new layers**, so the beat grows as people play.
4. **Reactive light:** the LEDs react to the sound (level and hits), across the light zones.
5. **Control:** everything is started, stopped and watched from the **web page**. There is no physical stop button for now.

Not in milestone 1: scenarios 2 and 3.

**Status 01.10:** milestone 1 reached; scenarios 2 and 3 built as well. Since 01.10 evening the room starts **idle** (GROUND + MIDDLE only); presence no longer starts a TOP moment unless "Presence starts it" is switched on.

## 4. Architecture (updated 01.10, evening)

- **One room = one node** (booklet node diagram). The **controller** is the Raspberry Pi 5 "dexy" running the host (`host\`, autostart); everything else is a **subnode** on the Wi-Fi: WLED light subnodes (ESP8266 table, ESP32 wall), the presence sensor (Pi GPIO now, an ESP later). A **spot** = speaker channels + a light zone.
- **Three sensorial levels**:
  - **GROUND** (room program, always): circadian day per season on all lights + soundscape bed.
  - **MIDDLE** (room program, every few minutes): weather accents — light on the wall (cloud, sun ray, rain, lightning) + sounds travelling between the Top speaker and the room speaker.
  - **TOP** (scenarios, when someone is there): Morning Jam etc.; Ground dims and Middle pauses meanwhile.
  - Top-down approach (seasons, variation) = Ground + Middle; bottom-up (moments) = Top.
- **Sound**: Top on the wired USB speaker (beat-accurate). Ground/Middle may use a Bluetooth room speaker (the JBL): latency doesn't matter for ambient sound.
- **Core / scenario / config**: scenario-independent core (`core\`), one file per scenario (`scenarios\`), the room in `room.toml`, per-machine audio in `machine.toml`.
- **Messaging**: MQTT for events, state and commands (topics in `host\README.md`) — broker since 01.10 = **Mosquitto in the HA Docker stack** (the host's embedded amqtt broker remains as fallback); light frames straight to WLED over DDP; the web page via a WebSocket bridge.
- **Device layer (01.10)**: Home Assistant + Music Assistant + ESPHome builder + Mosquitto in Docker on dexy (`../Plan/Migration_HA.md`). The host appears in HA as the device "Easter-egged room" (19 entities). The host stays the experience layer (live jam, DDP light).
- **Web page**: http://192.168.178.158:8080 — all three levels, controls (season, day speed, accents, start/stop, volumes), simulator.

## 5. Hardware

**Have (01.10):** PC (LAN), Raspberry Pi 5 "dexy" (+ a 2nd, older Pi), USB stand mic, USB speaker, JBL Bluetooth box, ESP8266 (table, WLED), ESP32 DevKit V1 USB-C (wall, WLED), SK6812 RGBW strips (77 LEDs; more strips to check), big power bank 5 V 3 A + mini power bank 5 V 1 A, HC-SR04 + HY-SRF05, resistors/capacitors/jumpers, fablab with a 3D printer. **From a friend:** 2× HLK-LD2450 radar, Gledopto GL-C-015WL (ESP32 WLED controller), INMP441 I2S mic. Details: `../Setup_Log/Setup_Reference.md`.

**Milestone 1 setup:**
- **LEDs:** the ESP8266 runs WLED (flashed from the web installer) and drives the strip (one output; a 2nd strip later needs a 2nd board or an ESP32).
  - Check the strip first. 3 wires (5V, GND, DIN) is addressable, which is what we need. 4 wires (12V, R, G, B) is not.
- **Presence:** an ultrasonic sensor (HC-SR04) on the Raspberry Pi GPIO.
  - The echo pin needs a voltage divider (5 V → 3.3 V).
  - A small Python script publishes the presence to MQTT.
  - Pi 5: use `gpiozero`, not `RPi.GPIO`.
- **Sound:** the laptop plays to the USB speaker (if it shows up as a Windows output; otherwise aux). One speaker = one node for milestone 1. Two nodes later via the audio interface, not two Bluetooth speakers at once.
- **Mic:** the USB stand mic (no interface needed).
- **Power:** mini power bank (1 A) for the ESP8266 + strip, WLED limit 850 mA; the big one (3 A) for the Pi or a strip.
- **Network:** the home FritzBox network for now (Pi on Wi-Fi .158, PC on LAN .101); an own local network later (see `../Setup_Log/Setup_Reference.md`).

**Later (scenarios 2–3, more nodes):**
- USB audio interface with 4 outputs and 2+ inputs (e.g. Behringer UMC404HD), for 4 speaker nodes and an XLR mic.
- 2nd LED strip.
- 3rd and 4th speaker.
- 3D-printed diffuser channels.
- Scenario 3 "message" trigger: open. It must stay portable (e.g. a self-contained object, or triggered from the web page). Decide when scenario 3 starts.

**Dropped (01.10):** PIR sensor and piezo tap pads. They tie the installation to one piece of furniture and duplicate what the mic already hears. See the principle in section 1.

## 6. Who does what

| Task | Tool |
|---|---|
| Host software, MQTT topics, web page, connecting and tuning the real hardware | Claude Code (`MorningJam_Progress.md`) |
| Shopping with links, WLED flashing and wiring step by step at the bench | ChatGPT |
| Self-contained code tasks with strict file ownership (01.10: HA entity bridge, FLAC/MP3 stream, test suite — `../Prompts/Copilot_HA_Tasks.md`) | GitHub Copilot |
| Setup sketch image, test protocol, thesis write-up drafts | ChatGPT; Claude Code checks them against the build |

## 7. Assets

- **Sounds in the host:** `host\stems\` — Morning Jam stems (from `E:\UE\Tools\transit_src\audio\S1v2\`) and the real VR recordings for room/scenarios (`host\stems\SOURCES.md`, import script `host\tools\import_vr_sounds.py`).
- **Scenario texts:** `Design Dokuz\Working Documents\Scenarios_v4.md` and `Scenario_Scripts_v1.md`.
- **Voices (optional, later):** `E:\UE\Tools\transit_src\audio\VO\` and `E:\UE\Tools\transit_src\v5\voice\`.
- **Design system:**
  - Fonts: PP Pangaia (titles), PP Neue Montreal (text).
  - Colours: bg #171310, bone #F2EAE3, rust #E37156, peach #F2AD9D, teal #76DBD8.
  - Level colours (as in the node diagram): TOP sand #E37156 · MIDDLE blue #76DBD8 · GROUND white #F2EAE3.
