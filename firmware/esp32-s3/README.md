# ESP32-S3 N16R8 – firmvér 0.7.0-controls

Dva INA219, hlavný zdroj, dve svetelné vetvy a Wi-Fi telemetria pre FastAPI na PC. Panel je na odnímateľnej streche. Pinová tabuľka: [ZAPOJENIE.md](../../docs/ZAPOJENIE.md).

1. Arduino IDE: ESP32S3 Dev Module, flash 16 MB, PSRAM OPI. Core Espressif 3.3.12 bol použitý pri overovaní návrhu.
2. Knižnice Adafruit INA219 a ArduinoJson 7 vrátane závislostí.
3. Sketch, backup_power.h a switch_input.h vlož do priečinka energia_esp32_s3 podľa názvu .ino.
4. secrets.example.h skopíruj na secrets.h; doplň Wi-Fi, LAN URL a DEVICE_KEY z data/device_key.txt. Súbor s heslami necommituj.
5. Pri programovaní odpoj externých 5 V. Pri prevádzke je ESP na MT3608 nastavenom na 5 V. Dve napájania USB nespájaj bez overenia konkrétnej dosky.

Úloha local-control číta každých 10 ms prepínače na GPIO5/6, spína LED tranzistory GPIO7/10 a sleduje hlavný zdroj cez delič 22 kΩ/10 kΩ na GPIO4. Kontakty sa prijmú až po 30 ms stabilného stavu. Relé prepína zdroje LED hardvérovo. Prepínače A/B sú na paneli C01 vľavo vpredu, nie v chodníku. GPIO11 indikuje hlavný zdroj. GPIO12–16 sú nepoužité.

I²C GPIO8/9: panel 0x40, batéria 0x41, logické napájanie 3,3 V. Chýbajúci panelový merač zabráni odoslaniu vymyslených dát; chýbajúci batériový merač vynechá jeho hodnoty. Telemetria sa posiela každú sekundu. Prúd batérie je kladný pri nabíjaní, percentá voltage_estimate sú orientačné a nemerajú kapacitu článku.

SIMULATED_SENSORS=1 používa náhradné analógové vstupy GPIO1/17/18. WIFI_ENABLED=0 umožňuje iba výpis do Serial monitora. Tieto voľby sú len v oddelenom simulačnom balíku. Skutočná doska musí mať SIMULATED_SENSORS=0 a WIFI_ENABLED=1. Starší firmvér s dodatočnými telemetrickými poľami treba pred používaním tejto verzie aplikácie aktualizovať.
