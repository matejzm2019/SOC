# ESP32-S3 merací uzol

Firmvér pre Arduino IDE pripája ESP32-S3 k domácemu routeru a každú sekundu odošle meranie panela do FastAPI servera.

## Knižnice

V Arduino Library Manager nainštalujte:

- Adafruit INA219
- BH1750 od Christophera Laws

`WiFi`, `HTTPClient` a `Wire` sú súčasťou Arduino ESP32 core.

## Príprava

1. Spustite PC aplikáciu aspoň raz. Vznikne `data/device_key.txt`.
2. Skopírujte `secrets.example.h` ako `secrets.h`.
3. Vyplňte Wi-Fi, IP adresu PC zo štartovacieho okna a kľúč zariadenia.
4. V Arduino IDE vyberte svoju konkrétnu dosku ESP32-S3 a nahrajte `energia_esp32_s3.ino`.

`secrets.h` sa neukladá do Gitu. ESP32 aj PC musia byť v rovnakej lokálnej sieti. Router s izoláciou Wi-Fi klientov musí mať túto izoláciu vypnutú, inak sa zariadenia neuvidia.

## Zapojenie

| ESP32-S3 | Modul |
|---|---|
| 3V3 | INA219 VCC, BH1750 VCC |
| GND | INA219 GND, BH1750 GND, mínus panela |
| GPIO 8 | SDA oboch I²C modulov |
| GPIO 9 | SCL oboch I²C modulov |
| GPIO 4 | tlačidlo výpadku proti GND |
| GPIO 5 | prepínač záťaže 1 proti GND |
| GPIO 6 | prepínač záťaže 2 proti GND |
| GPIO 7 | LED záťaže 1 cez rezistor 220 Ω do GND |
| GPIO 10 | LED záťaže 2 cez rezistor 220 Ω do GND |
| GPIO 11 | modrá LED siete cez rezistor 220 Ω do GND |

Panel plus pripojte na `INA219 VIN+`, `VIN-` na kladný vývod 47 Ω / 2 W záťaže a druhý vývod záťaže na spoločný GND. Kratšia nožička každej LED ide na GND. ESP32 napájajte cez USB z 5 V výstupu modulu PowerBoost 1000C. K modulu patrí chránená 3,7 V batéria cez JST a powerbanka na jeho micro-USB nabíjacom vstupe. Panel nepripájajte na GPIO, batériu ani na napájací pin ESP32. Presný nákupný zoznam a schéma sú v [docs/KOMPONENTY.md](../../docs/KOMPONENTY.md).

GPIO čísla možno zmeniť na začiatku `.ino` podľa konkrétnej dosky. Pri paneli s vyšším výkonom zvoľte záťaž podľa jeho parametrov; táto schéma je určená pre približne 6 V / 1 W panel.
