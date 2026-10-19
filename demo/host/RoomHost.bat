@echo off
rem Room Host on/off: starts the host in its own log window, or stops it if it is running (see RoomHost.ps1).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0RoomHost.ps1"
