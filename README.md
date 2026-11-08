# SOČ – kompletný projekt a BenchTwin

- [Stiahnuť celý aktualizovaný projekt ZIP](SOC-vsetko.zip?raw=1)
- [Podrobný návod pre BenchTwin](BENCHTWIN-NAVOD.txt)
- [Skúšobný kód pre BenchTwin ZIP](BENCHTWIN-KOD.zip?raw=1)

Rozbaľ SOC-vsetko.zip. Priečinok SOC obsahuje aplikáciu, firmvér, model domu a stavebné podklady. SOC-simulacia je samostatne vedľa projektu. Začni súborom BENCHTWIN-NAVOD.txt.

V BenchTwin postupuj Build → Wire → Code → Simulate podľa návodu. BENCHTWIN-KOD.zip importuje iba skúšobný sketch, nie zapojenú 3D scénu. Produkčný firmvér používa FreeRTOS, ktorý simulátor aktuálne nepodporuje; priložený profil overuje prepínače, svetlá a detekciu hlavného zdroja cez loop()/millis(). Nevyrába percentá ani telemetriu. Napätia/prúdy sleduj meradlami; podpora druhej I2C adresy a siete závisí od konkrétnej verzie. Kompletný obvod v BenchTwin tu nebol interaktívne spustený.

AI chat podporuje sformátované nadpisy, zoznamy, zvýraznenie, tabuľky a bloky kódu. Knižnice sú pribalené lokálne, bez CDN. Zmeny sú v [PR #3](https://github.com/matejzm2019/SOC/pull/3).

Aktualizované 8. 11. 2026. ZIP obsahuje zdroje z commitu f711a8a127ca86fd3b5c3db8fd85163d10ac1490.
