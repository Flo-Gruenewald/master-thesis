# Guide · Presentation setup (three units)

Hands-on steps to turn the bench prototype into the defence setup. Tick as you go. **Flo** = your hands, **Claude** = I do it over SSH/USB, **sudo** = you type it (needs your password).
Setup and reasons: `MorningJam_Progress.md` §7, booklet pp. 49–53. Change history: `Setup_Log/Log.md`.

> **State 05.10 evening:** C (spotlight) is done — differently than planned: WLED + an own LD2450 usermod on the ESP32 DevKit (no ESPHome, no sACN), radar on GPIO16. B: SPI output written; strip wiring to dexy caused a short (see Log.md 18:40). A: kellerkind not reachable yet. Live checklist: `MorningJam_Progress.md` §7.

Order: **A Wall (Pi 3B)** → **B Table (Pi 5)** → **C Spotlight (ESP32)** → **D Room + venue**. Network for now: the home FritzBox (2.4 GHz); the travel router comes in D.

---

## A · Wall unit — Raspberry Pi 3B

**A1 · Fresh SD card (Flo, 15 min)**
- [x] Install **Raspberry Pi Imager** from raspberrypi.com/software on the PC.
- [x] Device **Raspberry Pi 3** · OS **Raspberry Pi OS (64-bit)** — the version *with desktop* (needed for the room screen) · storage = the Pi 3B's SD card (everything on it is erased).
- [x] *Edit settings* → General: hostname **`wall`**, user **`pi`** + a password of your choice, Wi-Fi = the FritzBox network (+ password), country DE, time zone Europe/Berlin.
- [x] Services: **Enable SSH → public-key only**, paste the laptop key (Claude shows it: `~/.ssh/id_ed25519.pub`).
- [x] Write, put the card in the Pi 3B.

**A2 · First boot (Flo, 3 min)**
- [x] Power the Pi 3B (micro-USB, 5 V ≥ 2.5 A). Nothing else plugged in. Wait ~3 min (first boot resizes the card).
- [x] Tell Claude → **Claude** finds it (`wall.local` / FritzBox), logs in, read-only checks (model, OS, Wi-Fi, temperature, audio devices).
  - 05.10: the Pi 3B is named **kellerkind** (existing install); the FritzBox lists it at .59 but it does not answer → LAN cable next; SSH key still to install.
- [x] FritzBox: device `wall` → *Always assign this IPv4 address*. IP: ________

**A3 · Enable SPI (sudo, 1 min)** — Claude gives the exact lines (raspi-config SPI on, user `pi` into the `spi`/`gpio` groups, reboot).

**A4 · Wire the wall LED strip (Flo, 15 min) — Pi off, power bank unplugged**
```
 Power bank A, port 1 ─USB─► USB→wires adapter
     VCC ──► strip 5V            (+ 1000 µF across 5V/GND at the strip, stripe = GND)
     GND ──► strip GND ──┐
 Pi 3B pin 20 (GND) ─────┘       common ground
 Pi 3B pin 19 (GPIO10) ──[330 Ω]──► strip DIN   (input end: arrows point away)
 Power bank A, port 2 ─USB─► Pi 3B micro-USB
```
- Pin 1 = square pad; pins 19 and 20 sit next to each other, 10th pair from the SD-card end (19 inner row, 20 outer row).
- [ ] Photo of the wiring to Claude before powering on.

**A5 · Light test (Claude)** — `led_node.py` installed, test pattern, current limit set; host gets `[[wled]] id = "wall"` → the Pi 3B. You confirm the colours.

**A6 · Marsboy (Flo, 2 min)**
- [ ] 3.5 mm cable: Pi 3B jack → Marsboy **AUX**. Marsboy on, AUX mode, volume ~70 %.
- [ ] **Claude** plays a test tone and an accent; you check: loud enough? hiss? does it stay on during silence (wait 15 min)?

**A7 · Room screen (Flo + Claude)**
- [ ] Which screen? (size, HDMI, power: USB or mains) → tell Claude.
- [ ] HDMI to the Pi 3B; **Claude** sets up the kiosk browser with the Home view.

---

## B · Table unit — Raspberry Pi 5 "dexy"

- [x] B1 done 05.10: the old Dexy code drives LEDs over SPI (spidev0.0, 2.4 MHz, 3-bit encoding) — same method now in `core/light.py` (`kind = "spi"`).

**B1 · Power on dexy (Flo)** → tell Claude. **Claude** reads the old Dexy LED code (it used GPIO10) and checks SPI — read-only.

**B2 · sudo (Flo, 2 min)** — Claude gives the lines: stop and disable the old `dexy` service (it drives GPIO10 too), enable SPI, groups, reboot.

**B3 · Wire the table ring (Flo) — Pi off** — new pins (05.10): **pin 2 = 5V, pin 6 = GND, pin 38 = DIN (GPIO20, SPI1)**; needs `dtoverlay=spi1-1cs`. 5V last.
- Same as A4, with power bank B's USB-A port for the LEDs and pin 19/20 on the Pi 5. The Pi 5 gets USB-C PD.
- [ ] Photo to Claude.

**B4 · Claude** — `led_node.py` on dexy, host: table ring = Accent only, USB speaker = Moment, test.

**B5 · JBL (optional, later)** — PipeWire install (sudo, Flo), pairing (Claude).

---

## C · Spotlight unit — ESP32 DevKit (ESPHome: LED ring + radar)

Only after A5 works (the DevKit still runs the wall strip with WLED until then; WLED gets replaced).

- [x] C done 05.10: ESP32 DevKit = WLED 0.15.1 + LD2450 usermod (`wled/build.sh`), .170 `easteregged-top`, LEDs GPIO4, radar TX → GPIO16 (RX not needed), MQTT → dexy; radar live, proximity light running.
- [ ] C6 (mount + calibrate) still open.

**C1 · Radar firmware (Flo, 5 min)** — guide `Guide_Hardware_1_Presence.md` step 2 (HLKRadarTool app, V2.02.23090617 or newer).

**C2 · Wi-Fi secrets (Flo, 2 min)** — copy `esphome/secrets.example.yaml` → `secrets.yaml`, fill in Wi-Fi name + password, MQTT fields empty. Never share it.

**C3 · Cone LEDs (Flo)** — decide the LED piece for the cone (e.g. 12–24 LEDs cut from a spare SK6812 strip, cut at the copper pads) → tell Claude the count.

**C4 · Wiring (Flo) — USB unplugged**
```
 LD2450 5V ──► ESP32 VIN      LD2450 GND ──► ESP32 GND
 LD2450 TX ──► GPIO16         LD2450 RX  ◄── GPIO17
 Small power bank ─USB─► USB→wires: VCC ──► LED 5V + ESP32 VIN, GND ──► LED GND + ESP32 GND
 ESP32 GPIO4 (D4) ──[330 Ω]──► LED DIN    (+ 1000 µF at the LEDs)
```
- Never plug the ESP32 into the PC while it gets power on VIN.

**C5 · Claude** — config (board esp32dev, LD2450 + LED ring + sACN), flash over USB **with your OK** (hold BOOT), check MQTT presence + x/y, host sends the spotlight frames.

**C6 · Mount** — cone 1.5–2 m high, aimed at the table, radar with a clear view (not behind the foil). Sit at the table → Claude writes the spot positions.

---

## D · Room + venue

- [ ] Buy/arrive: folding table, 20,000 mAh PD bank, travel router, short USB cables, 3.5 mm cable, foil, filament, (74AHCT125 spare).
- [ ] Travel router: all three units + laptop join it; Claude adds a "venue" config.
- [ ] Full run: three scenarios, 30 min on batteries, shut-down routine.
- [ ] Film it for the booklet / defence.

## Troubleshooting

| Symptom | Likely cause → fix |
|---|---|
| Pi 3B not found after 5 min | wrong Wi-Fi password or 5 GHz-only network → re-write the card |
| LEDs flicker / wrong colours | no common ground, missing 330 Ω, long data wire → add a 74AHCT125 |
| LEDs dark | data on the output end of the strip, or SPI not enabled |
| Marsboy silent | not in AUX mode; Claude checks the Pi's audio output |
| Pi 5 audio drops | USB limited to 600 mA on a power bank → mains PSU for the test |
| ESP32 upload fails | hold BOOT; data USB cable, not charge-only |
