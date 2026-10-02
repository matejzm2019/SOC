# Lokálny asistent cez Ollamu

Predvolený model je **Qwen3 0.6B**, tag `qwen3:0.6b`. Jeho Q4_K_M balík má približne 523 MB. Veľkosť súboru nie je celková spotreba RAM; runtime a kontext potrebujú ďalšiu pamäť. Rýchlosť treba overiť na konkrétnom notebooku. Pri dostupnej pamäti môžete vybrať `qwen3:1.7b` (balík približne 1,4 GB). Zdroj: [katalóg Ollama 0.6B](https://ollama.com/library/qwen3:0.6b), [1.7B](https://ollama.com/library/qwen3:1.7b).

1. Nainštalujte [Ollamu pre Windows](https://ollama.com/download/windows) na počítač, kde beží backend Energie.
2. V novom PowerShelli spustite:

   ```powershell
   ollama pull qwen3:0.6b
   ```

3. Ponechajte Ollamu spustenú. Inštalátor Windows ju spravidla spustí na pozadí. Pri samostatnej CLI inštalácii použite `ollama serve`.
4. Spustite `start.cmd`. V aplikácii otvorte **Nastavenia → Lokálny asistent → Overiť pripojenie**. Predvolený model je už vybraný.
5. Na domovskej stránke použite pripravené otázky alebo napíšte vlastnú otázku. Telefón posiela otázku backendu na PC; na telefóne Ollama nemusí bežať.

Model aplikácia automaticky nesťahuje. Na stiahnutie modelu potrebujete internet; jeho následné spúšťanie je lokálne. Vybrané modely majú licenciu Apache 2.0. Aktuálne podmienky runtime sú v [dokumentácii Ollama Windows](https://docs.ollama.com/windows).

## Úsporné nastavenie

Backend volá `http://127.0.0.1:11434/api/chat`, nastavuje `think=false`, kontext 2048 tokenov a `keep_alive=60s`. Krátky prvý dotaz rozpoznáva požiadavku na nastavenia cez JSON schému (najviac 180 tokenov, limit 35 sekúnd). Pri bežnej otázke nasleduje odpoveď s relevantnými faktmi (najviac 256 tokenov). Celé spracovanie má limit približne 120 sekúnd. Spracúva jednu otázku naraz, potom nechá Ollamu model uvoľniť. Na slabšom CPU môže prvá odpoveď trvať dlhšie. Podporované sú iba lokálne modely. Dokumentácia: [Ollama Chat API](https://docs.ollama.com/api/chat), [štruktúrované odpovede](https://docs.ollama.com/capabilities/structured-outputs).

Voliteľná serverová premenná `SOC_OLLAMA_URL` môže zmeniť lokálny port; hostiteľ musí zostať localhost, 127.0.0.1 alebo ::1. Je to nastavenie správcu servera, nie URL zadávaná návštevníkom.

## Čo asistent smie robiť

Asistent dostáva aktuálne fakty o energii, počasí, cenách a modeli. Podľa témy vyberá podklady, aby sa napríklad cena za kWh nezamieňala s dennými nákladmi. Otázky môžu prirodzene nadväzovať na predošlé správy. Matematické predikcie počíta Python; LLM ich vysvetľuje.

## Nastavenia cez chat

Na karte **AI chat** napíšte napríklad:

- „Zapni internetové ceny.“
- „Nastav nákupnú cenu na 0,20 €/kWh.“
- „Nastav kapacitu malej batérie na 2000 mAh.“
- „Vypni demo režim.“
- „Vypni fotovoltaiku.“

Asistent zobrazí konkrétne hodnoty pred zmenou a po nej. **Použiť zmenu** ich uloží; **Zrušiť návrh** nič neuloží. Chat môže meniť vybrané tarify, režim, moduly, výkon FV, základnú modelovanú spotrebu a kapacity s uvedenou jednotkou. Neprepája zdroje elektriny, neovláda nabíjačku ani ESP a nemá prístup ku kľúčom alebo ľubovoľnému API. Lokalitu nastavte cez existujúci výber mesta/GPS.

Backend validuje hodnoty rovnakým modelom ako formulár nastavení. Ukladá iba potvrdený serverový návrh, nie ľubovoľné hodnoty odoslané klientom. Návrh platí desať minút, je jednorazový a pri zmene konfigurácie alebo datasetu sa odmietne ako neaktuálny. Zmena modelových parametrov vytvorí nový dataset; pôvodná história zostane uložená. Pri potvrdení cez chat zostáva konverzácia viditeľná, hodnoty starých správ však majú svoj pôvodný dataset.

Asistent odpovedá prirodzene. Číslované zoznamy, názvy ako ESP32 a overené hodnoty s jednotkami odpoveď neblokujú. Podporované ID faktov sa doplnia z podkladov. Ak číselná veličina nezodpovedá faktom ani ich zaokrúhleniu či podporovanej zmene jednotiek, označí sa iba tento úsek; zvyšok odpovede zostane viditeľný. Podklady možno rozbaliť pod správou.

Kontrola nie je úplným overením významu: model môže správne číslo priradiť nesprávnej veličine alebo slovne zle vysvetliť situáciu. Qwen3 0.6B je úsporný, ale slovenčina a interpretácia môžu byť slabé. Pre kvalitnejšie odpovede skúste ponúkaný 1.7B model podľa pamäte notebooku. Energetické výpočty a predikcie robí Python; model nemá ovládanie zariadení.

Konverzácia sa drží len v pamäti otvorenej stránky; po obnovení sa vymaže. Backend otázky neukladá. Do Ollamy sa posiela krátka história a aktuálne fakty; aplikácia ich neodosiela cloudovému LLM.

Ak model chýba alebo Ollama nebeží, energetika a počasie fungujú ďalej. Karta asistenta zobrazí konkrétny postup pripojenia.
