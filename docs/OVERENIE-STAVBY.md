# Overenie návrhu a aplikácie

Dátum: 4. 11. 2026, verzia 0.10.0-house. Toto je záznam softvérových kontrol návrhu, nie protokol skúšok hotového fyzického zariadenia.

## Vykonané kontroly

- `python -m pytest -q -rs`: **77 úspešných, 1 preskočený** test. Preskočený je test spúšťača pre Windows, pretože kontrola prebehla na Linuxe. Dve upozornenia sa týkajú zastarávajúcich rozhraní testovacích knižníc.
- C++ skúška používa priamo hlavičky `water_guard.h` a `backup_power.h` z firmvéru: bezpečné zastavenie čerpadla, strata povelu, maximálny čas, zablokovanie poruchy, reset, pretečenie časovača a orientačný odhad nabitia.
- Arduino CLI 1.5.1, ESP32 core 3.3.12, cieľ ESP32-S3 s 16 MB flash a OPI PSRAM: zostavenie produkčného firmvéru úspešné s vypnutou aj zapnutou podporou vody. Zapnutá voda: 1 062 363 B programu, 48 844 B globálnych dát. Knižnice Adafruit INA219 1.2.3 a ArduinoJson 7.4.3.
- Zostavená aj samostatná simulátorová verzia so simulovanými snímačmi a vypnutou WiFi: 422 092 B programu, 29 280 B globálnych dát. Táto verzia nie je určená na fyzické meranie.
- Chromium/WebGL: načítanie skutočnej geometrie, otáčanie, zdvih/odloženie strechy, pohľad zhora, výber komponentu, ovládanie klávesnicou a zobrazenie pri šírke 390 px. Bez JavaScriptových chýb pri kontrolovaných krokoch. Overené aj základné ovládanie vodného dema a stiahnutie stavebných súborov.
- Geometria a kusovník: rozmer podstavy, počet dielov odnímateľnej strechy, umiestnenie modulov v technickej miestnosti a zhodnosť CAD exportu s modelom aplikácie sú kontrolované testom. PDF má šesť strán formátu A3. SVG šablóny uvádzajú fyzické mm a kontrolnú mierku; pôdorys je 1 : 2.
- Samostatný lokálny tester mimo repozitára úspešne odoslal označenú testovaciu telemetriu oddelenému serveru. BenchTwin ani Wokwi neboli overené ako úplná fyzikálna simulácia všetkých konkrétnych súčiastok.

## Čo zostáva overiť na zostave

Pred zapojením LiPo zisti jej dovolený nabíjací prúd a nastav/over skutočný prúd konkrétnej dosky CN3791; údaj „max. 4 A“ na predajnej stránke nie je odporúčaný prúd tejto batérie. Pre úplné prednabitie odpoj systémovú záťaž podľa ZAPOJENIE.md. Modul nemá samostatný systémový power-path výstup.

Na stole over nastavenie MT3608 na 5 V, rozbeh ESP32 cez batériovú vetvu, prepnutie relé pri výpadku LAB a odber všetkých svetiel. Odhad percent z napätia nie je meranie skutočnej kapacity 2500 mAh. INA219 meria napätie a čistý prúd; nabíjanie i odber musia prechádzať batériovým bočníkom.

Filter a jeho tlaková strata, hadicové koncovky, závity plavákov a montážne otvory sa dokončia podľa skutočne zakúpených dielov. Skontroluj orientáciu všetkých štyroch plavákov, tesnosť a zastavenie pri každej poruche. Plavák vo vaničke zachytí nahromadenú vodu, nie prvú kvapku. AI cez Ollamu nebola v tomto prostredí hodnotená so stiahnutým jazykovým modelom; aplikácia má aj lokálne odpovede a kontrolu dostupnosti servera.

Elektronické obálky a hadičky v 3D slúžia na rozmiestnenie. Nevŕtaj modulové otvory ani nevyrábaj nádrže len podľa týchto obálok. Hmotnosť 4–6 kg je výpočet/odhad, nie výsledok váženia.
