# Jednotný kusovník – menšia zostava

Platný návrh 7. 11. 2026. Ceny orientačne podľa overenia 2. 11. 2026, bez dopravy; nie potvrdenie dnešnej skladovej dostupnosti. Vybraný je CN3791 + MT3608. Nekombinovať náhodne so starším návrhom BQ24074/MAX17048 alebo Waveshare Power Manager.

| ID | Ks | Diel | Cena spolu | Umiestnenie / poznámka |
|---|---:|---|---:|---|
| E01 | 1 | [ESP32-S3 N16R8](https://techfun.sk/produkt/esp32-s3-n16r8-wifi-a-bluetooth-5-0-vyvojova-doska/) | 9,95 € | technická doska; už objednaný nekupovať znovu; naposledy vypredaný |
| E02 | 1 | [Chránená LiPo 104050 – 2500 mAh](https://techfun.sk/produkt/li-pol-bateria-kablik-ochranny-obvod/) | 5,80 € podľa fotografie | 3,7 V / 4,2 V, 50×40×10 mm, PH2.0; už vybraná |
| E03 | 1 | [CN3791, variant 6 V](https://techfun.sk/produkt/solarna-nabijacka-cn3791-pre-litiove-baterie/) | 4,40 € | solárna nabíjačka, prúd overiť/nastaviť podľa článku |
| E04 | 1 | [MT3608 bez USB](https://techfun.sk/produkt/step-up-menic-mt3608/) | 0,85–0,95 € | nastaviť 5,00 V; údaj 2 A nie je zaručený výstup pri všetkých podmienkach |
| E05 | 1 | [Panel 6 V / 5 W](https://techfun.sk/produkt/waveshare-solarny-panel-6v-5w/) | 14,25 € | 230×195×17 mm, cca 533 g, na prednej strešnej rovine 35° |
| E06/E07 | 2 | [INA219](https://techfun.sk/produkt/snimac-prudu-ina219-obojsmerny/) | 9,00 € | panel 0x40, batéria 0x41, logické napájanie 3,3 V |
| E08 | 1 | [REL300 relé 5 V s optočlenom](https://techfun.sk/produkt/rele-modul-1-kanal-5v-so-zabudovanym-optoclenom/) | 1,40 € | spínanie LOW, NO/NC prepínajú LED |
| E09/E10 | 2 | [2N2222A](https://techfun.sk/produkt/bjt-npn-tranzistor-2n2222-800ma/) | 0,10 € | dve vetvy po 3 LED; overiť poradie vývodov |
| L01–L06 | 6 + 4 rezerva | [Biele LED 3 mm](https://techfun.sk/produkt/led-ka-1-kus-3mm-rozne-farby/) | 0,30 € za 10 | po tri na každý svetelný okruh |
| L07 | 1 + 1 rezerva | Modrá LED z rovnakej ponuky | 0,06 € za 2 | stav hlavného zdroja |
| S01/S02 | 2 | [SMTS-102](https://techfun.sk/produkt/kovovy-dvojpolohovy-prepinac-smts-102/) | 0,80 € | prepínače svetiel, logické kontakty proti GND |
| R | 4 balenia | [Rezistory ¼ W](https://techfun.sk/produkt/rezistor-rozne-hodnoty-1-4w-10-kusov/): 330 Ω, 1 kΩ, 10 kΩ, 22 kΩ | 1,00 € | 10 ks každej hodnoty; rezerva zostane |
| C | 1 + 1 rezerva | [470 µF / 25 V](https://techfun.sk/produkt/elektrolyticky-kondenzator-47uf-25v/) | podľa variantu | pri ESP 5 V, dodržať polaritu |
| J | 1 | [PH2.0 2-pin protikus/káblik](https://techfun.sk/produkt/ph2-0-kablik-samecsamica-2p/) | 0,40 € | naposledy vypredaný; XH2.54 ani JST1.25 nesedia |
| K | 2 balenia | [Dupont 20 cm](https://techfun.sk/produkt/kabliky-40-kusov-20-cm/), M–F a F–F | 4,40 € | na signály, nie motorové/hlavné napájanie |

## Ďalšie montážne diely

- Jedna univerzálna spájkovacia doska približne 50×30 mm (vyrezať z väčšej univerzálky), pinové lišty 2,54 mm a malé skrutkové svorky. ESP má podľa predajcu lišty pribalené, treba ich prispájkovať.
- Dátový USB-C kábel na programovanie ESP; samostatný napájací USB-C kábel/prepojka od overených 5 V meniča. Neprepájať dve USB napájania bez overenia dosky.
- DC zásuvka/adaptér 3,5×1,35 mm k panelu na skrutkové svorky; presný konektor CN3791 nepredpokladať bez porovnania dielov.
- Izolované vodiče približne 5 m červených a 5 m čiernych 0,25–0,5 mm², približne 10 m farebných 0,14–0,25 mm². Predstrihy sú v `model-domu/dlzky-vodicov.csv`; používaj z existujúcich zásob, netreba kupovať každú farbu zvlášť.
- Servisná rozpojiteľná dvojpinová prepojka medzi batériovým uzlom a MT3608, aby bolo možné pri úplnom prednabití odpojiť všetky záťaže.
- Izolačné stĺpiky pod PCB 4 mm, skrutky, sťahovacie pásky, príchytky vodičov, zmršťovacia bužírka. Batériu upevni mäkkým pásikom; nezovri ani neprepichni obal.
- Štyri nožičky pod dom, výška 10 mm, aby sa nestrihali vodiče pod podstavou.
- Štyri príchytky kovového rámu panela, dve montážne lišty L04 a dve výstuhy L03. Pôvodný rozpojiteľný konektor panela a odľahčenie ťahu; vodiče W18 po 650 mm vrátane pôvodného kábla. Konkrétny úchyt vyber podľa skutočného rámu, články nevŕtaj.
- Na fasádu balsa/cédrové lišty, rámy, parapety a voliteľný difúzny akrylát/papier. Kusy a dĺžky sú v model-domu/detaily-fasady.csv.
- Materiál domu: preglejka 8, 6 a 4 mm, lišta 10×10, lepidlo na drevo, brúsny papier, difúzny papier za okná a páska/tenká krycia lišta na spoj strechy. Presné diely Pxx/Lxx sú v rezacom pláne.
- Existujúci laboratórny zdroj, multimeter, spájkovačka, píla a vrtáky. Notebook a router nemusíš kupovať, ak ich už máš.

Hlavné moduly bez ESP a batérie vychádzajú približne na 30,05 €. S drobnosťami približne 42–55 €, bez dreva, úchytov panela a dopravy. Pri nákupe všetkého pripočítaj ESP a batériu. Cena batérie 5,80 € je z používateľovej fotografie, nie novo overená cena konkrétneho variantu.

## Otvorené parametre pred dokončením zapojenia

1. Predajca pri článku nezverejňuje dovolený nabíjací prúd. Potvrď jeho hodnotu a zmeraj/nastav limit konkrétneho CN3791. Čip má maximum 4 A, ale to neurčuje ani skutočné nastavenie dosky, ani povolený prúd batérie.
2. Ak sa limit CN3791 musí meniť, používa sa merací rezistor: podľa datasheetu I = 0,120 V / RCS. Pre príklad 0,5 A je RCS = 0,24 Ω. Presné puzdro prenes z dosky; vhodný rezistor nebol v ponuke Techfun overený. Bežné rezistory 330 Ω/1 kΩ túto úpravu nenahrádzajú. Toto je reálna chýbajúca položka, ak má dodaná doska nevhodný limit; nedá sa poctivo predpokladať hotové zapojenie bez kontroly.
3. Potvrď rozmery a konektory fyzických modulov. Na ich montáž sú v 3D modeli rezervované obálky, nie garantované presné vrtné šablóny.
