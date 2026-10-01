# Overenie lokálneho MVP

Dátum: 1. 10. 2026. Prostredie: Windows, Python 3.12.14, verzie závislostí v `constraints.txt`.

- `python -m pytest -q`: **37 úspešných testov**. Dve upozornenia na zastarávanie API pochádzajú z testovacích závislostí Starlette/httpx/AnyIO; nejde o chyby testov.
- `node --check frontend/app.js`: úspešná syntaktická kontrola.
- `python -m compileall -q backend`: úspešná kontrola Python modulov.
- Reálny lokálny server: health `ok`, osem scenárov cez HTTP bez porušenia bilancie; spustenie simulátora pridalo vzorky, pauza zastavila posúvanie času.
- Spúšťač `start.ps1` počúva na `0.0.0.0:8765` a vypíše lokálnu aj LAN adresu. `start.cmd` je jednoduchý obal pre tento skript.
- Prehliadač: prejdené všetky tri kroky wizardu, uloženie experimentu, výpadok siete, história 24 h/7 dní, predikcia, ekonomika.
- Modularita v UI: vypnuté ceny a batéria, zapnutý vietor; ekonomika a SOC zmizli, objavila sa veterná výroba. Následne bol obnovený predvolený experiment.
- Vizuálna kontrola prepracovaného svetlého dashboardu na desktope a v mobilnom viewporte 390 × 844; bez vodorovného pretečenia stránky. Mobil má vlastný čitateľný prehľad energetických tokov.
- Prepínač DEMO MODE bol overený v API aj rozhraní. V monitorovacom režime sú intervaly 1 s, pripravené scenáre a zrýchlenie sú zablokované a health endpoint hlási `monitor`.
- Prehliadač po spustení aktualizoval čas za 1,7 s bez chyby JavaScriptu. Živý stav sa načítava každých 0,5 s, grafové dáta najviac každých 1,5 s. V rozhraní nie je text SOČ.
- Prezentácia bola zostavená ako editovateľný PPTX, vyrenderovaná a skontrolovaná po jednotlivých snímkach.
- Po načítaní finálneho JavaScriptu prehliadač nehlásil chyby v konzole. Nový stav zariadenia sa zmestí do desktopového aj mobilného ovládacieho panela.

Testy simulátora pokrývajú 300 krokov každého z ôsmich scenárov so zapnutou aj vypnutou batériou; overujú aj účinnosť batérie, ekonomiku, tarify, vypnuté moduly, predikčný holdout, validáciu a obnovu stavu. Hybridné testy overujú kľúč zariadenia, online stav, validáciu telemetrie, škálovanie výkonu panela a odmietnutie kroku pri odpojenom ESP32. Samostatný test overuje návrat času a energie pri zlyhaní zápisu do databázy.

Neoverené: kompilácia a beh firmvéru na konkrétnej doske ESP32-S3, reálne senzory, batériový modul a kalibrácia panela, prístup z druhého fyzického zariadenia cez konkrétny router, dlhodobá prevádzka s veľkou databázou, Linux/macOS, internetové API, pokročilý ML a llama.cpp. Tieto časti nie sú prezentované ako fyzicky overené.
