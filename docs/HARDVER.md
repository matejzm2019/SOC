# Bezpečný model domu

Úplný nákupný zoznam, schéma napájania a tabuľka pinov sú v [KOMPONENTY.md](KOMPONENTY.md). Model má dva fyzické energetické okruhy: malý solárny panel so samostatnou rezistorovou záťažou a chránenú 3,7 V batériu s USB nabíjačkou a 5 V výstupom. Panel meria INA219, svetlo BH1750 a ESP32-S3 posiela hodnoty cez lokálnu Wi-Fi do notebooku. Dve LED v dome reprezentujú zapnuté spotrebiče; tretia ukazuje dostupnosť virtuálnej siete.

Powerbanka nabíja fyzickú batériu cez modul s riadením nabíjania a prepínaním napájania. Po odpojení powerbanky batéria ďalej napája ESP32 a LED. V aplikácii zobrazené kWh, percento SOC domáceho úložiska, import/export a ceny zostávajú výpočtovým modelom. Napätie, prúd a výkon malého panela a osvetlenie sú reálne merané hodnoty. Pri ukážke treba tieto dva typy údajov pomenovať.

Na panel sa svieti USB LED lampou. Jeho aktuálny výkon sa vydelí kalibračným maximom zmeraným pod tou istou lampou. Tento pomer riadi výkon virtuálnej fotovoltaiky. Napríklad 0,25 W z maxima 0,50 W znamená 50 % nastavenej virtuálnej FV. Malý panel fyzicky nenapája domácnosť ani batériu modelu.

## Postup ukážky

1. Zapnite notebook, router a model. Na PC aj mobile otvorte LAN adresu aplikácie.
2. Osvetlite a zakryte panel; sledujte meraný výkon a prepočítanú virtuálnu FV.
3. Prepínačmi rozsvieťte dve LED v dome a sledujte zmenu virtuálnej spotreby.
4. Tlačidlom výpadku vypnite LED siete a sledujte nulový import/export.
5. Odpojte powerbanku od nabíjacieho modulu; batéria udrží ESP32 a LED v prevádzke. Pre zachovanie spojenia musí router zostať napájaný.
6. Zapnite demo režim v nastaveniach pre pripravené scenáre a zrýchlenú históriu.

Internet nie je potrebný. Router musí umožniť komunikáciu medzi klientmi Wi-Fi. Pred prezentáciou skontrolujte polaritu JST konektora, stabilitu napájania, kalibračný výkon panela a výdrž notebooku aj routera.
