#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_INA3221.h>
#include "ina3221_reading.h"
#include "secrets.h"
#include "backup_power.h"
#include "switch_input.h"
#ifndef SIMULATED_SENSORS
#define SIMULATED_SENSORS 0
#endif
#ifndef WIFI_ENABLED
#define WIFI_ENABLED 1
#endif
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Select ESP32 Dev Module for the photographed ESP-32D board (not ESP32-S3)."
#endif
// ADC1 GPIO34 remains available while Wi-Fi is active. Avoid flash and boot strapping pins.
constexpr int MAIN_PIN=34,SW_A=32,SW_B=33,LED_A=25,LED_B=26,GRID_LED=27;
constexpr int SIM_SUN=35,SIM_BAT=36,SIM_CURRENT=39;
Adafruit_INA3221 panelSensor,batterySensor;
constexpr uint8_t PANEL_ADDRESS=0x40,BATTERY_ADDRESS=0x41;
uint32_t panelStarted=0,batteryStarted=0;
bool panelReady=false,batteryReady=false;
float filteredVoltage=NAN;
uint32_t lastSend=0,lastWifiAttempt=0,lastSensorAttempt=0;
portMUX_TYPE controlMux=portMUX_INITIALIZER_UNLOCKED;
bool mains=false;int loadStage=0;

bool readRegister16(uint8_t address,uint8_t reg,uint16_t &value){
 Wire.beginTransmission(address);Wire.write(reg);
 if(Wire.endTransmission(false)!=0)return false;
 if(Wire.requestFrom(address,uint8_t(2))!=2){while(Wire.available())Wire.read();return false;}
 value=(uint16_t(Wire.read())<<8)|uint8_t(Wire.read());return true;
}
bool startSensor(Adafruit_INA3221 &sensor,uint8_t address,uint32_t &started){
 if(!sensor.begin(address,&Wire))return false;
 sensor.setShuntResistance(0,INA3221_SHUNT_OHMS); // CH1 is channel 0 in the library
 if(!sensor.setAveragingMode(INA3221_AVG_16_SAMPLES))return false;
 started=millis();return true;
}
bool readSensor(uint8_t address,Ina3221Reading &reading){
 uint16_t manufacturer,die,bus,shunt;
 // Checked transport reads: the library's float getters cannot report I2C NACKs.
 if(!readRegister16(address,INA3221_REG_MANUFACTURER_ID,manufacturer)||manufacturer!=INA3221_MANUFACTURER_ID||
    !readRegister16(address,INA3221_REG_DIE_ID,die)||die!=INA3221_DIE_ID||
    !readRegister16(address,INA3221_REG_BUSVOLTAGE_CH1,bus)||
    !readRegister16(address,INA3221_REG_SHUNTVOLTAGE_CH1,shunt))return false;
 return decodeIna3221(bus,shunt,reading);
}
void controlTask(void*) {
 bool currentMain=false;DebouncedSwitch switchA,switchB;
 TickType_t wake=xTaskGetTickCount();
 for(;;){
  currentMain=mainSupplyPresent(analogReadMilliVolts(MAIN_PIN),currentMain);
  const uint32_t now=millis();
  bool a=switchA.update(digitalRead(SW_A)==LOW,now),b=switchB.update(digitalRead(SW_B)==LOW,now);
  digitalWrite(LED_A,a);digitalWrite(LED_B,b);digitalWrite(GRID_LED,currentMain);
  portENTER_CRITICAL(&controlMux);
  mains=currentMain;loadStage=(a?1:0)+(b?2:0);
  portEXIT_CRITICAL(&controlMux);
  vTaskDelayUntil(&wake,pdMS_TO_TICKS(10));
 }
}
void setup(){
 Serial.begin(115200);
 pinMode(MAIN_PIN,INPUT);analogSetPinAttenuation(MAIN_PIN,ADC_11db);
 pinMode(SW_A,INPUT_PULLUP);pinMode(SW_B,INPUT_PULLUP);
 for(int p:{LED_A,LED_B,GRID_LED}){digitalWrite(p,LOW);pinMode(p,OUTPUT);}
 if(xTaskCreatePinnedToCore(controlTask,"local-control",4096,nullptr,2,nullptr,1)!=pdPASS){
  while(true)delay(1000);
 }
#if !SIMULATED_SENSORS
 Wire.begin(21,22);Wire.setClock(100000);Wire.setTimeOut(50);
 panelReady=startSensor(panelSensor,PANEL_ADDRESS,panelStarted);
 batteryReady=startSensor(batterySensor,BATTERY_ADDRESS,batteryStarted);
#endif
#if WIFI_ENABLED
 WiFi.mode(WIFI_STA);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);lastWifiAttempt=millis();
#endif
}
void loop(){
 if(uint32_t(millis()-lastSend)<1000){delay(5);return;}
 lastSend=millis();
#if WIFI_ENABLED
 if(WiFi.status()!=WL_CONNECTED&&uint32_t(millis()-lastWifiAttempt)>=10000){lastWifiAttempt=millis();WiFi.begin(WIFI_SSID,WIFI_PASSWORD);}
#endif
 float panelV,panelA,panelW,batV=NAN,batA=NAN;
#if SIMULATED_SENSORS
 const float sun=analogRead(SIM_SUN)/4095.0f;
 // Synthetic 12 V / 1 W test profile, NOT the unknown real panel rating.
 panelV=12.0f;panelW=1.0f*sun;panelA=panelW/panelV;
 batV=3.0f+1.2f*analogRead(SIM_BAT)/4095.0f;
 batA=(analogRead(SIM_CURRENT)/4095.0f-.5f)*1.0f;
#else
 if(uint32_t(millis()-lastSensorAttempt)>=5000){
  lastSensorAttempt=millis();
  if(!panelReady)panelReady=startSensor(panelSensor,PANEL_ADDRESS,panelStarted);
  if(!batteryReady)batteryReady=startSensor(batterySensor,BATTERY_ADDRESS,batteryStarted);
 }
 // Three enabled channels, 1.1ms bus + shunt, 16 samples: allow first conversion.
 if(!panelReady||uint32_t(millis()-panelStarted)<150)return;
 Ina3221Reading panel;
 if(!readSensor(PANEL_ADDRESS,panel)){
  panelReady=false;Serial.println("Chyba INA3221 PANEL CH1: I2C, identita alebo rozsah; telemetria neposlana.");return;
 }
 panelV=max(0.0f,panel.bus_v+panel.shunt_v);panelA=panel.current_a;panelW=panelV*max(0.0f,panelA);
 if(batteryReady&&uint32_t(millis()-batteryStarted)>=150){
  Ina3221Reading battery;
  if(readSensor(BATTERY_ADDRESS,battery)){batV=battery.bus_v;batA=battery.current_a;}
  else{batteryReady=false;Serial.println("Chyba INA3221 BAT CH1; bateria v telemetrii vynechana.");}
 }
#endif
 if(!isfinite(panelV)||!isfinite(panelA)||!isfinite(panelW))return;
 bool grid;int loads;
 portENTER_CRITICAL(&controlMux);
 grid=mains;loads=loadStage;
 portEXIT_CRITICAL(&controlMux);
 JsonDocument doc;
 doc["device_id"]="energia-esp32";doc["firmware_version"]="0.9.0-ina3221";
 doc["telemetry_origin"]=SIMULATED_SENSORS?"software_test":"hardware";
 doc["panel_voltage_v"]=max(0.0f,panelV);doc["panel_current_a"]=max(0.0f,panelA);doc["panel_power_w"]=max(0.0f,panelW);
 doc["load_stage"]=loads;doc["grid_available"]=grid;
 if(isfinite(voltageSoc(batV))&&isfinite(batA)&&abs(batA)<=INA3221_MODULE_LIMIT_A + 0.00005f){
  filteredVoltage=isfinite(filteredVoltage)?filteredVoltage+.1f*(batV-filteredVoltage):batV;
  doc["battery_voltage_v"]=batV;doc["battery_current_a"]=batA;
  doc["battery_soc_pct"]=voltageSoc(filteredVoltage);doc["battery_soc_method"]="voltage_estimate";
 }else{filteredVoltage=NAN;}
 String payload;serializeJson(doc,payload);Serial.println(payload);
#if WIFI_ENABLED
 if(WiFi.status()!=WL_CONNECTED)return;
 HTTPClient http;http.setConnectTimeout(400);http.setTimeout(600);
 http.begin(SERVER_URL);http.addHeader("Content-Type","application/json");http.addHeader("X-Device-Key",DEVICE_KEY);
 const int status=http.POST(payload);
 Serial.printf("HTTP %d\n",status);http.end();
#endif
}
