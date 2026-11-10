# SOČ – ESP-32D, aktuálny balík

Aktualizované 10. 11. 2026 podľa fotografie používateľovej 38-pinovej USB-C dosky ESP-32D. Zdrojový commit: 593a6b108e7d6476cc2f29b11e189640b731f2b0.

- [Stiahnuť celý projekt ZIP](SOC-vsetko.zip?raw=1)
- [Aktuálne zapojenie ESP-32D](ZAPOJENIE-ESP32D.md)
- [Návod pre BenchTwin](BENCHTWIN-NAVOD.txt)
- [Skúšobný kód pre BenchTwin ZIP](BENCHTWIN-KOD.zip?raw=1)
- [Zmeny zdrojov – PR #4](https://github.com/matejzm2019/SOC/pull/4)

Rozbaľ SOC-vsetko.zip. SOC obsahuje aplikáciu, firmware/esp32/energia_esp32.ino, model a stavebné PDF. SOC-simulacia je samostatne vedľa projektu. Použi aktuálne zapojenie; pôvodné S3 GPIO6–11 na klasickom ESP32 patria flash.

| Pripojenie | GPIO |
|---|---|
| Hlavný zdroj cez delič 22 kΩ / 10 kΩ | 34 (ADC1) |
| Prepínače A / B proti GND | 32 / 33 |
| BC547 svetiel A / B cez 1 kΩ | 25 / 26 |
| Modrá LED cez 330 Ω | 27 |
| INA219 SDA / SCL | 21 / 22 |

Dva BC547BBK zo zásob stačia na dve vetvy po troch malých LED s vlastným 330 Ω. Kondenzátor 470 µF / 16 V patrí na 5 V vetvu, plus na 5 V a mínus na GND. GPIO používajú iba 3,3 V logiku. Over poradie C/B/E konkrétnych tranzistorov.

Arduino IDE: ESP32 Dev Module, PSRAM Disabled; kapacitu flash over pri nahrávaní, z fotografie nie je známa. Kompilácia produkcie aj samostatného skúšobného sketchu pre klasické ESP32 prešla. Automatické kontroly PR tiež prešli. Fyzický beh na používateľovej doske ani celý BenchTwin obvod tu nebol overený.

BenchTwin: Build → Wire → Code → Simulate. BENCHTWIN-KOD.zip importuje kód, nie zapojenú 3D scénu. Produkčný firmvér používa FreeRTOS, ktorý BenchTwin aktuálne nepodporuje; skúšobný sketch používa loop()/millis(), overuje ovládanie a hlavný zdroj, nevyrába percentá ani HTTP telemetriu. Podpora druhej adresy INA219 a siete závisí od konkrétnej verzie/funkcií BenchTwin.

AI zostáva na PC cez Ollamu. Chat má sformátované nadpisy, zoznamy, tabuľky a kód; knižnice sú pribalené bez CDN.
