# Instrukcja uruchomienia `main.py` (po polsku)

Ten skrypt jest przeznaczony do uruchamiania w kontekście headless Blendera (bez GUI). Przyjmuje argumenty przez `argparse` — Blender przekazuje dodatkowe argumenty po separatorze `--`.

**Wywołanie w trybie headless (przykład)**

```bash
blender -b scena.blend --python /ścieżka/do/main.py -- [ARGUMENTY]
```

Zamiast `scena.blend` możesz podać własny plik .blend lub uruchomić Blendera bez pliku, jeśli skrypt tworzy scenę samodzielnie.

**Dostępne argumenty**

- `--render-frames START END` : zakres klatek do renderowania; dwa całkowite liczby (START, END). START musi być <= END.
	- Przykład: `--render-frames 1 100`

- `--fpd N` : frames per datapoint — ile klatek przypada na jeden datapunkt (int). Domyślnie `1`.
	- Przykład: `--fpd 2`

- `--render-mode MODE [MODE ...]` : tryby renderowania; można podać jedną lub więcej z wartości `rgb`, `mask`, `depth`. Skrypt wykona wszystkie podane tryby.
	- Przykład pojedynczy tryb: `--render-mode rgb`
	- Przykład wiele trybów: `--render-mode rgb mask depth`

- `--data-path PATH` : ścieżka do folderu z danymi (wejściowe obrazy).
	- Przykład: `--data-path ./data/images`

- `--save-path PATH` : ścieżka, gdzie zapisywane będą wyniki (np. obrazy, metadane).
	- Przykład: `--save-path ./out`

- `--data-index N` : indeks (0-based) pliku w katalogu `--data-path`, od którego zaczyna się wczytywanie danych.
	- Przykład: `--data-index 5` — skrypt zaczyna od szóstego pliku w katalogu.

- `--margin F` : margines między obrazem a ramą obrazu (float). Domyślnie `1.01`.
	- Przykład: `--margin 1.02`

- `--light-shape SHAPE` : kształt źródeł światła; jedno z `square`, `disk`, `random` (domyślnie `random`).
	- Przykład: `--light-shape square`

- `--light-spread MIN MAX` : zakres (w stopniach) losowania kąta rozprzestrzeniania światła od MIN do MAX. Domyślnie `60 180`.
	- Przykład: `--light-spread 45 120`

- `--render-resolution WIDTH HEIGHT` : rozdzielczość, w której zapisywane będą rendery (dwa inty: szerokość i wysokość).
	- Przykład: `--render-resolution 1024 768`

UWAGA: Gdy uruchamiasz skrypt przez `blender --python`, wszystkie argumenty skryptu muszą być podane po dwukropku `--`, np. `-- --render-frames 1 10`.

**Przykłady użycia**

- Renderuj klatki 1–100, tryby `rgb` i `mask`, zapisuj w `./out`, wczytuj dane z `./data` zaczynając od indeksu 5, 2 klatki na datapunkt:

```bash
blender -b scena.blend --python /ścieżka/do/main.py -- \
	--render-frames 1 100 --fpd 2 --render-mode rgb mask --data-path ./data --save-path ./out --data-index 5 \
	--margin 1.02 --light-shape square --light-spread 45 120 --render-resolution 1024 768
```

- Prosty przykład tylko z domyślnym `fpd` i jednym trybem:

```bash
blender -b scena.blend --python /ścieżka/do/main.py -- \
	--render-frames 10 10 --render-mode rgb --data-path /mnt/images --save-path /mnt/save
```

**Pomoc / debug**

Żeby zobaczyć opis wszystkich argumentów:

```bash
blender -b --python /ścieżka/do/main.py -- --help
```

Plik `main.py` eksportuje funkcję `parse_cli_args()` która normalizuje wartości (np. tuple dla `render_frames`, tuple dla `render_mode`, absolutne ścieżki dla `data_path` i `save_path`) — użyj jej w skrypcie, aby pobrać już sparsowane ustawienia.

