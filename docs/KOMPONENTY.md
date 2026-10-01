# Komponenty a zapojenie modelu domu

Zostava používa malé jednosmerné napätie. Powerbanka nabíja **skutočnú batériu modelu** cez nabíjací modul. Batéria cez modul napája ESP32-S3 a LED svetlá domu aj po odpojení powerbanky. Malý solárny panel sa meria samostatne cez INA219; pod stolovou lampou nemá dosť stabilného výkonu na napájanie celého modelu. V aplikácii je výroba veľkej FV, domáca spotreba, sieť a jej virtuálny SOC stále modelová veličina.

## Nákupný zoznam

| Počet | Komponent | Špecifikácia a úloha |
|---:|---|---|
| 1 | ESP32-S3 DevKit | Wi-Fi, odosielanie meraní, ovládanie LED |
| 1 | Solárny panel | 5–6 V, asi 0,5–1 W; meraný vstup osvetľovaný lampou |
| 1 | INA219 | I²C senzor napätia, prúdu a výkonu panela |
| 1 | BH1750 | I²C senzor osvetlenia v luxoch |
| 1 | Výkonový rezistor | 47 Ω / aspoň 2 W ako záťaž panela |
| 1 | PowerBoost 1000C alebo ekvivalent s **load sharing** | Nabíjanie 1-článkovej 3,7 V LiPo batérie z USB a stabilný 5 V výstup pre ESP32 |
| 1 | Chránená LiPo batéria | 3,7 V, približne 2 000 mAh, JST-PH 2-pin, polarita zhodná s nabíjacím modulom |
| 1 | USB-A výstupný konektor pre modul | Umožní pripojiť ESP32 bežným USB dátovým káblom k 5 V výstupu modulu |
| 1 | Powerbanka | 5 V, aspoň 10 000 mAh; napája vstup nabíjacieho modulu a lampu |
| 1 | USB LED lampa | 5 V, nastaviteľná; svieti na panel |
| 2 | LED pre okná domu | napríklad teplá biela, nízky odber |
| 1 | LED stavu siete | modrá alebo zelená |
| 3 | Rezistor pre LED | 220–330 Ω, 0,25 W, každý v sérii s jednou LED |
| 3 | Tlačidlo alebo prepínač | dve záťaže a simulovaný výpadok siete |
| 1 | Breadboard a Dupont vodiče | prototypové zapojenie senzorov a prepínačov |
| 1 | USB dátový kábel pre ESP32 | programovanie a napájanie z výstupu modulu |
| 1 | Micro-USB kábel pre PowerBoost 1000C | 5 V vstup z powerbanky |
| 1 | Wi-Fi router | existujúci alebo cestovný USB router; spája ESP32, notebook a mobil |
| 1 | Notebook a materiál domu | notebook beží na vlastnej batérii; dom z kartónu alebo penovej dosky |

Batéria a PowerBoost musia mať správne zhodnú polaritu konektora JST. Odporúčaná chránená batéria [Adafruit 3,7 V / 2 000 mAh](https://www.adafruit.com/product/2011) má ochranný obvod. [PowerBoost 1000C](https://learn.adafruit.com/adafruit-powerboost-1000c-load-share-usb-charge-boost) má nabíjanie, prepínanie medzi USB a batériou a približne 5,2 V výstup. Jeho žltá a zelená LED ukazujú nabíjanie a dokončenie nabíjania; červená upozorňuje na nízke napätie batérie. Model nepočíta percentuálny SOC z tejto fyzickej batérie.

## Tok napájania a dát

```text
Powerbanka 5 V ──micro-USB──> PowerBoost 1000C <──JST── chránená LiPo 3,7 V
                                    │ 5 V výstup cez USB-A
                                    └──USB──> ESP32-S3 ──GPIO──> 2 LED svetlá + LED siete

Powerbanka 5 V ──USB──> stolová LED lampa ──svetlo──> solárny panel
                                                      │
                                                      └──INA219──47 Ω záťaž
ESP32-S3 <──I²C── INA219 + BH1750
ESP32-S3 ──Wi-Fi──> router ──Wi-Fi──> notebook s webovou aplikáciou
                                  └──Wi-Fi──> mobilný prehliadač
```

Pri odpojení powerbanky od nabíjacieho modulu batéria ďalej napája ESP32 a LED. Lampa sa vypne, ak bola na tej istej powerbanke; panel potom prestane vyrábať a dashboard to ukáže. Router musí mať vlastné napájanie, napríklad druhú powerbanku alebo batériu, aby Wi-Fi zostala dostupná aj pri tejto ukážke. Na bežné predvedenie môže zostať router aj lampa stále napájaná.

## Zapojenie k ESP32-S3

| ESP32-S3 | Pripojenie |
|---|---|
| USB konektor | 5 V výstup nabíjacieho modulu cez USB-A a dátový kábel |
| 3V3 | VCC INA219 a BH1750 |
| GND | GND senzorov, prepínačov a troch LED |
| GPIO 8 / GPIO 9 | spoločná I²C zbernica SDA / SCL pre INA219 a BH1750 |
| GPIO 4 | tlačidlo simulovaného výpadku do GND |
| GPIO 5 / GPIO 6 | prepínače dvoch záťaží do GND |
| GPIO 7 / GPIO 10 | dve domové LED, každá cez vlastný 220–330 Ω rezistor do GND |
| GPIO 11 | LED stavu siete cez vlastný 220–330 Ω rezistor do GND |

Panel: `+` → INA219 `VIN+` → `VIN-` → 47 Ω / 2 W → mínus panela. Mínus panela musí mať spoločnú referenciu GND s meracou časťou. Panel sa **nepripája** na USB, GPIO ani na batériu. LED sú pripojené na výstupy ESP32, nie priamo na panel. Pred zapojením treba skontrolovať polaritu panela a batérie.

## Čo bude vidieť pri ukážke

1. Zakrytie alebo osvetlenie panela zmení reálne nameraný výkon a lux; aplikácia podľa toho prepočíta virtuálnu FV.
2. Dva prepínače rozsvietia domové LED a zároveň zvýšia virtuálnu spotrebu.
3. Tlačidlo výpadku vypne LED siete a nastaví virtuálny import/export na nulu.
4. Odpojenie powerbanky od nabíjacieho modulu ukáže, že ESP32 a domové LED bežia z fyzickej batérie. Ak sa vypne aj lampa, výkon panela klesne.
5. Notebook a mobil otvoria ten istý lokálny dashboard. Internet nie je potrebný.

Všetky spoje a batéria majú byť upevnené v krabičke; breadboard slúži na prototyp, nie na trvalé uloženie článku. Použite iba chránenú batériu a kompatibilný nabíjací modul. Nenabíjajte LiPo článok priamo z powerbanky ani zo solárneho panela. [Výrobca výslovne upozorňuje](https://learn.adafruit.com/adafruit-powerboost-1000c-load-share-usb-charge-boost/pinouts) aj na možnú opačnú polaritu niektorých cudzích JST konektorov.
