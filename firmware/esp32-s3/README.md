# ESP32-S3 merací uzol

Firmware 0.2.0 pre Arduino IDE posiela každú sekundu výkon panela, osvetlenie, prepínače a voliteľne meranie malej batérie. ESP a svetlá napája laboratórny zdroj; batériu nabíja solárny panel cez BQ24074. Presné zapojenie a nastavenie nabíjacieho prúdu sú v [KOMPONENTY.md](../../docs/KOMPONENTY.md).

V Library Manager nainštalujte **Adafruit INA219**, **Adafruit MAX1704X**, **BH1750** od Christophera Laws a ich ponúknuté závislosti. WiFi, HTTPClient a Wire sú v Arduino ESP32 core. [Oficiálny MAX17048 Arduino návod](https://learn.adafruit.com/adafruit-max17048-lipoly-liion-fuel-gauge-and-battery-monitor/arduino).

1. Spustite PC aplikáciu, aby vznikol `data/device_key.txt`.
2. Skopírujte `secrets.example.h` ako `secrets.h`. Doplňte Wi-Fi, LAN adresu PC a kľúč zariadenia.
3. Vyberte konkrétnu ESP32-S3 dosku a nahrajte `.ino`.
4. V aplikácii vypnite Demo a nastavte kapacitu článku v mAh. Kalibrujte výkon panela pod používaným osvetlením.

`secrets.h` a merania zostávajú mimo Gitu. Router nesmie izolovať klientov. Pri nahrávaní z PC odpojte USB napájanie z laboratórneho zdroja.

I²C: SDA GPIO 8, SCL GPIO 9, logika 3,3 V. INA219 0x40, MAX17048 0x36 a BH1750 0x23 zdieľajú zbernicu. Gauge musí byť pripojený na článok; bez neho nemusí odpovedať. Firmware jeho pripojenie opakovane skúša, panel funguje ďalej. Prepínače: GPIO 4/5/6 proti GND. LED: GPIO 7/10/11 cez samostatné rezistory. Skontrolujte piny svojej dosky.

Panel `+ → INA219 VIN+ → VIN− → BQ24074 solárny vstup +`. Mínus panela je GND. Stará 47 Ω záťaž sa nepoužíva. Nabíjačka BATT a chránený článok idú na dva paralelné JST porty Adafruit MAX17048. BQ24074 LOAD zostáva voľný; batéria+ sa nespája s laboratórnymi 5 V.

Nové voliteľné JSON polia: `battery_voltage_v`, `battery_soc_pct`, `battery_charge_rate_pct_h`. SOC a napätie sa posielajú spoločne; trend nie je meranie prúdu. Starší firmware zostáva kompatibilný a batériu zobrazuje ako nedostupnú. API kontroluje kľúč, rozsahy aj nečíselné hodnoty.

Kompilácia na konkrétnej doske a fyzické nabíjanie vyžadujú overenie na zakúpenom hardvéri.
