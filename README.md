# Breaking the Monotony Spiral on a Mars Mission: co-sense

MSc thesis, Product & Service Design, Sapienza University of Rome (Florian Grünewald, 2026).
This repository is the physical demonstrator: one room "node" that turns light,
sound and presence into three scenarios for a long-duration Mars mission crew.

## Folders

| Folder | What it is |
|---|---|
| `host/` | The room host (Python, asyncio): light program, sound engine, radar fusion, the scenarios, the web interface (`host/web/`). Run `python main.py`, open http://localhost:8080. Settings: `room.toml`. |
| `host/scenarios/` | S1 Morning Jam (table, monotony → moments of connection), S2 Spring Cleaning (corridor, transition), S3 I Miss You, Sis (sleeping pod, connection to home). |
| `wled/` | WLED 0.15 usermods for the ESP32 light units (LD2450 radar, audio stream) and the PlatformIO overrides. |
| `postcard_fw/` | Firmware of the tactile postcard (ESP32, touch + vibration, MQTT). |
| `esphome/` | Earlier ESPHome configs for the presence sensor (`secrets.example.yaml` shows the needed keys). |
| `pi/` | Earlier Raspberry Pi setup (the host now runs on a laptop). |
| `Setup_Log/`, `Plan/` | Change log and planning notes. |

Not included: sounds and music (licences: see `Sounds/SOURCES.md`), the PP Neue Montreal web fonts (commercial
licence), recorded table loops, Wi-Fi credentials. Without the sounds the host runs but stays silent.
