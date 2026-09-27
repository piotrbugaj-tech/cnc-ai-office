# Regał nieregularny: rekonstrukcja z odzyskanych rozkrojów

## Status
Komplet odzyskanych plików przeanalizowany (10 plików w `../_odzyskane/`). Układ frontowy odtworzony jako **rev A, propozycja do potwierdzenia przez klienta**: `uklad.json` + `widok-przod.svg/png` (generator: `render_widok.py`).

| Plik | Zawartość |
|---|---|
| `rozkroj_18mm_ark1..5.dxf` | korpus (wieńce, półki, 41 przegród), 11 frontów szuflad, 10 drzwiczek |
| `rozkroj_12mm_ark1..2.dxf` | skrzynki 11 szuflad (44 elementy) |
| `rozkroj_6mm_ark1.dxf` | 11 den szuflad |
| `rozkroj_4mm_ark1.dxf` | 10 pleców szafek |
| `rozkroj_stronaB.dxf` | obróbka drugiej strony przegród 25, 38, 39, 40 |
| `rozkroj_lista.csv` | lista rozkroju (orientacja słojów frontów: pionowo) |

Pełna lista 141 elementów z obróbkami: `../_odzyskane/inwentarz-z-rozkrojow.csv`.

## Wykonane: co wynika z plików

### Siatka i gabaryt
- Model był budowany na **siatce 100 mm**: osie wszystkich płyt 18 mm leżą na liniach siatki. Wieńce są licowane z gabarytem, stąd skrajne rzędy mają 273 mm zamiast 282.
- Poziomy (osie): wieniec dolny 0–18, półki na 300 / 400 / 600 / 700 / 900 / 1200 / 1400 / 1700, wieniec górny 1982–2000. Wysokość **2000 mm**, głębokość **400 mm**.
- Wysokości rzędów w świetle (od dołu): 273 / 82 / 182 / 82 / 182 / 282 / 182 / 282 / 273.
- Półki 2, 3, 4 i 6 są dzielone. Przerwy w nich tworzą 4 wysokie wnęki otwarte: 282×282, 182×282, 382×282, 282×482.
- Długości kawałków półek (791, 1191, 1391, 291, 391) = n·100 − 9. Kawałek biegnie od krawędzi 0 do lica przegrody na linii siatki.

### Błąd gabarytu w starym modelu
Skrajne przegrody stały na liniach siatki 0 i 1900 (wystawały 9 mm poza półki), a półki miały 1900 mm. Jest to sprawdzone solverem: przy bokach licowanych z półkami wymiary frontów się nie zgadzają.
**Poprawka rev A:** poziomy wydłużone do **1918 mm** (lico w lico z bokami). Fronty i przegrody bez zmian; kawałki półek dzielonych mają okrągłe długości 800 / 1200 / 1400 / 300 / 400.

### Fronty
- 18 mm, **wpuszczane (licowane z korpusem)**, szczelina 2 mm dookoła (front = światło − 4 mm), słoje pionowo.
- Drzwiczki: puszka Ø35, 22,5 mm od krawędzi (K = 5 mm). Pozycje puszek są symetryczne, więc drzwiczki są uniwersalne L/P (obrót o 180°).
- Brak otworów pod gałki i pod mocowanie frontów do skrzynek.

### Odtworzenie układu (solver ograniczeń)
Każde drzwiczki mają zawias na dokładnie jednej przegrodzie, a każda szuflada prowadnice na dwóch. Wysokości przegród wyznaczają rzędy. Z tych ograniczeń przeszukano wszystkie ustawienia na siatce 100 mm:
- **Pewne:** poziomy, przerwy w półkach (z dokładnością do odbicia lustrzanego całości), sąsiedztwo drzwiczek/szuflad z przegrodami, wszystkie wymiary.
- **Wybrane heurystycznie:** odbicie L/P (numeracja przegród 33→36 i 37→41 rośnie od lewej), kolejność elementów w rzędach, strony zawiasów. Pliki nie zawierają pozycji przegród wzdłuż półek, a szerokości wnęk otwartych nie są nigdzie zapisane.

## Blockery / błędy w starych plikach (do naprawy w rev A)
1. Boki szuflad L i P identyczne zamiast lustrzanych (rowek pod dno po złej stronie w jednym boku).
2. Otwory prowadnic na dwóch licach przegród przesunięte względem siebie o 16 mm (37/165/293 vs 53/181/309 od frontu): szuflada byłaby skośna. Poprawna jest seria 53 = 18 (front) + 35.
3. Prowadniki zawiasów na 37 mm od krawędzi, czyli wartość dla frontów nakładanych. Przy frontach wpuszczanych prowadnik trzeba cofnąć o grubość frontu (dokładnie wg karty wybranego zawiasu).
4. Drzwiczki 78 mm (D5, D6) na jednym zawiasie. W rev A: 2 mini zawiasy Ø26.
5. Brak nawiertów montażowych korpusu, brak otworów pod gałki i mocowanie frontów.
6. Plecy bez sposobu mocowania. Decyzja: klipsy bez wkręcania i bez rowków.
7. Otwory Ø5 w warstwie `WKRET_45`, brak głębokości obróbek, obróbka strony B tylko jako notatka.

## Decyzje klienta (27.09.2026)
- Arkusz **2500 × 1250 mm**.
- Rowki pod dna szuflad do poprawy.
- Niskie drzwiczki: szukać mini zawiasów.
- Plecy: bez wkręcania i rowków, mocowanie klipsami (druk 3D).
- **Bez graweru** numerów elementów: etykiety naklejane.
- Fronty szuflad i drzwiczek **zlicowane z korpusem**.

## Rekomendacje (następne kroki)
1. Potwierdzenie układu rev A (`widok-przod.png`) i pytań otwartych: zamiana rzędu szuflad z góry na dół, szerokość 1918, wybór prowadnic.
2. Model parametryczny, nawierty korpusu (wkręty), okucia, nowe DXF (warstwy z głębokością, strona A/B, warstwa etykiet), nesting 2500×1250.
3. BOM + lista okuć, instrukcja montażu, arkusz etykiet, model klipsów pleców (druk 3D).
