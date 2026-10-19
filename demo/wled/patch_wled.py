"""Patch a WLED 0.15.1 checkout: register the LD2450 usermod and fix the double MQTT connect.
Usage: python patch_wled.py <WLED src dir>"""
import sys, os
src = sys.argv[1]

p = os.path.join(src, "wled00", "usermods_list.cpp")
s = open(p).read()
if "USERMOD_LD2450" not in s:
    s = s.replace('#ifdef USERMOD_LD2410',
                  '#ifdef USERMOD_LD2450\n#include "../usermods/LD2450_easteregged/usermod_ld2450.h"\n#endif\n\n#ifdef USERMOD_LD2410', 1)
    s = s.replace('  #ifdef USERMOD_LD2410',
                  '  #ifdef USERMOD_LD2450\n  UsermodManager::add(new LD2450Usermod());\n  #endif\n\n  #ifdef USERMOD_LD2410', 1)
    open(p, "w").write(s)

# easteregged mic stream (table unit, 15.10): register AudioStreamUsermod when USERMOD_AUDIO_STREAM is set
p = os.path.join(src, "wled00", "usermods_list.cpp")
s = open(p).read()
if "USERMOD_AUDIO_STREAM" not in s:
    inc = ('#ifdef USERMOD_AUDIO_STREAM\n#include "../usermods/AudioStream_easteregged/usermod_audio_stream.h"\n'
           '#endif\n\n')
    add = '  #ifdef USERMOD_AUDIO_STREAM\n  UsermodManager::add(new AudioStreamUsermod());\n  #endif\n\n'
    s = s.replace("#ifdef USERMOD_LD2410", inc + "#ifdef USERMOD_LD2410", 1)
    s = s.replace("  #ifdef USERMOD_LD2410", add + "  #ifdef USERMOD_LD2410", 1)
    open(p, "w").write(s)

# WLED 0.15.1: initInterfaces() and the main loop both call initMqtt() right after Wi-Fi connects ->
# two sessions with one client id, the broker kicks one and WLED keeps the dead one. Guard: one connect per 10 s.
p = os.path.join(src, "wled00", "mqtt.cpp")
s = open(p).read()
if "lastMqttConnectCall" not in s:
    s = s.replace("  if (mqtt->connected()) return true;\n",
                  "  if (mqtt->connected()) return true;\n"
                  "  static unsigned long lastMqttConnectCall = 0;  // easteregged: no double connect\n"
                  "  if (lastMqttConnectCall && millis() - lastMqttConnectCall < 10000) return true;\n"
                  "  lastMqttConnectCall = millis();\n", 1)
    open(p, "w").write(s)

# ESP32-C3 SuperMini (table unit) on the home mesh "G": most logins failed with AUTH_FAIL (reason 202).
# 1) WLED lowered the TX power only after WiFi.begin() -> the first auth frames went out at 19.5 dBm, distorted by
#    the board's poor antenna match. 2) With several APs under one SSID the ESP joined the first AP found, not the
#    strongest. Fix both before WiFi.begin(); in debug builds also log the disconnect reason.
p = os.path.join(src, "wled00", "wled.cpp")
s = open(p, encoding="utf-8").read()
if "WIFI_CONNECT_AP_BY_SIGNAL" not in s:
    a = "    WiFi.begin(multiWiFi[selectedWiFi].clientSSID, multiWiFi[selectedWiFi].clientPass);"
    assert a in s, "WiFi.begin line not found"
    s = s.replace(a,
                  "#ifdef ARDUINO_ARCH_ESP32\n"
                  "    // easteregged: TX power BEFORE the login (C3 SuperMini antenna), join the strongest AP of a mesh\n"
                  "    if (WiFi.getMode() == WIFI_MODE_NULL) WiFi.mode(WIFI_STA);\n"
                  "    WiFi.setTxPower(wifi_power_t(txPower));\n"
                  "    WiFi.setScanMethod(WIFI_ALL_CHANNEL_SCAN);\n"
                  "    WiFi.setSortMethod(WIFI_CONNECT_AP_BY_SIGNAL);\n"
                  "#endif\n" + a, 1)
    b = "  WiFi.onEvent(WiFiEvent);\n"
    s = s.replace(b, b +
                  "  #if defined(WLED_DEBUG) && defined(ARDUINO_ARCH_ESP32)   // easteregged: log why the router drops us\n"
                  "  WiFi.onEvent([](WiFiEvent_t e, WiFiEventInfo_t info) {\n"
                  "    Serial.printf(\"STA disconnect reason: %d\\n\", (int)info.wifi_sta_disconnected.reason);\n"
                  "  }, ARDUINO_EVENT_WIFI_STA_DISCONNECTED);\n"
                  "  #endif\n", 1)
    open(p, "w", encoding="utf-8").write(s)
print("patched")
