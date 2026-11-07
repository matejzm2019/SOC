# SOČ – všetko na stiahnutie

**[STIAHNUŤ CELÝ BALÍK SOC-vsetko.zip](https://github.com/matejzm2019/SOC/raw/refs/heads/baliky-na-stiahnutie/SOC-vsetko.zip)**

Balík pripravený 7. 11. 2026 obsahuje 93 súborov (približne 5,5 MB):

- **SOC/** – aplikácia, firmvér ESP32-S3, dokumentácia, kusovník, zapojenie, 3D modely Blender/GLB/STL, rezací plán, šablóny SVG 1:1, stavebný návod PDF a dĺžky vodičov/hadičiek.
- **SOC-simulacia/** – samostatný TXT návod, lokálny softvérový tester a súbory Wokwi. Simulácia je vedľa projektu, nie v jeho priečinku.

Rozbaľ celý ZIP tak, aby priečinky SOC a SOC-simulacia zostali vedľa seba. Na Windows spusti SOC/start.cmd. Simuláciu spusti podľa **[AKO-SIMULOVAT.txt](AKO-SIMULOVAT.txt)**. ZIP neobsahuje skutočné prihlasovacie údaje, databázy ani nainštalované knižnice; postup inštalácie je v návodoch.

[Zdrojový projekt a jednotlivé súbory](https://github.com/matejzm2019/SOC/tree/codex/soc-dom-stavba-2026-11) · [Návrh zmien PR #1](https://github.com/matejzm2019/SOC/pull/1)

Táto vetva baliky-na-stiahnutie slúži na odovzdanie balíka. Hlavná vetva a zdrojová vetva projektu sa týmto nahratím nemenia. Balík zodpovedá zdrojovému commitu f34a7d490265d582302ef7117522ddf85e217912.

SHA-256 SOC-vsetko.zip: `c3b3097bf39a25c28bff05b91dc1a7dfd7a390e4b02cae88ab17f3347c491aca`.

Pred fyzickým zapojením over nabíjací prúd konkrétnej CN3791 a dovolený prúd batérie; vhodný filter a spoje sa vyberajú podľa skutočných dielov. Podrobnosti sú v SOC/docs/KOMPONENTY.md a SOC/docs/ZAPOJENIE.md.
