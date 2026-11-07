# SOČ – aktuálny balík 0.11.0-roof

**[STIAHNUŤ VŠETKO – SOC-vsetko.zip](https://github.com/matejzm2019/SOC/raw/refs/heads/baliky-na-stiahnutie/SOC-vsetko.zip)**

Verzia 7. 11. 2026: **bez vodného okruhu, panel priamo na odnímateľnej streche**. Dom má rámované okná, parapety, drevený obklad, pevné dvere, falcovanú strechu a detailný rám/články/úchytenie panela. Podstava celého modelu je 600 × 450 mm, strecha 35°.

![Aktuálny model domu](https://raw.githubusercontent.com/matejzm2019/SOC/codex/soc-dom-stavba-2026-11/model-domu/nahlady/dom-zatvoreny.jpg)

ZIP obsahuje 86 súborov (približne 7,8 MB):

- **SOC/** – aplikácia, firmvér ESP32-S3, lokálna AI/server dokumentácia, aktualizovaný kusovník a zapojenie, detailné 3D Blender/GLB/STL, sedemstranové A3 PDF, SVG šablóny 1:1, rezací plán, doplnkové lišty a dĺžky vodičov.
- **SOC-simulacia/** – aktualizovaný samostatný TXT návod, lokálny testovací server/zariadenie a Wokwi. Zostáva vedľa projektu, nie v ňom.

Rozbaľ oba priečinky vedľa seba. Na Windows spusti **SOC/start.cmd**. Pri aktualizácii fyzickej dosky nahraj aj nový firmvér 0.6.0-roof; stará telemetria s dodatočnými poľami sa už neprijíma.

[Simulačný návod TXT](AKO-SIMULOVAT.txt) · [Zdrojový projekt](https://github.com/matejzm2019/SOC/tree/codex/soc-dom-stavba-2026-11) · [Aktuálny PR #2](https://github.com/matejzm2019/SOC/pull/2)

Pred úplným odložením strechy rozpoj označený konektor panela. Pred zapojením over prúd CN3791 podľa článku, napätie MT3608 a mechanické úchyty skutočného panelového rámu. Všetky skúšky a zostávajúce fyzické kontroly sú v SOC/docs/OVERENIE-STAVBY.md.

Zdrojový commit: `21d2ab5145940c3539bf34bcdaf01d671e9de787`. Táto vetva slúži iba na odovzdanie balíka. ZIP neobsahuje súkromné kľúče, databázy ani nainštalované knižnice.

SHA-256 SOC-vsetko.zip: `f13812a8723e4ec584a84c6a580aef42f04732747452361107142f2dadb5aba9`.
