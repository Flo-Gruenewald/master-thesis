@echo off
rem Easter-egged host: double-click or run "run.bat". Ctrl+C stops it.
cd /d "%~dp0"
python -c "import numpy, scipy, sounddevice, soundfile, aiohttp, paho.mqtt, amqtt, zeroconf" 2>nul || python -m pip install -r requirements.txt
python main.py %*
pause
