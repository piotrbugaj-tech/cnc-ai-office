# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
**Runda 9:** dwa dolne rzędy dostają szuflady na prowadnicach Blum TANDEM
562H (realne wymiary handlowe, nie przybliżenie). Pierwsza wersja miała dwa
błędy złapane przez klienta (zniknięty dzielnik, nierealna grubość 16 mm) —
naprawione, patrz § 3.

**Runda 9.1 — audyt `qa-inspector` (opus):** pełny audyt „od ogólnych
założeń po najmniejszą śrubkę" znalazł **7 blokujących usterek** w
warstwie, której żaden test wcześniej nie sprawdzał — punkty wiercenia
(łby śrub, kotwy) generowane bez sprawdzenia, czy w tym miejscu nie stoi
już inny materiał. Naprawione tam, gdzie poprawka nie wymagała zgadywania
nowych danych producenta (patrz § 3, § 5, § 7). **Jedna usterka pozostaje
świadomie otwarta**: dokładny sposób mocowania prowadnicy Blum wymaga
zweryfikowanej karty katalogowej, nie kolejnego domysłu — dwa domysły z
rzędu (16 mm, teraz to) już raz kosztowały przeróbkę, trzeci byłby
kosztowniejszy na etapie CAM niż na etapie projektu. Patrz § 3, „Otwarte:
sposób mocowania prowadnicy".

**Runda 9.2:** klient obejrzał bryłę po audycie i zauważył, że mimo
naprawy 7 usterek blokujących nikt nie zamodelował, **czym** jest
w ogóle złożona szuflada — dno bez rowka, brak złącza narożnego. Trafna
uwaga: runda 9.1 (NC-03) tylko opisała propozycję tekstem w tym pliku, nie
przełożyła jej na geometrię. Naprawione — patrz § 3, „Łączenie korpusu
szuflady".

## Status

**36/36 testów** w `checks.py` (było 26 przed audytem, 31 po pierwszej
turze poprawek — kolejne 5 domyka rowek/kołki szuflady z rundy 9.2), zero
kolizji na 120 elementach. `qa-inspector` (opus) wykonał pełny audyt
rundy 9 — werdykt **NOT READY**, 7 usterek blokujących + 11 „do poprawy" +
drobne. Usterki niezależne od niezweryfikowanych danych Blum zostały
naprawione (9.1), a złącze korpusu szuflady — wtedy tylko propozycja
tekstowa — zostało w rundzie 9.2 rzeczywiście zamodelowane po uwadze
klienta. `safety-officer` jeszcze nie widział projektu.

Konstrukcja jest zamknięta technicznie poza jednym punktem (sposób
mocowania prowadnicy Blum, § 3). Otwarte pozostają dwa punkty biznesowe
**do Ciebie** (nie do stolarza) — patrz § 7.

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

Plecki: sklejka 4 mm, 4 płyty (nos + 3 przęsła) — nos 150 × 1900 mm,
przęsła skrajne 553 × 1900 mm, przęsło środkowe 544 × 1900 mm (piony
środkowe dzielą szerokość nierówno w połowie grubości) — wszystkie mieszczą
się na arkuszu 2440 × 1220.

**Otwarte — audyt rundy 9.1 (NC-15):** `PARAMS["BACK_GROOVE_W/D"]` (4 × 8 mm)
opisuje wpust powyżej, ale **nigdy nie trafiło to do geometrii** — plecki w
`shelf_model.py` są dziś modelowane jako proste płyty stykające się z
tylną krawędzią ramy (piony/płyty), bez żadnego wycięcia po żadnej stronie.
Nic mechanicznie ich nie przytrzymuje poza pozycją w złożonym meblu. To
luka z rundy 7, nie z rundy 9 — wyszła dopiero teraz przy audycie. Do
zrobienia przed DXF: albo faktycznie wyfrezować wpust w geometrii (piony i
płyty dostają rowek 4 mm na tylnej krawędzi), albo świadomie zrezygnować z
wpustu na rzecz innego mocowania i skorygować ten opis. **Wymaga decyzji
joinery-specialist, nie jest zamknięte.**

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
| Luz systemowy | **13 mm na stronę** (niepotwierdzone, patrz niżej) | `RUNNER_CLEAR` — zgadnięte w rundzie 7 |
| Nośność statyczna | **~45 kg/parę** | wg wariantu długości 533 mm, NIE 350 mm jak w projekcie — do potwierdzenia dla NL 350 |
| Mocowanie | wkręty w lico pionu (strona korpusu) + w bok szuflady (strona ruchoma) — **niepotwierdzone, patrz niżej** | `runner_positions()` |

### Otwarte: sposób mocowania prowadnicy — audyt rundy 9.1 (NC-05, NC-06)

`qa-inspector` znalazł to samo, co zawiodło przy grubości 16 mm: dane o
Blum wzięte z fragmentów wyników wyszukiwania, nie z karty katalogowej, a
tym razem chodzi o coś bardziej fundamentalnego niż grubość — **sposób
mocowania**. Model zakłada boczne skręcanie (wkręty w płaskie lico pionu i
boku szuflady, `runner_positions()`). Kilku sprzedawców opisuje jednak
TANDEM 562H jako *„concealed **undermount** slide"* — prowadnicę mocowaną
**pod dnem** szuflady, nie w bok. Jeśli to prawda, cały schemat
`runner_positions()` (12 punktów wiercenia na parę, w lica pionów i boków)
mierzy złe miejsce — undermount potrzebuje innej geometrii (wycięcia w
dnie, inny sposób mocowania kątowników) i luz `RUNNER_CLEAR = 13 mm` może
być nieprawidłowy dla tego wariantu.

**Świadomie NIE zgaduję trzeci raz.** Dwa błędy z rundy 9 (limit 16 mm,
zniknięty dzielnik) już raz wynikły z pracy na fragmentach wyszukiwania
zamiast karty katalogowej. Zamiast poprawiać `runner_positions()` na
kolejny domysł, zostawiam go bez zmian i **jawnie oznaczam jako
prowizoryczny** — punkty wiercenia są matematycznie spójne z resztą
modelu (12/parę, bez duplikatów, sprawdzane automatycznie), ale **nie
wolno ich wiercić** bez wcześniejszego potwierdzenia kartą katalogową
Blum dla TANDEM 562H NL 350. Wycofuję też stwierdzenie „model gotowy pod
eksport DXF" z § 7 w części dotyczącej okucia szuflad — reszta modelu
jest gotowa, ale nie ten fragment.

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
`hinge_positions()`. **72 wkręty łącznie (12 na parę × 6 par)** — 6 w lico
pionu + 6 w bok szuflady na każdej parze — osobno liczone od 24 śrub M6
konstrukcji nośnej. (Poprawka rundy 9.1, NC-10: wcześniejsza wersja tego
dokumentu podawała błędnie „6 na parę × 6 par" = 36 ≠ 72.)

Poziom 0 = komora tuż nad dolną płytą. Przęsła 0–2 od lewej. **Poprawka
rundy 9.1 (NC-11):** ten akapit wcześniej twierdził „włączenie komory
automatycznie pomija w niej półkę" — to opisywało zachowanie usunięte
właśnie w tej rundzie (patrz niżej, „Drugi błąd rundy 9"). Aktualnie: półka
na kołkach buduje się **zawsze**, niezależnie od tego, czy komora jest
szufladą, drzwiczkami czy zwykłym wnętrzem.

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
komór — 12 fizycznych półek zamiast 9. Nie koliduje z geometrią szuflady
(sprawdzone: prześwit komory `z1` już wcześniej kończył się dokładnie na
spodzie tej płyty, niezależnie od tego czy `Part` istniał) — czysto
addytywna poprawka, potwierdzona przez `checks.py` (0 kolizji na 84
elementach).

**Skutek uboczny złapany przez audyt (NC-02):** przywrócona półka przęsła 0
zaczyna się dokładnie w licu pionu (x = 168), czyli dokładnie tam, gdzie
śruby małych półeczek narożnika (§ 4) mają swój łeb. Zanim audyt to
wychwycił, 8 z 8 tych śrub nie miałoby gdzie usiąść. Naprawione: wąski
pasek półki najbliższy pionowi (20 mm) jest teraz podzielony na kawałki z
oknami dokładnie przy obu pozycjach śrub (`NOSE_CORNER_BOLT_Y`, ten sam
mechanizm co zebra cokołu niżej) — reszta półki (od 20 mm w prawo) bez
zmian. Fizycznie to nadal jedna półka sklejona z kilku kawałków, nie kilka
osobnych półek — stąd w BOM (`checks.py`) `shelf-bay` pokazuje teraz 24
sztuk (kawałki CNC), nie 12 (fizyczne jednostki po montażu).

### Szuflada — 5 elementów, dwa materiały

| Element | Wymiar | Materiał |
|---|---|---|
| Front (nakładany w świetle, szczelina 3 mm) | 520 × 352 mm | sklejka 18 |
| Boki (2 szt.) | 350 × 220 mm | sklejka 18 |
| Tył | 464 × 220 mm | sklejka 18 |
| Dno | 464 × 332 mm | sklejka **9** |

(Poprawka rundy 9.1, NC-09: ta tabela wcześniej podawała dno jako
460 × 348 mm w sklejce 4 mm — nie zgadzało się z modelem nawet przed
poprawką grubości. Aktualne wymiary czytane wprost z `checks.py`.)

**Grubość dna podniesiona z 4 na 9 mm (NC-04, audyt qa-inspector).** Dno w
sklejce 4 mm (tej samej co plecy) uginałoby się wyraźnie ponad przyjęty
limit L/300 pod obciążeniem, jakie prowadnica ma udźwignąć — 9 mm
sprowadza ugięcie z powrotem w bezpieczny zakres. Osobny parametr
`DRAWER_BOTTOM_T`, nie `BACK` (plecy mają inny przypadek obciążenia —
usztywnienie na skręcanie, nie dźwiganie zawartości szuflady).

Prowadnice kulkowe boczne NL 350, luz **13 mm na stronę** (Blum,
niepotwierdzone — patrz „Otwarte: sposób mocowania prowadnicy" wyżej) —
stąd korpus szuflady jest o 26 mm węższy od światła przęsła (526 → 500 mm).

### Łączenie korpusu szuflady — runda 9.2: zaprojektowane i zamodelowane

Klient (po obejrzeniu bryły): *„nie widzę żadnego rowka ani połączeń dla
spodu szuflady. przemyślałeś to jak ma być złożona cała szuflada?"* —
słuszna uwaga: runda 9.1 (NC-03) tylko **opisała** propozycję złącza w tym
dokumencie, nie przełożyła jej na geometrię. Dno po prostu „leżało" w
bryle bez żadnego wcięcia, boki/tył/front nie miały modelowanego
połączenia w ogóle. Naprawione — teraz to prawdziwa geometria, nie tylko
tekst:

**Dno — rowek na 3 stronach (oba boki + tył), bez rowka z przodu.**
Każdy bok i tył to w modelu 3 sklejone pasma w pionie — pełne / rowek /
pełne (`DRAWER_GROOVE_MARGIN` = 10 mm od dołu do rowka, głębokość rowka
`DRAWER_GROOVE_DEPTH` = 6 mm, zostawia ściankę 12 mm) — fizycznie jedna
deska, frezowana jednym przejściem wraz z resztą konturu, tak jak wpust
plecków korpusu głównego (§ 2). Dno wsuwa się w ten rowek z luzem
`DRAWER_GROOVE_CLEAR` = 0,5 mm. Przód nie ma rowka — dno kończy się
dokładnie w licu frontu (y = T), tam trzymają je kołki poniżej.

**Naroża — klej + kołki Ø8 mm** (`DRAWER_DOWEL_D`), nie wkręty ani
mimośrody: w odróżnieniu od korpusu głównego (który klient wprost chce
**wielokrotnie rozbieralny**), pojedyncza szuflada nie jest czymś, co
użytkownik kiedykolwiek rozkłada — to zamknięta podzespołowa całość,
złożona raz w warsztacie, więc nie musi trzymać się zasady „żadnych
wkrętów w płytę" tej samej wagi co reszta mebla.

- **Bok↔tył** (`drawer_corner_dowel_positions()`): 2 kołki na naroże × 2
  naroża = 4 na szufladę, otwór ślepy 15 mm (`DRAWER_DOWEL_DEPTH`),
  wiercone poziomo od zewnętrznego lica boku w materiał tyłu.
- **Front↔bok** (`drawer_front_dowel_positions()`): 2 kołki na bok × 2 =
  4 na szufladę, wiercone od tylnego (niewidocznego) lica frontu w
  materiał boku — nie przechodzą na wylot, bez śladu na licu widocznym.

Sprawdzane automatycznie: rowek zostawia ściankę ≥ 10 mm; wszystkie 24+24
kołki (po 4 na 6 szuflad) trafiają w rzeczywisty materiał; pasma
boku/tyłu sumują się z powrotem do pola pełnego, niescienionego panelu
(bez tego `Part.area_m2()` liczyłby błędną masę dla wąskich pasm rowka —
ta sama kategoria błędu co NC-16, złapana i naprawiona przy tej samej
okazji). Osobny podgląd 3D: `design/drawer-detail.html`, sekcja „Złącze
korpusu".

### Drzwiczki — strona zawiasów nie zmienia listy cięć

Bez zmian względem rundy 7: **płyta drzwi jest identyczna w obu wariantach.**
Strona zawiasów zmienia wyłącznie pozycję puszek Ø35: oś 22,5 mm od krawędzi
zawiasowej, 100 mm od góry i od dołu. Sprawdzane automatycznie.

### Materiał — przeliczone (runda 9.1, po poprawkach audytu)

„Takie same elementy × ilość", z pełnego wydruku `checks.py`. Liczby to
kawałki CNC — `plinth-rib` i `shelf-bay` zawierają teraz doliczone kawałki
odciążające pod łby śrub (NC-01/NC-02), fizycznie nadal 3 żebra i 12 półek
(patrz uwaga w wydruku `checks.py`):

| Grupa | Szt. (CNC) | Materiał |
|---|---|---|
| `drawer-front` | 6 | sklejka 18 |
| `drawer-side` | 12 | sklejka 18 |
| `drawer-back` | 6 | sklejka 18 |
| `drawer-bottom` | 6 | sklejka **9** |
| `door` | 2 | sklejka 18 |
| `shelf-bay` | 24 (12 fizycznych) | sklejka 18 |
| `plinth-rib` | 9 (3 fizyczne) | sklejka 18 |

Masa netto całego mebla: **148,9 kg** (było 127,6 kg z 3 szufladami przed
rundą 9; runda 9 „pierwsza wersja" pokazywała błędnie 135,5 kg — brakowało
jej 3 dzielników i miała cieńsze, nierealne boki szuflad; runda 9.1
„naprawiona, przed audytem" pokazywała 145,5 kg; audyt doliczył grubsze
dno szuflady (+9 mm zamiast 4 mm) i poprawił błąd w liczeniu masy
zakrzywionego pasa narożnika cokołu (NC-16) do dzisiejszych 148,9 kg).

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

**Poprawka rundy 9.1 (NC-01, audyt qa-inspector):** śruby pion↔płyta
wchodzące od spodu (§ 1) miały łeb dokładnie na wysokości żebra — 0 mm
luzu, nie do zamontowania mimo że test „korpus siada dokładnie na górze
cokołu" przechodził (sprawdzał tylko styk płyta-cokół, nie łeb-vs-żebro).
Każde żebro dostało teraz wąskie okna (24 mm) dokładnie przy obu pozycjach
śrub — reszta długości żebra nadal przenosi obciążenie. Fizycznie to
nadal 3 żebra, jedno na każdy z pierwszych trzech pionów; w BOM
(`checks.py`) `plinth-rib` liczy teraz 9 kawałków CNC (3 na żebro), nie 3
fizyczne żebra.

*Nieumodelowana usterka wykonawcza (audyt, nie blokująca):* górne śruby
(wieniec) mają łeb na zewnętrznej, widocznej powierzchni górnej płyty
(z = 2000 mm) — łeb śruby M6 z gniazdem imbusowym wystaje z niej ok. 6 mm,
co technicznie przekracza budżet wysokości „dokładnie 2000 mm" z rundy 4.
Potrzebne raczej pogłębienie (Ø12 × 6 mm) pod każdą z 8 górnych śrub niż
zmiana geometrii płyty — cecha CAM-owa, nie bryłowa, do uwzględnienia w
rundzie DXF.

*Uwaga wykonawcza:* pas 18 mm na łuku R128 wykonać jako kilka prostych
cięciw albo nacinany (kerf-bent) — przy 100 mm wysokości i cofnięciu 22 mm
różnica jest niewidoczna w cieniu pod korpusem.

---

## 6. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Dolna i górna płyta | dowolne | złożony obrys (łuk) — **w tym górna, widoczna powierzchnia**: wyjątek od normy „widoczne elementy wzdłużnie" (CLAUDE.md § 6) świadomy, nie przeoczony — łuk R150 nie pozwala na jeden spójny kierunek słojów na całej płycie |
| Piony (4 szt.) | wzdłużne (Z) | nośność na wyboczenie |
| Półki środkowe | wzdłużne (X) | sztywność na rozpiętości 526 mm |
| Plecki | wzdłużne (Z) | usztywnienie na skręcanie |
| Fronty szuflad, drzwiczki | wzdłużne | stabilność wymiarowa lica, powierzchnia widoczna |
| Boki i tył szuflady | wzdłużne | jak korpus — nieeksponowane, ale spójne z resztą |
| Dno szuflady | dowolne | cienka płyta nośna, nie widoczna |
| Poleczki narożnika nosa | dowolne | złożony obrys (łuk) |
| Cokół — szyny i żebra | wzdłużne | jak elementy ramowe |
| Cokół — narożnik | dowolne | złożony obrys (łuk) |

Sprawdzane automatycznie dla każdego elementu.

---

## 7. Do rozstrzygnięcia

**Konwencja numeracji poziomów (NC-13, audyt qa-inspector):** w tym pliku i
w kodzie poziomy są zawsze liczone **od 0** — poziom 0 = komora tuż nad
dolną płytą. `brief.md` w jednym miejscu (tabela specyfikacji, §1) liczyła
od 1 („poziom 3" dla drzwiczek) — poprawione tam na tę samą konwencję.

Jeden punkt techniczny (czeka na Twoje potwierdzenie, ale nie blokuje
niczego innego) i dwa punkty biznesowe:

1. **[TECHNICZNE, do potwierdzenia]** Złącze korpusu szuflady — klej +
   kołki Ø8 (§ 3) — zaprojektowane i zamodelowane w rundzie 9.2, ale to
   nadal moja rekomendacja inżynierska, nie coś klient wprost zamówił.
   Jeśli wolisz inne złącze (np. wkręty zamiast kołków), to zmiana
   parametryczna, nie przebudowa.
2. **Czy masa 148,9 kg z sześcioma szufladami jest akceptowalna** przy
   transporcie i montażu w dwie osoby. Model przyjmuje dowolną kombinację
   `DRAWER_CELLS`/`DOOR_CELLS`, więc zakres wyposażenia można jeszcze zmienić.
3. **Kiedy zrobić szablon DXF do cięcia CNC.** Większość modelu ma teraz
   realne, poprawione wymiary — ale **nie cały**: sposób mocowania
   prowadnicy Blum (§ 3) pozostaje otwarty i musi się zamknąć przed DXF,
   inaczej warstwa wiercenia dla 72 wkrętów byłaby zgadywanką. To jawnie
   osobna runda pracy (patrz `brief.md` §6, „poza zakresem"), nie coś
   pominiętego przez przeoczenie.

**Zamknięte w rundzie 9.1 (audyt qa-inspector, 7 usterek blokujących):**
łeb śruby dno↔pion vs żebro cokołu (NC-01), łeb śruby półeczki narożnika
vs półka przęsła 0 (NC-02), grubość dna szuflady vs ugięcie (NC-04),
głębokość otworów kołków w pionach środkowych (NC-07 — kołki półkowe),
luz kotwy cokołu od krawędzi ramy (NC-08), błąd liczenia masy pasa
narożnika cokołu (NC-16), martwe parametry i błędne cytowania (NC-17
częściowo). Dodana nowa klasa testów (NC-19) sprawdzająca łby śrub/kotew
wprost przeciwko materiałowi — to jej brak pozwolił powyższym przejść
niezauważenie mimo 26/26 w rundzie 9.

**Zamknięte w rundzie 9.2 (uwaga klienta po obejrzeniu bryły):** złącze
korpusu szuflady (NC-03) — rowek pod dno na 3 stronach + kołki naroży,
rzeczywiście zamodelowane (nie tylko opisane tekstem jak w rundzie 9.1).
Po drodze złapany i naprawiony ten sam typ błędu co NC-16 (`area_m2()` źle
liczyło masę wąskich pasm rowka) — regresja zablokowana nowym testem.

**Świadomie NIE zamknięte (wymaga zweryfikowanych danych producenta, nie
kolejnego domysłu):** sposób mocowania prowadnicy Blum — bok czy spód
(NC-05), datum wkrętów prowadnicy (NC-06, powiązane z NC-05), głębokość
otworów wkrętów prowadnicy (NC-07 — wkręty, ta sama przyczyna). **Wymaga
decyzji joinery-specialist:** wpust plecków nieobecny w geometrii (NC-15).
**Poza zakresem tej rundy, do DXF:** klasy tolerancji IT6/IT8 z CLAUDE.md
§6 nie mają jeszcze jawnych testów (NC-18); dog-bone'y nieaktualne (zero
wrębów od rundy 7 — do jawnego zapisania) i tabsy dla małych elementów
(`plinth-corner` 128×128 mm < 200×200 mm z CLAUDE.md §6) jeszcze nie
zaprojektowane.

**Zamknięte wcześniej:** wręby (usunięte całkowicie), dostęp dla łba śruby
pion↔płyta, reguła 1/3 grubości, mocowanie plecków (poza samym wpustem,
patrz NC-15 wyżej), konstrukcja półek środkowych, wymiary okucia
pion↔płyta, konstrukcja ramy cokołu, kotwienie korpus ↔ cokół, nawis
prawego boku (§ 5), półeczki narożnika nosa (§ 4), prowadnice szuflad —
model i liczba (Blum TANDEM 562H, 6 par), grubość boków szuflady (18 mm —
mieści się w oficjalnym zakresie Blum 12,7–19,0 mm), rozmieszczenie dwóch
rzędów szuflad, dzielnik między rzędami szuflad.

**Do zapisania w instrukcji montażu:** masa netto **148,9 kg** z pełnym
wyposażeniem — sześć szuflad, dwoje drzwiczek (same płyty i okucie,
bez lakieru). Montaż w dwie osoby, na miejscu ustawienia — kolejność:
dolna płyta → piony → plecki → górna płyta → półeczki narożnika →
półki/szuflady/drzwiczki → cokół.
