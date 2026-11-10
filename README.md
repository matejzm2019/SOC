# SOČ – jeden celý zoznam a dva INA3221

**[OTVORIŤ CELÝ ZOZNAM KOMPONENTOV A MATERIÁLU](ZOZNAM-KOMPONENTOV.md)**

Toto je jediný platný nákupný zoznam pre aktuálnu zostavu: elektronika, presné množstvá rezistorov/LED, konektory, vodiče, drevené diely, detaily, úchyty a vybavenie. Ostatné dokumenty popisujú zapojenie a funkciu. Objednávaj len to, čo ešte nemáš.

- [Stiahnuť celý aktuálny projekt ZIP](SOC-vsetko.zip?raw=1)
- [Zapojenie domu](ZAPOJENIE-ESP32D.md)
- [INA3221 – adresy, meracie piny a rozdiely dosiek](INA3221.md)
- [12 V solár a dobíjanie zo zdroja](PANEL-12V-A-OBJEDNAVKA.md)
- [BenchTwin návod](BENCHTWIN-NAVOD.txt)
- [BenchTwin skúšobný kód ZIP](BENCHTWIN-KOD.zip?raw=1)
- [Zdrojové zmeny PR #5](https://github.com/matejzm2019/SOC/pull/5)

Aktualizované 10. 11. 2026, source commit 41a0b022bce204b8fda5e0027a1d267da8b2403d. Archív má SOC a samostatný SOC-simulacia vedľa seba.

Používame ESP-32D, existujúci panel označený 12 V, chránenú LiPo 2500 mAh, CN3791 variant 12 V, MT3608, dva INA3221 CH1, 5 V relé, BC547 a 470 µF / 16 V iba na 5 V vetve. Hlavné moduly CN3791 + MT3608 + dva INA3221 + relé vychádzajú na 16,15–16,25 € bez dopravy/drobností; plná objednávka je v uvedenom zozname.

PANEL 0x40, BAT 0x41, čipové VS/VCC senzorov 3V3. Kladné meracie vstupy sú oddelené. Staršia doska má spoločný výkonový POW a CH1/GND, novšia IN1+/IN1−. Meracie piny over podľa R100; dvojica CH1/GND nie sú dva konce bočníka. Dodrž predajcov limit dosky 1,1 A pri nabíjaní aj vybíjaní a rezervu pod 26 V. Výkon, Voc a rozmery panela sú stále nepotvrdené. Over prúd článku a RCS nabíjačky.

Firmvér 0.9.0-ina3221 používa Adafruit INA3221 Library 1.0.3, BusIO a ArduinoJson 7. Prešla kompilácia pre klasické ESP32, 85 testov (1 preskočený), kontrola znamienka/prúdu/registra, I2C chýb, geometrie a odkazov. Fyzická elektronika ani celý BenchTwin obvod tu neboli odskúšané. Softvér nezastaví elektrické preťaženie.

BenchTwin má samostatnú loop()/millis() diagnostiku s I2C identitou, produkcia používa FreeRTOS. Podpora konkrétneho INA3221 modelu v simulátore nie je potvrdená; elektrická skúška meradlami nie je úplný test registrov. AI zostáva na PC cez Ollamu.
