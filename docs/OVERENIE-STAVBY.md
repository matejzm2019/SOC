# Overenie verzie 0.11.0-roof

7. 11. 2026. Toto je overenie softvéru a rozmerového návrhu, nie skúška postaveného fyzického domu.

- Python: **76 úspešných testov, 1 preskočený** (Windows spúšťač na Linuxe). Dve upozornenia testovacích knižníc sa týkajú zastarávajúcich rozhraní.
- Overený príjem svetelnej/solárnej telemetrie, autentifikácia, chýbajúce odstránené API a odmietnutie starých nadbytočných telemetrických polí. Pri prechode na túto verziu nahraj aj nový firmvér.
- C++ skúška používa priamo backup_power.h: napäťový odhad nabitia, neplatné hodnoty, monotónnosť a hysterézia detekcie hlavného zdroja.
- Arduino CLI 1.5.1, ESP32 core 3.3.12, ESP32S3 Dev Module, flash 16 MB, OPI PSRAM; Adafruit INA219 1.2.3 a ArduinoJson 7.4.3. Produkčný firmvér zostavený: **1 055 123 B programu, 48 804 B globálnych dát**. Simulátorová verzia zostavená: **420 804 B / 29 256 B**.
- Chromium/WebGL: geometria domu a panel na streche, spoločný zdvih/skrytie strechy a panela, automatické odkrytie elektroniky pri výbere, reset, klávesnica, šírka 390 px bez horizontálneho pretečenia, stiahnutie PDF/GLB. Bez zachytených JavaScriptových chýb pri týchto krokoch.
- Rozmerové testy: podstava 600 × 450, panel v pôdoryse strechy, odstup jeho spodnej strany od strešnej plochy, presné rozmery rezacieho plánu a zhodnosť CAD exportu s modelom aplikácie. Návrh má 381 geometrických objektov; detaily sú aj v GLB/STL a nie iba v renderi.
- Výstupy Blender 4.3.2; sedemstranové A3 PDF; nosné diely P01–P11 a L01–L04; samostatný kusovník drobných líšt; šablóny SVG 1:1 a pôdorys 1:2. Okná sú v geometrickom modeli skutočné otvory.

## Skúšky pred fyzickým zapojením

Over dovolený nabíjací prúd článku a skutočné nastavenie CN3791. Predajný údaj 4 A MAX nie je odporúčanie pre tento článok. CN3791 nemá oddelený systémový power-path; úplné prednabitie sa robí s odpojenou záťažou podľa ZAPOJENIE.md.

Zmeraj MT3608 na 5 V a jeho stabilitu pri Wi-Fi špičkách, adresy INA219, polaritu batérie a správne znamienko prúdu. Odpoj hlavný zdroj a over prepnutie relé pri skutočne zapnutých LED. Percentá z napätia nie sú meranie skutočnej kapacity.

Panel má približne 533 g. Skontroluj tuhosť strechy a výstuh L03, uchytenie za rám, dĺžku skrutiek a odľahčenie kábla. Pred úplným odložením rozpoj označený konektor. Detailové obálky elektroniky nie sú garantované vrtné šablóny.

Simulácia je samostatne mimo projektu. Náhradné analógové snímače neoverujú nabíjanie ani prúdy fyzickej LiPo. Úplná elektrická podpora všetkých konkrétnych modulov v BenchTwin nebola potvrdená. Kvalitu konkrétneho Ollama modelu treba odskúšať na prezentačnom PC. Hmotnosť 4–5 kg je odhad bez váženia.
