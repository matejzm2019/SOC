# SOČ – inteligentný dom s lokálnou AI

Projekt tvorí drevený prezentačný dom na podstave 600 × 450 mm, strešný solárny panel, chránená LiPo 2500 mAh, záloha osvetlenia a lokálna aplikácia. ESP32-S3 N16R8 meria panel a článok dvoma INA219 a cez Wi-Fi posiela údaje serveru FastAPI/SQLite na PC. AI cez Ollamu vysvetľuje dostupné merania a navrhuje potvrdené nastavenia.

Celé steny, rámované okná, cédrový obklad a odnímateľná strecha so sklonom 35° vytvárajú jednoduchý, vyrobiteľný model bez nábytku. Panel 230 × 195 mm je na streche, ktorá sa zdvíha v jednom kuse. LED sú na pevných stenách, elektronika v prístupnej technickej miestnosti. Pred odložením strechy sa rozpojí kábel panela.

Prezentácia: živé napätie/prúd a orientačný stav článku, dva svetelné okruhy, hardvérové prepnutie pri výpadku hlavného 5 V zdroja, história, modelové predikcie a lokálna AI. Malý panel ani článok fyzicky nenapájajú kilowattové toky energetického modelu. Testovacie údaje sú označené.

Nabíjanie CN3791 a MT3608 vyžadujú fyzické overenie prúdu a výstupného napätia. CN3791 nemá samostatný power-path; prednabitie sa robí s odpojenou záťažou podľa ZAPOJENIE.md. Percentá z napätia nie sú meranie skutočnej kapacity. Overenie návrhu opisuje OVERENIE-STAVBY.md.
