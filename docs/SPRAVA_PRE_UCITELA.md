# Správa pre učiteľa

Dobrý deň,

na SOČ pripravujem projekt „Inteligentný lokálny systém pre monitorovanie, predikciu a optimalizáciu energetickej spotreby a výroby domácnosti“.

Aplikácia beží na notebooku a cez lokálny Wi-Fi router ju možno otvoriť aj na mobile. Ukazuje spotrebu, výrobu fotovoltaiky, tok energie, históriu, ekonomiku a predikciu. Má tiež demo režim s pripravenými scenármi.

Chcem pripraviť malý fyzický model domu bez použitia 230 V. ESP32-S3 bude merať výkon malého solárneho panela cez INA219 a osvetlenie cez BH1750. Panel budem osvetľovať USB LED lampou. Dva prepínače rozsvietia LED svetlá v dome a zmenia modelovanú spotrebu; tretie tlačidlo ukáže výpadok siete.

Model bude mať aj skutočnú nabíjateľnú batériu. Powerbanka ju bude nabíjať cez hotový modul s riadeným nabíjaním a 5 V výstupom. Po odpojení powerbanky bude batéria ďalej napájať ESP32 a LED svetlá. Veľká domáca batéria a jej SOC v aplikácii budú samostatným matematickým modelom; fyzická batéria napája iba stolový model.

Potrebovali by sme:

- ESP32-S3 DevKit a USB dátový kábel,
- solárny panel 5–6 V / približne 0,5–1 W,
- senzory INA219 a BH1750,
- rezistor 47 Ω / aspoň 2 W pre panel,
- nabíjací modul PowerBoost 1000C alebo ekvivalent s prepínaním USB/batéria,
- chránenú 3,7 V LiPo batériu približne 2 000 mAh s kompatibilným JST konektorom,
- USB-A výstupný konektor modulu a micro-USB kábel pre jeho nabíjanie,
- powerbanku aspoň 10 000 mAh a USB LED lampu,
- dve LED na osvetlenie domu, tretiu LED na stav siete a tri rezistory 220–330 Ω,
- tri tlačidlá alebo prepínače, breadboard, vodiče a materiál na model domu,
- Wi-Fi router; ak školská sieť izoluje zariadenia, malý cestovný router s USB napájaním.

Notebook môže bežať na vlastnej batérii. Router vytvorí lokálnu sieť, internet počas prezentácie nepotrebujeme. Solárny panel bude samostatne meraný vstup; nebude priamo nabíjať batériu ani napájať ESP32. Pri prezentácii rozlíšim reálne merané veličiny od prepočítanej domácej energetiky.

Takto bude možné predviesť fungujúci model, nabíjanie a prevádzku z batérie, svetlá domu aj zmeny na dashboarde bez pripojenia k sieťovému napätiu.

Ďakujem.
