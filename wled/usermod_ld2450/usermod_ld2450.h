#pragma once
/*
 * LD2450 radar for WLED (the TOP spotlight subnode: ESP32 DevKit V1, LEDs + radar on one board).
 *
 * The HLK-LD2450 streams frames by itself; only its TX is needed (→ GPIO16 on the ESP32 DevKit).
 * Publishes the same MQTT topics as esphome/presence_ld2450.yaml, so the host needs no change:
 *   <prefix>/in/presence/state            ON / OFF        (on change + every second)
 *   <prefix>/in/presence/count            0..3            (on change + every second)
 *   <prefix>/in/presence/target/<n>/<x|y> mm             (every 200 ms while seen)
 *   <prefix>/status/presence              online (retained)
 * Frame (30 bytes): AA FF 03 00 | 3 × (x, y, speed, resolution: int16 LE) | 55 CC.
 * Sign of x/y/speed: bit 15 set = positive, clear = negative; value = bits 0..14.
 *
 * Build: -D USERMOD_LD2450 (see ../platformio_override.ini). Settings: WLED → Config → Usermods.
 * A second radar (wall unit, 16.10.2026): -D LD2450_SOURCE='"presence_wall"' → topics in/presence_wall/...,
 * so the two radars don't overwrite each other. ESP32-C3 has no Serial2: the radar uses Serial1 there.
 */
#include "wled.h"

#ifndef WLED_ENABLE_MQTT
#error "USERMOD_LD2450 needs MQTT"
#endif

#ifndef LD2450_SOURCE
#define LD2450_SOURCE "presence"        // topic part: in/<source>/..., status/<source>
#endif
#if defined(CONFIG_IDF_TARGET_ESP32C3)
#define LD2450_UART Serial1             // the C3 has two UARTs (Serial0 + Serial1)
#else
#define LD2450_UART Serial2
#endif

class LD2450Usermod : public Usermod {
  private:
    bool enabled = true;
#ifndef LD2450_RX_PIN
#define LD2450_RX_PIN 16                // ESP32 DevKit: GPIO16 = RX2 (Gledopto would be 13)
#endif
    int8_t rxPin = LD2450_RX_PIN;
    String prefix = "easteregged";     // host topic prefix
    String source = LD2450_SOURCE;
    bool pinOk = false;

    uint8_t buf[30];
    uint8_t len = 0;
    unsigned long lastFrame = 0, lastBeat = 0, lastXY = 0;
    int16_t x[3] = {0, 0, 0}, y[3] = {0, 0, 0};
    bool seen[3] = {false, false, false};
    int8_t count = -1, lastCount = -1;
    uint32_t frames = 0, sent = 0;

    static const char _name[];

    static int16_t sval(uint8_t lo, uint8_t hi) {
      uint16_t v = lo | (hi << 8);
      int16_t m = v & 0x7FFF;
      return (v & 0x8000) ? m : -m;
    }

    void pub(const String &sub, const String &val, bool retain = false) {
      if (!WLED_MQTT_CONNECTED) return;
      String t = prefix + "/" + sub;
      if (mqtt->publish(t.c_str(), 0, retain, val.c_str())) sent++;
    }

    void parse() {
      uint8_t c = 0;
      for (uint8_t i = 0; i < 3; i++) {
        const uint8_t *p = buf + 4 + i * 8;
        bool any = p[0] | p[1] | p[2] | p[3];
        seen[i] = any;
        if (any) { x[i] = sval(p[0], p[1]); y[i] = sval(p[2], p[3]); c++; }
      }
      count = c;
      frames++;
      lastFrame = millis();
    }

    void report(bool force) {
      unsigned long now = millis();
      bool alive = now - lastFrame < 2000;           // no frames for 2 s → report nobody
      int8_t c = alive ? count : 0;
      if (c != lastCount || force) {
        pub("in/" + source + "/state", c > 0 ? F("ON") : F("OFF"));
        pub("in/" + source + "/count", String(c));
        lastCount = c;
      }
      if (alive && now - lastXY >= 200) {
        lastXY = now;
        for (uint8_t i = 0; i < 3; i++) {
          if (!seen[i]) continue;
          String base = "in/" + source + "/target/" + (i + 1) + "/";
          pub(base + "x", String(x[i]));
          pub(base + "y", String(y[i]));
        }
      }
    }

  public:
    void setup() override {
      if (!enabled || rxPin < 0) return;
      pinOk = PinManager::allocatePin(rxPin, false, PinOwner::UM_Unspecified);
      if (pinOk) LD2450_UART.begin(256000, SERIAL_8N1, rxPin, -1);
    }

    void connected() override {}

    void onMqttConnect(bool sessionPresent) override {
      pub("status/" + source, F("online"), true);
      report(true);
    }

    void loop() override {
      if (!enabled || !pinOk) return;
      while (LD2450_UART.available()) {
        uint8_t b = LD2450_UART.read();
        // sync on the 4-byte header, then collect 30 bytes and check the tail
        static const uint8_t hdr[4] = {0xAA, 0xFF, 0x03, 0x00};
        if (len < 4) {
          if (b == hdr[len]) buf[len++] = b;
          else len = (b == 0xAA) ? (buf[0] = b, 1) : 0;
          continue;
        }
        buf[len++] = b;
        if (len == 30) {
          if (buf[28] == 0x55 && buf[29] == 0xCC) parse();
          len = 0;
        }
      }
      unsigned long now = millis();
      bool beat = now - lastBeat >= 1000;
      if (beat) lastBeat = now;
      report(beat);
    }

    void addToJsonInfo(JsonObject &root) override {
      JsonObject user = root["u"];
      if (user.isNull()) user = root.createNestedObject("u");
      JsonArray a = user.createNestedArray(F("LD2450"));
      if (!enabled) { a.add(F("disabled")); return; }
      if (!pinOk) { a.add(F("pin busy")); return; }
      if (millis() - lastFrame > 2000) { a.add(F("no data")); }
      a.add(count);
      a.add(String(F(" people · mqtt ")) + (WLED_MQTT_CONNECTED ? F("on") : F("off")) + F(" · sent ") + sent);
    }

    void addToConfig(JsonObject &root) override {
      JsonObject top = root.createNestedObject(FPSTR(_name));
      top[F("enabled")] = enabled;
      top[F("rxPin")] = rxPin;
      top[F("topicPrefix")] = prefix;
    }

    bool readFromConfig(JsonObject &root) override {
      JsonObject top = root[FPSTR(_name)];
      bool ok = !top.isNull();
      ok &= getJsonValue(top[F("enabled")], enabled, true);
      ok &= getJsonValue(top[F("rxPin")], rxPin, (int8_t)LD2450_RX_PIN);
      ok &= getJsonValue(top[F("topicPrefix")], prefix, String("easteregged"));
      return ok;
    }

    uint16_t getId() override { return USERMOD_ID_UNSPECIFIED; }
};

const char LD2450Usermod::_name[] PROGMEM = "LD2450";
