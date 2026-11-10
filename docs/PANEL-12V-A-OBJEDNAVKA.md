# Existujúci 12 V solárny panel – čo objednať a ako to funguje

Overené na Techfun 10. 11. 2026. Používateľ pozná iba označenie panela 12 V; jeho výkon, Voc, Vmp a rozmery zatiaľ nepoznáme. Panel ani ESP nekupovať znova.

| Ks | Objednať, ak ešte nemáš | Cena s DPH | Poznámka |
|---:|---|---:|---|
| 1 | [CN3791 – zvoliť **12 V**](https://techfun.sk/produkt/solarna-nabijacka-cn3791-pre-litiove-baterie/) | 4,40 € | pre 1S LiPo 3,7/4,2 V; 12 V variant pri kontrole 2 ks skladom; prúd a MPPT overiť |
| 1 | [MT3608, bez micro USB](https://techfun.sk/produkt/step-up-menic-mt3608/) | 0,85–0,95 € podľa variantu | zo 3,7 V článku vytvorí 5,00 V; nastaviť a zmerať pred pripojením ESP |
| 2 | [INA219](https://techfun.sk/produkt/snimac-prudu-ina219-obojsmerny/) | 9,00 € spolu | jeden panel, druhý čistý prúd batérie; adresy 0x40 a 0x41 |
| 1 | [Relé modul 5 V, LOW trigger, COM/NO/NC](https://techfun.sk/produkt/rele-modul-1-kanal-5v-so-zabudovanym-optoclenom/) | 1,40 € | hardvérové prepnutie LED na zálohu |

**Spolu 15,65–15,75 €** bez dopravy a drobností. Ceny sú z aktuálnych produktových stránok, dostupnosť sa môže zmeniť. Tento súčet neobsahuje batériu ani materiál domu.

Už máš/vybral si: ESP-32D, 12 V panel, LiPo 2500 mAh s ochranou, 2× BC547BBK, 470 µF / 16 V. Ak LiPo ešte len objednávaš, zostáva ten istý 1S 3,7 V / 4,2 V variant; nekupuje sa 12 V batéria.

## Drobnosti, aby sa to dalo zapojiť

- 6 bielych + 1 modrá LED; každá vlastný 330 Ω (7 ks, vhodné mať rezervu).
- 2× 1 kΩ do báz BC547, 3× 10 kΩ (dve bázy a delič), 1× 22 kΩ. Voliteľne ďalšie 2× 10 kΩ pull-up prepínačov na 3V3. [Rezistory Techfun, balenia po 10 ks](https://techfun.sk/produkt/rezistor-rozne-hodnoty-1-4w-10-kusov/).
- 2× [dvojpolohový prepínač SMTS-102](https://techfun.sk/produkt/kovovy-dvojpolohovy-prepinac-smts-102/), ak ich ešte nemáš.
- Protikus ku konektoru vybranej batérie (over PH2.0 aj polaritu), rozpojiteľný 2-pin pre panel, servisná prepojka k MT3608, svorky a univerzálna spájkovacia doska približne 50 × 30 mm.
- Napájacie vodiče 0,25–0,5 mm², signálové 0,14–0,25 mm², bužírka, izolačné stĺpiky. Presné predstrihy sú v model-domu/dlzky-vodicov.csv; konektor ani uchytenie neznámeho panela neobjednávať podľa starého 6 V výrobku.

Nabíjací limit CN3791 môže vyžadovať zmenu RCS. Presný rezistor a jeho puzdro sa vyberú podľa dodanej dosky a dovoleného prúdu článku; nie je poctivé tvrdiť, že údaj 4 A na e-shope je pripravené nastavenie pre túto LiPo. Praktická požiadavka pri objednávke/pred montážou: overiť s predajcom alebo učiteľom limit článku a nabíjačky. Samotná ochrana batérie nenahrádza nastavenie nabíjacieho prúdu.

## Tok energie

```text
12 V panel → INA219 PANEL → CN3791 IN
CN3791 BAT ── batériový uzol ── INA219 BAT → chránená LiPo 1S
                    └→ MT3608 → 5 V pre ESP a záložný kontakt relé
LAB 5 V → relé hlavný kontakt a cievka
relé spoločný kontakt → LED vetvy cez BC547
```

Pri dostupnom LAB LED berú hlavné 5 V. Pri jeho výpadku relé samo prejde na 5 V z batérie. ESP je stále na meničovom výstupe. CN3791 znižuje vstupné napätie pri nabíjaní jedného článku; MT3608 ho potom z batérie zvyšuje na 5 V. Ďalší menič 12→5 V pred nabíjačkou v tomto návrhu netreba.

Batériový INA219 je medzi plusom článku a spoločným uzlom nabíjačky/meniča, aby meral všetok čistý prúd. Kladný prúd znamená nabíjanie, záporný vybíjanie. Aplikácia ukazuje napätie, prúd a výkon panela, batériový prúd a **orientačné percentá z napätia**. Nie je to presné meranie využiteľnej kapacity.

## Jedno nutné overenie panela pred zapojením

Na odpojenom paneli zmeraj napätie naprázdno Voc multimetrom vo V DC. „12 V“ panel nemusí dávať presne 12 V. INA219 má elektrický limit 26 V a CN3791 čip 28 V; platí aj prípadný nižší limit modulu. Nezapájaj to pri 24 V alebo viac bez preverenia rezervy a maximálneho Voc. Meranie v interiéri nie je potvrdenie zimnej vonkajšej prevádzky. Podrobný postup a polarita: [ZAPOJENIE.md](ZAPOJENIE.md).

CN3791 variant 12 V je predbežná voľba pre označenie tvojho panela. MPPT bod je pevný deličom, nie univerzálne automatické hľadanie; pri inom skutočnom Vmp ho treba doladiť. Nepriraďujeme panelu výkon z iného výrobku. Ak by výkon prekročil 20 W alebo prúd merací rozsah INA219, tento malý merací návrh a API limity treba najprv upraviť.

470 µF / 16 V zostáva **iba na 5 V vetve**, nie na solárnom vstupe. BC547 zostávajú pre malé LED, nie výkonový LED pás. Pripojenie batérie priamo na panel alebo LAB sa nepoužíva.

## Dobitie zo zdroja a nastavenie aplikácie

Na úplné dobitie odpoj servisnú prepojku k MT3608 a všetky záťaže. Odpoj solár, LAB pripoj iba na IN CN3791 a nastav podľa jeho overeného MPPT bodu a limitov (pri MPPT 12 V napr. 13–14 V). Nikdy tým súčasne nenapájaj hlavnú 5 V vetvu; pred jej obnovením vráť LAB na 5,00 V. CN3791 nemá samostatný power-path, preto zapnuté ESP môže ovplyvniť ukončenie nabíjania.

V aplikácii nemeníš článok na 12 V. Zostáva LiPo 2500 mAh. Kalibračný výkon panela je maximum reálne namerané pod prezentačným svetlom vo W; nezadávaj tam číslo 12 len preto, že panel má 12 V. Predvolená kalibrácia nie je overený výkon konkrétneho panela. Fyzické merania sú nezávislé od škálovania virtuálnej FV.

## Strecha a simulácia

Panel zostáva na odnímateľnej streche. Existujúci 3D obrys 230 × 195 × 17 mm je výslovne predbežný, kým sa skutočný panel nezmeria. Lišty/klipy a konektor sa prispôsobia skutočnému kusu. Z označenia 12 V nemožno určiť rozmery ani hmotnosť.

BenchTwin návod je samostatne v SOC-simulacia/BENCHTWIN-NAVOD.txt. Vyber 12 V solárny vstup a 12 V variant CN3791 pre 1S; neznámy výkon v simulácii označ ako testovaciu hodnotu, nie ako parameter svojho panela. Produkčný firmvér používa FreeRTOS; BenchTwin má samostatný diagnostický sketch. Celé fyzické nabíjanie ani kompletný BenchTwin obvod tu neboli odskúšané.

Zdroje: [Techfun CN3791](https://techfun.sk/produkt/solarna-nabijacka-cn3791-pre-litiove-baterie/), [datasheet CN3791 odkazovaný predajcom](https://www.laskakit.cz/user/related_files/dse-cn3791-2.pdf), [TI INA219](https://www.ti.com/lit/ds/symlink/ina219.pdf). Kontrola 10. 11. 2026.
