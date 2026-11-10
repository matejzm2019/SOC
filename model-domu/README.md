# Drevený dom so strešným panelom – výrobný balík

Verzia 0.12.0-assistant, 10. 11. 2026. Celé steny, žiadny nábytok. Teplá biela fasáda, cédrový obklad, okenné rámy a parapety, pevné dvere, antracitová strecha s naznačenými falcami a skutočný panel 230 × 195 × 17 mm. Geometria je rozmerová; nie je to iba ilustračný obrázok.

| Časť | Rozmer |
|---|---|
| Celá podstava | 600 × 450 × 8 mm |
| Dom | 480 × 330 mm; X60–540, Y70–400 |
| Steny / priečky | 120 / 100 mm, hrúbka 6 mm |
| Strecha | 35°, dve roviny 504 × 230 × 4 mm |
| Štít | základňa 330, výška 115,53 mm (výroba 115,5) |
| Technická miestnosť | 158 × 138 mm |
| Vyberateľná doska | 150 × 132 × 4 mm; X380 Y257 |
| Panel | 230 × 195 × 17 mm, približne 533 g |
| Výška s nožičkami a panelom | približne 27 cm |

Celý model ostáva na podstave 60 × 45 cm. Hmotnosť podľa materiálu približne 4–5 kg, fyzicky nezvážená. Preglejka: orientačne 600×450×8, 600×900×6, 600×900×4 mm, plus lišty podľa oboch CSV. Výrez rozlož s rezervou na šírku rezu a smer vlákien.

## Súbory

- STAVEBNY-NAVOD.pdf: sedemstranový A3 prehľad, nie šablóna 1:1.
- 3d/dom.blend: editovateľná uzavretá zostava; všetky ROOF a SOLAR objekty patria k jednej odnímateľnej streche.
- 3d/dom.glb: výmenný model v metroch podľa glTF; model.json v aplikácii používa mm.
- 3d/dom-mm.stl: viacdielna vizuálna zostava v mm, nie jeden vodotesný tlačiteľný objekt.
- rezaci-plan.csv: nosné diely. detaily-fasady.csv: všetky doplnkové lišty a ich dĺžky.
- dlzky-vodicov.csv: predstrihy s rezervou. W18 zahŕňa pôvodný kábel a servisnú slučku.
- vykresy/Pxx-1ku1.svg: šablóny v mm vrátane C01; tlač 100 %, skontroluj 100 mm mierku (C01: 50 mm). Väčšie diely tlač na vhodný formát alebo dlaždicovo. podorys.svg je 1:2.

## Montáž

1. P01–P09 nasucho zostav pri skutočnej hrúbke materiálu. Bočné steny 318 mm sú medzi čelnými pri hrúbke 6 mm. LED a vodiče sú na pevných stenách.
2. Pridaj priečky, povrch podlahy môže byť len vyznačený. Elektronika je na odnímateľnej doske s 4 mm izolačnými stĺpikmi. Rozmery PCB sú rezervované obálky, nie vrtné šablóny.
3. Jednoduché nalepené detaily A01–A10 sú v samostatnom CSV: bez pántov, posuvných okien či nábytku. Okenné výplne môžu byť papier alebo tenký akrylát. Falce sa dajú len nakresliť, ak chceš znížiť prácnosť.
4. P10/P11, L01/L02 zlep do jedného odnímateľného rámu. Dorazy ponechaj s vôľou 0,5–1 mm. L03 dĺžky 440 mm vystužujú prednú strešnú rovinu medzi bočnými nosníkmi. L02 sú nalepené na spodnej strane L01, Z112–118. Hrebeň zakry lištami A07.
5. Dve lišty L04 sú na prednej streche; štyri príchytky držia kovový rám panela. Konkrétne otvory prenes zo skutočného rámu. Nevŕtaj články ani zadnú fóliu, over dĺžky skrutiek. Strecha sa nelepí k stenám.
6. Panel má rozpojiteľný označený konektor a aspoň 200 mm voľnú servisnú slučku. Pred úplným odložením ho rozpoj. Nezdvíhaj za kábel ani panel. LED sa pri odložení neodpájajú.
7. Ovládanie je na paneli C01 100 × 40 × 4 vľavo vpredu (X30/Y18), mimo chodníka. Štyri 15 mm stĺpiky vytvárajú miesto na telá prepínačov pod doskou; páčky sú hore. A/B: X56/X96, Y36; modrá LED: X119/Y36. Použi šablóny C01 a P01 a závity over na skutočných dieloch. Skrutky zospodu zapusti do podstavy.
8. Elektrické uzly, prúdy a zálohu najprv otestuj mimo dreva podľa docs/ZAPOJENIE.md. Dĺžky vodičov skráť až po uložení do trasy, pod podstavou nechaj 10 mm nožičky.

Obnova modelu: blender -b --python tools/build_house.py. PDF a šablóny: python tools/build_documents.py s requirements-build.txt; Unicode font sa hľadá na Linuxe, Windows aj macOS alebo cez SOC_PDF_FONT. Panel, elektronika a spojky sú vizuálne modely podľa menovitých rozmerov, nie garantované detaily konkrétneho dodaného výrobku.

Aktuálna doska: ESP-32D (klasické ESP32) z fotografie používateľa. Model rezervuje obálku 70 × 32 mm; skutočné rozmery a otvory dosky premeraj pred vŕtaním. Zapojenie je v docs/ZAPOJENIE.md, firmvér v firmware/esp32/. Použité tranzistory BC547B a kondenzátor 470 µF / 16 V sú zahrnuté v aktuálnom kusovníku.
