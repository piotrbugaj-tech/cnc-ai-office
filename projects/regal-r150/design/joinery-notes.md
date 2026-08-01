# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
**Runda 9:** dwa dolne rzędy dostają szuflady na prowadnicach Blum TANDEM
562H (realne wymiary handlowe, nie przybliżenie). **Poprawka w rundzie 9:**
pierwsza wersja (a) błędnie usuwała dzielnik między dwoma rzędami szuflad i
(b) ścieniała boki/tył szuflady do 16 mm myśląc, że to twardy limit systemu —
klient złapał oba błędy. Naprawione, patrz § 3.

## Status

**26/26 testów** w `checks.py`, zero kolizji na 66 elementach. Nie było
jeszcze walidacji przez `qa-inspector` ani `safety-officer` — runda 9
przewiduje pełny audyt `qa-inspector` (opus) przed przekazaniem do produkcji.

Konstrukcja jest zamknięta technicznie. Otwarte pozostają dwa punkty **do
Ciebie** (nie do stolarza) — patrz § 7.

---

## 1. Konstrukcja nośna — runda 7

Decyzja klienta: *„wręby przelotowe możemy całkowicie usunąć, chciałem to
zrobić na pewno na górnej płycie i dolnej"* → **piony stoją między płytami**.

| | do rundy 6 | runda 7 |
|---|---|---|
| Dolna i górna płyta | przechodziły przez piony wrębem | **jeden kawałek 1800 mm**, nic ich nie przecina |
| Piony | ciągłe 1900 mm, grzebienie z wrębami | **proste płyty 1864 mm** między płytami, pełne 18 mm |
| Półki środkowe | wręb oporowy / przelotowy | **leżą na kołkach Ø5** |
| Wręby w meblu | 6 poziomów × 3 piony | **zero** |
| Śruby M6 | 12 | 16 (pionowe, pion ↔ płyta) |

### Dlaczego to zamyka wszystkie stare problemy naraz

Wszystkie kłopoty rund 3–6 brały się z jednego źródła: piony biegły ciągle,
a poziome elementy musiały się jakoś przez nie przedostać. Stąd wręby, stąd
ścienianie pionów o 2 × 5 mm (56 % grubości — poza regułą „nigdy więcej niż
1/2"), i stąd brak dostępu do łba śruby.

Gdy piony stoją **między** płytami, wszystkie te problemy przestają istnieć:

- **Nic nie jest ścieniane.** Każdy pion to pełne 18 mm na całej wysokości.
  Sprawdzane automatycznie.
- **Łeb śruby zawsze ma na czym usiąść.** Śruba idzie pionowo przez czoło
  płyty w mimośród osadzony w czole pionu. Lico płyty jest wolne z góry
  (wieniec) i od spodu (dno, nad cokołem) — dostęp z obu stron bez wyjątku.
- **Kolejność montażu się domyka:** dolna płyta → piony → półki na kołkach →
  górna płyta → plecki → cokół.

### Złącze pion ↔ płyta

| Element | Wartość |
|---|---|
| Śruba | M6 × 45 mm, łeb walcowy imbusowy |
| Mimośród beczkowy | Ø10 × 13 mm, oś 35 mm od czoła pionu |
| Otwór w płycie | Ø6,5 przelotowy |
| Otwór pod mimośród | Ø10, **ślepy 13 mm** — w płycie 18 mm zostaje 5 mm |
| Liczba | 2 na czoło × 4 piony × 2 końce = **16 szt.** |
| Pozycje w głąb | 120 i 300 mm |

Mimośród beczkowy to metalowa tuleja z gwintem wewnętrznym — **nie wkręt**.
Można rozkręcać wielokrotnie bez zużycia gniazda, zgodnie z Twoim warunkiem.

### Półki środkowe — kołki Ø5

Cztery środkowe poziomy nie są niczym skręcone ani osadzone: **48 otworów Ø5**
w licach pionów (po 2 na stronę przęsła, na 4 wysokościach), półka po prostu
na nich leży. Konsekwencje, wszystkie korzystne:

- półki są **przestawialne i wyjmowalne**,
- przęsło z szufladą albo drzwiczkami po prostu zostaje bez półki — bez
  żadnej zmiany w konstrukcji,
- zero okuć, zero wierceń w płytę półki.

Rozpiętość 526 mm przy sklejce 18 mm i głębokości 400 mm — bezpieczna,
sprawdzane automatycznie.

---

## 2. Plecki — runda 7: wpust, bez okuć

Do rundy 6 sposób mocowania plecków **nie był ustalony** (dokumentacja mówiła
tylko „przykręcane do grzbietów", co przy zakazie wkrętów w płytę nie
przechodziło). Rozstrzygnięcie:

**Wpust 4 × 8 mm w tylnych krawędziach pionów i płyt; plecki wsuwane.**

| Rozważane | Werdykt |
|---|---|
| **Wpust, plecki wsuwane** | ✅ zero okuć, niewidoczne, ciągłe podparcie na całym obwodzie |
| Gwinty osadzone + śruby M4 | ❌ ~24 inserty, drogo i żmudnie jak na płytę 4 mm |
| Wkręty wprost w krawędź 18 mm | ❌ łamie zasadę „żadnych wkrętów w płytę" |

Uzasadnienie: plecki nie są elementem, który zdejmuje się osobno — a odkąd
piony tylko stoją między płytami, to **plecki przenoszą skręcanie**. Ciągły
wpust na całym obwodzie robi to lepiej niż punktowe mocowanie. Frezowanie
rowka 4 mm w krawędzi to jedno przejście na tym samym ustawieniu CNC.

Cena: plecków nie da się zdjąć bez rozłożenia mebla, a montaż ma narzuconą
kolejność (plecki wsuwa się przed założeniem górnej płyty). Przy meblu
rozbieralnym to akceptowalne.

Plecki: sklejka 4 mm, 4 płyty (nos + 3 przęsła), każda ~553 × 1900 mm —
mieści się na arkuszu 2440 × 1220.

---

## 3. Szuflady i drzwiczki — runda 9: realne okucie Blum

Sterowane parametrami w `shelf_model.PARAMS`:

```python
"DRAWER_CELLS": ((0,0),(0,1),(0,2),(1,0),(1,1),(1,2)),  # dwa dolne rzedy
"DOOR_CELLS":   {(2, 0): "L", (2, 2): "R"},              # przesunieta wyzej
```

Klient: *„jednak chciałbym aby dwa dolne rzędy miały szuflady"* — poprzednio
(runda 7) szuflady były tylko w dolnym rzędzie (3 szt.), drzwiczki na
poziomie 1. Poziom 1 jest teraz w całości szufladami, więc drzwiczki
przeniosły się o poziom wyżej (2).

### Prowadnice — Blum TANDEM 562H (wariant ekonomiczny)

Klient: *„znajdź i pobierz wymiarowanie szyn do szuflady firmy Blum, wybierz
jakiś tańszy model"*. **TANDEM 562H** to podstawowa pełnowymiarowa prowadnica
kulkowa Blum — bez mechanizmu BLUMOTION (samodociąg), pełny wysuw. Droższy
wariant tej samej rodziny (**569H**) dodaje tylko BLUMOTION — mechanicznie
identyczny montaż.

| Parametr | Wartość | Źródło |
|---|---|---|
| Model | Blum TANDEM 562H, bez BLUMOTION | wwhardware.com / cabinetparts.com specyfikacje 562H |
| Długość nominalna (NL) | **350 mm** | dopasowana do `DRAWER_DEPTH`; 350 mm to standardowa metryczna długość w ofercie |
| Zakres grubości boku szuflady | **1/2"–3/4" (12,7–19,0 mm)** | [blum.com/us/en/products/runnersystems/tandem](https://www.blum.com/us/en/products/runnersystems/tandem/programme/) — „specially designed for wood drawers with a drawer side thickness of 1/2" to 3/4"" |
| Luz systemowy | **13 mm na stronę** | `RUNNER_CLEAR` — już to miałem poprawnie zgadnięte w rundzie 7 |
| Nośność statyczna | **~45 kg/parę** | wg konkretnego wariantu długości 533 mm w specyfikacji handlowej |
| Mocowanie | wkręty w lico pionu (strona korpusu) + w bok szuflady (strona ruchoma) | `runner_positions()` |

**Poprawka rundy 9 — błąd znaleziony przez klienta:** pierwsza wersja
przeczytała „system 16 mm" (nazwa wzoru na luz montażowy u dystrybutorów,
`wwhardware.com`/`cabinetparts.com`) jako twardy górny limit grubości boku i
ścieniła boki/tył korpusu szuflady z 18 na 16 mm — osobny parametr, osobny
arkusz sklejki. Klient słusznie zauważył, że **sklejka 16 mm nie jest
standardowym arkuszem u dostawcy** (Paged Sklejka: 4, 6, 9, 12, 15, 18, 21,
24, 27, 30 mm — nie 16). Dokładniejsze źródło — oficjalna strona Blum —
pokazuje, że TANDEM działa z bokami **1/2"–3/4" (12,7–19,0 mm)**: 16 mm to
tylko punkt odniesienia we wzorze na luz, nie granica systemu. **18 mm
mieści się w tym zakresie**, więc boki i tył korpusu szuflady wracają do
T = 18 mm — ten sam materiał co reszta mebla, bez dodatkowego zamówienia.
Sprawdzane automatycznie („boki/tył szuflad w zakresie Blum TANDEM
12,7–19,0 mm").

Model **nie generuje geometrii samej prowadnicy** (kupowane okucie
metalowe, nie płyta) — tylko punkty pod wiercenie wkrętów montażowych
(`runner_positions()`), tym samym schematem co `bolt_positions()` i
`hinge_positions()`. 72 wkręty łącznie (6 na parę × 6 par), osobno liczone
od 24 śrub M6 konstrukcji nośnej.

Poziom 0 = komora tuż nad dolną płytą. Przęsła 0–2 od lewej. Włączenie
komory automatycznie pomija w niej półkę (bez zmian względem rundy 7).

### Drugi błąd rundy 9 — zniknięty dzielnik między rzędami szuflad

Pętla generująca półki na kołkach (`_build_corpus`, `shelf_model.py`)
pomijała półkę na poziomie `li`, gdy komora `(li, b)` była szufladą —
myśląc o tej płycie wyłącznie jako o „dnie komory z szufladą" (niepotrzebnym,
bo szuflada ma własne dno na prowadnicach). Błąd: ta sama płyta jest
**jednocześnie sufitem komory poniżej** — a z dwoma rzędami szuflad (poziom
0 i 1) sufit komory 0 = dno komory 1, więc pomijanie usuwało **jedyny
fizyczny dzielnik między dwoma rzędami szuflad**. Klient to zauważył
(„zniknęły nam półki pomiędzy szufladami").

Poprawka: półka na kołkach buduje się teraz **zawsze** na każdym z 4
środkowych poziomów × 3 przęseł, niezależnie od zawartości obu sąsiadujących
komór — 12 półek zamiast 9. Nie koliduje z geometrią szuflady (sprawdzone:
prześwit komory `z1` już wcześniej kończył się dokładnie na spodzie tej
płyty, niezależnie od tego czy `Part` istniał) — czysto addytywna poprawka,
potwierdzona przez `checks.py` (0 kolizji na 66 elementach).

### Szuflada — 5 elementów, jeden materiał

| Element | Wymiar | Materiał |
|---|---|---|
| Front (nakładany w świetle, szczelina 3 mm) | 520 × 352 mm | sklejka 18 |
| Boki (2 szt.) | 350 × 220 mm | sklejka 18 |
| Tył | 464 × 220 mm | sklejka 18 |
| Dno | 460 × 348 mm | sklejka 4 |

Prowadnice kulkowe boczne NL 350, luz **13 mm na stronę** (Blum, potwierdzone
wyżej) — stąd korpus szuflady jest o 26 mm węższy od światła przęsła
(526 → 500 mm).

### Drzwiczki — strona zawiasów nie zmienia listy cięć

Bez zmian względem rundy 7: **płyta drzwi jest identyczna w obu wariantach.**
Strona zawiasów zmienia wyłącznie pozycję puszek Ø35: oś 22,5 mm od krawędzi
zawiasowej, 100 mm od góry i od dołu. Sprawdzane automatycznie.

### Materiał — przeliczone (runda 9, po poprawkach)

„Takie same elementy × ilość", z pełnego wydruku `checks.py`:

| Grupa | Szt. | Materiał |
|---|---|---|
| `drawer-front` | 6 | sklejka 18 |
| `drawer-side` | 12 | sklejka 18 |
| `drawer-back` | 6 | sklejka 18 |
| `drawer-bottom` | 6 | sklejka 4 |
| `door` | 2 | sklejka 18 |
| `shelf-bay` | 12 (było 9) | sklejka 18 |

Masa netto całego mebla: **145,5 kg** (było 127,6 kg z 3 szufladami przed
rundą 9; pierwsza wersja rundy 9 pokazywała błędnie 135,5 kg — brakowało jej
3 dzielników i miała cieńsze, nierealne boki szuflad). Wzrost względem
wersji z 3 szufladami: ~18 kg — sześć kompletów okucia/materiału zamiast
trzech, plus przywrócony dzielnik, plus boki w pełnej grubości 18 mm.

## 4. Nos zaoblony

## 4. Nos zaoblony

Łuk **R150**, środek (150, 150), styczny do frontu w x = 150 i do lewego boku
w y = 150 — przechodzi w płaszczyzny bez załamania. Sprawdzane automatycznie.
Bez żeber i bez poszycia giętego (usunięte w rundzie 2).

### Małe półeczki narożnika — runda 8: przywrócone

Runda 7 usunęła wręby, więc strefa zaokrąglonego narożnika (0–150 mm) zrobiła
się pusta na czterech środkowych poziomach — zostało to od razu zauważone.
Rozwiązanie: półeczki wracają jako **osobne, małe elementy** (nie scalone
z resztą przęsła jak w rundach 2–6), wspornikowo skręcone do lica lewego
boku.

To działa teraz prościej niż kiedykolwiek: lico lewego boku w x = 150 jest
**płaskie i odsłonięte** (nie ma już grzebienia ani wrębu z rundy 7), więc
mocowanie to zwykłe złącze na 2 śruby M6 w mimośrody — ten sam schemat co
wszędzie indziej w meblu, bez żadnej nowej techniki.

| Element | Wartość |
|---|---|
| Liczba | 4 (na każdym z czterech środkowych poziomów) |
| Obrys | ćwiartka koła R150 do lica pionu (x = 150), pełna głębokość 396 mm |
| Mocowanie | 2 śruby M6 poziomo w lico pionu, mimośrody w krawędzi półeczki |
| Pozycje śrub (w głąb) | 60 i 300 mm |

Dolna i górna płyta **nie potrzebują** tego zabiegu — obejmują cały obrys
łuku R150 w jednym kawałku (§ 1), więc tam półeczka i tak już jest.

## 5. Cokół — runda 4–6, bez zmian w rundzie 7

| Parametr | Wartość |
|---|---|
| Wysokość | 100 mm (85 mm listwy + 15 mm luzu) |
| Cofnięcie | 22 mm jednolicie na wszystkich czterech bokach |
| Konstrukcja | płyty **18 mm na rąb** + 3 żebra poprzeczne pod pionami |
| Narożnik | pas 18 mm, R128 → R110, współśrodkowy z łukiem korpusu |
| Kotwienie | **10 kotew M6** przez dolną płytę w mimośrody w szynach |

22 mm > 20 mm listwy przypodłogowej, więc rama nadal ją omija (2 mm zapasu).
Żebra są konieczne — bez nich dolna płyta przenosiłaby obciążenie pionów na
zginanie w świetle do 526 mm.

*Uwaga wykonawcza:* pas 18 mm na łuku R128 wykonać jako kilka prostych
cięciw albo nacinany (kerf-bent) — przy 100 mm wysokości i cofnięciu 22 mm
różnica jest niewidoczna w cieniu pod korpusem.

---

## 6. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Dolna i górna płyta | dowolne | złożony obrys (łuk) |
| Piony (4 szt.) | wzdłużne (Z) | nośność na wyboczenie |
| Półki środkowe | wzdłużne (X) | sztywność na rozpiętości 526 mm |
| Plecki | wzdłużne (Z) | usztywnienie na skręcanie |
| Fronty szuflad, drzwiczki | wzdłużne | stabilność wymiarowa lica |
| Cokół — szyny i żebra | wzdłużne | jak elementy ramowe |
| Cokół — narożnik | dowolne | złożony obrys (łuk) |

Sprawdzane automatycznie dla każdego elementu.

---

## 7. Do rozstrzygnięcia

Dwa punkty, oba decyzje klienta/biznesowe, nie problemy techniczne:

1. **Czy masa 145,5 kg z sześcioma szufladami jest akceptowalna** przy
   transporcie i montażu w dwie osoby. Model przyjmuje dowolną kombinację
   `DRAWER_CELLS`/`DOOR_CELLS`, więc zakres wyposażenia można jeszcze zmienić.
2. **Kiedy zrobić szablon DXF do cięcia CNC.** Model ma teraz realne,
   poprawione wymiary handlowe (grubość boków szuflady, rozstaw wkrętów
   Blum), więc jest gotowy pod eksport — ale sam generator DXF z warstwami
   (wg CLAUDE.md) jeszcze nie istnieje. To jawnie osobna runda pracy (patrz
   `brief.md` §6, „poza zakresem"), nie coś pominiętego przez przeoczenie.

**Zamknięte w rundzie 9 (po poprawkach):** prowadnice szuflad (Blum TANDEM
562H, realne wymiary z blum.com), grubość boków szuflady (18 mm — mieści się
w oficjalnym zakresie Blum 12,7–19,0 mm, jeden materiał w całym meblu),
rozmieszczenie dwóch rzędów szuflad, dzielnik między rzędami szuflad
przywrócony po błędzie. **Zamknięte wcześniej:** wręby (usunięte całkowicie),
dostęp dla łba śruby, reguła 1/3 grubości, mocowanie plecków, konstrukcja
półek środkowych, wymiary okucia pion↔płyta, konstrukcja ramy cokołu,
kotwienie korpus ↔ cokół, nawis prawego boku (§ 5), półeczki narożnika nosa
(§ 4).

**Do zapisania w instrukcji montażu:** masa netto **145,5 kg** z pełnym
wyposażeniem — sześć szuflad, dwoje drzwiczek (same płyty i okucie,
bez lakieru). Montaż w dwie osoby, na miejscu ustawienia — kolejność:
dolna płyta → piony → plecki → górna płyta → półeczki narożnika →
półki/szuflady/drzwiczki → cokół.
