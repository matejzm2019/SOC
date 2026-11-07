# SOČ – aktuálny balík 0.12.0-assistant

**[STIAHNUŤ VŠETKO – SOC-vsetko.zip](https://github.com/matejzm2019/SOC/raw/refs/heads/baliky-na-stiahnutie/SOC-vsetko.zip?v=0.12.0)**

Verzia 8. 11. 2026, 91 súborov, približne 8 MB.

- **Všeobecná AI pre Qwen3 4B:** otázky aj mimo energetiky, kalendárna predpoveď pre zajtrajšok/ďalšie dni, iné mestá a konkrétne hodiny, čítacie online nástroje a odkazy na zdroje. Online zdroje majú vlastný prepínač. Pri nedostupnom verejnom vyhľadávači je označená náhrada Wikipédiou; nie je to overenie aktuálnych správ. Lokálny model a Open-Meteo nepotrebujú API kľúč. Voliteľný OLLAMA_API_KEY umožňuje oficiálne širšie vyhľadávanie podľa podmienok Ollamy. Podrobnosti: SOC/docs/LOKALNY_ASISTENT.md.
- **Ovládanie mimo chodníka:** označený panel C01 vľavo vpredu, telá prepínačov pod doskou na 15 mm stĺpikoch, A/B a hlavná indikácia. Aktualizované otvory, vodiče a kusovník. Miestne odrušenie kontaktov vo firmvéri nezávisí od siete.
- Detailný drevený dom 600 × 450 mm, panel na odnímateľnej streche 35°, bez nábytku a vodného okruhu. Rámy okien, parapety, obklad a strešné detaily sú aj v editovateľnej geometrii.

![Aktuálny model](https://raw.githubusercontent.com/matejzm2019/SOC/codex/soc-dom-stavba-2026-11/model-domu/nahlady/dom-zatvoreny.jpg)

ZIP obsahuje **SOC/** (aplikácia, nový firmvér 0.7.0-controls, kompletné stavebné podklady a 3D) a **SOC-simulacia/** (samostatný tester, Wokwi a návod TXT vedľa projektu).

Rozbaľ oba priečinky vedľa seba. Na Windows spusti **SOC/start.cmd**. V Nastavenia → Asistent over nainštalovaný 4B model a povoľ online zdroje; pre predpoveď vyber mesto alebo sa opýtaj na konkrétne mesto. Nahraj aj nový firmvér so súbormi backup_power.h a switch_input.h. Pred odložením strechy rozpoj označený konektor panela.

[Simulačný návod TXT](AKO-SIMULOVAT.txt) · [Zdrojový projekt](https://github.com/matejzm2019/SOC/tree/codex/soc-dom-stavba-2026-11) · [Aktuálny PR #3](https://github.com/matejzm2019/SOC/pull/3)

Overené: 84 testov, 1 Windows test preskočený na Linuxe; reálna online predpoveď a encyklopedické dohľadanie; prehliadač s testovacou odpoveďou Ollamy; skutočné zostavenie firmvéru. Reálna inferencia 4B a fyzický hardvér sa tu nespúšťali. Podrobný záznam a fyzické kontroly sú v SOC/docs/OVERENIE-STAVBY.md.

Zdrojový commit: `ebb8b0902fe7a1bf30590de030b9e1e1bcbbb1bd`. Táto vetva slúži iba na odovzdanie balíka. Neobsahuje súkromné kľúče, databázy ani nainštalované knižnice.

SHA-256 SOC-vsetko.zip: `f238be8012948bcb03775e64cdb308e59099df8da12c16ba2f693572d2094fdb`.
