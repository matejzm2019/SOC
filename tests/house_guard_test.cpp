#include <cassert>
#include <cmath>
#include "../firmware/esp32-s3/backup_power.h"
#include "../firmware/esp32-s3/water_guard.h"
int main(){
 assert(std::isnan(voltageSoc(NAN)));assert(std::isnan(voltageSoc(5)));
 assert(voltageSoc(3.0f)==0);assert(voltageSoc(4.2f)==100);
 float previous=0;for(float v=2.5f;v<4.35f;v+=.001f){float p=voltageSoc(v);assert(p>=previous&&p<=100);previous=p;}
 assert(mainSupplyPresent(1562,false));assert(!mainSupplyPresent(0,true));assert(mainSupplyPresent(1300,true));assert(!mainSupplyPresent(1300,false));
 WaterInputs good={true,true,false,false,true};
 WaterGuard g;g.command(true,1500,5000,false,0,good);assert(g.running);
 g.tick(1500,good);assert(!g.running&&g.fault==WaterFault::LinkLost);
 g.command(true,1500,5000,false,1501,good);assert(!g.running);
 g.command(false,1500,5000,true,1600,good);assert(g.fault==WaterFault::None);
 WaterGuard timeout;timeout.command(true,1500,5000,false,0,good);
 for(unsigned i=1000;i<=5000;i+=1000)timeout.command(true,1500,60000,false,i,good);
 assert(!timeout.running&&timeout.fault==WaterFault::Timeout);
 for(int fault=0;fault<4;++fault){
  WaterGuard x;x.command(true,1500,5000,false,0,good);WaterInputs bad=good;
  if(fault==0)bad.sourceOK=false;
  if(fault==1)bad.leak=true;
  if(fault==2)bad.targetFull=true;
  if(fault==3)bad.mainOK=false;
  x.tick(10,bad);assert(!x.running);x.command(false,1500,5000,true,11,bad);assert(x.fault!=WaterFault::None);
 }
 WaterGuard full;WaterInputs atFull={true,false,true,false,true};full.command(true,1500,5000,false,0,atFull);assert(!full.running);
 WaterGuard wrap;wrap.command(true,1500,5000,false,0xfffffff0U,good);wrap.tick(0x10U,good);assert(wrap.running);wrap.tick(0x700U,good);assert(!wrap.running);
 WaterGuard invalid;invalid.command(true,99999,99999,false,0,good);assert(!invalid.running);
}
