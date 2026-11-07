#pragma once
#include <cstdint>
// Stable contact state after 30 ms. Unsigned elapsed time also survives millis wrap.
class DebouncedSwitch {
  bool candidate=false, stable=false;
  uint32_t since=0;
 public:
  bool update(bool raw,uint32_t now) {
    if(raw!=candidate){candidate=raw;since=now;}
    if(stable!=candidate&&uint32_t(now-since)>=30)stable=candidate;
    return stable;
  }
};
