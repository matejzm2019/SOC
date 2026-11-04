# Drevený dom – výrobný balík

Aktuálna konštrukcia má **celé steny a strechu odnímateľnú v jednom kuse**, bez nábytku. Solárny stojan a vodný modul sú vedľa domu a odnímateľné na prenášanie. 3D model nie je iba ilustračný generovaný obrázok: geometria vychádza z milimetrových rozmerov rezacieho plánu.

## Čo otvoriť

- **STAVEBNY-NAVOD.pdf:** A3 prehľad montáže a zapojenia.
- **3d/dom.blend:** editovateľný Blender 4.3 model, strecha v uzavretej polohe. Všetky diely strechy majú prefix ROOF a tvoria jeden odnímateľný kus. Pri upravovaní označ všetky ROOF diely spolu.
- **3d/dom.glb:** výmenný 3D model, jednotky metre podľa glTF; aplikácia používa exportované model.json v mm.
- **3d/dom-mm.stl:** geometria celej zostavy v mm na vizuálny import. Je to viacdielna zostava vrátane rozmerových rezerv, nie jeden vodotesný tlačiteľný objekt ani hydraulická nádoba.
- **vykresy/Pxx-1ku1.svg:** šablóny jednotlivých drevených dielov v mm, tlač 100 %. Over modrú 100 mm mierku. Čierny obrys/otvory sú geometria, text a modrá mierka sú iba poznámky. Väčšie diely treba tlačiť na vhodný formát alebo dlaždicovo; A4 „prispôsobiť strane“ by zmenšilo rozmery.
- **vykresy/podorys.svg:** rozmiestnenie na podstave; samostatné šablóny sú určené na presnú mierku.
- **rezaci-plan.csv, dlzky-vodicov.csv, hadicky.csv:** diely a predstrihy.

## Rozmery

| Časť | Rozmer |
|---|---|
| Podstava domu | 600 × 450 × 8 mm |
| Dom, vonkajší pôdorys | 480 × 330 mm, začiatok X60/Y70 na podstave |
| Vonkajšie steny | 120 mm vysoké, preglejka 6 mm |
| Vnútorné priečky | 100 mm vysoké, preglejka 6 mm |
| Strecha | sklon 25°, dve roviny 504 × 196 × 4 mm |
| Výška zostaveného domu | približne 219 mm vrátane 10 mm nožičiek |
| Technická miestnosť | vnútorný priestor 158 × 138 mm |
| Vyberateľná doska elektroniky | 150 × 132 × 4 mm |
| Solárny stojan, podstava | 250 × 150 × 8 mm, panel 230 × 195 mm |
| Podstava vodného modulu | 280 × 160 × 8 mm |
| Dve nádrže, rozmerová rezerva | každá do 80 × 80 × 110 mm |

Pri bočnom rozmiestnení ako v 3D zaberie komplet približne **1 150 × 450 mm**, nie iba 600 × 450. Na stole nechaj rezervu na káble. Na prenášanie sa bočné moduly odpoja. Samotné drevené diely majú pri bežnej hustote preglejky rádovo 3 kg; celá zostava môže mať približne 4–6 kg podľa materiálu, nádob a vody. Hmotnosť nie je overená fyzickým vážením.

Na drevo orientačne stačí po jednej tabuli: 600×900×8 mm, 600×900×6 mm a 600×600×4 mm, plus približne 1 m lišty 10×10 mm. Je to nákupný odhad s rezervou, nie automaticky optimalizovaný kladačský plán. Diely rozlož s prihliadnutím na smer vlákien a šírku rezu píly.

## Poradie drevenej montáže

1. Over hrúbku zakúpenej preglejky. Bočné steny P04/P05 dĺžky 318 sú medzi čelnými stenami pri hrúbke 6. Ak materiál nie je 6 mm, prepočítaj ich ako 330 − 2×hrúbka.
2. Vyrež P01–P14, okná a otvory, obrús hrany. Predná stena je na Y70, zadná na Y394. Bočné steny sa zmestia medzi ne.
3. Priečky: X370, ľavá priečna na Y235, pravá priečna na Y250; presne podľa pôdorysu. Nevyžadujú nábytok ani zložitý interiér.
4. Do zadnej pravej miestnosti vlož vyberateľnú dosku elektroniky. Pod PCB použi približne 4 mm izolačné stĺpiky; batériu uchyť mäkkým pásikom v jej vlastnej rezerve.
5. Dva trojuholníkové štíty, nosníky 316 mm a dve roviny strechy zlep do jedného kusu. Horný spoj prekry 20 mm páskou alebo ľahkou krycou lištou. Strecha sa nelepí k stenám. Dorazy dolaď s vôľou 0,5–1 mm; nosníky majú pri 318 mm vnútornom rozpätí 1 mm vôľu na každom konci.
6. LED a ich vedenie upevni na pevné steny, nie strechu. Za okná môžeš dať difúzny papier. Dvere sú iba naznačené, netreba ich vyrábať ako otvárací prvok.
7. Vodiče veď cez priechody a po spodnej strane podstavy, chráň hrany otvorov. Nožičky vysoké 10 mm nechajú miesto na vedenie; nič nezvieraj medzi podstavu a stôl.
8. Vodnú vaničku a solárny stojan zostav samostatne. Tesnenie a montážne otvory plavákov dokonči až podľa skutočných nádob a závitov.

Elektronické moduly sú rezervované obálky. ESP32 64×28 a batéria 50×40×10 sú podľa uvedených výrobkov; ostatné PCB obálky sú návrhové rezervy. **Neber ich ako garantované výrobné rozmery dosiek alebo vrtné šablóny.** Nádržky a filter sa podľa tohto 3D modelu nemajú tlačiť ako tlakové alebo vodotesné výrobky.

Aktuálny kusovník a elektrické skúšky sú v ../docs/KOMPONENTY.md a ../docs/ZAPOJENIE.md. Na obnovu 3D použi `blender -b --python tools/build_house.py` z koreňa projektu; na PDF potom `python tools/build_documents.py` s requirements-build.txt. Simulačné návody sú zámerne mimo repozitára.
