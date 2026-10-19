# Setup reference

How the physical kit is actually set up: devices, settings, wiring, addresses, how to run it. Look things up here; update it when something changes. Open points: `00_Bots/Prototype/Prototype_Bot_Onboarding.md`. Change history: `Log.md`.

Last checked: 01.10.2026, 16:30 (WLED values read from the device API, Pi checked over SSH).


> **State 05.10.2026 evening (newer than the sections below — see Log.md 05.10):** three subnodes named by level. **TOP** = ESP32 DevKit V1 (MAC 44:1d:64:fb:4a:f0) at **192.168.178.170**, mDNS `easteregged-top`, WLED 0.15.1 + LD2450 usermod (`../wled/`), LEDs GPIO4 (77, ring light), radar TX → GPIO16, MQTT → dexy, client id `easteregged-top`. **ACCENT** = 89-LED strip, to be driven by dexy over SPI1 (pin 38, `kind = "spi"`, not deployed). **GROUND** = 60-LED strip on kellerkind (Pi 3B, not reachable yet). **Gone:** Joy-IT ESP8266 "easter-egged" (.169) burned on 05.10; Gledopto removed (still has test firmware + radar usermod on IO13 — flash stock WLED before reuse). HC-SR04 script off (`~/easteregged/use_ultrasonic` to switch back). Old `dexy.service` still enabled (to disable, sudo).

---

## Overview

One room = one **node**. The Raspberry Pi is the node's controller; everything else is a **subnode** on the Wi-Fi.

```
                      Home Wi-Fi (FritzBox, 192.168.178.x)
                                    │
     ┌──────────────────────────────┼──────────────────────────────┐
     │                              │                              │
 CONTROLLER  Pi 5 "dexy"        LIGHT SUBNODE 1              TOP SPOTLIGHT
 192.168.178.158                ESP8266 + WLED               Gledopto GL-C-015WL + WLED
 ├ host (broker, audio,         "easter-egged"               "WLED-Gledopto"
 │  light, web :8080)           192.168.178.169              192.168.178.171
 ├ presence.py (HC-SR04)        table strip                  77 LEDs RGBW · warm-rust TOP cue
 ├ USB speaker  (TOP sound)     mini power bank
 ├ USB mic
 └ big power bank / mains       (next: JBL via Bluetooth = room speaker)
```

| Who talks to whom | How |
|---|---|
| Sensor → host | MQTT `easteregged/in/presence` `{"distance_cm": x}` (both on the Pi, 127.0.0.1:1883) |
| Host → WLED | DDP over UDP port 4048, 40 frames/s; JSON API on port 80 for on/off and status |
| Browser ↔ host | `http://192.168.178.158:8080`, WebSocket `/ws` (mirrors MQTT) |
| Other devices → host | MQTT broker on the Pi, port 1883 (open to the network) |

**Control page: http://192.168.178.158:8080** (phone, laptop, anything on the same Wi-Fi)

---

## Controller: Raspberry Pi 5 "dexy"

| What | Value |
|---|---|
| Board | Raspberry Pi 5 Model B, Debian 13 (trixie), Python 3.13 — the Pi from the Erasmus "Dexy" project |
| Hostname / IP | `dexy` → **192.168.178.158** (also `dexy.fritz.box`) |
| Login | user **`pi`**, password **`admin`**. The laptop's SSH key is installed → `ssh pi@192.168.178.158` needs no password. `sudo` asks for the password. |
| Power | big power bank (1700-0148, 5 V 3 A) or the Pi's mains supply. Checked on the power bank: 4.98 V, no throttling. Note: below 5 A the Pi limits **all USB ports to 600 mA** → if audio drops out, use mains. |
| Folder | `~/easteregged/` |
| Host | `~/easteregged/host/` (copy of `host\` from Nextcloud) + `host/machine.toml` (= `host\machine.pi.toml`: ALSA, device names, 48 kHz) |
| Presence | `~/easteregged/presence.py` (source `pi\presence.py`), publishes to 127.0.0.1 |
| Python env | `~/easteregged/venv` (venv with system packages: `gpiozero`/`lgpio` from the OS; numpy, scipy, sounddevice, soundfile, aiohttp, amqtt, zeroconf, paho-mqtt from pip; no sudo needed) |
| Scripts | `~/easteregged/run.sh` (start host + presence, each restarts itself after a crash), `stop.sh` (clean stop), `bt_pair.sh` (pair a Bluetooth speaker), `test_sensor.py`. Sources in `pi\` |
| **Autostart** | crontab of user pi: `@reboot sleep 20 && /home/pi/easteregged/run.sh` → power on, wait ~40 s, page is live |

### Current TOP spotlight output

Dexy remains the room host and lighting controller. It sends DDP directly to the online Gledopto GL-C-015WL (`192.168.178.171`, WLED `WLED-Gledopto`), configured for 77 SK6812 RGBW LEDs on GPIO16, GRB. In `host/room.toml` this is the `gledopto` WLED device and the `top_spotlight` moment spot. The fixture is dim warm-rust when no scenario runs and bright warm-rust while any scenario runs. It is TOP, not MIDDLE weather/accent lighting.

**Kellerkind is the separate Raspberry Pi 3B wall unit. It is currently offline/not connected and is not the Gledopto.** Do not use the Gledopto's `.171` address as Kellerkind's address.
| Logs | `~/easteregged/host.log`, `~/easteregged/presence.log` |
| PipeWire / Bluetooth | PipeWire runs for user pi; `pw-cat`, `wpctl`, `bluetoothctl` available; controller powered + pairable → the JBL can be the room speaker without sudo (`bt_pair.sh`, then `machine.toml` `[room] room_output = "pw:JBL"`) |
| Old Dexy server | still enabled at boot (`dexy.service`, port 8000, LEDs on GPIO 10). Not in the way. Disable: `sudo systemctl disable --now dexy` |

### USB devices on the Pi

| Device | ALSA name (matched by name, card numbers change between boots) | Role |
|---|---|---|
| USB speaker | `USB2.0 Device` — 48 kHz only | TOP: beat, layers, one-shots |
| USB mic | `USB PnP Sound Device` — 44.1/48 kHz, mono | hits and humming |

### Presence sensor wiring (HC-SR04 on the Pi GPIO)

```
 HC-SR04                          Pi 5 header
 VCC  ─────────────────────────► pin 2   5V
 TRIG ─────────────────────────► pin 16  GPIO23
 ECHO ──[1 kΩ]──┬──────────────► pin 18  GPIO24
                [2 kΩ]
                │
 GND  ──────────┴──────────────► pin 6   GND
```

- Pin 1 = square solder pad; odd pins inner row, even pins outer row (board edge). Pins 2, 6, 16, 18 are all in the outer row.
- **The 2 kΩ is required:** ECHO outputs 5 V, the Pi's GPIO takes 3.3 V max.
- Library: `gpiozero` (`DistanceSensor`), **not** `RPi.GPIO` (doesn't work on the Pi 5).
- Spare sensor: HY-SRF05.
- Lesson from 01.10: sensor VCC/GND swapped → both GPIOs read high. The sensor survived.
- Test: `~/easteregged/venv/bin/python -u ~/easteregged/test_sensor.py` (prints raw and gpiozero distances).

---

## Light subnode 1: ESP8266 + WLED ("easter-egged")

| Setting | Value |
|---|---|
| Board | Joy-IT ESP8266 (NodeMCU-style), USB chip **CP2102** (COM4 on the laptop when plugged in) |
| Firmware | WLED **16.0.1** (ESP8266 build, install.wled.me) |
| IP | **192.168.178.169** → `http://192.168.178.169` |
| mDNS | `easter-egged` (doesn't resolve on Windows; the host finds it via mDNS or the IP in `room.toml`) |
| Lost Wi-Fi | it opens **WLED-AP**, password `wled1234`, page `4.3.2.1` |
| LEDs | **77 × SK6812 RGBW**, colour order GRB |
| Data pin | **GPIO2 = D4** |
| Current limit | **850 mA** (mini power bank 1 A) — raise to 2500 mA on a 3 A supply |
| Wi-Fi sleep | **disabled** (01.10, via API) → smoother beat light |
| Spots in `room.toml` | `table` = LEDs 0–37 (TOP, moment), `wall` = LEDs 38–76 |
| Power | Usewell Fuel Man 2600 mini power bank (2600 mAh, 5 V 1 A), runs ~2–4 h |

### Wiring (standalone, one power bank for board + strip)

```
 Mini power bank ─USB─► USB-to-wires adapter
                         VCC ──► breadboard + rail ──┬──► strip 5V
                                                     └──► ESP8266 VIN
                         GND ──► breadboard − rail ──┬──► strip GND
                                                     └──► ESP8266 G
                         S, D+, D− : not connected (data lines, no power)

 ESP8266 D4 ──[330 Ω]──► strip DIN   (input end: the arrows on the strip point away)
 1000 µF capacitor across + and − (striped leg on −), close to the strip
```

- **Never plug the board into the PC while it gets power from VIN.** Changes: WLED page in the browser.
- The breadboard is fine at ≤ 1 A. For more current (big supply), run the strip's power directly from the adapter and only branch the ESP through the breadboard.

---

## Light subnode 2: ESP32 DevKit V1 + WLED ("easter-egged-wall")

| Setting | Value |
|---|---|
| Board | Gledopto GL-C-015WL (ESP32-based WLED controller, 5–24 V input) |
| Firmware | WLED **0.15.1** (ESP32 build), preinstalled |
| mDNS | `wled-6b0744` (WLED name `WLED-Gledopto`) |
| IP | **192.168.178.171** → `http://192.168.178.171` |
| Data pin | **GPIO16** (board output label) |
| LEDs | 77 × SK6812 RGBW, GRB; single output |
| Current limit | **850 mA** |
| Role | TOP spotlight: fixed warm-rust cue, dim while idle and bright while a scenario runs; excluded from MIDDLE accents |
| Status 05.10 | ✓ online and receiving DDP from Dexy; color test passed |

Wiring: same as subnode 1, data from the pin labelled `D4` (= GPIO4 on the ESP32):
5 V → strip 5V + ESP32 `VIN`; GND → strip GND + ESP32 `GND`; GPIO4 (D4) → 330 Ω → strip DIN; 1000 µF across 5V/GND.

---

## Spare / incoming hardware (01.10)

| Part | Plan |
|---|---|
| 2× HLK-LD2450 radar (from a friend) | presence + positions via ESPHome on the ESP32 DevKit (`esphome/presence_ld2450.yaml`): 5V→VIN, GND, TX→GPIO16, RX→GPIO17; test first with the HLKRadarTool app |
| Gledopto GL-C-015WL black (ESP32 WLED controller, 5–24 V) | online at 192.168.178.171; 77-LED RGBW strip is Dexy's TOP spotlight output |
| Raspberry Pi 3B "Kellerkind" | wall unit intended for the presentation setup; currently offline/not connected; address not yet confirmed |
| INMP441 I2S MEMS mic | spare; later on an ESP32 sensing node or a Sendspin speaker |
| ESP32 board "ESP32-D" (likely ESP-WROOM-32D), USB chip CH340 (COM5) — **maybe pile** | tested 02.10: chip, flash and USB answer (ROM boot log, an old program in flash), but it won't enter download mode with BOOT held and later fell into a reset loop (`rst:0x10 RTCWDT`, output cut off) — points to unstable power (cable/port or its 3.3 V regulator). Not hot. Retest with another cable on a rear USB port before using it; not for the radar until it boots reliably |
| 2nd ESP8266 board (found 02.10), CH340 (COM6) — **healthy spare** | ESP8266EX, 26 MHz, 4 MB flash, MAC 5c:cf:7f:20:6d:c3; auto-enters download mode. Still runs a previous project ("Dual ultrasonic potato counter + LED control"). Use: a 3rd WLED light node (e.g. a second spotlight) |
| 3× ESP32-C3 SuperMini (found 02.10) — **not tested yet** | native USB; candidate for the LD2450 radar (UART on GPIO20/21; avoid GPIO2/8/9; lower Wi-Fi TX power on SuperMinis) |
| 2nd ESP32 board "ESP32-D", CH340 — **broken pile** | tested 02.10: power LED dark, the CH340 enumerates but the ESP32 sends nothing (4 garbage bytes at reset). Measured on USB: **VIN ≈ 2.6 V** (should be 5 V), **3V3 ≈ 1.4 V** (should be 3.3 V) → supply collapses, most likely a short/overload on the board. Cable ruled out (it flashed another board fine). Don't feed external 3.3 V; dispose of it or keep it for parts |
| JBL Bluetooth box | room speaker (`bt_pair.sh`, `room_output = "pw:JBL"`) |

## Network

**Current setup (01.10, decided by Flo): everything on the home FritzBox network `192.168.178.x`.**

| Device | Connection | Address |
|---|---|---|
| PC (Flo's control machine) | LAN cable | 192.168.178.101 (ignore `25.x.x.x` = Hamachi VPN) |
| Pi "dexy" (controller + HA stack) | Wi-Fi (`wlan0`, no cable) | 192.168.178.158 |
| WLED ESP8266 (table) | Wi-Fi | 192.168.178.169 |
| Gledopto WLED (TOP spotlight) | Wi-Fi | 192.168.178.171 |

- PC → Pi works through the FritzBox (cable ↔ Wi-Fi), ~7 ms. SSH, the control page, HA, Music Assistant and ESPHome are all reached this way.
- Recommended: fix these IPs in the FritzBox (Home Network → Network → device → "Always assign this IPv4 address").
- Other devices on this network are not ours (e.g. a Pioneer receiver and an LG TV, visible in HA / Music Assistant): leave them alone; the Music Assistant providers stay on for now (Flo, 01.10).

**Later: own local network for the thesis / exhibition** (planned, not yet decided in detail: laptop-only setup or a local server). What changes then:
- all devices join the new network (WLEDs: WLED-AP `wled1234` → `4.3.2.1` to enter it; Pi: new Wi-Fi via sudo `nmcli` — Flo);
- IPs in `host/room.toml` (`[[wled]] host`), `host/machine.pi.toml` / the Pi's `machine.toml` (`[ha] url`), the ESPHome `broker` substitution, HA's network URL, the Pi's address in docs/bookmarks;
- WLED/ESP: 2.4 GHz only; hotspot vs. travel router see the progress file.

## Operating it

| Task | How |
|---|---|
| Use it | open **http://192.168.178.158:8080** |
| Start everything | power the Pi (autostart), or `ssh pi@192.168.178.158` then `~/easteregged/run.sh` |
| Stop everything | `~/easteregged/stop.sh` (clean: LEDs switch off, ~1 s) |
| Read logs | `tail -f ~/easteregged/host.log` |
| Deploy changes from the laptop | in `Prototype\Demo`: `tar czf - --exclude=__pycache__ host \| ssh pi@192.168.178.158 "cd ~/easteregged && tar xzf - && cp host/machine.pi.toml host/machine.toml"` then restart with `run.sh` |
| Run on the laptop instead | stop it on the Pi first (two hosts would fight over the LEDs), then `host\run.bat` |
| Change room/colours/timings | `host\room.toml` (then deploy + restart) |
| Shut down the Pi safely | `sudo poweroff` (asks for the password), wait for the green LED to stop blinking |

## Home Assistant stack (running since 01.10, onboarding open)

Docker on dexy (option A), started 01.10. Step-by-step, rollback: `Plan/Migration_HA.md`.

| Service | Address | Notes |
|---|---|---|
| Home Assistant | http://192.168.178.158:8123 | set up (Flo); MQTT integration → device "Easter-egged room" (19 entities, ids `*.easter_egged_room_*`); Music Assistant integration; sidebar dashboards music-assistant / esphome-builder / room-host; network URL: set to http://192.168.178.158:8123 |
| Music Assistant | http://192.168.178.158:8095 | admin `flo` set up; connected to HA; Sendspin built in; web player "This Device" for tests |
| ESPHome Device Builder | http://192.168.178.158:6052 | configs in `~/ha/esphome/` (copies of `esphome\*.yaml`); secrets.yaml still to create |
| Mosquitto (MQTT) | 192.168.178.158:1883 | **the room's broker now** (no login, private Wi-Fi); the host no longer starts its own |

- Stack folder on the Pi: `~/ha/` (`docker-compose.yml`, `mosquitto/`, `ha-config/`, `ma-data/`, `esphome/`). Start/stop: `cd ~/ha && docker compose up -d` / `docker compose down`; logs: `docker compose logs -f <service>`. Containers restart by themselves after a reboot.
- Host: `~/easteregged/host/machine.toml` = `machine.pi.toml` with `[mqtt] mode = "external"` and `[ha] discovery = true`.
- **Not ours — never use:** `media_player.pioneer_vsx_832_e76957` (Pioneer VSX-832 receiver of Flo's parents, auto-discovered by HA). Test players: Music Assistant's web player in a browser, later our own Sendspin speakers.
- HA token for the host: `~/.easteregged_ha_token` on the Pi (chmod 600, read by `run.sh` as `HA_TOKEN`); HA token name: `easteregged-host`. Never put it into machine.toml or any synced file.
- Order at boot: Docker brings Mosquitto up; the host (crontab, +20 s) connects and retries until it's there.
- **Rollback to the old setup:** `docker compose down`, remove the `[mqtt]` and `[ha]` blocks from `machine.toml`, `~/easteregged/run.sh`.

## Audio assets

| What | Where |
|---|---|
| Morning Jam stems (84 BPM) | `host\stems\` (copied from `E:\UE\Tools\transit_src\audio\S1v2\`) |
| Room + scenario sounds | `host\stems\ground\`, `accent\`, `s2\`, `s3\` — real recordings from the VR prototype, imported with `host\tools\import_vr_sounds.py`; sources/licences `host\stems\SOURCES.md` (~99 MB) |
| Accent sounds (MIDDLE) | `Sounds\accent\<name>.wav` (missing ones: placeholders from `host/core/synth.py`) |
| Soundscape beds (GROUND) | `host\stems\ground\<name>.wav` (`rain`, `wind`, `crickets`, `fire`, `room_tone`) — placeholders until then |
