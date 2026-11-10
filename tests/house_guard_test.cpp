#include <cassert>
#include <cmath>
#include "../firmware/esp32/backup_power.h"
#include "../firmware/esp32/switch_input.h"
#include "../firmware/esp32/ina3221_reading.h"
int main(){
 assert(std::isnan(voltageSoc(NAN)));assert(std::isnan(voltageSoc(5)));
 assert(voltageSoc(3.0f)==0);assert(voltageSoc(4.2f)==100);
 float previous=0;for(float v=2.5f;v<4.35f;v+=.001f){float p=voltageSoc(v);assert(p>=previous&&p<=100);previous=p;}
 assert(mainSupplyPresent(1562,false));assert(!mainSupplyPresent(0,true));assert(mainSupplyPresent(1300,true));assert(!mainSupplyPresent(1300,false));
 DebouncedSwitch input;assert(!input.update(true,0));assert(!input.update(false,5));assert(!input.update(true,10));assert(!input.update(true,39));assert(input.update(true,40));assert(input.update(false,50));assert(!input.update(false,80));
 DebouncedSwitch wrap;assert(!wrap.update(true,0xfffffff0U));assert(wrap.update(true,0x20U));
 // INA3221 register units, current sign and selected board limit.
 Ina3221Reading r;
 assert(decodeIna3221(475u<<3,500u<<3,r));
 assert(std::fabs(r.bus_v-3.8f)<.0001f && std::fabs(r.current_a-.2f)<.0001f);
 assert(decodeIna3221(475u<<3,uint16_t(-4000),r));
 assert(std::fabs(r.current_a+.2f)<.0001f);
 assert(decodeIna3221(1500u<<3,500u<<3,r));
 assert(std::fabs(r.bus_v+r.shunt_v-12.02f)<.0001f);
 assert(decodeIna3221(0,0,r) && r.current_a==0);
 assert(decodeIna3221(475u<<3,2750u<<3,r));
 assert(!decodeIna3221(475u<<3,2751u<<3,r) && std::isnan(r.current_a));
 assert(!decodeIna3221(475u<<3,uint16_t(-22008),r));
 assert(!decodeIna3221(0xffff,0xffff,r));
 assert(!decodeIna3221(3275u<<3,0,r)); // 26.2V is outside chip rating
 assert(!decodeIna3221(100u<<3,1,r)); // reserved bits are not data
}
