# Komponenty a zapojenie modelu domu

**Laboratórny zdroj napája ESP32 a LED domu. Solárny panel cez nabíjačku nabíja samostatnú malú Li-ion batériu.** Batéria nenapája ESP ani svetlá. Notebook spracúva merania a poskytuje web pre PC aj mobil.

## Nákupný zoznam

| Počet | Komponent | Požiadavka a účel |
|---:|---|---|
| 1 | ESP32-S3 DevKit | Wi-Fi, Arduino ESP32 core, USB napájanie |
| 1 | Solárny panel | Nominálne 6 V, približne 1–3 W; napätie naprázdno musí vyhovovať nabíjačke |
| 1 | INA219 breakout | Napätie, prúd a výkon panela; I²C adresa 0x40 |
| 1 | BQ24074 solar charger breakout | Adafruit Universal USB/DC/Solar Charger alebo overená ekvivalentná doska s riadením solárneho vstupu |
| 1 | Chránený Li-ion/LiPo článok | Jeden článok: nominálne 3,7 V, nabíjanie na 4,2 V; 1 000–2 000 mAh, povolený nabíjací prúd aspoň 0,5 A, kompatibilný JST-PH konektor a polarita |
| 1 | MAX17048 breakout | Odhad SOC a meranie napätia článku; Adafruit doska s dvoma paralelnými JST konektormi, adresa 0x36 |
| 1 | BH1750 | Voliteľný merač osvetlenia, adresa 0x23; firmware ho podporuje |
| 1 | Laboratórny zdroj | Stabilizovaných 5 V DC, prúdový limit podľa dosky a záťaží |
| 1 | USB napájací adaptér/kábel | Privedenie 5 V zo zdroja do USB ESP; skontrolovaná polarita |
| 1 | Multimeter | Kontrola napätia a polarity pred pripojením |
| 1 | LED lampa | Napájanie podľa požiadaviek lampy, napríklad USB 5 V; dostatočné osvetlenie |
| 3 | LED | Dve pre okná domu, jedna modrá pre stav modelovanej siete |
| 3 | Rezistor LED | 220–330 Ω; každý v sérii so svojou LED |
| 3 | Prepínač/tlačidlo | Dve záťaže a výpadok modelovanej siete |
| 1 sada | Vodiče, breadboard a konektory | Izolovaný kryt batérie a materiál domu |
| existujúce | Notebook, router a mobil | Rovnaká sieť bez izolácie Wi-Fi klientov |

**PowerBoost a 47 Ω záťaž z predchádzajúceho návrhu už netreba.** Panel má ako záťaž nabíjačku. Powerbanka je iba voliteľný alternatívny 5 V zdroj pre ESP; nenabíja článok v tomto zapojení.

## Schéma

```text
Laboratórny zdroj 5 V DC ── USB napájanie ── ESP32-S3 ── rezistory ── LED domu
                                           │
                        SDA 8 / SCL 9 ──────┼── INA219 (0x40)
                                           ├── MAX17048 (0x36)
                                           └── BH1750 (0x23, voliteľný)

Panel + ── INA219 VIN+ → VIN− ── BQ24074 solar/DC vstup +
Panel − ─────────────────────── BQ24074 vstup GND
BQ24074 BATT JST ── MAX17048 JST č. 1
Chránená batéria ── MAX17048 JST č. 2 (paralelné JST porty)

Všetky GND majú spoločnú referenciu.
BQ24074 LOAD výstup zostane nezapojený.
Batéria + sa NESPÁJA s laboratórnymi 5 V.

ESP32 ── Wi-Fi ── router ── notebook/FastAPI/SQLite/Ollama
                         └── mobil alebo ďalší PC v prehliadači
```

MAX17048 je merač, nie nabíjačka ani ochrana článku. Dva JST porty uvedenej Adafruit dosky umožňujú pripojiť batériu a nabíjačku na rovnaký článok. Pri inom breakoute overte schému a polaritu; cudzí JST konektor môže mať opačnú polaritu. [MAX17048 pinouts](https://learn.adafruit.com/adafruit-max17048-lipoly-liion-fuel-gauge-and-battery-monitor/pinouts).

## ESP32 piny

| Pin | Pripojenie |
|---|---|
| USB | Stabilných 5 V z laboratórneho zdroja |
| 3V3 | Logické napájanie INA219, MAX17048 VIN a BH1750 |
| GND | Senzory, nabíjačka, panel, prepínače a LED |
| GPIO 8 / 9 | Spoločné SDA / SCL všetkých troch senzorov |
| GPIO 4 | Tlačidlo výpadku proti GND |
| GPIO 5 / 6 | Prepínače záťaží proti GND |
| GPIO 7 / 10 / 11 | Tri LED, každá cez samostatný rezistor do GND |

Skontrolujte dostupnosť GPIO na konkrétnej doske. I²C pull-up odpory musia smerovať na 3,3 V. Nikdy neposielajte 5 V na GPIO. Pri programovaní z PC odpojte USB napájanie ESP z laboratórneho zdroja; dva 5 V zdroje nespájajte bez vhodného oddelenia.

## Nastavenie nabíjačky

Adafruit BQ24074 má predvolený nabíjací prúd 1 A. Pre tento návrh nastavte **0,5 A** podľa výrobcu: prerušte jumper 1 A a prepojte jumper 0,5 A. Konkrétna batéria musí takýto prúd povoľovať; kapacita sama neurčuje povolený prúd. Solárny vstup dosky je určený pre panel 6–10 V; skontrolujte maximálne napätie naprázdno. [BQ24074 nastavenie a pinouts](https://learn.adafruit.com/adafruit-bq24074-universal-usb-dc-solar-charger-breakout/pinouts).

Výstup LOAD má približne 3–4,4 V, nie 5 V; tu sa nepoužíva. Článok nikdy nepripájajte priamo na panel ani laboratórnych 5 V. Použite chránený kompatibilný článok, správnu polaritu a izolované spoje. Poškodený či nafúknutý článok nepoužívajte. Montáž a prvé nabíjanie skontrolujte s učiteľom.

Na modeli sú iba nízke DC napätia. Bežný laboratórny zdroj však môže mať vstup 230 V vo svojom uzavretom prístroji; tvrdenie „celá zostava vôbec nepoužíva 230 V“ by nebolo presné. Na modeli sa so sieťovým napätím nepracuje.

## Reálne meranie

Normálny režim ukazuje SOC od MAX17048, napätie článku, menovitú kapacitu a orientačnú zostávajúcu energiu. Trend SOC je odhad v percentuálnych bodoch za hodinu, **nie meranie nabíjacieho prúdu**. Bez gauge/batérie sú hodnoty nedostupné; percentá nevytvárame jednoduchým pomerom napätia.

Osvetlenie zmení výkon panela a môže začať nabíjanie. Pod bežnou lampou však nemusí vzniknúť dostatok energie; overte to vopred aj na slnečnom svetle. Nabíjačka pri slabom vstupe obmedzuje odber. SOC sa mení pomaly; okamžitú zmenu ukáže výkon panela, dlhšie nabíjanie história SOC. [BQ24074 solárny vstup](https://learn.adafruit.com/adafruit-bq24074-universal-usb-dc-solar-charger-breakout).

Škálované kW domu a import/export sú výpočtové veličiny, nie meranie laboratórneho zdroja. V demo režime je aj batéria softvérová.
