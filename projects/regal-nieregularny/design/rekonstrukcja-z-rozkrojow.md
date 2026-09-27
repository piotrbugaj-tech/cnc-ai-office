# Regał nieregularny: rekonstrukcja z odzyskanych rozkrojów

## Status
Etap 1/n. Przeanalizowano pierwszą paczkę odzyskanych plików (5 × DXF). Czekam na resztę plików (pozostałe arkusze 18 mm, fronty).

Źródła, zachowane bez zmian w `../_odzyskane/`:

| Plik | Materiał | Elementy | Uzysk arkusza |
|---|---|---|---|
| `rozkroj_18mm_ark1.dxf` | sklejka 18 mm | 7 (wieńce, półki, przegrody) | 91.4 % |
| `rozkroj_12mm_ark1.dxf` | sklejka 12 mm | 36 (skrzynki szuflad) | 83.1 % |
| `rozkroj_12mm_ark2.dxf` | sklejka 12 mm | 8 (skrzynki szuflad) | 15.4 % |
| `rozkroj_6mm_ark1.dxf` | sklejka 6 mm | 11 (dna szuflad) | 44.8 % |
| `rozkroj_4mm_ark1.dxf` | sklejka 4 mm | 10 (plecy szafek) | 21.8 % |

Pełna lista elementów z wymiarami: `../_odzyskane/inwentarz-z-rozkrojow.csv` (72 elementy).

## Wykonane: co wynika z plików

### Konwencje odzyskanych DXF
- Arkusz **2500 × 1250 mm**, margines 12 mm, odstęp między elementami 8 mm.
- Warstwy: `ARKUSZ` (obrys arkusza), `OPIS` (etykiety), `OBRYS` (cięcie przelotowe), `ROWEK_6` (rowek 6.2 mm pod dno), `PILOT_3` (Ø3), `WKRET_45` (Ø4.5, ale na przegrodzie 13 są tu też Ø5).
- Etykieta `A x B` podaje wymiar w orientacji elementu, `[OBR]` oznacza element obrócony o 90° w rozkroju.
- Brak głębokości wierceń i rowków, brak warstwy `GRAIN`, brak grawerowanych oznaczeń elementów.

### Korpus (sklejka 18 mm)
- Szerokość **1900 mm**, głębokość **400 mm**.
- Wieniec górny, wieniec dolny i półka 1 mają po 1900 mm, czyli poziomy biegną na całą szerokość, a piony (przegrody, także skrajne) stoją **między** poziomami. To konstrukcja w stylu Tylko.
- `Polka 4.2` = 1191 mm, więc półka 4 jest dzielona (4.1 + 4.2); prawdopodobnie tu jest „nieregularność” (uskok poziomu).
- Przegrody 12, 13 i 16 mają 400 × 82, co oznacza rząd o świetle 82 mm.
- Przegroda 13: 2 × Ø5 w rozstawie 32 mm, 37 mm od krawędzi, w połowie wysokości. To nawierty pod prowadnik zawiasu puszkowego (system 32), a więc drzwiczki nakładane.
- Wysokość całkowita i położenie przegród: **nieznane** (w półkach i wieńcach nie ma nawiertów, które by je zdradzały).

### Wymiary światła modułów (wyprowadzone)
- Wysokości światła rzędów: **82 / 182 / 273 / 282 mm**
- Szerokości światła: **182 / 282 / 382 / 582 mm**

### Szuflady (11 szt.): skrzynka 12 mm, dno 6 mm
Zasady konstrukcji odczytane z geometrii:
- Boki 350 mm nakładają na czoła przodu i tyłu (wkręty Ø4.5 w bokach, 6 mm od końców, 3 lub 2 na złącze).
- Dno 6 mm w rowku 6.2 mm, 10 mm od dolnej krawędzi (w bokach i przodzie). Tył jest niższy o 16.2 mm, więc dno wsuwa się od tyłu pod tylną ściankę.
- Szerokość skrzynki = światło − 26 mm, co oznacza **prowadnice boczne kulkowe 12.7 mm**.
- Wysokość skrzynki = światło − 15 mm.
- Ø3 w bokach (pod prowadnicę): 25 mm od dołu, 35 / 175 / 300 mm od przodu, więc prowadnice 350 mm.

| Szuflada | Skrzynka szer. × wys. × gł. | Przód/tył (dł.) | Dno | Światło (szer. × wys.) |
|---|---|---|---|---|
| 1 | 356 × 167 × 350 | 332 | 343 × 344 | 382 × 182 |
| 2 | 556 × 167 × 350 | 532 | 543 × 344 | 582 × 182 |
| 3 | 256 × 167 × 350 | 232 | 243 × 344 | 282 × 182 |
| 4 | 356 × 67 × 350 | 332 | 343 × 344 | 382 × 82 |
| 5 | 356 × 67 × 350 | 332 | 343 × 344 | 382 × 82 |
| 6 | 356 × 267 × 350 | 332 | 343 × 344 | 382 × 282 |
| 7 | 556 × 267 × 350 | 532 | 543 × 344 | 582 × 282 |
| 8 | 256 × 258 × 350 | 232 | 243 × 344 | 282 × 273 |
| 9 | 356 × 258 × 350 | 332 | 343 × 344 | 382 × 273 |
| 10 | 556 × 258 × 350 | 532 | 543 × 344 | 582 × 273 |
| 11 | 256 × 258 × 350 | 232 | 243 × 344 | 282 × 273 |

### Szafki (10 szt.): plecy 4 mm
Plecy mają wymiar światła − 1 mm (brak rowka/wręgu):

| Szafka | Plecy (szer. × wys.) | Światło |
|---|---|---|
| 1, 2 | 381 × 272 | 382 × 273 |
| 3 | 281 × 181 | 282 × 182 |
| 4, 8 | 381 × 181 | 382 × 182 |
| 5 | 281 × 81 | 282 × 82 |
| 6 | 181 × 81 | 182 × 82 |
| 7 | 181 × 181 | 182 × 182 |
| 9, 10 | 381 × 281 | 382 × 282 |

## Blockery / wykryte problemy
1. **Boki L i P szuflad są identyczne, a nie lustrzane.** Rowek pod dno jest jednostronny, więc jeden z boków wyjdzie rowkiem na zewnątrz. Odwrócenie elementu zamienia wzory otworów przód/tył: tylny wkręt trafia wtedy 3.8 mm od krawędzi tylnej ścianki i ją rozsadzi. Naprawa: P = lustro L.
2. **Brak nawiertów montażowych w elementach 18 mm** (wieńce, półki, przegrody). Do zaprojektowania od zera.
3. **Brak frontów** (szuflad i drzwiczek) w otrzymanych plikach.
4. **Szafki 5 i 6 (światło 82 mm):** na drzwiczkach ~100 mm mieści się tylko 1 zawias (zgodne z przegrodą 13). Wymaga decyzji: 1 zawias / klapka / zamiana na szufladę / wnęka otwarta.
5. **Plecy = światło − 1 mm, bez rowka.** Sposób mocowania pleców nieokreślony.
6. **Niespójne warstwy/średnice** (Ø5 w warstwie `WKRET_45`), brak głębokości (Ø3 pod prowadnice muszą być nieprzelotowe).
7. **Format arkusza 2500 × 1250** zamiast firmowego 2440 × 1220. Przyjmuję 2500 × 1250 zgodnie z plikami (do potwierdzenia z wykonawcą CNC).
8. **Niski uzysk** arkuszy 4 / 6 / 12-2. Do ponownego nestingu po skompletowaniu listy.

## Rekomendacje (następne kroki)
- Zebrać pozostałe pliki i, jeśli istnieje, widok z przodu / szkic / zrzut ekranu z modelu (pozycje przegród).
- Odtworzyć model układu (siatka modułów), potem nawierty korpusu, fronty, okucia.
- Nowe DXF: warstwy z głębokością obróbki, lustrzane boki, grawer numeru elementu, warstwa `GRAIN`.
