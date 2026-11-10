# ESP-32D / klasické ESP32 – firmvér 0.8.0-esp32d

Aktuálna doska je používateľova 38-pinová USB-C doska s modulom označeným ESP-32D. Nie je to ESP32-S3. Dva INA219, hlavný zdroj, dve svetelné vetvy a Wi-Fi telemetria pre FastAPI na PC. Pinová tabuľka: [ZAPOJENIE.md](../../docs/ZAPOJENIE.md).

1. Arduino IDE: balík **esp32 by Espressif Systems**, doska **ESP32 Dev Module**, PSRAM **Disabled**. Pre bežný 4 MB variant použi predvolené 4 MB; skutočnú flash over pri nahrávaní/esptool, z fotografie sa jej kapacita nedá určiť. Nevyberaj S3, 16 MB ani OPI PSRAM podľa pôvodného návodu.
2. Knižnice Adafruit INA219 a ArduinoJson 7 vrátane závislostí.
3. `energia_esp32.ino`, `backup_power.h`, `switch_input.h` vlož do priečinka `energia_esp32` podľa názvu .ino.
4. `secrets.example.h` skopíruj na `secrets.h`; doplň Wi-Fi, LAN URL a DEVICE_KEY z `data/device_key.txt`. Súbor s heslami necommituj.
5. Pri programovaní odpoj externých 5 V. Pri prevádzke je ESP na MT3608 nastavenom na 5 V, pripojenom na označený 5V vstup dosky alebo jej USB napájací konektor. USB a externých 5 V nespájaj bez overenia napájania konkrétnej dosky. Ak nahrávanie stojí na Connecting, podrž BOOT do začiatku zápisu a potom ho pusť.

Úloha local-control číta každých 10 ms prepínače GPIO32/33, spína BC547 vetiev GPIO25/26 a sleduje hlavný zdroj cez delič 22 kΩ/10 kΩ na GPIO34 (ADC1, použiteľný aj s Wi-Fi). Kontakty sa prijmú až po 30 ms stabilného stavu, nezávisle od servera. GPIO27 indikuje hlavný zdroj. Relé prepína zdroje LED hardvérovo.

I²C: GPIO21 SDA / GPIO22 SCL, panel 0x40, batéria 0x41, logické napájanie 3,3 V. GPIO6–11 patria flash pamäti a nesmú sa použiť. Použité riadenie obchádza aj bootovacie strapping piny. GPIO34 je iba vstup, čo je pre delič správne.

Chýbajúci panelový merač zabráni odoslaniu vymyslených dát; chýbajúci batériový merač vynechá jeho hodnoty. Telemetria sa posiela každú sekundu. Prúd batérie je kladný pri nabíjaní. Percentá `voltage_estimate` sú orientačné, nemerajú kapacitu článku.

`SIMULATED_SENSORS=1` používa náhradné ADC1 vstupy GPIO35/36/39; `WIFI_ENABLED=0` umožní iba Serial. Na skutočnú zostavu patria predvolené `SIMULATED_SENSORS=0` a `WIFI_ENABLED=1`. Firmvér nemá bežať v BenchTwin bez úprav FreeRTOS; na BenchTwin je samostatný sketch mimo projektu.
