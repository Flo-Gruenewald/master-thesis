# Morning Jam: progress

The working file for the physical prototype. Tick boxes as things get done. Full context: `Plan/Plan_Physical_Prototype.md`. Change history with undo steps: `Setup_Log/Log.md`. Devices, settings, wiring, IPs: `Setup_Log/Setup_Reference.md`.

Milestone 1 target: **~08.10.2026** — reached 01.10 (Morning Jam works in the room). Defence: 21.10.2026.

**State 01.10, 22:00:** host on the Pi (idle room by default: GROUND + MIDDLE, TOP from the page), all three scenarios built, HA stack running (Mosquitto, Home Assistant with the room device, Music Assistant), Copilot C1–C3 done (merge tonight), system diagram `Plan/System_Diagram.svg`. Tonight: interface v2.

**TOP spotlight naming (05.10):** Dexy (Pi 5) remains the host/controller. The online Gledopto WLED at `192.168.178.171` drives the 77-LED RGBW TOP spotlight cue: dim warm-rust while idle, bright warm-rust whenever any scenario runs. This is a TOP/moment fixture, not a MIDDLE/weather accent. **Kellerkind is the separate Pi 3B wall unit and is currently offline/not connected**; it is not the Gledopto.

---

## 1. Devices

- [x] **LED strip:** number of wires (3 = addressable ✓, 4 = not), 5 V or 12 V, chip name printed on it (e.g. WS2812B), length, LEDs per metre.
	- WS2812B, 3 pins, 5V, about 1-2 m
	- (Claude, 01.10: WLED reads it as **SK6812 RGBW**, 77 LEDs — it has a white chip)
- [x] **ESP32:** board model; a USB cable that carries data (not charge-only).
	- ESP8266 Microcontroller plus USB cable
- [x] **Mic:** stand mic model; USB or XLR? (XLR without an interface → start with the laptop mic.)
	- stand mic USB one, fun generation with a cable that is USB-A
- [x] **Speaker:** does at least one have an aux input? (If not, one Bluetooth speaker is fine for milestone 1.)
	- Speaker, also USB-A
- [x] **Raspberry Pi:** model; SD card with Raspberry Pi OS; SSH works.
	- Pi 5, SSH works, it is set up (I might need to test again) + power jack
- [x] 5 V power supply, 4 A, + DC barrel-jack adapter (assumes a 5 V strip, ~2 m at 60 LED/m)
	-  Power bank; 1700-0148; 10000mAh / 37Wh LiPro; Micro USB QC3.05V = 3A / 9V = 3A / 12V =1.5 A 18W output
- [x] 330 Ω resistor, 1000 µF capacitor, jumper wires
	- I have some in my electronic fun kit
- [x] HC-SR04 ultrasonic sensor + 1 kΩ and 2 kΩ resistors (voltage divider on echo)
	- HC-SR04 or HY-SRF05 (i have both)
- [x] Aux cable(s)
	- not needed for now ( I think)
- [x] **Own Wi-Fi:** small travel router (~€25, recommended) or phone hotspot. University Wi-Fi (eduroam) usually won't let the ESP32 join and often blocks device-to-device traffic. Own network = the kit works the same in any room.
	- phone hotspot is fine for now
	- (01.10: everything runs on the home FritzBox network; own network later — see Setup_Reference "Network")

## 2. Bench work (ChatGPT step by step)

Adjusted 01.10 to the kit above (ESP8266, power bank, USB speaker, Pi 5, phone hotspot).

**2a. Quick checks first (5 min)**
- [x] **Speaker:** plug it into the laptop. Does it appear in Windows sound settings as an output device? Yes → it's a USB sound card, no aux needed. No (it only lights up) → USB is just power; then it needs an aux cable after all.
	- I have used it before, the raspi could play it so I am sure whatever I am using also can do; otherwise I have a bluetooth JBL box
- [x] **Mic:** plug it in; does it appear as an input device in Windows sound settings?
	- I have used it before as well, I know it works on the pc.
- [x] **ESP8266 board:** which one (NodeMCU, Wemos D1 mini, …)? Plug it in: if Windows shows no COM port, install the USB driver (CH340 or CP2102, printed on the chip next to the USB port).
	- Brand newES8266 MODfrom joy it net and can do wifi. I get something for COM1 and COM4, but I dont know what they are. Installing WLED
- [x] **Hotspot on 2.4 GHz:** the ESP8266 can't see 5 GHz. iPhone: turn on "Maximize Compatibility". Android: set the band to 2.4 GHz. Laptop and Pi join the same hotspot.
	- it is "maximize connectivity"
- [x] **A way to get 5 V out of the power bank onto wires:** a USB-A breakout with screw terminals (~€3) or an old USB cable cut open (red = 5 V, black = GND). Have one? ___
	- yes, I have one USB to cables adapter, that is actually S, GND, D+, D- and VCC

**2b. LEDs**
- [x] Flash WLED from install.wled.me (Chrome or Edge), pick the **ESP8266** build. Use the laptop USB for flashing.
- [x] Wire the strip, powered from the power bank (it gives plain 5 V unless a fast-charge device asks for more, so a plain cable is safe):
  - power bank 5 V → strip 5V, and → ESP8266 `VIN`/`5V` pin
  - power bank GND → strip GND, and → ESP8266 `GND` (**common ground** is a must)
  - ESP8266 `D4` (GPIO2, WLED's default on ESP8266) → 330 Ω → strip DIN
  - 1000 µF capacitor across 5V/GND at the strip end (stripe = minus = GND)
  - While the ESP is also on laptop USB: still fine, keep the common ground.
- [x] WLED settings → LED Preferences: LED count (count them, ~60 per metre), data pin GPIO2, **brightness limiter on, max current 2500 mA** (the power bank gives 3 A; this keeps a margin).
	- now 850 mA (mini power bank 1 A); Wi-Fi sleep off
- [x] WLED → Wi-Fi: join the hotspot. Set the mDNS name (chosen: `easter-egged`). **IP today:** `192.168.178.169`
	- Checked by Claude 01.10 via the WLED API: WLED 16.0.1, mDNS `easter-egged`, 77 LEDs, type SK6812 **RGBW**, GRB, GPIO2, limiter 2500 mA. On the home Wi-Fi (192.168.178.x), not the hotspot — fine for development. Windows doesn't resolve `easter-egged.local`, so the host uses the IP (in the room config).
- [x] Test: change colours from the WLED web page on your phone.
- [x] Watch for: the power bank switching itself off when the LEDs are dark (some do below ~100 mA). If it happens, tell Claude; the host can keep a faint glow.

**2c. Presence (Pi 5)**
- [x] Use the **HC-SR04** (5 V, needs the divider). Wiring: VCC → Pi 5V (pin 2), GND → GND (pin 6), TRIG → GPIO23 (pin 16), ECHO → 1 kΩ → GPIO24 (pin 18), with 2 kΩ from GPIO24 to GND.
- [x] Pi presence script with Copilot, against the topics in `host\README.md` (once it exists). Tell Copilot: **Pi 5 → use `gpiozero` (`DistanceSensor`), not `RPi.GPIO`** (it doesn't work on the Pi 5).
- [x] First run of the host on the laptop: allow it through the Windows firewall (private network), otherwise the Pi can't reach the broker.

## 3. Decisions

- [x] **MQTT broker.** A: Mosquitto (separate Windows install, admin rights). B: broker built into the Python host (nothing to install, one command, Pi can still publish to it). **Recommended: B.** → chosen: **B** (amqtt inside the host)
	- since 01.10 evening: **Mosquitto in the HA Docker stack** is the room's broker (`[mqtt] mode = "external"`); the embedded one stays as fallback
- [x] **Home Assistant:** option A — Docker on dexy next to the host (01.10)
- [x] **Idle room by default:** after boot only GROUND + MIDDLE; TOP moments start from the page (`auto_start = false`) (01.10)
- [x] **Network:** home FritzBox for now; foreign devices (Pioneer, LG) are left alone; own local network later (01.10)
- [x] **Level colours** as in the booklet node diagram: TOP sand, MIDDLE blue, GROUND white (01.10)

## 4. Software (Claude Code)

- [x] Host scaffold in `host\`: core (audio engine, light engine, inputs), scenario file, room config, one start command
- [x] Runs fully in the simulator (no hardware)
- [x] Beat loop from S1v2 stems (84 BPM)
- [x] Mic onsets/humming → snapped to the beat → added as loop layers
- [x] Sound-reactive light, preview on the web page
- [x] Web page (Mars Rust): state, presence, mic level, layers, light zones; start/stop, clear layers, volume, simulator buttons
- [x] MQTT topics documented in `host\README.md`
- [x] Connect real WLED over DDP
- [x] Connect the Pi presence sensor
- [x] Host moved onto the Pi ("dexy", the room controller) with its own USB mic + speaker → **http://192.168.178.158:8080**
- [x] Autostart on the Pi (`~/easteregged/run.sh` via crontab `@reboot`)
- [x] Clean stop on the Pi: SIGTERM handled, `~/easteregged/stop.sh`; WLEDs switch off; shutdown ~1 s
- [x] `run.sh` = clean restart (no double hosts anymore; fixed 01.10)
- [x] System diagram (technical: protocols, native vs. Docker, level-coloured links): `Plan/System_Diagram.svg` + `.png`
- [ ] Tune with real mic and room; test with 2–3 people; film

**Noted after the first real test (01.10)**
- [x] Loops and layers work with the real mic; mic sensitivity slider fixed the self-recording.
- [ ] Sometimes misses taps (likely the cheap mic; try placement first).
- [x] **Unclear when it records** → bright "listening" core on the table light while a sound is captured + "● recording" on the web page; layer taken = white flash.
- [x] Presence smoothed: median of the last 5 distances, 3 confirming readings (`room.toml [presence]`). Check how it feels.

## 5. Next: sensorial levels (node diagram)

The booklet's node diagram has three levels. Ground and Middle are the **room** (always running, top-down: seasons and variation); Top is the **moment** (bottom-up: the scenarios). When a Top moment starts, Ground dims a little and Middle pauses.

| Level | Light | Sound | Status |
|---|---|---|---|
| TOP · moment | spotlight on the table spot | main sound from the table speaker, on the beat | ✓ Morning Jam |
| MIDDLE · accent | **weather** on a wall strip: a passing cloud, a sun ray, rain-grey | **sound variance**: short sounds that travel table speaker ↔ room speaker (a bird crossing, a bee, a cat) | ✓ software, real sounds; room speaker (JBL) still open |
| GROUND · general | circadian day curve (warm ↔ cool white), season sets peak and dusk | soundscape bed (rain, wind, insects) from the room speaker | ✓ software, real sounds |

### Next session (Flo) — checklist
- [ ] Interface v2 — left rail: Home (light, clock + circadian rhythm, events), Node (diagram, devices, levels), Scenarios, Turn off: `Plan/Plan_Interface_v2.md`, prompt `Prompts/Night_2026-10-01_Interface_v2.md` — Claude, night 01.→02.10
- [x] **Claude first:** deploy the latest host (HA prep + level backend) to dexy (01.10 20:22)
- [x] Power the Pi → after ~40 s open **http://192.168.178.158:8080** (everything autostarts)
- [ ] Power both light subnodes (table ESP8266 + wall ESP32); check both show green under *Subnodes*
- [x] Try the room: Ground tile → *8 min* day speed, switch seasons; Middle tile → press the accent buttons (Flo: "sounds immersive, lights mostly nice" — fine tuning another day)
- [ ] Pair the JBL: JBL in pairing mode → tell Claude (or `ssh pi@192.168.178.158` → `~/easteregged/bt_pair.sh`)
- [ ] Wall strip: test, place, power bank; if not 77 LEDs → tell Claude (or WLED + `room.toml`)
- [ ] Try all three scenarios (web page: scenario buttons, "Postcard from Earth")
- [ ] ElevenLabs (optional): only `bee_pass`, `thunder_far` (accent) and `fire` (ground) are still placeholders; everything else uses the real VR recordings
- [ ] Fine tuning light + sound (levels, timings) — "another day"
- [x] Gledopto GL-C-015WL is online as Dexy's TOP spotlight output (`192.168.178.171`); it is not Kellerkind and not MIDDLE accent lighting.

### 5a. MIDDLE · accent (weather) — step by step

**Hardware plan:** wall strip on a **2nd ESP with WLED** (light subnode "wall"); **JBL paired to dexy over Bluetooth** as the room speaker (no 2nd ESP/Pi for sound: ambient sounds don't need beat accuracy, so Bluetooth latency is fine). Fallback if Bluetooth on dexy is flaky: the spare Pi as an audio subnode playing local files on MQTT commands.

**Flo**
- [x] 1. Get a 2nd board: **ESP32 DevKit (WROOM-32)** recommended (same price, more headroom, 2+ LED outputs); another ESP8266 NodeMCU also works.
	- ESP32 DevKit V1 USB-C: not fried, works (checked 01.10).
- [ ] 2. Get/choose the 2nd strip: ideally **SK6812 RGBW** like the first (warm whites for weather), 1–2 m. + 5 V supply (2nd power bank or a 5 V 3 A USB charger), 330 Ω, 1000 µF.
	- Enough strips available; **check which work** and find a **3rd power bank** (the mini one runs the ESP8266, the big one the Pi). Tested so far by swapping the ESP32 into the ESP8266's setup.
- [x] 3. Flash WLED (install.wled.me), same as strip 1: LED count, GPIO, RGBW type if RGBW, current limiter, join the home Wi-Fi.
	- WLED 16.0.1, data on the pin labelled **D4 = GPIO4** on the ESP32, 77 LEDs SK6812 RGBW, 850 mA, Wi-Fi sleep off. Colour test passed. (Flashing: hold BOOT.)
- [x] 4. (Historical 01.10 setup) ESP32 WLED wall node used mDNS `easter-egged-wall`, `192.168.178.170`; this is not the current TOP spotlight output.
- [ ] 5. Place it: strip along the wall or a shelf **behind / across from the table**, not at the table (the table is Top).
- [ ] 6. JBL: put it in a corner **opposite the table speaker**, switch it to **pairing mode**, tell Claude (Claude pairs it from dexy over SSH).
- [~] 7. Generate the accent sounds with ElevenLabs (Sound Effects), list below. Save as WAV (or MP3) into `host\stems\accent\` with exactly these file names.
	- mostly replaced by the real VR recordings (bird, cat, gust, rain); only `bee_pass` and `thunder_far` are still placeholders

**Claude**
- [x] A. Room program in the core (`core/room.py`): Ground/Middle run independently of scenarios; Top ducks them.
- [x] B. (Historical 01.10 setup) ESP32 WLED wall node at `192.168.178.170`; superseded for current TOP spotlight control by the Gledopto at `192.168.178.171`.
- [x] C. Room speaker in software: `room_output` = `main` / a sound card / `pw:<name>` (PipeWire, e.g. the JBL). Sink lookup tested on dexy ✓. **Pairing still to do** (`~/easteregged/bt_pair.sh`).
- [x] D. Weather accents: every 1.5–4 min (demo: 25–60 s), season-dependent; light on the middle spots + sound travelling Top ↔ room speaker. Placeholder sounds generated in code until the ElevenLabs files exist.
- [x] E. Web page: Ground tile (clock, K, season, day speed, time slider), Middle tile (accent buttons, next accent), level tags, room-sound volume.
- [x] F. Recording feedback in Top (listening core while capturing, white flash when a layer is taken).

**Accent sounds (ElevenLabs Sound Effects, 2–10 s, no music)**

| File | Season | Prompt |
|---|---|---|
| `bird_cross.wav` | spring, summer | A single small songbird chirping as it flies past the listener, close, natural, no background noise |
| `bee_pass.wav` | summer | A bee buzzing as it flies past close to the listener from left to right, short |
| `cat_meow.wav` | any | A domestic cat meowing softly once, friendly, indoors, close |
| `wind_gust.wav` | autumn, winter | A soft gust of wind through trees, rising and fading away |
| `rain_pass.wav` | autumn, spring | A short light rain shower on a window, starting gently and fading out |
| `thunder_far.wav` | summer, autumn | Very distant soft thunder rumble, calm, no rain |
| `crickets.wav` | summer | Crickets chirping on a warm summer evening, a few seconds |
| `fire_crackle.wav` | autumn, winter | A fireplace crackling softly for a few seconds, cosy |

### 5b. GROUND · general (later)
- [x] Circadian day curve on all lights (white channel), season presets from the booklet (Summer 6500 K … Winter 4000 K)
- [x] "Day in ~8 min" demo mode + season switch for the defence (web page: Real / 8 min / 2 min)
- [x] Soundscape beds (rain, wind, crickets, fire, room tone) — placeholders in code; real files go to `host\stems\ground\<name>.wav`
- [~] Generate the ground beds with ElevenLabs too — replaced by the real VR recordings (rain, birds, crickets, wind, winter, room tone); only `fire` is a placeholder

### 5c. TOP · moment (polish)
- [x] Recording feedback (see 5a F), smoother presence
- [x] Scenario 2 · Spring Cleaning (passive): winter → birds + rain → warming light (a tap = faster) → Miso → "Rewind?" (tap = the last jam returns) → room switches to spring. Tested silently ✓
- [x] Scenario 3 · I Miss You, Sis: "Postcard from Earth" button / MQTT → table breathes teal → tap = open → warm light + rain + Lena's voice → rain travels to the room speaker → cosy screen flicker + invitation chime. Tested silently ✓
- [x] Scenario switch on the web page + visitor hints per moment
- [x] Real sounds from the VR prototype in `host\stems\` (CC0 Freesound + Lena L01): room beds and accents now real; placeholders only for fire, bee, thunder
- [ ] Try S2 and S3 in the room: levels, timing, does the tap work with the real mic (`tap_min_strength`)?

## 6. Open (later)

- [x] Scenarios 2 and 3 built (see 5c); S3 trigger = web page / MQTT `in/postcard` (portable)
- [ ] More nodes: USB audio interface (4 out), 2nd strip, 3rd/4th speaker
- [x] Prepared for Home Assistant + ESPHome + Sendspin (`Plan/Migration_HA.md`): external broker, HA discovery, LD2450 inputs + radar map, room sound as a stream, ESPHome configs (validated), HA Docker stack — **now running on dexy** (phase B below).
- [x] LD2450: **2× HLK-LD2450 from a friend** (+ Gledopto GL-C-015WL, INMP441 mic); the ESP32 DevKit becomes the radar board once the Gledopto drives the wall strip
- [ ] Later per room speaker: ESP32-S3 N16R8 + MAX98357A + speaker (shopping list in `Plan/Migration_HA.md`)
- [ ] Phase A (before the defence): LD2450 presence subnode with ESPHome
- [ ] Phase B (after the defence or a half-day spike): Home Assistant + Music Assistant on dexy, Sendspin speakers — decided: Docker on dexy (option A)
	- [x] 1 Latest host on the Pi (Claude, 01.10 20:22)
	- [x] 2 Docker on dexy (Flo, 01.10)
	- [x] 3 Stack started (HA :8123, Music Assistant :8095, ESPHome Device Builder :6052, Mosquitto :1883), host on Mosquitto, discovery published (Claude, 01.10 20:48)
	- [x] 4 HA onboarding + long-lived token `easteregged-host` in `~/.easteregged_ha_token` (Flo, 01.10)
	- [x] 5a MQTT integration → device "Easter-egged room" with 19 entities, round trip tested (HA button → host accent) (01.10 21:19)
	- [x] 5b Music Assistant integration in HA (Flo, 01.10). Foreign players (Pioneer, LG) stay enabled for now (Flo) — never used by the prototype
	- [~] 6 Room stream: `/room.wav` works (browser test via `/static/listen.html`, Flo heard it); for Music Assistant → MP3/FLAC (Copilot C2, merge tonight), then test on MA's web player
	- [x] C3 Test suite (Copilot) — run by Claude 01.10: 8 passed, 1 skipped (no ffmpeg on the laptop), 1 xfail (test expects 6500 K to be bluish — it's daylight white; fix the test)
	- [x] C1 HA entity bridge (Copilot) — merge into main.py / room.toml / README tonight
	- [x] C2 Room stream as FLAC/MP3 (Copilot) — merge tonight; Pi has ffmpeg
	- [ ] Merge C1–C3 (Claude, tonight: `Plan/Plan_Interface_v2.md` task 5)
	- [x] 8 LD2450 (2×, from a friend)
	- [ ] 9 Sendspin speaker parts (Flo, later)

---

## 7. Presentation setup (defence 21.10) — three subnodes, named by level

Simple by design: per unit one battery, one LED data wire, everything else plugs in. Booklet pages 49–53 (`Design Dokuz/Exports/SVG/Filled/`), sketch `Plan/Sketch_Presentation_Setup_2026-10-05.jpg`. Details + undo steps: `Setup_Log/Log.md` (05.10).

| Subnode | Controller | Light | Sound / sensing | State 05.10 evening |
|---|---|---|---|---|
| **TOP** · spotlight | ESP32 DevKit, WLED 0.15.1 + own LD2450 usermod (`wled/`), .170 `easteregged-top` | ring light, 77 LEDs (GPIO4) | LD2450 radar (TX → GPIO16), MQTT presence + x/y | ✓ running |
| **ACCENT** · table | Pi 5 "dexy" (host) | 89-LED strip under the table, straight on dexy (SPI) | USB mic, USB speaker (moment + accents) | strip shorted while rewiring → measure first; SPI1 sudo step open |
| **GROUND** · wall | Pi 3B "kellerkind" | 60-LED strip (circadian) | Marsboy on AUX (soundscape) | strip tested ✓; kellerkind not reachable on the network |

**Done 05.10**
- [x] TOP subnode: ESP32 DevKit flashed with WLED + radar usermod (Gledopto removed); MQTT double-connect bug patched
- [x] Radar live in the host (ultrasonic sensor switched off, switchable via `~/easteregged/use_ultrasonic`)
- [x] Ghost filter (1 s confirm, 40 cm merge) + proximity light (off → soft → bright as you come closer), `[light.proximity]`
- [x] Radar page in the web interface (`#radar`, raw dots + counted people)
- [x] One level per spot (`level = ground | accent | top`); spotlight = the scenario's lamp (sunrise, tap flashes, listening glow, beat); fixed: half the jam layers played silently
- [x] Table strip tested + counted (89); wall strip repaired (solder joint) + counted (60)
- [x] SPI output for strips on a Pi (`kind = "spi"`, software current cap) — written + tested, not deployed

**Next**
- [ ] 89-LED strip: measure +5V–GND (several kΩ = ok), check the first pads; Joy-IT ESP8266 is dead (smoke)
- [ ] dexy (sudo): `sudo systemctl disable --now dexy` + `dtoverlay=spi1-1cs` + reboot → Claude deploys `spi_bus = 1`
- [ ] Wire the table strip to dexy: pin 6 GND, pin 38 DIN (100–1000 Ω), pin 2 5V last; photo first
- [ ] kellerkind on the network (LAN cable), SSH key, then the wall: LED receiver for the 60-LED strip, Marsboy, room screen
- [ ] Spotlight: LED count of the ring (still 77), mount radar rigidly under the ring, calibrate proximity numbers + spot `pos`
- [ ] Code cleanup: core / plugins / subnode, "middle" → "accent" everywhere (open questions: sound routing, JBL)
- [ ] Buy: folding table, 20,000 mAh PD bank, travel router, short USB cables, 3.5 mm cable, resistors 330 Ω, filament
- [ ] Venue mode, rehearsal, film

## Prompts

- New chat: `Prompts/NewChat_Prompt.md`
- Tonight (interface v2): `Prompts/Night_2026-10-01_Interface_v2.md`
- GitHub Copilot (HA tasks C1–C3, done 01.10): `Prompts/Copilot_HA_Tasks.md`, results `Prompts/Copilot_Integration_Notes.md`, log `Setup_Log/Log_Copilot.md`
