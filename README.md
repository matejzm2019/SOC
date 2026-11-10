# SOČ – ESP-32D a existujúci 12 V solárny panel

Aktualizácia 10. 11. 2026. Kompletné zdroje z commitu c0dfdf277da1b203b2bf85182aa39044608a9a1a.

- [Stiahnuť kompletný projekt ZIP](SOC-vsetko.zip?raw=1)
- [Čo objednať pre 12 V panel a ako to funguje](PANEL-12V-A-OBJEDNAVKA.md)
- [Zapojenie ESP32 a solárnej vetvy](ZAPOJENIE-ESP32D.md)
- [Návod BenchTwin](BENCHTWIN-NAVOD.txt)
- [Skúšobný kód BenchTwin ZIP](BENCHTWIN-KOD.zip?raw=1)
- [Zdrojové zmeny PR #4](https://github.com/matejzm2019/SOC/pull/4)

**Panel už máš, nekupovať znova.** Potvrdený je iba údaj 12 V; výkon, Voc, Vmp, rozmery ani konektor zatiaľ nie. CN3791 zvoliť variant 12 V pre jednu LiPo 3,7/4,2 V; hlavná aj záložná vetva domu zostávajú 5 V. Štyri hlavné nákupné položky vrátane dvoch INA219 stoja podľa Techfun 10. 11. spolu 15,65–15,75 € bez drobností a dopravy.

Pred prvým pripojením zmeraj Voc odpojeného panela a zachovaj rezervu pod limitom INA219 26 V a CN3791 28 V alebo nižším limitom konkrétneho modulu. Pri 24 V alebo viac panel nepripájaj bez preverenia. Over tiež dovolený nabíjací prúd článku a limit CN3791; 4 A MAX nie je pripravené nastavenie pre túto batériu. Podrobný postup je v zapojení. 470 µF / 16 V patrí iba na 5 V pri ESP.

Rozbaľ ZIP. SOC obsahuje aplikáciu, firmware/esp32/energia_esp32.ino, model a stavebné PDF. SOC-simulacia je samostatne vedľa projektu. V 3D modeli zostáva pôvodný obrys panela ako predbežná rezerva, kým sa skutočný 12 V kus nezmeria. Nepriraďujeme mu výkon ani rozmery iného panela z Techfun.

ESP32 Dev Module, PSRAM Disabled. GPIO34 hlavný ADC cez delič, 32/33 prepínače, 25/26 BC547 LED, 27 indikácia, 21/22 I²C. GPIO6–11 sa nepoužívajú. Kapacitu flash over na konkrétnej doske.

Prešlo 85 testov (1 preskočený na Linuxe), príjem skutočných 12 V aj 22 V, kompilácia produkcie 0.8.1-panel12 a automatické kontroly GitHub. API limit nenahrádza elektrickú ochranu. Fyzický beh ani celý BenchTwin obvod tu nebol overený.

BenchTwin používa samostatný loop()/millis() diagnostický sketch, pretože produkcia používa nepodporované FreeRTOS úlohy. ZIP s kódom nie je import celej zapojenej 3D scény. Neznáme parametre zadané do simulátora sú testovacie, nie meranie reálneho panela. AI beží na PC cez Ollamu.
