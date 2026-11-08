# energia. — lokálny energetický systém pre SOČ

**Inteligentný lokálny systém pre monitorovanie, predikciu a optimalizáciu energetickej spotreby a výroby domácnosti**

Lokálna aplikácia používa FastAPI, SQLite a responzívny webový dashboard. Beží na PC a cez domáci router je dostupná z mobilu aj ďalšieho počítača. Prepínač Demo v nastaveniach automaticky volí softvérový simulátor alebo model domu s ESP32. CSV je samostatná analýza historických údajov:

- **DEMO MODE:** celý experiment funguje bez hardvéru, má pripravené scenáre a zrýchlený päťminútový simulačný krok.
- **CSV história:** import vlastnej intervalovej spotreby a voliteľne FV, história, výpočtová ekonomika a výhľad podľa dostupných dát. Nepotrebuje ESP32.
- **Normálny režim:** model domu s ESP32-S3, malým panelom a prepínačmi záťaží cez Wi-Fi. Backend na notebooku spracúva meranie v sekundových intervaloch; pri odpojení ESP čaká na dáta a po pripojení automaticky pokračuje. Energetika domácnosti je škálovaný výpočtový model.

Na model sa privádza iba nízke DC napätie. Laboratórny zdroj môže mať sieťový vstup vo svojom uzavretom prístroji; so sieťovým napätím sa na modeli nepracuje.

## Aktuálna stavba: smart dom s odnímateľnou strechou

Verzia **0.12.0-assistant**: celé steny, bez nábytku, podstava 600 × 450 mm, dom 480 × 330 mm. Malé moduly CN3791 a MT3608, LiPo 2500 mAh, dva INA219, automatické prepnutie LED pri výpadku; panel 230 × 195 mm priamo na streche so sklonom 35°. AI zostáva na PC/serveri cez Ollamu, ESP komunikuje cez Wi-Fi.

- **[Stavebný návod PDF](model-domu/STAVEBNY-NAVOD.pdf)**, [rezací plán](model-domu/rezaci-plan.csv), [vodiče](model-domu/dlzky-vodicov.csv) a [detaily fasády](model-domu/detaily-fasady.csv).
- **[3D Blender](model-domu/3d/dom.blend)**, [GLB](model-domu/3d/dom.glb), [pôdorys](model-domu/vykresy/podorys.svg), šablóny dielov 1:1 v model-domu/vykresy/.
- **[Kusovník](docs/KOMPONENTY.md)**, **[zapojenie](docs/ZAPOJENIE.md)** a **[čo celý systém robí](docs/AKO-TO-FUNGUJE.md)**.
- Ovládanie A/B je na paneli C01 pri ľavom okraji podstavy, mimo chodníka. Montážne otvory a vedenie sú aktualizované.
- AI je všeobecný chat s predpoveďou konkrétnych dní/miest a čítacími online nástrojmi pre Qwen3 4B. [Podrobný návod](docs/LOKALNY_ASISTENT.md).
- V aplikácii karta **3D model a stavba**. Výrobné súbory otvoríš aj na `/stavba/`.

Elektronické moduly sú v 3D modeli rozmerové rezervy; presné montážne otvory treba preniesť zo zakúpených dielov. Úprava nabíjacieho prúdu CN3791 zostáva kontrolou pred fyzickou montážou, nie garantovanými parametrami z obrázka. Návod a pripravené súbory simulácie sú na želanie používateľa v samostatnom balíku mimo projektu.

## Spustenie

1. Na Windows spustite **`start.cmd`**.
2. Na PC otvorte `http://127.0.0.1:8765`.
3. Telefón pripojte k rovnakému routeru a otvorte LAN adresu, ktorú vypíše štartovacie okno, napríklad `http://192.168.1.25:8765`.
4. Pri prvom upozornení Windows Firewall povoľte Python pre **súkromnú sieť**.

Opakovaný štart rozpozná už bežiacu Energiu a otvorí jej dashboard bez druhého servera a chyby portu 8765. LAN výpis používa aktívne fyzické adaptéry; neuvádza Hamachi ani adresy 169.254.x.x. Ak port obsadí iná aplikácia, oznámi to a jej proces neukončí.

PC musí počas prezentácie bežať. Router nepotrebuje internet; vytvára iba lokálnu sieť medzi PC, ESP32 a telefónom. Dashboard sa neinštaluje ako APK, takže rovnaké rozhranie funguje na PC, Androide aj iPhone a aktualizuje sa iba na jednom mieste.

Prvý štart na novom PC potrebuje internet na stiahnutie Python balíkov. Internetové počasie vyžaduje pripojenie; demo, importovaná história a časová predikcia fungujú offline. Server je určený pre dôveryhodnú domácu sieť. Nemá používateľské účty a nie je určený na vystavenie do verejného internetu.

### Počasie a lokálna AI

V nastaveniach vyberte mesto alebo jednorazovo povoľte polohu. Predvolený poskytovateľ je Open-Meteo. Pri GPS na mobile cez LAN HTTP adresu použite výber mesta alebo nakonfigurujte HTTPS. [Návod na používanie bez hardvéru](docs/REALNE_POUZITIE.md) vysvetľuje režimy, import CSV a pôvod hodnôt.

Nainštalujte [Ollamu](https://ollama.com/download/windows) na PC s backendom a spustite:

```powershell
ollama pull qwen3:0.6b
```

Model je už prednastavený v aplikácii. Ponechajte Ollamu spustenú, v nastaveniach overte pripojenie a použite kartu asistenta na domovskej stránke. Chat a zhrnutia sú lokálne. Pre výkonnejší PC možno v nastaveniach vybrať `qwen3:1.7b`. Podrobnosti a obmedzenia číselných odpovedí sú v [návode asistenta](docs/LOKALNY_ASISTENT.md).

Pre prirodzenejší rozhovor odporúčame stiahnuť `ollama pull qwen3:4b-instruct-2507-q4_K_M` a vybrať **Qwen3 4B** v nastaveniach. Menšie verzie zostávajú dostupné pre slabší notebook. Pozdravy odpovedajú bez energetického prehľadu; odpoveď vytvára lokálny model.

**AI chat vie navrhnúť aj nastavenia:** „Zapni internetové ceny“, „Nastav nákup na 0,20 €/kWh“, „Vypni demo režim“ alebo „Nastav kapacitu malej batérie na 2000 mAh“. Návrh zobrazí pôvodné aj nové hodnoty; tlačidlo **Použiť zmenu** ho uloží. Bežné otázky nastavenia nemenia.

### Manuálne spustenie

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c constraints.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8765 --workers 1
```

## ESP32-S3 a fyzický model

Hlavný 5 V zdroj napája cez relé LED. Pri výpadku LED prejdú na MT3608 z chránenej LiPo. ESP je stále na tomto zálohovanom výstupe; CN3791 nabíja článok zo soláru. Percentá sú orientačný odhad z napätia, prúd sa meria druhým INA219.

Postup firmvéru je v [firmware/esp32-s3/README.md](firmware/esp32-s3/README.md), schéma v [docs/ZAPOJENIE.md](docs/ZAPOJENIE.md). Server pri prvom štarte vytvorí `data/device_key.txt`; do ignorovaného `secrets.h` doplň Wi-Fi, LAN URL PC a tento kľúč. Arduino AI nespúšťa, jeho úlohou je meranie a bezpečné miestne riadenie. Úplný popis: [AKO-TO-FUNGUJE.md](docs/AKO-TO-FUNGUJE.md).

## Funkcie

- Nastavenia pre zdroj dát, miesto a počasie, moduly, model domácnosti, tarifu a lokálneho asistenta. Zmena modelu vytvorí nový súbor údajov; zmena asistenta alebo zobrazenia zachová históriu.
- Tmavý a svetlý vzhľad s predvoleným tmavým režimom. Voľba sa ukladá len v prehliadači a nemení experiment.
- Živé modelované energetické toky; v deme virtuálna batéria s odhadom do limitu, v normálnom režime meranie INA219: napätie, znamienkový prúd a orientačné percentá článku.
- Osem prezentačných scenárov vrátane prebytku, večernej špičky a výpadku siete.
- História 24 h, 7 dní, 30 dní a celého experimentu, intervalové kWh a CSV export.
- Ručná/časová tarifa alebo aktuálny slovenský spot Energy-Charts, zadaná prirážka a DPH; nezávislý výkup, distribúcia a fixný poplatok. Spot nie je automaticky cena z faktúry. SK dáta sú na súkromné použitie; verejné demo používa ručné ceny.
- 24 h predikcia klasickým sezónnym time-series modelom; LLM sa na matematickú predikciu nepoužíva.
- Výhľad FV podľa internetového počasia, orientácie a sklonu panelov, cache a označenie starých meteorologických údajov.
- Lokálny chat a zhrnutia cez Ollamu, kontrola dostupnosti modelu a číselné hodnoty viazané na podkladové fakty.
- Import CSV, výber starších súborov údajov a ekonomické porovnanie taríf nad rovnakými importovanými intervalmi.
- Pravidlové odporúčania z vypočítaných hodnôt fungujú aj bez LLM.
- SQLite persistencia a validované API; dátový zdroj je oddelený od dashboardu a analytiky.

V DEMO MODE predstavuje krok päť minút. V monitorovacom režime vzniká vzorka každú sekundu a prehliadač aktualizuje živé hodnoty približne každých 0,5 sekundy. Pri zdroji ESP32 pomer aktuálneho výkonu malého panela ku kalibračnému výkonu riadi virtuálnu FV elektráreň. Ide o názorný model správania výroby, nie o tvrdenie, že malý panel fyzicky vyrába kilowatty. Dáta majú označenie `source=hybrid` a `quality=mixed`.

Aktuálna správa pre učiteľa je v [docs/SPRAVA_PRE_UCITELA.md](docs/SPRAVA_PRE_UCITELA.md). Staršie súbory v `deliverables/` zachytávajú pôvodný návrh; na stavbu používaj nové ZAPOJENIE.md a model-domu/.

## Testy

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c constraints.txt
.\.venv\Scripts\python.exe -m pytest -q
node --check frontend/app.js
```

Testy overujú bilanciu výkonov, SOC a účinnosť batérie, tarify, výpadok, predikciu, persistenciu, API validáciu, autentifikáciu ESP32 a hybridný prepočet panela. Aktuálne kontroly sú v [docs/OVERENIE-STAVBY.md](docs/OVERENIE-STAVBY.md).

Integračné testy používajú riadené HTTP odpovede pre počasie a Ollamu. Overujú cache pri výpadku internetu, záznamy plánovania, atomický CSV import, časovú tarifu, archívy, modelové nastavenia a označenie neoverených číselných veličín bez zablokovania odpovede. Skutočnú kvalitu a rýchlosť nainštalovaného LLM treba overiť na konkrétnom PC.

## Repozitár

```text
backend/                 FastAPI, modely, simulátor, SQLite, analytika
frontend/                responzívny dashboard bez build kroku
firmware/esp32-s3/       Arduino firmvér a zapojenie
tests/                   automatické testy
docs/                    architektúra, hardvér, demo a overenie
deliverables/            prezentácia a správa pre učiteľa
data/                    lokálne dáta a kľúč; ignorované Gitom
start.cmd, start.ps1     Windows spúšťače
```

Technická architektúra a vedecké predpoklady sú v [docs/ARCHITEKTURA.md](docs/ARCHITEKTURA.md). Prezentačný postup je v [docs/DEMO.md](docs/DEMO.md).
