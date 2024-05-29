# KIV/IR – Information Retrieval

## Komplexní IR systém

Tento repozitář obsahuje řešení semestrální práce z předmětu **KIV/IR – Information Retrieval** na **Katedře informatiky a výpočetní techniky**, **Fakulty aplikovaných věd**, **Západočeské univerzity v Plzni**.

Tato semestrální práce implementuje vlastní systém pro automatickou indexaci a vyhledávání dokumentů. Systém podporuje základní i pokročilé funkce informačního vyhledávání s možností využití různých vyhledávacích modelů.

---

## Obsah

* [Popis projektu](#popis-projektu)
* [Požadavky](#požadavky)
* [Použití](#použití)
* [Struktura projektu](#struktura-projektu)
* [Odkazy](#odkazy)

---

## Popis projektu

Tento projekt implementuje komplexní systém pro informační vyhledávání (IR) zahrnující automatickou indexaci a vyhledávání dokumentů. Systém umožňuje práci s textovými daty v českém a slovenském jazyce a nabízí různé modely vyhledávání, včetně booleovského a vektorového modelu. Součástí je také web crawler pro získávání dat z internetu.

* **Tokenizace a předzpracování dat**
  Podpora českého i slovenského jazyka.
  Odstranění HTML tagů, interpunkce, stopslov.
  Možnost stemmatizace a lemmatizace (použití knihovny Simplemma).

* **Indexace dokumentů**
  Vytvoření in-memory invertovaného indexu.
  Podpora modifikace indexu (přidání, úprava, smazání dokumentů).
  Ukládání mezivýpočtů pro rychlejší vyhledávání.

* **Vyhledávání**
  Podpora dvou modelů:

  * Vektorový model (TF-IDF, cosine similarity)
  * Booleovský model (logické operátory AND, OR, NOT)
    Vyhledávání v různých sekcích dokumentu (nadpis, obsah, tabulka, hlavní text).
    Podpora vyhledávání frází a vyhledávání slov v okolí (proximity search).

* **Web crawler**
  Stahování a indexace webových stránek zadaných URL, včetně možnosti "seedování" a stahování všech odkazovaných stránek.

* **Uživatelské rozhraní**
  Grafické GUI založené na PyQt5.
  Možnost zadávání dotazů přes GUI nebo příkazovou řádku.
  Výsledky s náhledem (snippetem) a celkovým počtem nalezených dokumentů.

* **Evaluace**
  Podpora evaluace výsledků vyhledávání nad evaluačními daty.

---

## Požadavky

* Python 3.7+
* NumPy
* Pandas
* Lxml
* Simplemma
* PyQt5

Instalace všech závislostí:

```bash
pip install -r requirements.txt
```

---


## Použití

1. **Nastavení projektu:**

    * Před prvním spuštěním upravte konfigurační soubor `config.py` podle požadovaných parametrů indexace a vyhledávání.
    * Pro vytvoření nebo aktualizaci indexů spusťte příslušné skripty dle dokumentace.

2. **Spuštění aplikace:**

    * Hlavní grafické uživatelské rozhraní spustíte souborem `searcher_gui.py`.
    * Alternativně lze využít příkazovou řádku nebo demonstrační skript `demo.py` pro ukázku základních funkcí systému.

3. **Indexace dat:**

    * Pro indexaci webových stránek spusťte crawler se zadanou seedovací URL.
    * Pro práci s existujícím datasetem načtěte data a vytvořte invertovaný index.

4. **Vyhledávání:**

    * Zvolte vyhledávací model (vektorový nebo booleovský).
    * Zadejte dotaz s podporou logických operátorů, frází a proximity search.
    * Výsledky se zobrazí v GUI nebo CLI včetně náhledu dokumentů.

5. **Správa indexu:**

    * Přidávejte, upravujte nebo mažte dokumenty bez nutnosti kompletní rekonstrukce indexu.

6. **Evaluace:**

    * Vyhodnocujte kvalitu vyhledávání pomocí dostupných evaluačních dat.

Podrobné příklady použití najdete v souboru `demo.py`.

---

## Struktura projektu
```
/
├── data/                  # Složka s datovými soubory (JSON dokumenty)
├── img/                   # Obrázky pro GUI
├── models/                # Implementace vyhledávacích modelů
├── utils/                 # Pomocné skripty a utility
├── config.py              # Konfigurační soubor systému
├── demo.ipynb             # Ukázkový Jupyter notebook s příklady použití
├── evaluation.py          # Skript pro evaluaci výsledků vyhledávání
├── Index.py               # Implementace invertovaného indexu
├── IR_dokumentace.pdf     # Dokumentace k projektu
├── preprocessing_pipelines.py # Předzpracování a tokenizace dat
├── searcher_gui.py        # Hlavní GUI aplikace
├── searcher.py            # Hlavní logika vyhledávání
├── web_crawler.py         # Web crawler pro stahování dat
├── requirements.txt       # Seznam požadovaných Python knihoven
└── README.md              # Tento soubor s popisem projektu
```