# Päťminútová SOČ prezentácia

1. Spustite `start.cmd`, otvorte http://127.0.0.1:8765. Pred prezentáciou overte štart bez internetu. V nastaveniach zapnite **DEMO MODE**. Predvolené FV 6 kWp, batéria 10 kWh, ceny zapnuté; vyberte ručný zdroj cien.
2. Vysvetlite banner **DEMO MODE** a simulačný čas. Ukážte predgenerovaný deň histórie; nejde o meranie domácnosti.
3. **Slnečný deň**: výroba pokrýva časť spotreby a nabíja batériu, prebytok ide do siete. Výsledok závisí od času a parametrov; pri poludňajšom štarte predvolene vidno slnko.
4. **Zamračenie**: výroba poklesne. Ukážte zmenu batériového toku alebo importu.
5. **Večerná špička** a **Vybitá batéria**: porovnajte spotrebu, SOC a odber zo siete. Každá zmena scenára inicializuje SOC a pridá päťminútový interval.
6. **Vysoký prebytok**: takmer plná batéria a vysoká FV výroba spôsobia export. V ekonomike ukážte príjem; zmena tarify ovplyvňuje nové intervaly, nie spätne celú históriu.
7. **Výpadok siete**: sieť má presne 0 W. Batéria kryje spotrebu do rezervy; zrýchlite 20× a sledujte nepokrytú spotrebu. Nie je potrebných 230 V ani fyzický model.
8. **Nízka cena energie / Vysoká cena energie**: ukážte cenu a pravidlové odporúčanie. Model automaticky nenakupuje energiu ani neriadi zariadenia.
9. V predikciách vysvetlite `t − 24 h`, hranice baseline a význam MAE/RMSE. Po cca 24 ďalších simulačných hodinách sa objaví hodnotenie.
10. Exportujte CSV a ukážte zdroj `simulator`, kvalitu `synthetic`, intervaly a jednotky. V nastaveniach vypnite batériu alebo FV a vytvorte nový experiment: výpočty aj dashboard sa prispôsobia.

Ak je pripojený model, na záver vypnite DEMO MODE; automaticky sa vyberie **Normálny režim · model domu s ESP32** a ukážte, že zakrytie panela, dve záťaže a tlačidlo výpadku menia dashboard v sekundovom intervale. ESP a LED napája laboratórny zdroj. Panel cez BQ24074 nabíja samostatný článok a MAX17048 zobrazuje jeho SOC a napätie. Nabíjanie pod lampou overte vopred; zmenu SOC sledujte dlhšie. Článok nenapája model domu.

## Čo obhájiť

- Oddelenie dátového kontraktu, simulátora, analytiky a dashboardu umožňuje v budúcnosti vymeniť zdroj dát.
- kWh vznikajú integráciou výkonu za simulačný interval, nie sčítaním výkonov.
- Import a export sa integrujú samostatne, neodpočítajú sa pred výpočtom ceny.
- Batéria má výkonový limit, rezervný SOC a straty; pri nedostatku energia nemôže vzniknúť zo vzduchu.
- Baseline je matematický časový model. Pravidlové zhrnutie nie je LLM; lokálny LLM cez Ollamu iba interpretuje schválené fakty.
- Výsledky na simulátore sú dôkaz implementácie, nie dôkaz presnosti na reálnych domácnostiach.

Pre vedeckú časť ďalšej iterácie porovnajte rovnaký dataset bez FV/batérie a s nimi, rovnaké počiatočné SOC, tarifné podmienky a pokrytie spotreby. Návratnosť investície zatiaľ nie je súčasťou ekonomiky MVP.
