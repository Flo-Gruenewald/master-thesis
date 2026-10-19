# Hardware guide 1 · Presence sensor (LD2450 radar)

Goal: the room knows **if** someone is there, **how many** (up to 3) and **where** (x/y in mm), instead of one distance from the ultrasonic HC-SR04. The radar runs on an ESP32 with ESPHome and talks to the host over MQTT (Mosquitto on dexy) — the host is already prepared for it.

**Current hardware correction (05.10):** Dexy (Pi 5) remains the host. The online Gledopto at `192.168.178.171` is currently configured by Dexy as the **TOP spotlight** (dim warm-rust idle, bright warm-rust during every scenario), not a wall/MIDDLE accent. Kellerkind is the separate Pi 3B wall unit and is currently offline. The steps below describe the planned ESP32/radar hardware migration; do not treat the Gledopto as Kellerkind.

Time: about 1 h (plus 15 min for step 1). Steps marked **Claude** I can do while you're at the hardware; just say so.

---

## 0 · What you need

- [x] 1× **HLK-LD2450** radar (you have 2 from your friend) + its little 4-wire cable
- [x] 1× **ESP32 DevKit V1** (the one now running the wall strip — see step 1)
- [x] 4× female–female jumper wires (if the radar's cable has no plugs that fit the ESP32 pins)
- [x] USB-C cable (data, not charge-only) to the laptop
- [x] Phone with the **HLKRadarTool** app (iOS / Android, free)
- [x] For step 1: the **Gledopto GL-C-015WL** + a small screwdriver
- [x] Tape measure (for step 8)

---

## 1 · Free the ESP32: the wall strip moves to the Gledopto (15 min)

The ESP32 DevKit currently runs WLED for the wall strip. ESPHome will replace WLED on it, so the wall strip first gets its own controller — the Gledopto is made for exactly this (WLED is pre-installed, it has a level shifter and screw terminals).

1. [x] Unplug the power bank from the wall strip.
2. [x] Take the strip's three wires off the ESP32 (5V, GND, data via the 330 Ω resistor).
3. [ ] Screw them into the Gledopto's output terminal: **V+** ← strip 5V, **GND** ← strip GND, **DATA/DIN** ← strip data. (The 330 Ω resistor and the 1000 µF capacitor are not needed with the Gledopto; the capacitor across 5V/GND at the strip doesn't hurt.)
4. [ ] Power the Gledopto from the power bank (its input takes 5–24 V; 5 V is fine).
5. [ ] On the phone or laptop join the Wi-Fi **`WLED-AP`** (password `wled1234`) → a page opens (or go to `4.3.2.1`) → **WiFi Setup**: your home Wi-Fi + password, **mDNS name `easter-egged-wall`** → Save. The Gledopto restarts in your network.
6. [ ] In the FritzBox: find the new device, note its IP, tick **"Always assign this IPv4 address"**.
7. [ ] Open the Gledopto's WLED page (its IP) → **Config → LED Preferences**: LED type **SK6812 RGBW**, color order **GRB**, length **77**, keep the **data pin WLED already shows** (Gledopto presets it). Max current 2500 mA. Save.
8. [ ] **Claude:** I set the new IP in `room.toml` (`[[wled]] id = "wall"`), restart the host, and check the strip on the Node page.

✔ The wall strip lights again, now from the Gledopto. The ESP32 DevKit is free.

---

## 2 · Check the radar firmware (5 min)

The ESPHome driver needs radar firmware **V2.02.23090617 or newer**.

1. [ ] Power the radar for a moment: plug the ESP32 into USB and connect only **5V → VIN** and **GND → GND** (step 3 shows the pins).
2. [ ] Open **HLKRadarTool**, allow Bluetooth → the radar shows up as `HLK-LD2450_xxxx` → connect.
3. [ ] Read the firmware version (device info / "About"). Older than V2.02.23090617 → update it in the app (keep the radar powered during the update).
4. [ ] Optional sanity check: walk in front of it — the app shows your dot moving.

---

## 3 · Wire the radar to the ESP32 (10 min, no soldering)

The radar's four pins are labelled on its board (usually **5V · GND · TX · RX**; check the silkscreen).

```
 HLK-LD2450                 ESP32 DevKit V1 (30-pin)
 ──────────                 ────────────────────────
 5V   ───────────────────▶  VIN   (5 V from USB)
 GND  ───────────────────▶  GND
 TX   ───────────────────▶  GPIO16  (labelled RX2 / D16)
 RX   ◀───────────────────  GPIO17  (labelled TX2 / D17)
```

- [ ] TX goes to RX and RX to TX (crossed) — that's the most common mistake.
- [ ] Nothing else: the radar's 3.3 V signals suit the ESP32 directly, no resistors.
- [ ] Power comes from the laptop USB now, later from a USB charger at the mounting spot.

---

## 4 · Wi-Fi secrets for ESPHome (2 min — you)

The sensor needs your Wi-Fi password; that stays with you.

1. [ ] In `Prototype\Demo\esphome\` copy `secrets.example.yaml` → **`secrets.yaml`**.
2. [ ] Fill in `wifi_ssid` and `wifi_password` (2.4 GHz network — the ESP32 has no 5 GHz). Leave `mqtt_username` / `mqtt_password` empty (Mosquitto on dexy needs no login).
3. [ ] Don't share or paste this file anywhere. (There's also one in `~/ha/esphome/` on dexy; same rule.)

---

## 5 · Flash ESPHome onto the ESP32 (10 min — **Claude** can do it)

Plug the ESP32 into the laptop. This **replaces WLED** on the board (intended).

Easiest: tell me "flash it" — I install ESPHome on the laptop and run the config.
By hand (PowerShell, in `Prototype\Demo\esphome`):

```bash
python -m venv .venv
```
```bash
.venv\Scripts\pip install esphome
```
```bash
.venv\Scripts\esphome run presence_ld2450.yaml
```

- Choose the USB/COM port when asked (the CP2102 port, COM4 last time).
- "Failed to connect"? **Hold the BOOT button** on the ESP32 until the upload starts.
- The first build takes a few minutes. Every later update goes over Wi-Fi.

✔ The log ends with the ESP32 on your Wi-Fi as **`presence-1`**, MQTT connected, and lines like `Target-1 X`, `Presence: ON` when you move.

---

## 6 · Check that the room hears it (5 min)

1. [ ] **Claude** (or you on dexy): watch the radar's messages:
   ```bash
   ssh pi@192.168.178.158 "docker exec mosquitto mosquitto_sub -t 'easteregged/in/presence/#' -v"
   ```
   You should see `in/presence/state ON/OFF`, `in/presence/count`, `in/presence/target/1/x …` while you move. Ctrl+C to stop.
2. [ ] Open `http://192.168.178.158:8080/#scenarios` → the bar at the bottom says **"Someone is here"** when you're in front of the radar and **"Nobody here"** a few seconds after you leave.

---

## 7 · Switch the host from ultrasonic to radar (**Claude**, 2 min)

Both sensors would otherwise send presence at the same time.

- [ ] **Claude:** stop `presence.py` in `run.sh` (HC-SR04) and restart the host. You can then unplug the HC-SR04 from the Pi (keep it as a spare).
- [ ] **Home Assistant** (optional now): Settings → Devices & services → "ESPHome: presence-1 discovered" → **Configure** → add. Presence, People and the target X/Y then exist in HA too.

---

## 8 · Mount and calibrate (15 min)

**Where:**
- [ ] On a wall facing the table, **1.5–2 m high**, the radar's face vertical or tilted slightly down. It sees up to ~6 m and ±60° to each side.
- [ ] Nothing metal in front of it (plastic or fabric is fine); avoid pointing it at fans, curtains or plants that move (radar sees motion).
- [ ] USB charger close by for the ESP32 (5 V, 1 A is plenty).

**Teach the room where its spots are** (the radar measures from its own position: **x** = left/right, **y** = straight out, in mm):
1. [ ] Sit at the table. Read `Target-1 X` and `Target-1 Y` (ESPHome log, Home Assistant, or tell me and I read MQTT).
2. [ ] Stand at the wall strip / second spot and read them again.
3. [ ] **Claude:** I put both into `room.toml` (`pos = [x, y]` for the table and wall spots) and restart. From then on the host knows which spot each person is nearest to.

---

## 9 · Done when

- [ ] The wall strip runs on the Gledopto, ESP32 runs ESPHome as `presence-1`
- [ ] "Someone is here" / "Nobody here" follows you within a few seconds
- [ ] With **Presence starts** on (Scenarios), sitting down starts the selected scenario
- [ ] `presence.py` stopped, HC-SR04 unplugged
- [ ] Table and wall `pos` in `room.toml`
- [ ] **Claude:** `Setup_Reference.md` (presence section, devices table, IPs) and `Log.md` updated

## If something's off

| Symptom | Likely cause → fix |
|---|---|
| No COM port when plugging in | charge-only cable, or missing driver (CP2102: Silicon Labs; CH340: WCH) |
| Upload "Failed to connect" | hold **BOOT** while it starts uploading |
| ESPHome log: no radar data / UART errors | TX/RX not crossed, or radar firmware too old (step 2) |
| Presence flickers ON/OFF | something moving in view (fan, curtain); turn or tilt the radar |
| ESP32 not on Wi-Fi | 5 GHz-only network or typo in `secrets.yaml`; it then opens its own hotspot **`presence-1`** to fix it |
| Page says "Nobody here" but MQTT shows ON | `presence.py` still running (step 7), or the host wasn't restarted |
| Wall strip dark after step 1 | wrong LED type/order/length in the Gledopto's WLED, or IP not updated in `room.toml` |

Next guide: **2 · Sound** (room speaker separate from the table speaker).
