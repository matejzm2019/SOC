#pragma once
#include <cstdint>
enum class WaterFault {None,SourceEmpty,Leak,SensorConflict,Timeout,LinkLost,MainLost};
inline const char* waterFaultName(WaterFault f) {
 switch(f){case WaterFault::None:return "none";case WaterFault::SourceEmpty:return "source_empty";case WaterFault::Leak:return "leak";case WaterFault::SensorConflict:return "sensor_conflict";case WaterFault::Timeout:return "timeout";case WaterFault::LinkLost:return "link_lost";case WaterFault::MainLost:return "main_lost";}
 return "sensor_conflict";
}
struct WaterInputs {bool sourceOK;bool targetLow;bool targetFull;bool leak;bool mainOK;};
struct WaterGuard {
 bool running=false;WaterFault fault=WaterFault::None;
 uint32_t started=0,renewed=0,lease=0,maxRun=0;
 WaterFault check(const WaterInputs& i) const {
  if(!i.mainOK)return WaterFault::MainLost;
  if(i.leak)return WaterFault::Leak;
  if(!i.sourceOK)return WaterFault::SourceEmpty;
  if(i.targetLow&&i.targetFull)return WaterFault::SensorConflict;
  return WaterFault::None;
 }
 void tick(uint32_t now,const WaterInputs& i){
  WaterFault bad=check(i);if(bad!=WaterFault::None){fault=bad;running=false;}
  if(running&&uint32_t(now-started)>=maxRun){fault=WaterFault::Timeout;running=false;}
  if(running&&uint32_t(now-renewed)>=lease){fault=WaterFault::LinkLost;running=false;}
  if(i.targetFull||fault!=WaterFault::None)running=false;
 }
 void command(bool on,uint32_t leaseMs,uint32_t maxMs,bool reset,uint32_t now,const WaterInputs& i){
  tick(now,i);
  if(!on){running=false;if(reset&&check(i)==WaterFault::None)fault=WaterFault::None;return;}
  if(fault!=WaterFault::None||i.targetFull||leaseMs<500||leaseMs>1500||maxMs<2000||maxMs>60000){running=false;return;}
  if(!running){started=now;maxRun=maxMs;}
  // Renewals cannot extend the original uninterrupted run limit.
  renewed=now;lease=leaseMs;running=true;
 }
};
