# ESP-32D – firmvér 0.9.0-ina3221

Aktuálna zostava: dva samostatné INA3221, na každom kanál CH1; panel 0x40, batéria 0x41. Hlavný zdroj, dve LED vetvy a Wi-Fi telemetria do FastAPI na PC. AI zostáva na PC. Jeden celý zoznam: [KOMPONENTY.md](../../docs/KOMPONENTY.md).

1. Arduino IDE: **ESP32 Dev Module**, PSRAM Disabled. Pre bežný 4 MB variant predvolené 4 MB; skutočnú flash over pri nahrávaní/esptool, z fotografie nie je známa. Nevyberať S3/N16R8.
2. Nainštaluj **Adafruit INA3221 Library 1.0.3**, **Adafruit BusIO** a **ArduinoJson 7**. Knižnica pre starší merač sa už nepoužíva.
3. Do priečinka `energia_esp32` patria `energia_esp32.ino`, `backup_power.h`, `switch_input.h` a **ina3221_reading.h**. `secrets.example.h` skopíruj na ignorovaný `secrets.h`, doplň Wi-Fi, LAN URL a DEVICE_KEY z `data/device_key.txt`.
4. Čipové VS/VCC senzorov napájaj 3V3. SDA=21, SCL=22. PANEL A0=GND, BAT A0=VS (3V3), najprv odstrániť pôvodný mostík na GND. R100 je 0,1 Ω. Meria sa hardvérový CH1, v knižnici kanál **0**, nie 1.
5. Pred zapojením rozlíš meracie piny konkrétnej revízie: spoločný POW/VIN+ a kladný CH1 na starej doske alebo IN1+/IN1− na novej. Druhý pin CH1 môže byť GND. VS/VCC logiky nie je merací výkonový vstup. Návod [INA3221.md](../../docs/INA3221.md).
6. Pri programovaní odpoj externých 5 V. V prevádzke ESP napája overených 5 V z MT3608, nie panel priamo. USB a externý zdroj nespájať bez overenia napájania dosky. Pri Connecting prípadne podrž BOOT do začiatku zápisu.

GPIO34 ADC1 cez 22 kΩ/10 kΩ meria hlavné 5 V aj so zapnutou Wi-Fi. Prepínače 32/33, BC547 LED 25/26, modrá indikácia 27; GPIO6–11 patria flash a nepoužívajú sa. Local-control má vzorku 10 ms a vyžaduje 30 ms stabilného kontaktu, nezávisle od HTTP. Relé prepína zdroje hardvérovo.

Konfigurácia a kontrola čipu používajú knižnicu Adafruit. Meracie registre sa čítajú s kontrolou výsledku I2C a dĺžky odpovede, vrátane identity 0x5449/0x3220. Priemerovanie 16 vzoriek, prvá konverzia má 150 ms rezervu. Shunt má znamienko a krok 40 µV; bus 8 mV. R100 = 0,1 Ω. Vybraný Techfun modul je limitovaný **1,1 A**, hoci samotný ADC má väčší číselný rozsah.

Pri chýbajúcom/chybnom panelovom meraní sa telemetria neposiela, pri batériovom sa vynechajú iba batériové hodnoty. Každých 5 s sa skúša obnovenie chýbajúceho modulu. Neplatné čítanie sa nevydáva za nulu. Pri batérii sa zachová znamienko (+ nabíjanie, − vybíjanie) a meria sa napätie IN1− na článku. Percentá `voltage_estimate` sú orientačné, nie meranie kapacity. Softvérové odmietnutie merania nie je elektrické odpojenie preťaženia.

`SIMULATED_SENSORS=1` používa iba výslovne syntetický test 12 V / 1 W a ADC1 35/36/39; `WIFI_ENABLED=0` vypne HTTP. Fyzická zostava používa predvolené 0/1. Výkon, Voc a rozmery reálneho 12 V panela nie sú potvrdené. Kalibračný výkon sa určuje v aplikácii podľa nameraných W. Samostatný BenchTwin sketch zostáva mimo projektu a nie je produkčný firmvér.
