# Zapojenie a skúšky pred montážou

Platí pre verziu 0.10.0-house: CN3791 + MT3608, chránená LiPo 104050 2 500 mAh, ESP32-S3 N16R8. Nepoužívaj starú schému s BQ24074/MAX17048.

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
           ├── relé VCC + JD-VCC (prepojka ponechaná), IN pevne GND
           └── DRV8833 VM
relé COM ── dve LED vetvy
Všetky prevádzkové GND majú spoločnú referenciu.
```

Batériový INA219 musí byť v ceste VŠETKÉHO prúdu do/z článku. CN3791 aj MT3608 sa pripájajú na strane VIN+, batéria na VIN−. Pripojenie boostu priamo na batériový plus mimo senzora by skreslilo čistý prúd. Používaj iba plus/mínus chránenej batérie s vyvedeným káblikom; neotváraj článok ani neobchádzaj jeho internú ochranu.

Menič MT3608 sám nie je ochrana LiPo pred hlbokým vybitím. Článok musí mať funkčnú ochranu. Podľa údajov modulu pri nastavovaní meniča používaj malú skúšobnú záťaž; najprv meraj výstup, až potom pripájaj ESP. Hodnota 2 A pri meničoch sa nesmie zameniť za zaručený trvalý prúd na 5 V pri vybitom článku. Testuj s limitom a reálnym odberom.

## GPIO a meranie

| GPIO ESP32-S3 | Pripojenie | Stav |
|---:|---|---|
| 4 | hlavné +5 V cez 22 kΩ na GPIO; 10 kΩ z GPIO na GND | pri 5 V je cca 1,56 V; priamych 5 V je neprípustných |
| 5 | prepínač A medzi GPIO a GND | LOW = svetlá A zapnuté |
| 6 | prepínač B medzi GPIO a GND | LOW = svetlá B zapnuté |
| 7 | 1 kΩ do bázy 2N2222A vetvy A | každá báza aj 10 kΩ na GND |
| 10 | 1 kΩ do bázy 2N2222A vetvy B | rovnaké zapojenie |
| 8 | SDA oboch INA219 | logické napájanie senzorov 3,3 V |
| 9 | SCL oboch INA219 | adresy 0x40 a 0x41 |
| 11 | rezistor 330 Ω, modrá LED na GND | indikácia prítomnosti hlavného zdroja |
| 12 | DRV8833 AIN1 | HIGH = pumpa zapnutá, LOW = vypnutá |
| 13 | sourceOK plavák na GND | LOW = zdroj má dosť vody; prerušenie = zákaz čerpania |
| 14 | cieľový dolný plavák na GND | HIGH = pod dolnou hladinou; kontakt zopne po jej dosiahnutí |
| 15 | cieľový horný plavák na GND | HIGH = horná hladina / prerušený vodič, zastaviť |
| 16 | dryOK plavák záchytnej vaničky na GND | LOW = suchá; pri vode/prerušení HIGH = stop |

Prepínače a plaváky sú kontakty do GND, používajú interné INPUT_PULLUP na 3,3 V. Nikde na ich GPIO neprivádzaj 5 V. Osadenie plavákov obráť podľa potrebného spínania a otestuj multimetrom aj firmvérom. Odpojenie dolného plaváka môže vyzerať ako nízka hladina, preto horný plavák, limit času a záchytný snímač zostávajú nezávislé ochrany.

Oba INA219 napájaj 3,3 V, nikdy cez 5 V pull-up na SDA/SCL. Druhý nastav adresovacou prepojkou A0 podľa konkrétnej dosky na 0x41. Over I²C skenerom; nespoliehaj sa na nepresnú tabuľku adries e-shopu. Voliteľný BH1750 z pôvodného návrhu nový firmvér nevyžaduje a nemeria ho.

## LED vetvy

COM relé → pre každú LED jej vlastný rezistor 330 Ω → anóda LED → katóda → kolektor 2N2222A. Emitor na GND. Tri LED v každom okruhu sú paralelné vetvy, každá s vlastným rezistorom. Ide o malé LED, nie o 12 V LED pásik. Pri bielej LED s úbytkom približne 3,1 V vychádza prúd na 5 V rádovo 5 mA. GPIO nenapája samotné svetlá.

## Motor a voda

DRV8833 VM na hlavné LAB 5 V, GND spoločná. AIN1=GPIO12, AIN2=GND. nSLEEP, ak je vyvedené, na 3,3 V; ak je na doske označené SLP a už má pull-up, over zapojenie konkrétneho modulu. Pumpa medzi AOUT1 a AOUT2. Nevyužitý kanál BIN1/BIN2 na GND. Niektoré dosky značia výstupy A1/A2 a vstupy IN1/IN2; nezameň ich. Odporúčaný 10 kΩ pulldown na ovládanom vstupe drží motor vypnutý počas štartu. Pri VM pridaj 470 µF s vhodným napäťovým rozsahom. Driver obsahuje mostík a recirkuláciu prúdu, nevkladaj náhodne diódu naprieč jeho výstupy.

Na prvú skúšku nechaj `WATER_ENABLED=0`. Najprv bez motora over všetky logické stavy snímačov, potom s nízkym prúdovým limitom skúšaj vodnú vetvu. Pracuj s malým objemom vody v záchytnej vaničke; nastav maximálny čas podľa nameraného prietoku tak, aby sa cieľová nádrž nemohla preliať pred limitom. Predvolených 15 s je iba východisko, nie zaručená bezpečná hodnota pre ľubovoľnú nádrž/pumpu.

Výtok do cieľovej nádrže zaisti nad maximálnou hladinou, aby nevznikal neželaný sifón. Začni T01=220 mm, T02=220 mm a ponechaj 60 mm rezervu; ak filter vyžaduje ďalšie pripojenia, doplň hadicu podľa reálnej montáže. Táto hadica nie je bez ďalšieho merania garantovaná na ľubovoľný kúpený filter. Snímač vo vaničke reaguje až na nahromadenú vodu.

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
- Odpoj Wi-Fi: LED a relé musia zostať funkčné, bežiace čerpadlo sa miestne zastaví najneskôr po vypršaní 1,5 s povelu.
- Vyskúšaj hornú hladinu, prázdny zdroj, vodu vo vaničke, prerušené snímače, časový limit a oneskorený HTTP server.
- Reštartuj server: čerpadlo má zostať vypnuté, kým nedáš nový platný povel.
- Over, že kladný prúd batérie naozaj znamená nabíjanie. Testovaciu softvérovú telemetriu aplikácia musí označiť ako TEST.

Podrobný opis systému: [AKO-TO-FUNGUJE.md](AKO-TO-FUNGUJE.md). Výrobné rozmery: [stavebný návod](../model-domu/STAVEBNY-NAVOD.pdf).
