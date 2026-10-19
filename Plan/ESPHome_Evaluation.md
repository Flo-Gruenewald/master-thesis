# ESPHome: evaluation for the physical prototype

> **Status 01.10 (late):** decided — hybrid with Home Assistant in Docker on dexy (running). 2× LD2450 available (from a friend); the Gledopto takes over the wall strip so the ESP32 DevKit becomes the radar board. Configs: `../esphome/`.

01.10.2026. Question: would ESPHome help our room (Pi host + WLED light subnodes + presence sensor), how would we use it, and what would it cost?

## What ESPHome is

Firmware for ESP8266/ESP32 that you **configure in YAML instead of programming**: you list the sensors/outputs, ESPHome compiles and flashes the firmware (USB once, then over Wi-Fi). Hundreds of ready drivers (ultrasonic, mmWave presence, buttons, LEDs, I2S audio …), built-in filters, OTA updates, a Wi-Fi fallback hotspot, and **native MQTT** — it runs without Home Assistant.

## Fit with our project, part by part

| Part | Today | With ESPHome | Useful? |
|---|---|---|---|
| **Light subnodes** | WLED on ESP8266/ESP32; the host streams frames over **DDP** (40 fps); WLED has its own phone UI | ESPHome lights can take E1.31 or WLED's UDP protocol, but **no DDP** (open feature request); no WLED UI | **No.** WLED is the better tool for addressable light. Keep it. |
| **Presence subnode** | HC-SR04 on the Pi's GPIO, `pi/presence.py` | an ESP (+ power bank) anywhere in the room publishes the distance itself; median filter on the device | **Yes, moderately**: frees the Pi's position, fits "works in any environment" and the subnode model. Host needs **no change**. |
| **Better presence (mmWave)** | ultrasonic: one narrow beam, noisy echoes, misses people who stand still or aside → "presence feels odd" | **LD2410** mmWave sensor (~€5): detects moving *and still* people, whole area, with distance. ESPHome has a ready driver | **Yes, the strongest case.** This is where ESPHome pays off: a better sensor with a 30-line config, no driver code. |
| **Room speaker** | JBL via Bluetooth on the Pi (planned) | ESP32 + I2S amp (MAX98357A, ~€5) + small speaker, `media_player` plays files from the Pi on MQTT command | **Not now.** Works for ambient accents (latency ~0.5–1 s is fine), but multi-speaker sync is still in development in ESPHome; the JBL is zero effort. Option for 3–4 corner speakers later. |
| **Extra inputs** (a "message" object, a button) | none (dropped for "any environment") | trivial in YAML | Only if a scenario needs one. |

## Strengths vs. weaknesses for us

**Strengths:** no code for sensors (YAML), large driver library (LD2410!), on-device filters, OTA updates over Wi-Fi, fallback hotspot when the Wi-Fi changes (exhibition), configs live as text files in the project → reproducible and documentable in the thesis.

**Weaknesses:** first build downloads a toolchain (~1 GB, 5–10 min); defaults assume Home Assistant (if `api:` stays in the config without Home Assistant, the ESP **reboots every 15 min** → remove it); no DDP for light; audio sync immature; one more tool to learn 3 weeks before the defence.

## Effort

| Step | Effort | Hardware |
|---|---|---|
| Install ESPHome on the laptop (`pip install esphome`) or use the browser flasher (web.esphome.io) | 15 min (+ first build 10 min) | — |
| **A. Ultrasonic presence on an ESP** (same HC-SR04, same divider) | **1–2 h** incl. wiring | 1 ESP (we have none spare: ESP8266 = table, ESP32 = wall) → buy one, ~€8 |
| **B. mmWave presence (LD2410C) on an ESP** | **2–3 h** incl. tuning the gates/sensitivity | ESP32 ~€8 + LD2410C ~€5 |
| Host change for B (accept `ON`/`OFF` from a binary sensor) | 10 min (Claude) | — |
| C. ESP audio node | 1 day | ESP32 + MAX98357A + speaker ~€15 |

## Recommendation

1. **Keep WLED** for all light subnodes.
2. **Don't move the HC-SR04 to an ESP just for the sake of it** — it works on the Pi.
3. **If presence keeps feeling odd after the room test, switch to an ESP32 + LD2410C with ESPHome (option B).** That fixes the actual weakness (still people, narrow beam), makes the sensor a portable subnode, and costs ~€13 and an afternoon. Order the parts now so the option is open (delivery takes days).
4. Audio: JBL first; an ESPHome audio node only if we want more than two speaker positions after the defence.

## Ready configs (for when we do it)

Both publish exactly what the host already understands (see `host\README.md`), with the last will for the "Presence" status on the web page. Put Wi-Fi credentials in `secrets.yaml` (not in the thesis folder).

**A. HC-SR04 on an ESP32** (TRIG → GPIO5, ECHO → 1 kΩ → GPIO18, 2 kΩ GPIO18 → GND, VCC → 5V/VIN, GND → GND)

```yaml
esphome:
  name: presence-1
esp32:
  board: esp32dev
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  ap: {}                      # fallback hotspot if the Wi-Fi is unknown
captive_portal:
ota:
  - platform: esphome
logger:
# no "api:" → otherwise it reboots every 15 min without Home Assistant
mqtt:
  broker: 192.168.178.158     # the Pi host
  discovery: false
  topic_prefix: easteregged/presence-1
  birth_message: {topic: easteregged/status/presence, payload: online, retain: true}
  will_message: {topic: easteregged/status/presence, payload: offline, retain: true}
sensor:
  - platform: ultrasonic
    trigger_pin: GPIO5
    echo_pin: GPIO18
    name: distance
    update_interval: 200ms
    timeout: 4m
    unit_of_measurement: cm
    accuracy_decimals: 0
    filters:
      - multiply: 100          # metres → cm
      - median: {window_size: 5, send_every: 1}
    state_topic: easteregged/in/presence/distance
```

**B. LD2410C on an ESP32** (LD2410 TX → GPIO16 (RX2), RX → GPIO17 (TX2), VCC → 5V, GND → GND)

```yaml
# … same esphome / esp32 / wifi / captive_portal / ota / logger / mqtt blocks as A …
uart:
  tx_pin: GPIO17
  rx_pin: GPIO16
  baud_rate: 256000
  parity: NONE
  stop_bits: 1
ld2410:
binary_sensor:
  - platform: ld2410
    has_target:
      name: present
      state_topic: easteregged/in/presence/state     # ON / OFF
sensor:
  - platform: ld2410
    detection_distance:
      name: distance
      state_topic: easteregged/in/presence/distance  # cm
```

Host change needed for B: accept `ON`/`OFF` on `in/presence/state` (Claude, 10 min). The sensitivity per distance gate is tuned in the LD2410's own app (Bluetooth) or via ESPHome numbers.

## Sources

- ESPHome MQTT (MQTT without Home Assistant, the 15-min reboot caveat, topics, birth/will): https://esphome.io/components/mqtt/
- Ultrasonic sensor: https://esphome.io/components/sensor/ultrasonic/
- LD2410 (still + moving targets, UART 256000): https://esphome.io/components/sensor/ld2410/
- ESPHome lights (E1.31, WLED UDP effect): https://esphome.io/components/light/index.html
- DDP for ESPHome lights is only a feature request: https://github.com/esphome/feature-requests/issues/1486
- Speaker media player (ESP32, ESP-IDF): https://esphome.io/components/media_player/speaker/
- Multi-speaker sync still requested: https://github.com/esphome/home-assistant-voice-pe/issues/322
- ESPHome vs WLED: https://led-matrix.com/comparisons/wled-vs-espxxx/

---

## Update 01.10 (night): Home Assistant, Sendspin, LD2450

Flo's points: expanding with more audio boxes (even Bluetooth) and more components could be much easier on an established platform (Home Assistant + ESPHome) than with our own software.

### What each piece would bring

| Piece | What it is | For us |
|---|---|---|
| **Home Assistant (HA)** | home-automation platform: discovers ESPHome devices, dashboards, automations, MQTT broker (Mosquitto add-on) | **Device platform**: adding sensors/speakers becomes "flash, it appears, use it". Not suited for TOP: automations react in ~0.1–1 s, no audio processing, no 40 fps DDP light — the live jam must stay in our host. |
| **Music Assistant (MA)** | HA add-on / server for playing audio to many players, with **sync groups** | Plays Ground/Middle sounds on many speakers in sync. Sync only within one ecosystem (Sendspin with Sendspin, AirPlay with AirPlay …). |
| **Sendspin** | new open protocol (Open Home Foundation) for **sample-accurate multi-room audio**; clients: ESPHome on ESP32, Linux on a Pi; native in MA; release candidate 1, near 1.0 | **The right answer for "more speakers"**: each speaker = ESP32 + I2S amp (~€15) running ESPHome's Sendspin client, all in sync. Still young (RC). |
| **Bluetooth boxes** | — | **Not easier in HA**: HA doesn't stream to Bluetooth speakers natively (needs an add-on/PulseAudio), and Bluetooth's variable delay makes them **impossible to keep in sync** with other speakers. Fine as *one* ambient speaker (our JBL plan), not as a multi-speaker system. |
| **LD2450** | 24 GHz radar, tracks **up to 3 people with X/Y position** (±3 m wide, 6 m deep), speed, 3 zones; ESPHome driver | **Better than the LD2410 for us**: not just "someone is here" but *where* and *how many*. Lets the host pick the spot (table vs. wall), let the S3 rain follow a person, have a 2nd person "join". To verify in the room: users report it holds very still people less reliably than the LD2410. |

### Architecture this suggests (hybrid, not a replacement)

```
 Experience layer   our host (Pi): scenarios, TOP live loop + mic, light rendering (DDP), room program logic
        │  MQTT (one broker: HA's Mosquitto instead of the embedded one)
 Device layer       Home Assistant + ESPHome + Music Assistant/Sendspin
        ├ ESPHome sensors (LD2450 presence/position, buttons, …)
        ├ Sendspin speakers (ESP32 + amp) in sync for GROUND/MIDDLE sound
        └ dashboards, device health, OTA updates
 Light              WLED subnodes (stay as they are, the host streams DDP)
```

For the thesis this is also a stronger story: a habitat would run on a standard automation layer; "the host" is the character layer on top that decides *when and how* the room offers something.

### Effort

| Step | Effort | Parts |
|---|---|---|
| LD2450 on an ESP32 with ESPHome, publishing to our broker (no HA needed) | 2–3 h (Flo: wiring/flash) | ESP32 ~€8 + LD2450 ~€8 |
| Host: use X/Y → nearest spot, people count, "follow" | 1–2 h (Claude) | — |
| HA + Mosquitto + ESPHome + MA in Docker on dexy (beside the host) | 2–4 h; Docker install needs `sudo` (Flo) | — |
| Host on HA's broker (configurable instead of embedded) | 1 h (Claude) | — |
| First Sendspin speaker (ESP32 + MAX98357A + speaker), then each further one | 2 h, then ~20 min each | ~€15 per speaker |
| Host sends Ground/Middle sounds via MA/Sendspin | ½–1 day (Claude) | — |
| Replacing the host with HA entirely | not feasible: loses the live jam and beat-synced light | — |

### Recommendation

1. **Before the defence (21.10): order 1–2 LD2450 + ESP32 now** and add the LD2450 as an ESPHome subnode on our existing MQTT (no HA yet). Highest value per hour: fixes presence and adds *where/how many*.
2. **Before the defence, optional (only if the room test is done): a half-day HA spike** on dexy in Docker, to see the device layer working, for a slide.
3. **After the defence: HA + Music Assistant + Sendspin** as the device and audio layer, with Sendspin ESP32 speakers instead of Bluetooth boxes. Present it in the defence as the next iteration.
4. **Now (Claude, small):** make the broker configurable (embedded or external) and accept ESPHome's `ON`/`OFF` and X/Y topics, so either path plugs in without rework.

Sources (update):
- Sendspin in Music Assistant: https://github.com/orgs/music-assistant/discussions/4200 · provider README: https://github.com/music-assistant/server/blob/dev/music_assistant/providers/sendspin/README.md · near 1.0: https://www.matteralpha.com/industry-news/sendspin-1-0-airplay-sonos-proprietary-speakers · DIY receiver: https://www.cnx-software.com/2026/04/21/diy-sendspin-audio-receiver-supports-multi-room-audio-synchronization-integrates-with-home-assistant/
- Music Assistant groups / sync limits: https://www.music-assistant.io/faq/groups/ · players: https://www.music-assistant.io/faq/stream-to/
- Bluetooth speakers in HA (add-on needed): https://github.com/scyto/ha-bluetooth-audio-manager · https://community.home-assistant.io/t/wth-pairing-bluetooth-audio-devices-in-the-ui/805012
- LD2450 in ESPHome: https://esphome.io/components/sensor/ld2450/
