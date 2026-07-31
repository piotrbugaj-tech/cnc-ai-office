# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
**Runda 8:** małe zaokrąglone półeczki w rogu nosa wracają jako osobne,
wspornikowo skręcane elementy (zniknęły w rundzie 7 razem z wrębami).

## Status

**24/24 testów** w `checks.py`, zero kolizji na 51 elementach. Nie było
jeszcze walidacji przez `qa-inspector` ani `safety-officer`.

Konstrukcja bez wrębów (runda 7) i przywrócone półeczki narożnika (runda 8)
są zamknięte technicznie. Otwarte pozostaje jedno pytanie **do Ciebie**
(nie do stolarza) — patrz § 7.

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

## 3. Szuflady i drzwiczki — opcja parametryczna (runda 7)

Sterowane wyłącznie parametrami w `shelf_model.PARAMS`:

```python
"DRAWER_CELLS": ((0, 0), (0, 1), (0, 2)),      # (poziom, przęsło)
"DOOR_CELLS":   {(1, 0): "L", (1, 2): "R"},    # + strona zawiasów
```

Poziom 0 = komora tuż nad dolną płytą. Przęsła 0–2 od lewej. Wariant w
podglądzie: **3 szuflady w dolnym rzędzie + 2 drzwiczki wyżej** (jedne na
lewych zawiasach, jedne na prawych) — po to, żeby oba warianty były widoczne
naraz. Włączenie komory automatycznie pomija w niej półkę.

### Szuflada — 5 elementów

| Element | Wymiar | Materiał |
|---|---|---|
| Front (nakładany w świetle, szczelina 3 mm) | 520 × 352 mm | sklejka 18 |
| Boki (2 szt.) | 350 × 220 mm | sklejka 18 |
| Tył | 464 × 220 mm | sklejka 18 |
| Dno | 464 × 350 mm | sklejka 4 |

Prowadnice kulkowe boczne 350 mm, luz **13 mm na stronę** — stąd korpus
szuflady jest o 26 mm węższy od światła przęsła (526 → 500 mm).

### Drzwiczki — strona zawiasów nie zmienia listy cięć

**Płyta drzwi jest identyczna w obu wariantach.** Strona zawiasów zmienia
wyłącznie pozycję puszek Ø35: oś 22,5 mm od krawędzi zawiasowej, 100 mm od
góry i od dołu. To celowe — przełożenie zawiasów na drugą stronę to zmiana
**wiercenia**, nie kształtu, więc nie rusza nestingu ani cut-listy.

Sprawdzane automatycznie: test pilnuje, że puszki są przy krawędzi zgodnej
z `DOOR_CELLS`, i że żadna komora nie dostała jednocześnie szuflady i drzwi.

---

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

Jeden punkt, decyzja klienta, nie problem techniczny:

1. **Ile komór finalnie dostaje szuflady/drzwiczki.** Model przyjmuje
   dowolną kombinację; podgląd pokazuje wariant demonstracyjny (3 szuflady +
   2 drzwiczki). Masa netto rośnie wyraźnie przy pełnym wyposażeniu.

**Zamknięte w rundzie 7:** wręby (usunięte całkowicie), dostęp dla łba śruby,
reguła 1/3 grubości, mocowanie plecków, konstrukcja półek środkowych.
**Zamknięte wcześniej:** wymiary okucia, konstrukcja ramy cokołu, kotwienie
korpus ↔ cokół, nawis prawego boku (§ 5).

**Do zapisania w instrukcji montażu:** masa netto **127,6 kg** z pełnym
wyposażeniem (same płyty, bez okuć). Montaż w dwie osoby, na miejscu
ustawienia — kolejność: dolna płyta → piony → plecki → górna płyta →
półeczki narożnika → półki/szuflady/drzwiczki → cokół.
