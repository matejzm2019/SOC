# 12 V solár – fungovanie, dobíjanie a prvé zapojenie

**Jeden celý nákupný zoznam je výhradne v [KOMPONENTY.md](KOMPONENTY.md)** – elektronika, rezistory, konektory, vodiče, drevo, úchyty aj vybavenie. Tu je prevádzkový návod; pôvodná nákupná tabuľka bola zlúčená do uvedeného zoznamu.

Aktuálne sa používajú **dva INA3221**, každý CH1 (PANEL 0x40, BAT 0x41). Revízie dosky majú odlišné meracie vývody, pozri [INA3221.md](INA3221.md). Limit použitého modulu je 1,1 A v oboch smeroch; CN3791 aj špičky MT3608 musia tento limit rešpektovať. Vstupy dvoch modulov sa kladne neprepájajú. Čipové napájanie oboch je 3V3.

## Tok energie

```text
12 V panel → INA3221 PANEL → CN3791 IN
CN3791 BAT ── batériový uzol ── INA3221 BAT → chránená LiPo 1S
                    └→ MT3608 → 5 V pre ESP a záložný kontakt relé
LAB 5 V → relé hlavný kontakt a cievka
relé spoločný kontakt → LED vetvy cez BC547
```

Pri dostupnom LAB LED berú hlavné 5 V. Pri jeho výpadku relé samo prejde na 5 V z batérie. ESP je stále na meničovom výstupe. CN3791 znižuje vstupné napätie pri nabíjaní jedného článku; MT3608 ho potom z batérie zvyšuje na 5 V. Ďalší menič 12→5 V pred nabíjačkou v tomto návrhu netreba.

Batériový INA3221 je medzi plusom článku a spoločným uzlom nabíjačky/meniča, aby meral všetok čistý prúd. Kladný prúd znamená nabíjanie, záporný vybíjanie. Aplikácia ukazuje napätie, prúd a výkon panela, batériový prúd a **orientačné percentá z napätia**. Nie je to presné meranie využiteľnej kapacity.

## Jedno nutné overenie panela pred zapojením

Na odpojenom paneli zmeraj napätie naprázdno Voc multimetrom vo V DC. „12 V“ panel nemusí dávať presne 12 V. INA3221 má elektrický limit 26 V a CN3791 čip 28 V; platí aj prípadný nižší limit modulu. Nezapájaj to pri 24 V alebo viac bez preverenia rezervy a maximálneho Voc. Meranie v interiéri nie je potvrdenie zimnej vonkajšej prevádzky. Podrobný postup a polarita: [ZAPOJENIE.md](ZAPOJENIE.md).

CN3791 variant 12 V je predbežná voľba pre označenie tvojho panela. MPPT bod je pevný deličom, nie univerzálne automatické hľadanie; pri inom skutočnom Vmp ho treba doladiť. Nepriraďujeme panelu výkon z iného výrobku. Ak by výkon prekročil 20 W alebo prúd merací rozsah INA3221, tento malý merací návrh a API limity treba najprv upraviť.

470 µF / 16 V zostáva **iba na 5 V vetve**, nie na solárnom vstupe. BC547 zostávajú pre malé LED, nie výkonový LED pás. Pripojenie batérie priamo na panel alebo LAB sa nepoužíva.

## Dobitie zo zdroja a nastavenie aplikácie

Na úplné dobitie odpoj servisnú prepojku k MT3608 a všetky záťaže. Odpoj solár, LAB pripoj iba na IN CN3791 a nastav podľa jeho overeného MPPT bodu a limitov (pri MPPT 12 V napr. 13–14 V). Nikdy tým súčasne nenapájaj hlavnú 5 V vetvu; pred jej obnovením vráť LAB na 5,00 V. CN3791 nemá samostatný power-path, preto zapnuté ESP môže ovplyvniť ukončenie nabíjania.

V aplikácii nemeníš článok na 12 V. Zostáva LiPo 2500 mAh. Kalibračný výkon panela je maximum reálne namerané pod prezentačným svetlom vo W; nezadávaj tam číslo 12 len preto, že panel má 12 V. Predvolená kalibrácia nie je overený výkon konkrétneho panela. Fyzické merania sú nezávislé od škálovania virtuálnej FV.

## Strecha a simulácia

Panel zostáva na odnímateľnej streche. Existujúci 3D obrys 230 × 195 × 17 mm je výslovne predbežný, kým sa skutočný panel nezmeria. Lišty/klipy a konektor sa prispôsobia skutočnému kusu. Z označenia 12 V nemožno určiť rozmery ani hmotnosť.

BenchTwin návod je samostatne v SOC-simulacia/BENCHTWIN-NAVOD.txt. Vyber 12 V solárny vstup a 12 V variant CN3791 pre 1S; neznámy výkon v simulácii označ ako testovaciu hodnotu, nie ako parameter svojho panela. Produkčný firmvér používa FreeRTOS; BenchTwin má samostatný diagnostický sketch. Celé fyzické nabíjanie ani kompletný BenchTwin obvod tu neboli odskúšané.

Zdroje: [Techfun CN3791](https://techfun.sk/produkt/solarna-nabijacka-cn3791-pre-litiove-baterie/), [datasheet CN3791 odkazovaný predajcom](https://www.laskakit.cz/user/related_files/dse-cn3791-2.pdf), [TI INA3221](https://www.ti.com/lit/ds/symlink/ina3221.pdf). Kontrola 10. 11. 2026.
