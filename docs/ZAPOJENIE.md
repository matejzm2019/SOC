# Zapojenie a skúšky pred montážou

Platí pre verziu 0.12.0-assistant: CN3791 + MT3608, chránená LiPo 104050 2 500 mAh, ESP32-S3 N16R8. Nepoužívaj starú schému s BQ24074/MAX17048.

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

## GPIO a meranie

| GPIO ESP32-S3 | Pripojenie | Stav |
|---:|---|---|
| 4 | hlavné +5 V cez 22 kΩ na GPIO; 10 kΩ z GPIO na GND | pri 5 V je cca 1,56 V; priamych 5 V je neprípustných |
| 5 | prepínač A medzi GPIO a GND | LOW = svetlá A zapnuté po odrušení kontaktu |
| 6 | prepínač B medzi GPIO a GND | LOW = svetlá B zapnuté |
| 7 | 1 kΩ do bázy 2N2222A vetvy A | každá báza aj 10 kΩ na GND |
| 10 | 1 kΩ do bázy 2N2222A vetvy B | rovnaké zapojenie |
| 8 | SDA oboch INA219 | logické napájanie senzorov 3,3 V |
| 9 | SCL oboch INA219 | adresy 0x40 a 0x41 |
| 11 | rezistor 330 Ω, modrá LED na GND | indikácia prítomnosti hlavného zdroja |

Prepínače sú na paneli C01 vľavo vpredu (X30/Y18), kontakty do GND s interným INPUT_PULLUP na 3,3 V. Pri 900 mm vedení možno doplniť 10 kΩ pull-up na 3,3 V pri ESP. Samostatná úloha vzorkuje každých 10 ms a prijme zmenu až po 30 ms stabilného kontaktu; funguje bez servera. Modrá LED GPIO11 je na tom istom paneli cez 330 Ω. Na GPIO neprivádzaj 5 V. GPIO12–16 nemajú v tomto projekte pripojené zariadenie.

Oba INA219 napájaj 3,3 V, nikdy cez 5 V pull-up na SDA/SCL. Druhý nastav adresovacou prepojkou A0 podľa konkrétnej dosky na 0x41. Over I²C skenerom; nespoliehaj sa na nepresnú tabuľku adries e-shopu. Voliteľný BH1750 z pôvodného návrhu nový firmvér nevyžaduje a nemeria ho.

## LED vetvy

COM relé → pre každú LED jej vlastný rezistor 330 Ω → anóda LED → katóda → kolektor 2N2222A. Emitor na GND. Tri LED v každom okruhu sú paralelné vetvy, každá s vlastným rezistorom. Ide o malé LED, nie o 12 V LED pásik. Pri bielej LED s úbytkom približne 3,1 V vychádza prúd na 5 V rádovo 5 mA. GPIO nenapája samotné svetlá.

## Ovládací panel C01

Doska 100 × 40 × 4 mm je na štyroch 15 mm stĺpikoch, spodok Z23 a vrch Z27. Telá prepínačov sú pod ňou, páčky nad ňou. A/B majú osi X56/X96, Y36; modrá LED X119/Y36. Použi C01-1ku1.svg a P01-1ku1.svg. M3 skrutky zospodu zapusti do podstavy, aby nezasahovali do nožičiek. Závit skutočného prepínača a hrúbku pod maticou over pred vŕtaním; podľa potreby lokálne zapusti spodok C01. W13/W14 sú páry po 900 mm, W25 dva vodiče po 900 mm.

## Panel na odnímateľnej streche

Panel 230 × 195 × 17 mm je na prednej rovine 35°. Dve lišty L04 a štyri príchytky držia kovový rám, nie články. Pod strešnou rovinou sú výstuhy L03. Nevŕtaj cez panel a skrutky neťahaj do jeho zadnej fólie. Panel má približne 533 g; strechu zdvíhaj za rám oboma rukami.

W18 sú dva vodiče po 650 mm vrátane pôvodného kábla panela. Nechaj aspoň 200 mm voľnú servisnú slučku, odľahčenie ťahu a označený rozpojiteľný konektor SOLÁR. Pôvodný konektor panela zachovaj, typ a polaritu over na dodanom kuse. Pred úplným odložením strechy konektor rozpoj. Kábel nesmie byť zovretý medzi stenou a strechou.

## Úplné prednabitie batérie

1. Vypni model, odpoj MT3608 aj všetky iné záťaže od batériového uzla. ESP sa pri tom vypne.
2. Odpoj panel od vstupu CN3791. LAB nastav samostatne na vhodné napätie pre variant 6 V, typicky s malou rezervou nad jeho MPPT bodom; konkrétnu hodnotu a prúd over podľa dodanej dosky. Nenastavuj týmto napätím súčasne hlavnú 5 V vetvu domu.
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
