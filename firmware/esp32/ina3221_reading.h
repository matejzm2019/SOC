#pragma once
#include <cmath>
#include <cstdint>

constexpr float INA3221_SHUNT_OHMS = 0.1f; // R100 on the selected Techfun module
constexpr float INA3221_MODULE_LIMIT_A = 1.1f; // seller's board rating, not ADC full scale
struct Ina3221Reading {
  float bus_v = NAN; // IN1- to GND: actual battery voltage in the battery circuit
  float shunt_v = NAN; // IN1+ minus IN1-
  float current_a = NAN; // positive into the battery for the documented wiring
};
inline bool decodeIna3221(uint16_t bus, uint16_t shunt, Ina3221Reading &out) {
  out = Ina3221Reading{};
  // Both registers are left-aligned by 3 bits; a negative bus or reserved bits
  // are invalid here. This also rejects an all-ones failed register read.
  if ((bus & 0x8007u) || (shunt & 7u)) return false;
  int32_t signedShunt = shunt >> 3;
  if (signedShunt & 0x1000) signedShunt -= 0x2000;
  const float busV = (bus >> 3) * 0.008f;
  const float shuntV = signedShunt * 0.000040f;
  const float amps = shuntV / INA3221_SHUNT_OHMS;
  const float sourceV = busV + shuntV;
  if (busV > 26 || sourceV > 26 || sourceV < -0.02f ||
      std::fabs(amps) > INA3221_MODULE_LIMIT_A + 0.00005f) return false;
  out.bus_v = busV; out.shunt_v = shuntV; out.current_a = amps;
  return true;
}
