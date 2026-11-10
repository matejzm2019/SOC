# Overenie verzie 0.12.0-assistant

Historický záznam 8. 11. 2026 pre pôvodné ESP32-S3; na dosku ESP-32D platí novšia sekcia nižšie. Overenie softvéru a rozmerového návrhu, nie protokol skúšok fyzicky postaveného domu.

- **84 úspešných testov, 1 preskočený**: Windows spúšťač na Linuxe. Dve upozornenia testovacích knižníc sa týkajú zastarávajúcich rozhraní.
- Testy asistenta: zajtrajšok cez miestnu polnoc, predpoveď iného mesta/časovej zóny a konkrétnej hodiny, chýbajúca lokalita, vypnutý internet, zachovanie všeobecných vedeckých čísel, natívne nástroje Ollamy, označená encyklopedická náhrada, neznáme nástroje a limit kôl. Zmena AI volieb nezmaže energetickú históriu a nepremiestni uloženú lokalitu domu.
- Reálne HTTP načítanie Open-Meteo overilo konkrétny nasledujúci kalendárny deň pre Bratislavu. Reálne vyhľadanie FreeRTOS vrátilo relevantný článok Wikipédie; verejný DuckDuckGo v tomto prostredí vrátil ochrannú stránku, preto bola použitá označená náhrada. Nejde o overenie neobmedzeného vyhľadávania celého internetu.
- Chromium/WebGL: panel A/B mimo chodníka, odkrytie elektroniky, strecha a panel spolu, aktuálna navigácia, mobilná šírka 390 px bez horizontálneho pretečenia. Prehliadačová skúška chatu spojila skutočnú online predpoveď s testovacou HTTP odpoveďou Ollamy a overila zdrojové odkazy aj všeobecné čísla. Bez zachytených JavaScriptových chýb pri kontrolovaných krokoch.
- **Skutočná inferencia 4B modelu sa v tomto prostredí nespúšťala.** Overené boli jeho HTTP požiadavky, kontext, výber nainštalovaného názvu a protokol nástrojov. Kvalita slovenčiny, rýchlosť a správanie nainštalovaného modelu sa overujú na prezentačnom PC.
- Arduino CLI 1.5.1, core ESP32 3.3.12, N16R8 (16 MB flash, OPI PSRAM), Adafruit INA219 1.2.3, ArduinoJson 7.4.3. Produkčný firmvér 0.7.0-controls zostavený: **1 055 439 B / 48 804 B**. Simulátor: **421 100 B / 29 256 B**.
- C++ skúšky používajú priamo backup_power.h a switch_input.h: napäťový odhad, hysterézia hlavného zdroja, odrušenie kontaktov a pretečenie millis. Miestna úloha vzorkuje po 10 ms a vyžaduje 30 ms stabilného kontaktu nezávisle od HTTP.
- Rozmerové testy: 600 × 450 mm podstava, panel na streche a jeho odstup, zhodnosť aplikácie s CAD exportom, ovládanie mimo chodníka, správna poloha strešných dorazov. Návrh má **395 geometrických objektov** aj v GLB/STL, nie iba v renderi. L03 sú skrátené na 440 mm medzi bočné nosníky; L02 sú pod L01.
- Sedemstranové A3 PDF, nosné diely P01–P11/L01–L04 a panel C01, samostatný kusovník detailov, aktualizované SVG a vodiče. C01 má kontrolnú mierku 50 mm, väčšie šablóny 100 mm.

## Čo skontrolovať na fyzickom modeli

Over dovolený nabíjací prúd článku a skutočné nastavenie CN3791; predajné 4 A MAX nie sú odporúčaný prúd tejto batérie. CN3791 nemá samostatný systémový power-path, úplné prednabitie sa robí s odpojenou záťažou podľa ZAPOJENIE.md.

Zmeraj MT3608 na 5 V, stabilitu pri Wi-Fi špičkách, adresy INA219, polaritu a znamienko prúdu. Vyskúšaj výpadok hlavného zdroja pri zapnutých LED. Percentá z napätia nie sú meranie využiteľnej kapacity. Hmotnosť 4–5 kg je odhad bez váženia.

Over úchyty skutočného rámu panela, dĺžky skrutiek, tuhosť strechy a odľahčenie kábla. Pred úplným odložením strechy rozpoj konektor panela. Na C01 over závity konkrétnych prepínačov a podľa potreby zapusti ich montážnu hrúbku; telá sú pod panelom na 15 mm stĺpikoch. Pri spodných skrutkách použi zápustné hlavy, aby nekolidovali s nožičkami.

Elektroobálky a spojky nie sú garantované vrtné šablóny. Samostatná simulácia neoverí skutočné nabíjacie prúdy ani ochrany LiPo. Úplná podpora konkrétnych modulov v BenchTwin nebola potvrdená.

## Doplnená kontrola formátovania chatu

Chromium overil nadpisy vrátane `###`, zvýraznenie, vnorené zoznamy, tabuľky, odkazy a kód. Skúška potvrdila, že HTML/script z odpovede sa nespustí, nebezpečné odkazy nie sú klikateľné a obrázky nespustia externú požiadavku. Pri šírke 390 px dlhý kód a tabuľka posúvajú svoj obsah bez roztiahnutia stránky; pri kontrolovaných krokoch neboli JavaScriptové chyby.

## Aktuálna doska ESP-32D – 10. 11. 2026

Fotografia používateľa potvrdzuje 38-pinovú USB-C dosku s modulom ESP-32D (klasické ESP32); kapacita flash ani presná revízia dosky sa z nej nedajú overiť. Aktuálny firmvér je `firmware/esp32/energia_esp32.ino`, verzia 0.8.0-esp32d. Staré S3 piny a nastavenie N16R8 sa nepoužívajú.

- Reálna kompilácia Arduino CLI 1.5.1, Espressif core 3.3.12, cieľ `esp32:esp32:esp32` (ESP32 Dev Module, predvolené 4 MB, PSRAM vypnutá), Adafruit INA219 1.2.3 a ArduinoJson 7.4.3: **1 063 388 B programu, 50 424 B RAM**. Produkčný kód výslovne odmietne nesprávny cieľ S3.
- Samostatný BenchTwin sketch mimo projektu sa zostavil pre rovnaké ESP32: **303 200 B programu, 23 612 B RAM**. Toto nie je vykonanie celého elektrického obvodu v BenchTwin.
- C++ test `house_guard_test.cpp` prešiel s `-Wall -Wextra -Werror`: odhad SOC, hysterézia, odrušenie a pretečenie millis. Je zaradený aj do CI. JavaScript prešiel syntaktickou kontrolou.
- GPIO34 je ADC1 pre hlavný zdroj (delič 22 kΩ/10 kΩ); prepínače 32/33, LED 25/26, indikácia 27, I²C 21/22. GPIO6–11 sa nepoužívajú. Náhradné ADC softvérového testu sú 35/36/39.
- Zapojenie, kusovník, PDF, vodiče, generátory, aplikácia, Blender/GLB/STL aj náhľady sú aktualizované. Obe kópie model.json sú zhodné; zostalo 395 objektov a podstava 600 × 450 mm. Obálka ESP 70 × 32 mm je montážna rezerva, nie meranie konkrétnej dosky.
- BC547BBK je vhodný pre cca 15–20 mA na vetvu troch malých LED s vlastnými 330 Ω. Kondenzátor 470 µF / 16 V je na 5 V vetve dostatočný. Poradie C/B/E, polarita, stabilita napájania a reálny nabíjací prúd sa overujú na fyzických dieloch. Firmvér tu nebol nahraný do používateľovej dosky.
