# Model domu s meraním solárnej batérie

Aktuálna zostava a schéma sú v [KOMPONENTY.md](KOMPONENTY.md). Laboratórny zdroj napája ESP32 a LED. Panel cez INA219 a BQ24074 nabíja samostatný chránený Li-ion článok; MAX17048 odhaduje SOC a meria napätie. Článok nenapája ESP ani svetlá.

Normálny režim prijíma meranie cez Wi-Fi. Výkon panela a prepínače ovplyvňujú škálované toky domácnosti. Stav článku je výstup merača; zostávajúca energia je odhad z kapacity a SOC. Internet je potrebný pre počasie a ceny, nie pre ESP či lokálny chat s už stiahnutým modelom.

Osvetlite a zakryte panel, prepnite LED a ukážte výpadok modelovanej siete. ESP zostáva na laboratórnom zdroji. Dostatočné svetlo môže nabíjať článok; slabá lampa to nezaručí. SOC sa mení pomaly, použite aj históriu. Odpojenie napájania ESP znamená offline uzol; batéria jeho napájanie nepreberá.

Demo je samostatný softvérový experiment bez hardvéru, so scenármi a virtuálnou domácou batériou.
