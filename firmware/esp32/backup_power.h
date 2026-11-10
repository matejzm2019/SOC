#pragma once
#include <cmath>
inline float voltageSoc(float v) {
  if (!std::isfinite(v) || v<2.5f || v>4.35f) return NAN;
  const float volts[]={3.30f,3.50f,3.60f,3.70f,3.75f,3.80f,3.85f,3.95f,4.05f,4.15f,4.20f};
  const float soc[]={0,5,10,25,40,50,60,75,85,95,100};
  if(v<=volts[0])return 0;
  for(unsigned i=1;i<sizeof(volts)/sizeof(volts[0]);++i)
    if(v<=volts[i])return soc[i-1]+(soc[i]-soc[i-1])*(v-volts[i-1])/(volts[i]-volts[i-1]);
  return 100;
}
inline bool mainSupplyPresent(unsigned mv,bool previous){return previous?mv>1200:mv>=1400;}
