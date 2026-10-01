#include <Adafruit_INA219.h>
#include <BH1750.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <Wire.h>

#include "secrets.h"

constexpr int SDA_PIN = 8;
constexpr int SCL_PIN = 9;
constexpr int GRID_BUTTON_PIN = 4;
constexpr int LOAD_1_PIN = 5;
constexpr int LOAD_2_PIN = 6;
constexpr int LOAD_1_LED_PIN = 7;
constexpr int LOAD_2_LED_PIN = 10;
constexpr int GRID_LED_PIN = 11;
constexpr unsigned long SEND_INTERVAL_MS = 1000;

Adafruit_INA219 panelSensor;
BH1750 lightSensor;
unsigned long lastSend = 0;

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.printf("\nWi-Fi: %s\nIP: %s\n", WIFI_SSID, WiFi.localIP().toString().c_str());
}

void setup() {
  Serial.begin(115200);
  pinMode(GRID_BUTTON_PIN, INPUT_PULLUP);
  pinMode(LOAD_1_PIN, INPUT_PULLUP);
  pinMode(LOAD_2_PIN, INPUT_PULLUP);
  pinMode(LOAD_1_LED_PIN, OUTPUT);
  pinMode(LOAD_2_LED_PIN, OUTPUT);
  pinMode(GRID_LED_PIN, OUTPUT);
  Wire.begin(SDA_PIN, SCL_PIN);
  if (!panelSensor.begin()) {
    Serial.println("INA219 sa nenasiel. Skontrolujte SDA, SCL, 3V3 a GND.");
    while (true) delay(1000);
  }
  lightSensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
  connectWifi();
}

void loop() {
  if (millis() - lastSend < SEND_INTERVAL_MS) return;
  lastSend = millis();
  if (WiFi.status() != WL_CONNECTED) connectWifi();

  const float voltage = max(0.0f, panelSensor.getBusVoltage_V());
  const float current = max(0.0f, panelSensor.getCurrent_mA() / 1000.0f);
  const float power = max(0.0f, panelSensor.getPower_mW() / 1000.0f);
  const float lux = max(0.0f, lightSensor.readLightLevel());
  const bool gridAvailable = digitalRead(GRID_BUTTON_PIN) == HIGH;
  const int loadStage = (digitalRead(LOAD_1_PIN) == LOW ? 1 : 0) +
                        (digitalRead(LOAD_2_PIN) == LOW ? 2 : 0);
  digitalWrite(LOAD_1_LED_PIN, digitalRead(LOAD_1_PIN) == LOW);
  digitalWrite(LOAD_2_LED_PIN, digitalRead(LOAD_2_PIN) == LOW);
  digitalWrite(GRID_LED_PIN, gridAvailable);

  char payload[320];
  snprintf(payload, sizeof(payload),
           "{\"device_id\":\"energia-esp32\",\"firmware_version\":\"0.1.0\","
           "\"panel_voltage_v\":%.4f,\"panel_current_a\":%.5f,"
           "\"panel_power_w\":%.5f,\"illuminance_lux\":%.1f,"
           "\"load_stage\":%d,\"grid_available\":%s}",
           voltage, current, power, lux, loadStage, gridAvailable ? "true" : "false");

  HTTPClient http;
  http.setConnectTimeout(2000);
  http.setTimeout(2000);
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", DEVICE_KEY);
  const int status = http.POST(reinterpret_cast<uint8_t *>(payload), strlen(payload));
  Serial.printf("HTTP %d | U=%.2f V I=%.3f A P=%.3f W lux=%.0f\n",
                status, voltage, current, power, lux);
  http.end();
}
