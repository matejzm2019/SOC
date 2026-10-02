# Používanie na PC bez ESP32

Aplikácia je určená na lokálne používanie v domácnosti. PC musí bežať; mobil a ďalší PC používajú ten istý backend cez domácu sieť. Automatické zisťovanie fyzickej spotreby bez zdroja meraní nie je možné. Preto rozhranie rozlišuje tieto režimy:

| Režim | Pôvod energie | Použitie |
|---|---|---|
| Plánovanie | Výpočtový model spotreby a batérie, FV a vietor podľa internetového počasia | Porovnanie parametrov a orientačný výhľad bez hardvéru |
| CSV história | Používateľské intervaly spotreby a voliteľne FV | Analýza vlastných údajov; sieť sa odvodzuje výpočtom bez batérie |
| Demo | Simulované energetické toky, pripravené scenáre a čas | Prezentácia aj bez internetu |
| Hybrid | Malý panel z ESP32 + model domácnosti | Voliteľná fyzická ukážka |

## Miesto a internetové počasie

V **Nastavenia → Miesto a počasie** ponechajte zdroj Open-Meteo. Zadajte mesto, stlačte Vyhľadať a vyberte výsledok podľa krajiny/oblasti. Alebo stlačte Použiť moju polohu a povoľte ju v prehliadači. Aplikácia nezisťuje polohu bez stlačenia tlačidla a nesleduje pohyb. Súradnice zaokrúhli na tri desatinné miesta a uloží vybranú oblasť do lokálnej SQLite databázy.

Počasie obsahuje teplotu, oblačnosť, vietor v m/s, zrážky, horizontálne žiarenie a žiarenie pre nastavenú rovinu panelov. Súradnice, sklon a orientácia sa odošlú Open-Meteo. Aktuálne údaje sú výstupom meteorologických modelov, nie lokálnej meteostanice. Rozhranie uvádza čas platnosti, získania a zdroj. Dokumentácia: [Open-Meteo](https://open-meteo.com/en/docs).

GPS v prehliadači vyžaduje HTTPS alebo dôveryhodný localhost. Pri otvorení `http://192.168…` z mobilu obvykle nebude povolené. Vyhľadanie mesta funguje aj cez lokálnu HTTP adresu. Pre GPS v celej LAN treba nakonfigurovať HTTPS s certifikátom dôveryhodným na klientskych zariadeniach. Zdroj: [MDN Geolocation](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/getCurrentPosition).

Počasie sa obnovuje približne každých desať minút, neúspešná obnova sa skúša v minútových intervaloch. Cache zostáva v databáze aj po reštarte. Po pol hodine od získania alebo pri starom čase pozorovania sa údaje označia ako staré. Pri výpadku internetu sa nevymenia za simulované údaje. Plánovanie zastaví tvorbu nových odhadov, kým sa neobnoví aktuálne počasie; staré hodnoty zostanú označené časom. Demo môže fungovať offline so zdrojom Počasie zo simulátora.

Bezplatné Open-Meteo API povoľuje súkromné domáce používanie, vzdelávanie a ďalšie nekomerčné účely. Pre komerčný produkt treba príslušnú licenciu/API plán. Atribúcia poskytovateľa je v karte počasia. [Podmienky Open-Meteo](https://open-meteo.com/en/terms).

## Plánovanie a predikcia

Vypnite Demo režim, vyberte **Plánovanie bez hardvéru** a nastavte miesto. Zadajte základnú spotrebu, kWp, orientáciu a sklon FV a prípadne kapacitu modelovanej batérie. Po uložení sa plánovanie spustí automaticky. Nové odhady vznikajú v minútových intervaloch; energetické údaje sú označené ako odhad. Počas odstávky PC sa údaje spätne nevyrábajú.

Výroba FV používa predpovedané žiarenie na rovine panelov, nominálny výkon, faktor strát a teplotnú korekciu. Veterný výhľad používa výkonovú krivku modelu a vietor z predpovede vo výške desať metrov; reálna turbína môže mať iné podmienky. Táto implementácia slúži na orientačný výhľad, jej presnosť zatiaľ nie je validovaná proti meraniu konkrétnej elektrárne.

Spotreba používa sezónny naivný časový model: opakuje posledný súvislý deň v hodinovom rozlíšení. Vyžaduje skutočne pokrytých 24 hodín s intervalmi najviac jednu hodinu. Počet záznamov sám nestačí. Ak história chýba, internetový výhľad použije zadaný model spotreby a túto skutočnosť označí. MAE a RMSE časového modelu potrebujú 48 súvislých hodín. Meteorologická FV predikcia sa týmito metrikami nepovažuje za overenú. LLM nevykonáva matematickú predikciu.

## Import vlastných intervalov

V **Režim a zdroj → Vlastná história** stiahnite vzor, upravte ho podľa vlastných údajov a nahrajte CSV. Príklad formátu:

```csv
timestamp,interval_minutes,load_kwh,pv_kwh
2026-09-01T01:00:00+02:00,60,0.35,0
2026-09-01T02:00:00+02:00,60,0.28,0
```

`timestamp` je koniec intervalu, musí obsahovať časové pásmo a rok 1970 až 2100. `load_kwh` je energia spotrebovaná domácnosťou v intervale; nejde o kumulatívny stav elektromera. `pv_kwh` je voliteľná energia FV v rovnakom intervale. Pri exporte dodávateľa s kumulatívnymi hodnotami treba najprv vypočítať rozdiely medzi odpočtami. Samotný čistý import zo siete nemožno považovať za celú spotrebu domu s FV.

Intervaly musia byť zoradené, bez prekrytia, od jednej minúty do jedného dňa. Medzery sú dovolené, ale blokujú časovú predikciu, ak chýba súvislý deň. Podporované sú oddeľovače čiarka alebo bodkočiarka; pri bodkočiarke možno použiť desatinnú čiarku. Limit je 3 MB a 35 040 intervalov. Import je atomický: chybný súbor neprepíše aktuálne údaje.

Import vypne demo, batériu a vietor. Dashboard zobrazuje priemer posledného importovaného intervalu a jeho dátum. Napätie a prúd sa nevymýšľajú. Odber/export siete sú odvodené z bilancie spotreba − FV; nezahŕňajú neznáme batériové toky a predstavujú intervalový výpočet. Ak sa v jednom intervale striedal import a export, čistá bilancia nedokáže rekonštruovať oba smery samostatne. Náklady preto zostávajú orientačnou analýzou podľa zadanej tarify.

Pri zmene tarify aplikácia vytvorí novú analýzu importovaných intervalov; pôvodný import zostane uložený. Jednotkovú cenu počas časovej tarify váži podľa času v intervale. Energia sa v intervale predpokladá rovnomerná. CSV neobsahuje automatické overenie pôvodu nameraných hodnôt.

V Histórii možno vybrať predchádzajúci súbor údajov a exportovať ho. História rôznych modelových nastavení sa nemieša do jednej časovej rady.

## Prevádzka a hranice nasadenia

Spúšťač inštaluje závislosti aj po aktualizácii projektu. Stav, konfigurácia, história a počasie sa ukladajú do SQLite. Zálohujte celý priečinok `data` pri vypnutom serveri. Používajte jeden proces backendu (`--workers 1`).

Server je pre dôveryhodnú domácu sieť. Nemá používateľské účty; každý s prístupom k tejto LAN aplikácii môže meniť nastavenia a importovať dáta. Nevystavujte port priamo do internetu. Verejné alebo viacužívateľské nasadenie vyžaduje autentifikáciu, HTTPS a ďalšie prevádzkové zabezpečenie. Túto verziu preto nepovažujeme za certifikovaný systém riadenia reálnej elektroinštalácie ani za verejnú cloudovú službu.

Ollama funguje lokálne podľa [návodu asistenta](LOKALNY_ASISTENT.md). Výpočty a pravidlové odporúčania fungujú aj bez nainštalovaného modelu.
