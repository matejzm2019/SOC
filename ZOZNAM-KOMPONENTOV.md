# Kompletný zoznam komponentov a materiálu

**Jediný platný nákupný zoznam pre aktuálnu zostavu, 10. 11. 2026.** ESP-32D, existujúci 12 V panel, chránená LiPo 2500 mAh, CN3791 12 V, MT3608 a **dva INA3221**. Staršie zoznamy v histórii commitov neplatia. Objednaj len položky, ktoré ešte nemáš.

## Elektronika

| ID | Potrebné množstvo | Komponent / odkaz Techfun | Stav a poznámka |
|---|---:|---|---|
| E01 | 1 | ESP32, 38-pinová USB-C doska označená ESP-32D | už máš; Arduino ESP32 Dev Module, PSRAM vypnutá |
| E02 | 1 | [Chránená LiPo 104050, 2500 mAh](https://techfun.sk/produkt/li-pol-bateria-kablik-ochranny-obvod/) | vybraný článok 1S 3,7 V / plný 4,2 V; kúpiť len ak ho ešte nemáš; cena z fotografie 5,80 € |
| E03 | 1 | [CN3791 – vybrať **12 V**](https://techfun.sk/produkt/solarna-nabijacka-cn3791-pre-litiove-baterie/) | 4,40 €; pre 1S LiPo, nie 12 V batériu; overiť prúd/RCS a MPPT bod |
| E04 | 1 | [MT3608, bez micro USB](https://techfun.sk/produkt/step-up-menic-mt3608/) | 0,85–0,95 € podľa variantu; nastaviť výstup 5,00 V pred pripojením ESP |
| E05 | 1 | Existujúci solárny panel označený 12 V | už máš, nový nekupovať; výkon, Voc, Vmp, rozmery a konektor nepotvrdené |
| E06/E07 | **2** | [INA3221, trojkanálový modul](https://techfun.sk/produkt/senzor-napatia-a-prudu-ina3221-3-kanalovy/) | **4,75 €/ks, 9,50 € spolu**; pri kontrole 55 ks skladom; každý meria CH1, PANEL 0x40 a BAT 0x41; limit dosky 1,1 A / čipu 26 V |
| E08 | 1 | [Relé 5 V, 1 kanál, LOW trigger, COM/NO/NC](https://techfun.sk/produkt/rele-modul-1-kanal-5v-so-zabudovanym-optoclenom/) | 1,40 €; hardvérové prepnutie svetiel |
| Q01/Q02 | **2** | BC547BBK, NPN 45 V / 100 mA / 500 mW | použi svoje; ak máš len jeden, chýba druhý; overiť vývody C/B/E |
| LED01–06 | 6, odporúčané 10 s rezervou | [Biele LED 3 mm](https://techfun.sk/produkt/led-ka-1-kus-3mm-rozne-farby/) | dve vetvy po 3 LED, nie výkonový LED pás; staršia cena 0,30 € za 10 |
| LED07 | 1, odporúčané 2 s rezervou | Modrá LED 3 mm z rovnakej ponuky | indikácia hlavného 5 V zdroja; staršia cena 0,06 € za 2 |
| S01/S02 | 2 | [Dvojpolohový prepínač SMTS-102](https://techfun.sk/produkt/kovovy-dvojpolohovy-prepinac-smts-102/) | kontakty proti GND; staršia cena 0,80 € za dva |
| R01–07 | **7× 330 Ω** | [Rezistory ¼ W, balenie 10 ks](https://techfun.sk/produkt/rezistor-rozne-hodnoty-1-4w-10-kusov/) | kúpiť 1 balenie; každá zo 7 LED má vlastný rezistor |
| R08/R09 | **2× 1 kΩ** | rovnaká ponuka rezistorov | 1 balenie; do báz BC547 |
| R10–12 | **3× 10 kΩ**, voliteľne ďalšie 2 | rovnaká ponuka rezistorov | 1 balenie; 2× báza–GND, 1× ADC delič; voliteľné 2× pull-up prepínačov na 3V3 |
| R13 | **1× 22 kΩ** | rovnaká ponuka rezistorov | 1 balenie; horná časť deliča hlavného 5 V zdroja; štyri balenia rezistorov staršie spolu cca 1,00 € |
| CE01 | 1 + voliteľná rezerva | 470 µF / 16 V elektrolyt | už máš; iba na BACKUP_5V pri ESP, dodržať polaritu; nie na solárny vstup |
| PCB01 | 1 | Univerzálna spájkovacia doska cca 50 × 30 mm | ovládače LED a merací delič; prípadne vyrezať z väčšej dosky |

**CN3791 + MT3608 + 2× INA3221 + relé = 16,15–16,25 €** bez dopravy, batérie, drobností a dreva. Ceny hlavných modulov overené 10. 11. 2026; sklad sa mení. Ostatné ceny označené ako staršie sú orientačné. Panel, ESP, BC547 ani kondenzátor nekupovať znova, ak ich už máš.

## Konektory, vodiče a elektrická montáž

| Položka | Množstvo | Poznámka |
|---|---:|---|
| [PH2.0 2-pin protikus/káblik](https://techfun.sk/produkt/ph2-0-kablik-samecsamica-2p/) | 1, ak zodpovedá batérii | overiť konektor a polaritu na skutočnom kuse; staršia cena 0,40 €, vtedy vypredaný; XH2.54 nie je PH2.0 |
| Rozpojiteľný 2-pin k panelu | 1 pár | typ podľa skutočného panela; pôvodný konektor zachovať, nezamieňať ho s batériovým |
| Servisná 2-pin prepojka batériový uzol → MT3608 | 1 pár | odpojí všetky systémové záťaže pri úplnom dobití |
| Dátový USB-C kábel ESP | 1 | pri programovaní odpojiť externé napájanie |
| Samostatný napájací USB-C kábel alebo vodiče na 5V vstup ESP | 1 | iba overených 5 V; nepripájať súčasne dva neoverené 5 V zdroje |
| [Dupont 20 cm](https://techfun.sk/produkt/kabliky-40-kusov-20-cm/), M–F a F–F | 1 balenie každého | signály a krátke I2C prepoje; staršia cena spolu cca 4,40 €; hlavné napájanie viesť hrubším vodičom |
| Napájací vodič 0,25–0,5 mm² | cca 5 m červený + 5 m čierny | rezerva na rozvody; nepoužité vodiče nekupovať podľa farby, ak už máš vhodný prierez |
| Signálový vodič 0,14–0,25 mm² | cca 15 m celkom | rôzne farby; W13/W14 prepínače 2×900 mm každý, W25 indikácia 2×900 mm |
| Krátke I2C prepojky | prvý modul 4×180 mm, druhý 4×100 mm | môžu byť z uvedenej zásoby vodičov; adresy sú rozdielne |
| Kábel panela W18 | 2×650 mm celkom vrátane existujúceho | aspoň 200 mm servisná slučka; skrátiť až podľa skutočnej trasy |
| Malé skrutkové svorky / rozvodné body | podľa zapojenia a dodaných modulov | plusové uzly panel, BAT_NODE, BACKUP_5V a MAIN_5V zostávajú oddelené; GND spoločná |
| Pinové lišty 2,54 mm | podľa neosadených modulov | na ESP z fotografie sú už osadené; INA3221 môže mať lištu neprispájkovanú |
| Izolačné PCB stĺpiky cca 4 mm, skrutky a matice | podľa otvorov dosiek | nevŕtať podľa obálok 3D; dosky bez dier upevniť izolovane vhodnou príchytkou |
| Zmršťovacia bužírka, sťahovacie pásky, príchytky, štítky vodičov | po 1 sade | označiť SOLÁR, BAT, MAIN_5V, BACKUP_5V a moduly PANEL/BAT |
| Mäkký pásik na LiPo | 1 | neprepichovať ani nestláčať článok |

Úplné predstrihy všetkých Wxx sú v [dlzky-vodicov.csv](https://github.com/matejzm2019/SOC/blob/codex/ina3221-jednotny-zoznam/model-domu/dlzky-vodicov.csv); množstvá vyššie sú nákupná zásoba, nie ďalšie vodiče navyše k CSV.

## Drevo – nosné diely a ovládací panel

Rozmery v mm. Podstava 600 × 450, dom 480 × 330; celá strecha je odnímateľná. Rozmer 12 V panela zatiaľ nie je známy, preto L04 a jeho klipy premerať pred rezaním.

| ID | Diel | Ks | Dĺžka × šírka × hrúbka (mm) |
|---|---|---:|---|
| P01 | Podstava domu | 1 | 600 × 450 × 8 |
| P02 | Predná stena | 1 | 480 × 120 × 6 |
| P03 | Zadná stena | 1 | 480 × 120 × 6 |
| P04 | Ľavá stena | 1 | 318 × 120 × 6 |
| P05 | Pravá stena | 1 | 318 × 120 × 6 |
| P06 | Pozdĺžna priečka | 1 | 318 × 100 × 6 |
| P07 | Ľavá priečna priečka | 1 | 304 × 100 × 6 |
| P08 | Pravá priečna priečka | 1 | 158 × 100 × 6 |
| P09 | Vyberateľná doska elektroniky | 1 | 150 × 132 × 4 |
| P10 | Rovina strechy | 2 | 504 × 230 × 4 |
| P11 | Štít strechy | 2 | 330 × 115.53 × 4 |
| L01 | Nosník strechy | 2 | 316 × 10 × 10 |
| L02 | Vodiaci doraz strechy | 4 | 30 × 10 × 6 |
| L03 | Výstuha pod panelom | 2 | 440 × 10 × 10 |
| L04 | Montážna lišta panela | 2 | 250 × 8 × 6 |
| C01 | Ovládací panel | 1 | 100 × 40 × 4 |

P11 je trojuholníkový štít (výška výroby 115,5 mm). Materiál na nákup orientačne: preglejka 600×450×8, 600×900×6 a 600×900×4 mm, plus lišty. Rez rozložiť s rezervou na šírku píly, smer vlákien a skutočnú hrúbku. Súbory SVG majú mierku 1:1; kontrolnú mierku premerať po tlači.

## Detaily fasády a strechy podľa 3D modelu

Tieto jednoduché lepené detaily nie sú nábytok. Falce možno iba nakresliť, ak chceš menej výroby.

| ID | Diel | Ks | Dĺžka × šírka × hrúbka (mm) |
|---|---|---:|---|
| A01a | Cédrový obklad čelný | 10 | 480 × 6 × 1.5 |
| A01b | Cédrový obklad bočný | 10 | 318 × 6 × 1.5 |
| A02 | Rohové lišty | 4 | 120 × 6 × 7 |
| A03v | Zvislé rámy okien | 16 | 54 × 3 × 2 |
| A03h64 | Vodorovné rámy predné | 6 | 70 × 3 × 2 |
| A03h56 | Vodorovné rámy ostatné | 10 | 62 × 3 × 2 |
| A03m | Stredové priečniky okien | 8 | 48 × 2 × 2 |
| A04a | Parapety predné | 3 | 74 × 7 × 2 |
| A04b | Parapety ostatné | 5 | 66 × 7 × 2 |
| A05a | Pevná doska dverí | 1 | 82 × 40 × 2 |
| A05b | Zárubne dverí | 2 | 86 × 4 × 3 |
| A05c | Nadpražie dverí | 1 | 48 × 4 × 3 |
| A05d | Prah dverí | 1 | 48 × 10 × 2 |
| A06 | Naznačené strešné falce | 24 | 230 × 1 × 1 |
| A07 | Dvojdielny hrebenáč | 2 | 504 × 12 × 1 |
| A08 | Odkvapové lišty | 2 | 504 × 6 × 4 |
| A09 | Štítové lišty | 4 | 230 × 6 × 4 |
| A10 | Vstupné nášľapy | 3 | 62 × 18 × 2 |

## Zostávajúce montážne diely a vybavenie

- 4× nožička pod podstavu, výška 10 mm.
- 4× stĺpik M3 výšky 15 mm pre C01, príslušné skrutky a matice; hlavy pod podstavou zapustiť. Hrúbku C01 pri závite prepínača prispôsobiť skutočnému kusu.
- Príchytky panela podľa jeho skutočného rámu; v modeli sú 4 ako priestorová predstava, nie potvrdený úchyt neznámeho panela. Odľahčenie ťahu kábla panela.
- Lepidlo na drevo, brúsny papier, voliteľná farba, difúzny papier alebo matný akrylát do okien, páska/tenká lišta na spoj strechy.
- Existujúci laboratórny zdroj, multimeter, spájkovačka, cín/tavidlo, píla, vrtáky a meradlo. PC/notebook, 2,4 GHz Wi-Fi router a prípadne prezentačné svetlo; zariadenia nekupovať znova, ak ich už máš.

## Čo overiť pred dokončením objednávky a prvým zapojením

1. **Nabíjací prúd:** podľa dovoleného prúdu batérie a konzervatívneho limitu použitého INA3221 1,1 A. Aj vybíjací prúd s meničom a Wi-Fi špičkami musí byť v limite. Označenie CN3791 „4 A MAX“ nie je pripravené nastavenie pre túto zostavu. RCS = 0,120 V / I; príklad 0,5 A znamená 0,24 Ω, ale puzdro a prúd treba overiť na dodanej doske a článku. Konkrétny výkonový rezistor sa neobjednáva naslepo namiesto bežného 330 Ω/1 kΩ.
2. **Solár:** poznať iba 12 V nestačí na potvrdenie Voc a výkonu. Pred pripojením zmerať Voc s rezervou pod 26 V (pri 24 V alebo viac najprv preveriť parametre a zvoliť potrebné diely). Overiť skutočný MPPT bod CN3791. Kalibračný výkon v appke je nameraný vo W, nie číslo 12.
3. **Revízia INA3221:** staršia doska má spoločné POW/VIN+ a výstupy CH1/GND, novšia priamo IN1+/IN1−. Podľa R100 identifikovať oba konce bočníka, nezameniť GND s IN1−. Čipové VS/VCC je 3V3; nie solárny vstup. Používame dva moduly s oddelenými kladnými meracími vstupmi.
4. **Mechanika a konektory:** rozmery 12 V panela, jeho úchyty, protikusy a polarita, rozteče dosiek a závity prepínačov. 3D obálky elektroniky/panela nie sú vrtné šablóny.

Zapojenie: [ZAPOJENIE.md](ZAPOJENIE-ESP32D.md). Rozdiely dosiek a adresy: [INA3221.md](INA3221.md). Funkcia soláru a dobíjania: [PANEL-12V-A-OBJEDNAVKA.md](PANEL-12V-A-OBJEDNAVKA.md). Tieto súbory nemajú ďalší konkurenčný nákupný zoznam.
