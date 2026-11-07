# Overenie verzie 0.12.0-assistant

8. 11. 2026. Overenie softvéru a rozmerového návrhu, nie protokol skúšok fyzicky postaveného domu.

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
