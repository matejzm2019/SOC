# Správa pre učiteľa – aktuálny návrh SOČ

Pripravujem funkčný drevený model inteligentného domu s celými stenami a odnímateľnou strechou, bez nábytku. Podstava domu je 60 × 45 cm; vodný modul a solárny stojan sú samostatné, aby sa model dal prenášať a elektronika zostala suchá.

ESP32-S3 N16R8 cez Wi-Fi posiela merania do lokálneho servera FastAPI na notebooku. Server ich ukladá do SQLite a poskytuje web na PC aj mobil. AI Ollama beží na notebooku a vysvetľuje dostupné údaje; bezpečnostné riadenie vody vykonáva miestny firmvér, nie AI.

Chránenú LiPo 3,7 V / 2500 mAh nabíja CN3791 zo solárneho panela. MT3608 vytvára záložných 5 V a relé pri vypnutí hlavného zdroja automaticky prepína svetlá. Dva INA219 merajú panel a batériu; percentá sú orientačný odhad z napätia. V modelovej aplikácii sa fyzické malé merania odlišujú od škálovaných tokov domácnosti v kW.

Vodný okruh má dve nádržky, malé čerpadlo cez DRV8833, mechanický ukážkový filter, štyri plaváky a záchytnú vaničku. Čerpadlo má nezávislé zastavenie pri strate povelu, chybe snímačov, prázdnom zdroji, hornej hladine, vode vo vaničke, výpadku hlavného zdroja a prekročení maximálneho času.

Prosím o kontrolu konkrétneho článku a jeho dovoleného nabíjacieho prúdu, nastavenia CN3791 a polarity, výstupu MT3608 pri Wi-Fi špičkách, rozbehového prúdu motora a vodných tesnení. Plaváky a montážne otvory treba prispôsobiť dodaným dielom. Na úplné prednabitie CN3791 sa odpája systémová záťaž, pretože modul nemá oddelený LOAD výstup.

Model pracuje iba s nízkonapäťovými DC vetvami. Server a router zostávajú počas ukážky vypnutia laboratórneho zdroja zapnuté. Automatické testy a simulácia sú podklad na overenie softvéru; fyzické napájanie, nabíjanie a tesnosť treba odskúšať na stole.

Výrobné podklady sú v model-domu/, jednotný kusovník v docs/KOMPONENTY.md, zapojenie v docs/ZAPOJENIE.md a úplný opis v docs/AKO-TO-FUNGUJE.md.
