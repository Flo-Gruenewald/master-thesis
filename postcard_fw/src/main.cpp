// Tactile postcard v4 (16.10.2026): a heartbeat you can hold, on Wi-Fi. One pressure strip, one coin motor.
// Ported from Hugbeat heartbeat_v4.ino (Arduino Uno) to the ESP32-C3 SuperMini; petting/purring left out.
//
// Wiring:  3V3 ── strip ──┬── GPIO1 (C3) / D34 (ESP32)   GPIO5/D5 ── 1 kΩ ── PN2222 base (21.10: 2 motors in parallel)
//                         └── 10 kΩ ── GND      motor + ── 5V, motor − ── collector, emitter ── GND
//
// Behaviour: always a faint resting heartbeat. The strip only knows held / not held (with the 10 kΩ pull-down it
// jumps from rest straight to the top when pressed), so the intensity comes from how long it is held:
// holding makes the beat stronger (over HOLD_S) and slowly faster ("charge", REST → MAX bpm); letting go,
// the strength falls back within RELEASE_S and the tempo drains slowly.
// Each reading is the average over 20 ms (cancels mains hum on the long strip wires). At start: 1 s calibration.
// Serial (115200), every 100 ms: reading min/avg/max of that window, held, intensity, charge, bpm, pwm.
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiManager.h>                // no password in the code: first start opens "postcard-setup", pick FLO-WORK there
#include <PubSubClient.h>

// Wi-Fi + MQTT (v4): the card reports holding to the room host; the host says when a postcard arrives.
static const char *BROKER = "192.168.137.1";
static const char *T_TOUCH = "easteregged/in/postcard/touch";   // {"held":0|1,"i":0..1} on change + every 0.5 s held
static const char *T_ARRIVED = "easteregged/postcard/arrived";  // → two short buzzes: the card wakes up

#ifndef PIN_FSR_GPIO
#define PIN_FSR_GPIO 1          // C3 SuperMini: GPIO1; classic ESP32 DevKit (env esp32): GPIO34 (D34, ADC1)
#endif
#ifndef PIN_MOTOR_GPIO
#define PIN_MOTOR_GPIO 6        // 21.10.2026: GPIO5 of the C3 died (motor wired straight to the pin) → GPIO6
#endif
static const int PIN_FSR = PIN_FSR_GPIO, PIN_MOTOR = PIN_MOTOR_GPIO;   // both motors through one transistor
static const float HOLD_ON_D = 80, HOLD_OFF_D = 40;   // 21.10: held = this far above the resting mean (raw units);
static const int HOLD_N = 3;                          //   the strip with 10 kΩ only rises ~+50…+150 when pressed
static const float HOLD_S = 4.0;        // seconds of holding to reach full strength
static const float RELEASE_S = 1.5;     // seconds for the strength to fall back after letting go
static const float CHARGE_UP = 0.12;    // tempo charge per second while held (≈ 8 s to the top)
static const float CHARGE_DOWN = 0.04;  // drain per second when not held (≈ 25 s back to rest)
static const float BPM_REST = 60, BPM_MAX = 130;
static const int PWM_REST = 170;        // the faint resting beat (120 was too weak to turn the motor)
static const int PWM_MAX = 255;         // the strongest beat after holding for HOLD_S
static const int KICK_MS = 25;          // each lub/dub starts at full duty for this long, so the motor surely spins up
static const int LUB_MS = 90, GAP_MS = 130, DUB_MS = 70;

float base = 0, intensity = 0, charge = 0;
bool held = false;
uint32_t lastBeat = 0, lastLog = 0, lastTick = 0;
int rMin = 4095, rMax = 0, rN = 0;      // readings of the current 100 ms log window
long rSum = 0;
WiFiManager wm;
WiFiClient net;
PubSubClient mqtt(net);
uint32_t lastMqttTry = 0, lastPub = 0, wakeAt = 0;
bool lastHeld = false;

void onMqtt(char *topic, byte *payload, unsigned int len) {
  if (!strcmp(topic, T_ARRIVED)) wakeAt = millis();       // the loop plays the wake-up buzzes
}

void network(uint32_t now) {
  wm.process();
  if (WiFi.status() != WL_CONNECTED) return;
  if (!mqtt.connected()) {
    if (now - lastMqttTry < 5000) return;
    lastMqttTry = now;
    if (mqtt.connect("postcard")) { mqtt.subscribe(T_ARRIVED); Serial.println("mqtt connected"); }
    return;
  }
  mqtt.loop();
  if (held != lastHeld || (held && now - lastPub >= 500)) {
    char msg[40];
    snprintf(msg, sizeof msg, "{\"held\":%d,\"i\":%.2f}", held ? 1 : 0, intensity);
    mqtt.publish(T_TOUCH, msg);
    lastHeld = held;
    lastPub = now;
  }
}

int reading() {                         // average over one 50 Hz period
  long sum = 0;
  for (int i = 0; i < 40; i++) { sum += analogRead(PIN_FSR); delayMicroseconds(500); }
  return sum / 40;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_MOTOR, OUTPUT);
  analogWrite(PIN_MOTOR, 0);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);       // full 0..3.3 V range
  delay(300);
  long sum = 0;
  for (int i = 0; i < 40; i++) sum += reading();           // resting mean (don't touch the card while it starts)
  base = sum / 40.0f;
  Serial.printf("postcard v3 ready, resting value %.0f\n", base);
  for (int i = 0; i < 2; i++) { analogWrite(PIN_MOTOR, 255); delay(250); analogWrite(PIN_MOTOR, 0); delay(250); }
  WiFi.mode(WIFI_STA);
  wm.setConfigPortalBlocking(false);    // the heartbeat keeps running while the setup portal is open
  wm.setConfigPortalTimeout(0);
  if (!wm.autoConnect("postcard-setup")) Serial.println("no saved Wi-Fi: join 'postcard-setup' and choose FLO-WORK");
  mqtt.setServer(BROKER, 1883);
  mqtt.setCallback(onMqtt);
  lastTick = millis();
}

void loop() {
  uint32_t now = millis();
  float dt = (now - lastTick) / 1000.0f;
  lastTick = now;

  int raw = reading();
  rMin = min(rMin, raw); rMax = max(rMax, raw); rSum += raw; rN++;
  static float f = -1;                                             // smoothed reading (~0.2 s): the strip is noisy
  f = (f < 0) ? raw : f + (raw - f) * 0.1f;
  if (!held && f - base > HOLD_ON_D) held = true;                  // pressed: clearly above the resting mean
  else if (held && f - base < HOLD_OFF_D) held = false;            // let go: back near rest
  if (f < base) base += (f - base) * 0.05f;                        // the rest: follows quickly down (a press at start-up
  else if (!held) base += (f - base) * 0.0005f;                    //   can't spoil it), slowly up (drift, wires)

  // intensity: grows the longer it is held, falls back quickly after letting go; the tempo follows slowly
  if (held) intensity = min(1.0f, intensity + dt / HOLD_S);
  else intensity = max(0.0f, intensity - dt / RELEASE_S);
  if (held) charge = min(1.0f, charge + CHARGE_UP * dt);
  else charge = max(0.0f, charge - CHARGE_DOWN * dt);

  float bpm = BPM_REST + (BPM_MAX - BPM_REST) * charge;
  int pwm = (int)(PWM_REST + (PWM_MAX - PWM_REST) * intensity);

  uint32_t interval = (uint32_t)(60000.0f / bpm);
  if (now - lastBeat >= interval) lastBeat = now;
  uint32_t t = now - lastBeat;
  int out = 0;
  uint32_t dub = LUB_MS + GAP_MS;
  if (t < LUB_MS) out = t < KICK_MS ? 255 : pwm;                                        // lub
  else if (t >= dub && t < dub + DUB_MS) out = t < dub + KICK_MS ? 255 : (int)(pwm * 0.85f);   // dub (softer)
  uint32_t w = now - wakeAt;            // a postcard arrived: two short buzzes over the heartbeat
  if (wakeAt && w < 700) out = (w < 150 || (w >= 350 && w < 500)) ? 255 : 0;
  analogWrite(PIN_MOTOR, out);
  network(now);

  if (now - lastLog >= 100) {
    lastLog = now;
    Serial.printf("raw %4d/%4ld/%4d  %s  intensity %.2f  charge %.2f  bpm %3.0f  pwm %3d\n", rMin, rSum / max(rN, 1),
                  rMax, held ? "HELD" : "    ", intensity, charge, bpm, pwm);
    rMin = 4095; rMax = 0; rSum = 0; rN = 0;
  }
}
