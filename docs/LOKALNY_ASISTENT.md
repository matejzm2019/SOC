# Všeobecný lokálny asistent – 0.12.0

Jazykový model beží cez Ollamu na tom istom PC ako aplikácia. Podporované sú Qwen3 4B Instruct (qwen3:4b-instruct-2507-q4_K_M), qwen3:4b a menšie 1.7B/0.6B. V Nastavenia → Asistent vyber nainštalovaný názov a over pripojenie. Ak pôvodný 0.6B nie je nainštalovaný, aplikácia rozpozná dostupný 4B; uložený výber nemení potichu. Pri existujúcom uloženom menšom modeli sa zachová jeho výber.

## Čo dokáže

- Bežné otázky a vysvetlenia aj mimo energetiky. Všeobecné čísla (napr. bod varu) sa nevymazávajú len preto, že nie sú v meraniach domu. Pod odpoveďou je uvedené, ak nebola overená online.
- Predpoveď počasia, teploty ráno/na obed/večer, iné mestá a konkrétna miestna hodina. Zajtrajšok znamená nasledujúci kalendárny deň v časovej zóne danej lokality. Zdrojom je Open-Meteo, nie odhad jazykového modelu ani súhrn nasledujúcich 24 hodín.
- Dohľadanie verejných zdrojov cez čítacie nástroje a odkazy pod odpoveďou. Bežné vyhľadávanie skúša DuckDuckGo; pri nedostupnosti je označená náhrada Wikipédiou. Encyklopédia nie je overenie dnešných správ alebo aktuálnych cien. Dostupnosť verejného vyhľadávača sa nedá garantovať.
- Domáce merania a modelové výpočty majú svoj pôvod a jednotky. Kontrola čísel sa používa pri odpovediach z meraní/predpovedí/zdrojov, nie ako zákaz všeobecných vedomostí.
- Pri výslovnej žiadosti pripraví povolenú zmenu nastavenia na potvrdenie. Obyčajná otázka nepotrebuje druhý klasifikačný beh modelu a sama nič nemení. Asistent nespína fyzické zariadenia.

Príklady: „Aká bude zajtra teplota?“, „A v Prahe o 14:00?“, „Bude cez víkend pršať?“, „Nájdi dokumentáciu k FreeRTOS“, „Pri akej teplote vrie voda?“, „Vysvetli rozdiel medzi výkonom a energiou.“ Bez vybratej lokality sa opýta na mesto. Lokalita zistená v chate neprepíše polohu ani históriu domu.

## Online zdroje a súkromie

Prepínač Online zdroje asistenta ich vie zakázať nezávisle od panelu Počasie. Zmena tejto voľby nezakladá novú energetickú históriu. Model a konverzácia zostávajú v lokálnej Ollame; vyhľadávací výraz alebo poloha sa posiela príslušnému online poskytovateľovi. Bez internetu ostávajú všeobecné znalosti a dostupné domáce údaje; model nesmie predstierať úspešné overenie.

Voliteľne možno nastaviť OLLAMA_API_KEY v prostredí servera. Potom sa na všeobecné vyhľadávanie prednostne použije oficiálne https://ollama.com/api/web_search. Kľúč nie je potrebný na lokálny model ani Open-Meteo a nepatrí do repozitára ani do chatu. Bez neho zostáva verejné vyhľadávanie s označenou encyklopedickou náhradou. Oficiálny cloudový vyhľadávač sa riadi aktuálnymi podmienkami účtu Ollama; nemožno sľúbiť neobmedzenú dostupnosť.

Lokálne volania Ollamy nepoužívajú proxy. Vonkajšie HTTP volania rešpektujú proxy a certifikáty nastavené na PC. Výsledky webu sú podklady, nikdy pokyny na zápis. Model má len povolené nástroje weather_forecast a search_web, limit počtu kôl/volaní a časový limit; nemá shell ani voľné načítanie interných URL.

Pri 4B je kontext 8192 tokenov a čas na dokončenie do troch minút; v bežnej krátkej otázke je rýchlejší. Obmedzená RAM alebo starší procesor môžu byť pomalé. Skutočnú kvalitu slovenčiny a ochotu používať nástroje treba overiť s nainštalovaným modelom na prezentačnom PC. HTTP a používateľské testy s testovacou odpoveďou modelu nie sú meranie kvality reálneho LLM.

Oficiálne podklady: https://docs.ollama.com/capabilities/tool-calling a https://docs.ollama.com/capabilities/web-search ; predpoveď https://open-meteo.com/en/docs .
