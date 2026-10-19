#!/bin/sh
# Build WLED 0.15.1 for a subnode: top_ld2450 (TOP spotlight, ESP32 DevKit V1 + LD2450, default) or
# table_c3 / table_c3_debug (table unit, ESP32-C3 SuperMini + INMP441; run the C3 build from PowerShell:
# Git Bash/MSYS breaks Espressif's tool installer).
# Usage: sh build.sh <short dir, e.g. C:/Users/Florian/.wb> [env]  (long paths break the Windows build)
# Output: <dir>/src/.pio/build/<env>/firmware.bin
#   first time: USB (esptool, see Plan/Guide_Presentation_Setup.md); later: WLED → Config → Security & Updates → OTA
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; W="$1"; ENV="${2:-top_ld2450}"; mkdir -p "$W"; cd "$W"
[ -d src ] || git -c core.longpaths=true clone --depth 1 --branch v0.15.1 https://github.com/wled/WLED.git src
[ -d venv ] || { python -m venv venv; ./venv/Scripts/pip install -q platformio esptool; }
mkdir -p src/usermods/LD2450_easteregged
cp "$HERE/usermod_ld2450/usermod_ld2450.h" src/usermods/LD2450_easteregged/
mkdir -p src/usermods/AudioStream_easteregged
cp "$HERE/usermod_audio_stream/usermod_audio_stream.h" src/usermods/AudioStream_easteregged/
cp "$HERE/platformio_override.ini" src/
python "$HERE/patch_wled.py" src
cd src && ../venv/Scripts/pio run -e "$ENV"
