# Správa pre učiteľa

Dobrý deň,

na SOČ pripravujem lokálny systém na monitorovanie a predikciu energetiky domácnosti. Webová aplikácia beží na notebooku a cez Wi-Fi ju možno otvoriť aj na mobile. Má softvérové demo aj normálny režim pre fyzický model domu.

Upravil som napájanie modelu: ESP32-S3 a LED svetlá bude napájať laboratórny zdroj na 5 V DC. Panel cez solárnu nabíjačku BQ24074 nabíja samostatný chránený Li-ion článok. MAX17048 meria napätie a odhaduje nabitie batérie, INA219 výkon panela. ESP pošle merania cez router do notebooku. Batéria nenapája ESP ani LED.

Potrebovali by sme:

- ESP32-S3 DevKit, USB kábel a adaptér na napájanie zo zdroja,
- 6 V solárny panel približne 1–3 W,
- INA219, MAX17048 breakout a voliteľne BH1750 na osvetlenie,
- solárnu nabíjačku Adafruit BQ24074 a kompatibilné konektory,
- chránený 3,7 V / 4,2 V Li-ion alebo LiPo článok 1 000–2 000 mAh s povoleným nabíjaním aspoň 0,5 A,
- laboratórny zdroj, multimeter a dostatočne silnú lampu s vhodným DC napájaním,
- tri LED, tri rezistory 220–330 Ω a tri tlačidlá/prepínače,
- vodiče, breadboard, izolovaný držiak batérie a materiál domu,
- notebook a router umožňujúci komunikáciu medzi zariadeniami.

Pri prvom zapojení prosím o kontrolu polarity, nastavenia nabíjačky na 0,5 A a prúdového limitu zdroja. Na model neprivádzame 230 V; používame nízkonapäťový DC výstup. Laboratórny zdroj môže byť sám napájaný zo siete, ktorá zostáva v uzavretom prístroji.

Osvetlenie panela ukáže zmenu výkonu a pri dostatočnom svetle aj nabíjanie článku. Slabá lampa môže byť nedostatočná, preto to vopred vyskúšame. Nabitie sa mení pomalšie než výkon. Prepínače rozsvietia LED a menia modelovanú spotrebu. Import/export a veľké výkony domácnosti sú výpočtový model.

Počasie sa získava z internetu podľa mesta alebo povolenej polohy. Nákupnú cenu možno zadať ručne alebo použiť slovenský spot, ktorý nie je automaticky cenou z faktúry. Na verejnú prezentáciu použijem demo s ručnými cenami. Lokálny jazykový model vysvetľuje údaje, matematické predikcie počíta Python.

Ďakujem.
