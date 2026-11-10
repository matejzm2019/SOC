#include <cassert>
#include <cmath>
#include "../firmware/esp32/backup_power.h"
#include "../firmware/esp32/switch_input.h"
int main(){
 assert(std::isnan(voltageSoc(NAN)));assert(std::isnan(voltageSoc(5)));
 assert(voltageSoc(3.0f)==0);assert(voltageSoc(4.2f)==100);
 float previous=0;for(float v=2.5f;v<4.35f;v+=.001f){float p=voltageSoc(v);assert(p>=previous&&p<=100);previous=p;}
 assert(mainSupplyPresent(1562,false));assert(!mainSupplyPresent(0,true));assert(mainSupplyPresent(1300,true));assert(!mainSupplyPresent(1300,false));
 DebouncedSwitch input;assert(!input.update(true,0));assert(!input.update(false,5));assert(!input.update(true,10));assert(!input.update(true,39));assert(input.update(true,40));assert(input.update(false,50));assert(!input.update(false,80));
 DebouncedSwitch wrap;assert(!wrap.update(true,0xfffffff0U));assert(wrap.update(true,0x20U));
}
