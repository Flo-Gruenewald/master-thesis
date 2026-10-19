#pragma once
// easteregged · table unit mic stream (15.10.2026)
// Reads the INMP441 (SD=4, WS=5, SCK=6, L/R=GND) over I2S at 48 kHz, averages 3 samples → 16 kHz mono int16,
// and sends it over UDP to the room host: "NMIC" + uint32 seq (LE) + 256 int16 samples (LE) every 16 ms.
// The host (core/netmic.py) turns it into bar rows for Morning Jam. Replaces the audioreactive usermod (same I2S).
// Settings (WLED → Config → Usermods → AudioStream): enabled, target (host IP), port, slot (-1 = auto L/R).
#include "wled.h"
#include <driver/i2s.h>
#include <WiFiUdp.h>

#ifndef AS_SD_PIN
#define AS_SD_PIN 4
#endif
#ifndef AS_WS_PIN
#define AS_WS_PIN 5
#endif
#ifndef AS_SCK_PIN
#define AS_SCK_PIN 6
#endif
#ifndef AS_TARGET
#define AS_TARGET "192.168.137.1"   // laptop host on its Windows hotspot (15.10)
#endif
#ifndef AS_PORT
#define AS_PORT 7010
#endif

class AudioStreamUsermod : public Usermod {
  bool enabled = true;
  String target = AS_TARGET;
  uint16_t port = AS_PORT;
  int8_t slot = -1;                 // -1 = auto: the slot with more signal during the first seconds
  bool i2sOk = false;
  TaskHandle_t th = nullptr;
  WiFiUDP udp;
  volatile uint32_t sent = 0;

  static void taskFn(void *arg) { ((AudioStreamUsermod *)arg)->run(); }

  void run() {
    static int32_t blk[256];        // 128 stereo frames at 48 kHz
    static uint8_t pkt[8 + 256 * 2];
    int16_t *out = (int16_t *)(pkt + 8);
    memcpy(pkt, "NMIC", 4);
    uint32_t seq = 0; int m = 0, k = 0; int32_t acc = 0;
    double e[2] = {0, 0}; uint32_t t0 = millis(); int use = slot;
    IPAddress ip; bool ipOk = false; String ipFor;
    for (;;) {
      size_t got = 0;
      if (i2s_read(I2S_NUM_0, blk, sizeof(blk), &got, portMAX_DELAY) != ESP_OK || !got) continue;
      int frames = got / 8;
      if (use < 0) {                                   // auto-pick the active slot (L/R pin)
        for (int j = 0; j < frames; j++) {
          double l = (double)(blk[2 * j] >> 16), r = (double)(blk[2 * j + 1] >> 16);
          e[0] += l * l; e[1] += r * r;
        }
        if (millis() - t0 > 1500) use = e[1] > e[0] ? 1 : 0;
        continue;
      }
      if (!enabled || !WLED_CONNECTED) { m = 0; continue; }
      if (!ipOk || ipFor != target) { ipOk = ip.fromString(target); ipFor = target; }
      if (!ipOk) continue;
      for (int j = 0; j < frames; j++) {
        acc += blk[2 * j + use] >> 16;
        if (++k == 3) {
          out[m++] = (int16_t)constrain(acc / 3, -32768, 32767); acc = 0; k = 0;
          if (m == 256) {
            memcpy(pkt + 4, &seq, 4); seq++;
            udp.beginPacket(ip, port); udp.write(pkt, sizeof(pkt)); udp.endPacket();
            sent++; m = 0;
          }
        }
      }
    }
  }

 public:
  void setup() override {
    i2s_config_t ic = {};
    ic.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
    ic.sample_rate = 48000;                              // SCK ~3 MHz: inside the INMP441's range
    ic.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
    ic.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
    ic.communication_format = I2S_COMM_FORMAT_STAND_I2S;
    ic.intr_alloc_flags = 0;
    ic.dma_buf_count = 12;                               // 12 × 256 frames ≈ 64 ms of buffer
    ic.dma_buf_len = 256;
    ic.use_apll = false;
    i2s_pin_config_t pc = {};
    pc.mck_io_num = I2S_PIN_NO_CHANGE;
    pc.bck_io_num = AS_SCK_PIN;
    pc.ws_io_num = AS_WS_PIN;
    pc.data_out_num = I2S_PIN_NO_CHANGE;
    pc.data_in_num = AS_SD_PIN;
    i2sOk = i2s_driver_install(I2S_NUM_0, &ic, 0, nullptr) == ESP_OK && i2s_set_pin(I2S_NUM_0, &pc) == ESP_OK;
    gpio_pulldown_en((gpio_num_t)AS_SD_PIN);             // an undriven data line reads 0, not noise
    if (i2sOk) xTaskCreate(taskFn, "netmic", 4096, this, 1, &th);
  }

  void loop() override {}

  void addToJsonInfo(JsonObject &root) override {
    JsonObject user = root["u"];
    if (user.isNull()) user = root.createNestedObject("u");
    JsonArray a = user.createNestedArray(F("Mic stream"));
    a.add(i2sOk ? (String(sent) + " packets → " + target + ":" + String(port)) : String(F("I2S failed")));
  }

  void addToConfig(JsonObject &root) override {
    JsonObject top = root.createNestedObject(F("AudioStream"));
    top[F("enabled")] = enabled;
    top[F("target")] = target;
    top[F("port")] = port;
    top[F("slot")] = slot;
  }

  bool readFromConfig(JsonObject &root) override {
    JsonObject top = root[F("AudioStream")];
    bool ok = !top.isNull();
    getJsonValue(top[F("enabled")], enabled);
    getJsonValue(top[F("target")], target);
    getJsonValue(top[F("port")], port);
    getJsonValue(top[F("slot")], slot);
    return ok;
  }

  uint16_t getId() override { return USERMOD_ID_UNSPECIFIED; }
};
