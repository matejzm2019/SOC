#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_INA219.h>
#include "secrets.h"
#include "backup_power.h"
#ifndef SIMULATED_SENSORS
#define SIMULATED_SENSORS 0
#endif
#ifndef WIFI_ENABLED
#define WIFI_ENABLED 1
#endif
constexpr int MAIN_PIN=4,SW_A=5,SW_B=6,LED_A=7,LED_B=10,GRID_LED=11;
constexpr int SIM_SUN=1,SIM_BAT=17,SIM_CURRENT=18;
Adafruit_INA219 panelSensor(0x40),batterySensor(0x41);
bool panelReady=false,batteryReady=false;
float filteredVoltage=NAN;
uint32_t lastSend=0,lastWifiAttempt=0,lastSensorAttempt=0;
portMUX_TYPE controlMux=portMUX_INITIALIZER_UNLOCKED;
bool mains=false;int loadStage=0;

bool present(uint8_t address){Wire.beginTransmission(address);return Wire.endTransmission()==0;}
void controlTask(void*) {
 bool currentMain=false;
 for(;;){
  currentMain=mainSupplyPresent(analogReadMilliVolts(MAIN_PIN),currentMain);
  bool a=digitalRead(SW_A)==LOW,b=digitalRead(SW_B)==LOW;
  digitalWrite(LED_A,a);digitalWrite(LED_B,b);digitalWrite(GRID_LED,currentMain);
  portENTER_CRITICAL(&controlMux);
  mains=currentMain;loadStage=(a?1:0)+(b?2:0);
  portEXIT_CRITICAL(&controlMux);
  vTaskDelay(pdMS_TO_TICKS(20));
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
 Wire.begin(8,9);panelReady=panelSensor.begin();batteryReady=batterySensor.begin();
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
 panelV=6.0f;panelA=.833f*sun;panelW=panelV*panelA;
 batV=3.0f+1.2f*analogRead(SIM_BAT)/4095.0f;
 batA=(analogRead(SIM_CURRENT)/4095.0f-.5f)*1.0f;
#else
 if(panelReady&&!present(0x40))panelReady=false;
 if(batteryReady&&!present(0x41))batteryReady=false;
 if(uint32_t(millis()-lastSensorAttempt)>=5000){lastSensorAttempt=millis();if(!panelReady)panelReady=panelSensor.begin();if(!batteryReady)batteryReady=batterySensor.begin();}
 if(!panelReady){Serial.println("Chyba INA219 panel 0x40; telemetria neposlana.");return;}
 panelV=panelSensor.getBusVoltage_V();panelA=panelSensor.getCurrent_mA()/1000.0f;panelW=panelSensor.getPower_mW()/1000.0f;
 if(batteryReady){batV=batterySensor.getBusVoltage_V();batA=batterySensor.getCurrent_mA()/1000.0f;}
#endif
 if(!isfinite(panelV)||!isfinite(panelA)||!isfinite(panelW))return;
 bool grid;int loads;
 portENTER_CRITICAL(&controlMux);
 grid=mains;loads=loadStage;
 portEXIT_CRITICAL(&controlMux);
 JsonDocument doc;
 doc["device_id"]="energia-esp32";doc["firmware_version"]="0.6.0-roof";
 doc["telemetry_origin"]=SIMULATED_SENSORS?"software_test":"hardware";
 doc["panel_voltage_v"]=max(0.0f,panelV);doc["panel_current_a"]=max(0.0f,panelA);doc["panel_power_w"]=max(0.0f,panelW);
 doc["load_stage"]=loads;doc["grid_available"]=grid;
 if(isfinite(voltageSoc(batV))&&isfinite(batA)&&abs(batA)<=5){
  filteredVoltage=isfinite(filteredVoltage)?filteredVoltage+.1f*(batV-filteredVoltage):batV;
  doc["battery_voltage_v"]=batV;doc["battery_current_a"]=batA;
  doc["battery_soc_pct"]=voltageSoc(filteredVoltage);doc["battery_soc_method"]="voltage_estimate";
 }else{filteredVoltage=NAN;batteryReady=false;}
 String payload;serializeJson(doc,payload);Serial.println(payload);
#if WIFI_ENABLED
 if(WiFi.status()!=WL_CONNECTED)return;
 HTTPClient http;http.setConnectTimeout(400);http.setTimeout(600);
 http.begin(SERVER_URL);http.addHeader("Content-Type","application/json");http.addHeader("X-Device-Key",DEVICE_KEY);
 const int status=http.POST(payload);
 Serial.printf("HTTP %d\n",status);http.end();
#endif
}
