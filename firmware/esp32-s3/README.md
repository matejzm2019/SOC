# ESP32-S3 N16R8 – firmvér 0.5.0-house

Aktuálny firmvér podporuje dva INA219, meranie hlavného zdroja, dve svetelné vetvy a voliteľný vodný okruh s DRV8833. MAX17048/BH1750 zo staršieho návrhu sa nepoužívajú. Backend na PC s Ollamou je oddelený od ESP. Schéma a pinová tabuľka: [docs/ZAPOJENIE.md](../../docs/ZAPOJENIE.md).

## Nahratie

1. Arduino IDE, ESP32 core od Espressif, doska **ESP32S3 Dev Module**, Flash **16 MB**, PSRAM **OPI** pre N16R8. USB port/CDC nastav podľa skutočnej dosky a použitého konektora.
2. Library Manager: **Adafruit INA219** a **ArduinoJson 7** vrátane závislostí. WiFi, Wire a HTTPClient sú súčasťou ESP32 core.
3. Celý obsah tohto priečinka presuň podľa požiadavky Arduino IDE do priečinka `energia_esp32_s3`, aby názov zodpovedal sketchu. Oba .h súbory musia zostať vedľa .ino.
4. `secrets.example.h` skopíruj na `secrets.h`. Doplň Wi-Fi, LAN adresu servera a kľúč z `data/device_key.txt`. Heslá ani kľúč necommituj.
5. Pri programovaní odpoj externých 5 V a použi programovacie USB. Pri prevádzke pripoj iba MT3608 nastavený na 5 V. Neprepájaj napájanie USB počítača s meničom bez overenia izolácie napájacích vetiev.
6. `WATER_ENABLED=0` ponechaj do pripojenia všetkých ochrán a odskúšania plavákov. Potom nastav 1, nahraj firmvér a povoľ vodný okruh aj v aplikácii. Čerpadlo sa samo nespustí.

## Riadenie

Úloha `local-control` každých 20 ms číta prepínače, sníma hlavný zdroj a vykonáva guard motora. Sieťový loop posiela JSON každú sekundu. Wi-Fi sa pripája bez blokujúceho čakania, HTTP má ohraničené timeouty. Staršia serverová odpoveď po 1 s sa nepoužije na obnovu motora. Každý povel má lease maximálne 1,5 s a súvislý limit 2–60 s; obnovovanie nemôže predĺžiť pôvodný limit.

Relé zálohy svetiel nemá GPIO ovládanie: je napájané priamo hlavným zdrojom a IN má na GND. ESP je stále zálohované cez menič. GPIO4 už nie je tlačidlo výpadku, ale ADC vstup z deliča 22 kΩ/10 kΩ. GPIO5/6 čítajú fyzické prepínače a GPIO7/10 ovládajú tranzistory LED. GPIO12 ovláda DRV8833; 13–16 sú plaváky.

I²C GPIO8/9: panel 0x40, batéria 0x41. Oba snímače majú logické napájanie 3,3 V. Bez panelového merača sa neodosielajú vymyslené nuly; bez batériového merača sa jeho hodnoty vynechajú.

## Dáta

Telemetria obsahuje `telemetry_origin=hardware`, výkon panela, `grid_available`, `load_stage`, voliteľné napätie/prúd/SOC batérie a voliteľnú vodu. Prúd batérie je kladný pri nabíjaní. `battery_soc_method=voltage_estimate` jasne označuje hrubý odhad percent z napätia. Kapacita článku sa ním nemeria.

Backend stále prijíma staršie telemetrie MAX17048, ale nový sketch ich nevytvára. Pole `battery_charge_rate_pct_h` zostáva len pre kompatibilitu a nemá sa zamieňať s meraným prúdom.

Simulačné preprocesorové vetvy `SIMULATED_SENSORS=1` a `WIFI_ENABLED=0` sú na logické skúšanie v oddelenom simulačnom balíku. V produkčnej doske ich nepoužívaj: generujú testovacie údaje a v offline variante GPIO2/3 zastupujú serverový povel/reset. Skutočná zostava musí mať `SIMULATED_SENSORS=0`, `WIFI_ENABLED=1`.
