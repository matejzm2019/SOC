# energia. — lokálny energetický systém pre SOČ

**Inteligentný lokálny systém pre monitorovanie, predikciu a optimalizáciu energetickej spotreby a výroby domácnosti**

Funkčný prototyp používa FastAPI, SQLite a responzívny webový dashboard. Beží na PC a cez domáci router je dostupný z mobilu aj ďalšieho počítača. Má dva režimy, ktoré sa prepínajú v nastaveniach:

- **DEMO MODE:** celý experiment funguje bez hardvéru, má pripravené scenáre a zrýchlený päťminútový simulačný krok.
- **Monitorovací režim:** prijíma ESP32-S3 alebo používa simulovaný vstup v sekundovom intervale. Malý 5–6 V panel sa meria fyzicky; energetika domácnosti zostáva matematickým modelom.

Projekt nikdy nepotrebuje pripojenie na 230 V. ESP32 sa napája cez USB a merací model používa iba bezpečné jednosmerné napätie.

## Spustenie

1. Na Windows spustite **`start.cmd`**.
2. Na PC otvorte `http://127.0.0.1:8765`.
3. Telefón pripojte k rovnakému routeru a otvorte LAN adresu, ktorú vypíše štartovacie okno, napríklad `http://192.168.1.25:8765`.
4. Pri prvom upozornení Windows Firewall povoľte Python pre **súkromnú sieť**.

PC musí počas prezentácie bežať. Router nepotrebuje internet; vytvára iba lokálnu sieť medzi PC, ESP32 a telefónom. Dashboard sa neinštaluje ako APK, takže rovnaké rozhranie funguje na PC, Androide aj iPhone a aktualizuje sa iba na jednom mieste.

Prvý štart na novom PC potrebuje internet na stiahnutie Python balíkov. Ďalšie spustenia, dashboard, simulátor, história a predikcia fungujú offline. Server nie je určený na vystavenie do verejného internetu.

### Manuálne spustenie

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c constraints.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8765 --workers 1
```

## ESP32-S3 a fyzický model

Odporúčaná zostava: ESP32-S3, panel približne 5–6 V / 0,5–1 W, INA219, BH1750, 47 Ω / 2 W rezistor, tri tlačidlá alebo prepínače, tri LED, chránená 3,7 V batéria a modul PowerBoost 1000C. Panel osvetľuje USB LED lampa. Powerbanka nabíja fyzickú batériu cez modul; pri jej odpojení batéria ďalej napája ESP32 a svetlá. Panel sa meria samostatne, domácu FV aplikácia prepočítava.

Firmvér, zapojenie a nastavenie Wi-Fi sú v [firmware/esp32-s3/README.md](firmware/esp32-s3/README.md). Presný nákupný zoznam je v [docs/KOMPONENTY.md](docs/KOMPONENTY.md) a priebeh ukážky v [docs/DEMO.md](docs/DEMO.md).

Pri prvom štarte server vytvorí tajný kľúč v `data/device_key.txt`. Skopírujte `firmware/esp32-s3/secrets.example.h` na `secrets.h`, doplňte Wi-Fi, LAN adresu PC a tento kľúč. Súbor `secrets.h` je ignorovaný Gitom. ESP32 odosiela JSON každé dve sekundy na `POST /api/device/telemetry`; dashboard jasne ukazuje online/offline stav.

## Funkcie

- Setup wizard pre moduly, parametre domácnosti, tarifu a zdroj merania.
- Živé energetické toky, výkon, napätie/prúd, SOC, energia batérie a odhad do limitu.
- Osem prezentačných scenárov vrátane prebytku, večernej špičky a výpadku siete.
- História 24 h, 7 dní, 30 dní a celého experimentu, intervalové kWh a CSV export.
- Manuálna alebo časová tarifa, nákup, výkup, distribúcia, fixný poplatok a prevádzková úspora.
- 24 h predikcia klasickým sezónnym time-series modelom; LLM sa na matematickú predikciu nepoužíva.
- Pravidlové odporúčania z vypočítaných hodnôt. Lokálny llama.cpp je plánovaná iterácia.
- SQLite persistencia a validované API; dátový zdroj je oddelený od dashboardu a analytiky.

V DEMO MODE predstavuje krok päť minút. V monitorovacom režime vzniká vzorka každú sekundu a prehliadač aktualizuje živé hodnoty približne každých 0,5 sekundy. Pri zdroji ESP32 pomer aktuálneho výkonu malého panela ku kalibračnému výkonu riadi virtuálnu FV elektráreň. Ide o názorný model správania výroby, nie o tvrdenie, že malý panel fyzicky vyrába kilowatty. Dáta majú označenie `source=hybrid` a `quality=mixed`.

Hotové podklady na odovzdanie sú v priečinku `deliverables/`: prezentácia a správa pre učiteľa. Ilustrovaný návrh modelu je v `docs/assets/model_soc.png`.

## Testy

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -c constraints.txt
.\.venv\Scripts\python.exe -m pytest -q
node --check frontend/app.js
```

Testy overujú bilanciu výkonov, SOC a účinnosť batérie, tarify, výpadok, predikciu, persistenciu, API validáciu, autentifikáciu ESP32 a hybridný prepočet panela. Záznam kontrol je v [docs/OVERENIE.md](docs/OVERENIE.md).

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
