# Zapojenie a skúšky pred montážou

Platí pre verziu 0.12.0-assistant: 12 V solárny vstup → CN3791 pre 1S LiPo + MT3608, chránená LiPo 104050 2 500 mAh, ESP32 (ESP-32D, 38-pinová USB-C doska z fotografie). Nepoužívaj starú schému s BQ24074/MAX17048.

## Napájacie uzly

```text
PANEL + → INA219 0x40 VIN+ → VIN− → CN3791 IN+
PANEL − ──────────────────────────→ CN3791 IN− / GND

CN3791 BAT+ ──┬── BATÉRIOVÝ UZOL + ── INA219 0x41 VIN+ → VIN− → LiPo +
MT3608 IN+ ───┘
LiPo −, CN3791 BAT−, MT3608 IN− → spoločná GND chránenej strany článku

MT3608 OUT+ nastavený na 5,00 V ──┬── ESP napájanie 5 V
                                 └── relé NC
LAB +5 V ──┬── relé NO
           └── relé VCC + JD-VCC (prepojka ponechaná), IN pevne GND
relé COM ── dve LED vetvy
Všetky prevádzkové GND majú spoločnú referenciu.
```

Batériový INA219 musí byť v ceste VŠETKÉHO prúdu do/z článku. CN3791 aj MT3608 sa pripájajú na strane VIN+, batéria na VIN−. Pripojenie boostu priamo na batériový plus mimo senzora by skreslilo čistý prúd. Používaj iba plus/mínus chránenej batérie s vyvedeným káblikom; neotváraj článok ani neobchádzaj jeho internú ochranu.

Menič MT3608 sám nie je ochrana LiPo pred hlbokým vybitím. Článok musí mať funkčnú ochranu. Podľa údajov modulu pri nastavovaní meniča používaj malú skúšobnú záťaž; najprv meraj výstup, až potom pripájaj ESP. Hodnota 2 A pri meničoch sa nesmie zameniť za zaručený trvalý prúd na 5 V pri vybitom článku. Testuj s limitom a reálnym odberom.

## Solárny panel označený 12 V

Zatiaľ je potvrdený iba údaj **12 V**. Výkon, napätie naprázdno Voc, pracovný bod Vmp, rozmery ani konektor nepoznáme. Nepriraďuj mu automaticky 1,8 W, 5 W alebo rozmery iného panela z ponuky. Nový panel sa neobjednáva.

Vyber **CN3791 – variant 12 V**, stále pre jednu chránenú LiPo 3,7 V / plne nabitú 4,2 V. Techfun tým označuje optimalizáciu pre solárny vstup, nie 12 V batériu. CN3791 používa pevný MPPT bod nastavený deličom; ak označenie panela 12 V znamená napr. pracovných 18 V, pre optimálny zisk treba doladiť MPPT podľa skutočného Vmp. Samotný názov variantu nepotvrdzuje presnú zhodu.

Pred prvým pripojením:

1. Panel nechaj odpojený od elektroniky. Multimeter nastav na jednosmerné napätie s rozsahom nad očakávanou hodnotou, napr. 60/200 V DC; káble patria do COM a V, nie do prúdového vstupu. Zmeraj plus/mínus panela pod najsilnejším zamýšľaným osvetlením. Znamienko určí aj polaritu.
2. Zaznamenaj Voc. Panelový INA219 môže mať na VIN+/VIN− najviac 26 V; tento limit platí aj pri vypnutom ESP. CN3791 má podľa datasheetu vstup 4,5–28 V, konkrétny modul môže mať nižší limit. V celej solárnej vetve platí najnižší limit a musí zostať rezerva. Ak nameriaš 24 V alebo viac, panel zatiaľ nepripájaj; treba preveriť maximálne Voc a zmeniť diely podľa potreby. 24 V je konzervatívna hranica prvého testu, nie nový limit senzora. Jedno meranie v teple nezaručuje bezpečnosť pri zimnom chlade; vonkajšiu prevádzku over podľa parametrov panela.
3. Pred LiPo over nabíjací limit dosky. Vyššie vstupné napätie neznamená vhodný prúd pre článok: menič vie previesť výkon na väčší batériový prúd. RCS určuje I = 0,120 V / RCS. Hodnota 4 A MAX nie je pokyn pre tento článok; príklad 0,5 A / 0,24 Ω sa smie použiť až po potvrdení dovoleného prúdu batérie a vhodného rezistora.

Panel sa zapája výhradne cez INA_PANEL do **IN+/IN− CN3791**. Batériová a 5 V vetva, hlavný zdroj 5 V aj GPIO zostávajú podľa schémy. MT3608 patrí za batériu, nie medzi 12 V panel a ESP. Na panel nepripájaj priamo LiPo, 5 V LED, ESP ani 470 µF / 16 V kondenzátor. Tento kondenzátor zostáva na BACKUP_5V.

## GPIO a meranie

| GPIO ESP32 | Pripojenie | Stav |
|---:|---|---|
| 34 | hlavné +5 V cez 22 kΩ na GPIO; 10 kΩ z GPIO na GND | pri 5 V je cca 1,56 V; priamych 5 V je neprípustných |
| 32 | prepínač A medzi GPIO a GND | LOW = svetlá A zapnuté po odrušení kontaktu |
| 33 | prepínač B medzi GPIO a GND | LOW = svetlá B zapnuté |
| 25 | 1 kΩ do bázy BC547B vetvy A | každá báza aj 10 kΩ na GND |
| 26 | 1 kΩ do bázy BC547B vetvy B | rovnaké zapojenie |
| 21 | SDA oboch INA219 | logické napájanie senzorov 3,3 V |
| 22 | SCL oboch INA219 | adresy 0x40 a 0x41 |
| 27 | rezistor 330 Ω, modrá LED na GND | indikácia prítomnosti hlavného zdroja |

Prepínače sú na paneli C01 vľavo vpredu (X30/Y18), kontakty do GND s interným INPUT_PULLUP na 3,3 V. Pri 900 mm vedení možno doplniť 10 kΩ pull-up na 3,3 V pri ESP. Samostatná úloha vzorkuje každých 10 ms a prijme zmenu až po 30 ms stabilného kontaktu; funguje bez servera. Modrá LED GPIO27 je na tom istom paneli cez 330 Ω. Na GPIO neprivádzaj 5 V. GPIO6–11 sú vyhradené pre flash; nepripájaj k nim svetlá ani prepínače. GPIO34 je vstup ADC1, funguje aj pri zapnutej Wi-Fi. Čísla GPIO sú popisy na doske, nie poradie kontaktov.

Oba INA219 napájaj 3,3 V, nikdy cez 5 V pull-up na SDA/SCL. Druhý nastav adresovacou prepojkou A0 podľa konkrétnej dosky na 0x41. Over I²C skenerom; nespoliehaj sa na nepresnú tabuľku adries e-shopu. Voliteľný BH1750 z pôvodného návrhu nový firmvér nevyžaduje a nemeria ho.

## LED vetvy

COM relé → pre každú LED jej vlastný rezistor 330 Ω → anóda LED → katóda → kolektor BC547B. Emitor na GND. Tri LED v každom okruhu sú paralelné vetvy, každá s vlastným rezistorom. Ide o malé LED, nie o 12 V LED pásik. Pri bielej LED s úbytkom približne 3,1 V vychádza prúd na 5 V rádovo 5 mA. GPIO nenapája samotné svetlá.

## Ovládací panel C01

Doska 100 × 40 × 4 mm je na štyroch 15 mm stĺpikoch, spodok Z23 a vrch Z27. Telá prepínačov sú pod ňou, páčky nad ňou. A/B majú osi X56/X96, Y36; modrá LED X119/Y36. Použi C01-1ku1.svg a P01-1ku1.svg. M3 skrutky zospodu zapusti do podstavy, aby nezasahovali do nožičiek. Závit skutočného prepínača a hrúbku pod maticou over pred vŕtaním; podľa potreby lokálne zapusti spodok C01. W13/W14 sú páry po 900 mm, W25 dva vodiče po 900 mm.

## Panel na odnímateľnej streche

Existujúci 12 V panel patrí na prednú strešnú rovinu 35°. Obálka 230 × 195 × 17 mm a lišty L04 v 3D modeli sú iba pôvodná priestorová rezerva; rozmery ani hmotnosť skutočného panela nie sú známe. Úchyty a otvory premeraj pred rezaním. Pod strešnou rovinou zostávajú výstuhy L03. Nevŕtaj články ani zadnú fóliu, strechu zdvíhaj za drevený rám.

W18 sú dva vodiče po 650 mm vrátane pôvodného kábla panela. Nechaj aspoň 200 mm voľnú servisnú slučku, odľahčenie ťahu a označený rozpojiteľný konektor SOLÁR. Pôvodný konektor panela zachovaj, typ a polaritu over na dodanom kuse. Pred úplným odložením strechy konektor rozpoj. Kábel nesmie byť zovretý medzi stenou a strechou.

## Úplné prednabitie batérie

1. Vypni model, odpoj MT3608 aj všetky iné záťaže od batériového uzla. ESP sa pri tom vypne.
2. Odpoj panel od vstupu CN3791. LAB nastav samostatne podľa skutočného MPPT bodu 12 V variantu; pri overenom MPPT bode 12 V môže ísť napr. o 13–14 V. Over limit dosky a prúd. Táto hodnota platí iba pre vstup nabíjačky, nikdy pre priamy článok alebo 5 V vetvu. Nenastavuj týmto napätím súčasne hlavnú 5 V vetvu domu.
3. LAB zapoj iba na IN+/IN− nabíjačky. Batéria zostáva na BAT cez INA219. Nie je pripojená priamo na LAB.
4. Pred pripojením článku over nabíjací limit podľa jeho datasheetu; prípadnú zmenu RCS urob s učiteľom. Techfun údaj 4 A MAX nie je vhodný návod na nastavenie.
5. Po dobití odpoj nabíjací LAB, nastav hlavný zdroj späť na 5,0 V, obnov panel a až potom záťaže. Nedobíjaj celý model z náhodne nastaveného laboratórneho výstupu.

CN3791 nemá samostatný power-path LOAD port. Pri zapnutom ESP sa môže rozhodovanie o ukončení nabíjania skresľovať. Na plné dobitie preto platí uvedený postup s odpojenou záťažou. Solárna prezentácia so zapnutou elektronikou ukazuje čistý prúd, nie automaticky úspešné nabíjanie.

## Skúšobný postup

- Zmeraj 5 V výstup meniča aj hlavný zdroj, polaritu PH2.0 a hodnotu ADC hlavného zdroja.
- Zapni svetlá, vypni LAB a over prepnutie na batériu bez resetu ESP. Pri LED je krátke bliknutie možné.
- Odpoj Wi-Fi: LED a relé musia zostať funkčné.
- Odpoj konektor panela, zlož strechu a over, že ostatné rozvody zostanú pripojené.
- Over, že kladný prúd batérie naozaj znamená nabíjanie. Testovaciu softvérovú telemetriu aplikácia musí označiť ako TEST.

Podrobný opis systému: [AKO-TO-FUNGUJE.md](AKO-TO-FUNGUJE.md). Výrobné rozmery: [stavebný návod](../model-domu/STAVEBNY-NAVOD.pdf).

## Náhrady dielov potvrdené 10. 11. 2026

- Dva BC547BBK (NPN, 45 V / 0,1 A / 500 mW) nahrádzajú pôvodné 2N2222 pre dve vetvy po troch malých bielych LED. Každá LED má 330 Ω; odber jednej vetvy je približne 15–20 mA. Báza cez 1 kΩ, 10 kΩ báza–GND. Poradie C/B/E over podľa datasheetu výrobcu konkrétneho kusu, nie podľa obrázka 2N2222. Náhrada neplatí pre výkonové LED pásy.
- Kondenzátor 470 µF / 16 V je vhodný na BACKUP_5V pri ESP: plus na +5 V, pásikom označený mínus na GND. 16 V je dovolené maximum kondenzátora, nie napájanie dosky. Nie je potrebné kupovať 25 V variant.
- Výber dosky Arduino IDE: ESP32 Dev Module, PSRAM Disabled. Kapacitu flash over pri nahrávaní, z fotografie nie je známa. Produkčný sketch je `firmware/esp32/energia_esp32.ino`; staré S3 zapojenie neplatí.
