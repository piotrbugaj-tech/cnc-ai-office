# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
Runda 2: geometria, bez poszycia giętego. Wymiary gniazd i dog-bone'ów wchodzą
do DXF w kolejnej rundzie.

## Status

Bryła czeka na akceptację. Stolarka poniżej jest zamodelowana i przetestowana
geometrycznie (16/16 testów w `checks.py`, w tym zero kolizji na 91 elementach),
ale **nie została jeszcze zwalidowana przez `qa-inspector` ani `safety-officer`**.

**Sekcja 2 (wrąb w lewym boku) wymaga przeglądu przed cięciem w szczególności** —
konkretne wymiary (310 mm otwarcia, 86 mm grzbietu) to moje techniczne
rozwinięcie decyzji klienta „wręby przelotowe, bok zostaje jedną płytą",
nie jego dosłowna specyfikacja w milimetrach.

## 1. Złącze półka ↔ pion (piony pośrednie i prawy bok)

Podstawowe złącze konstrukcji, powtarzalne dla **30 końców półek** (przęsła 1
i 2 na obu pionach pośrednich + prawy bok; przęsło 0 przy nosie łączy się z
lewym bokiem przez wrąb — patrz sekcja 2, nie przez to złącze).

| Element | Wartość |
|---|---|
| Czopy na koniec | 2 szt. |
| Szerokość czopa | 60 mm (wzdłuż głębokości) |
| Grubość czopa | 18 mm (= grubość półki) |
| Pozycje czopów (Y) | 40–100 mm i 236–296 mm |
| Gniazdo | 60,1 × 18,1 mm |
| Luz | 0,1 mm (CLAUDE.md § 6) |
| Dog-bone | R3,1 (= R freza Ø6 + 0,1) — na każdym narożniku wewnętrznym |
| Śruby | 2 × M6 na złącze + mimośród beczkowy Ø10 × 18 w czole półki |
| Pozycje śrub (Y) | złącze lewe 140 i 200 mm, prawe 320 i 380 mm |

### Dlaczego nie finger jointy

CLAUDE.md § 6 wymaga finger jointów z nieparzystą liczbą palców, ale **to jest
złącze teowe, nie narożne** — półka wchodzi w bok pionu w połowie jego wysokości,
a nie styka się z nim krawędzią. Palce są tu geometrycznie nie na miejscu.
Finger jointy wrócą, jeśli w rundzie 2 zdecydujemy o łączeniu elementów na długości.

### Długość czopa zależy od pozycji pionu

Pion ma 18 mm — z obu stron nie da się zrobić gniazd nieprzelotowych po 12 mm.
Stąd dwa przypadki (trzeci, lewy bok, opisany w sekcji 2 — to już nie czop):

- **Piony pośrednie** — czopy z obu przęseł mają po 9 mm i **spotykają się w osi
  pionu**, dzieląc jedno gniazdo przelotowe. Jedna operacja CNC zamiast dwóch,
  wszystkie półki mają identyczny raster czopów, a zakończenia są niewidoczne.
- **Prawy bok (x = 1782)** — czop przelotowy **wystający 2 mm** poza lico.
  Świadomy detal: widoczne zakończenia czopów czytają konstrukcję.

### Śruby nie kolidują z czopami

Sprawdzane automatycznie (`checks.py`, test „osie śrub M6 omijają czopy"):
osie 140 / 200 / 320 / 380 mm leżą w prześwitach między czopami (100–236 i 296–396),
z zapasem na średnicę otworu.

Na pionie pośrednim śruby przęsła lewego (320, 380) i prawego (140, 200) są na
różnych wysokościach Y, więc otwory przelotowe się nie spotykają.

## 2. Nos zaoblony — runda 2: bez poszycia, scalony z półką

Runda 1 miała 11 żeber profilowych owiniętych pasem sklejki giętej 4 mm.
Klient poprosił o usunięcie poszycia i żeber bez odpowiednika w reszcie regału.

**Diagnoza sprzed usunięcia:** rozstaw 11 żeber (198,2 mm) był dokładnie
połową rozstawu półek (396,4 mm) — 6 żeber (indeksy parzyste) leżało dokładnie
na wysokości prawdziwych półek, 5 (indeksy nieparzyste) siedziało na
wysokościach pośrednich bez żadnego odpowiednika gdziekolwiek indziej w
regale. Usunięto te 5. Pozostałe 6 przebudowano tak, by wynikały wprost z
`level_z` (poziomów półek), a nie z osobnego `rib_pitch` — matematycznie
niemożliwe jest teraz, żeby znów się rozjechały.

| Element | Wartość |
|---|---|
| Promień | R150, środek (150, 150), pełny — bez cofnięcia (poszycia już nie ma) |
| Nos + przęsło 0 | scalone w **jeden element** na każdym z 6 poziomów |
| Lewy bok | 1 grzbiet + 5 zębów, wrąb przelotowy zamiast czopów |

Łuk jest **styczny** do frontu w x = 150 i do lewego boku w y = 150 — przechodzi
w płaszczyzny bez załamania. Sprawdzane automatycznie.

### Scalenie z półką przęsła 0

Zamiast osobnego żebra i osobnej prostokątnej półki, każdy z 6 poziomów to
teraz **jedna płyta**: zaokrąglony front-lewy narożnik (R150) przechodzący
wprost w prostokątną resztę przęsła, od x = 0 do x = 694 (lico pionu
mid-1). Słoje: dowolne (złożony obrys).

### Wrąb w lewym boku (stopped housed dado) — moje rozwinięcie, wymaga przeglądu

Klient wybrał „wręby przelotowe, bok zostaje jedną płytą" zamiast „5 osobnych
słupków". Problem: scalona płyta zajmuje **pełną głębokość** (0–396 mm) na
całej szerokości. Wrąb, który przepuszcza ją na pełnej głębokości, fizycznie
przecina bok na wylot — to nie różni się geometrycznie od „5 słupków", tylko
inaczej się nazywa.

Żeby bok faktycznie pozostał jedną sztuką materiału, wrąb jest **zamknięty od
tyłu**:

| Element | Wartość |
|---|---|
| Otwarcie wrębu (od frontu) | 310 mm — tu płyta swobodnie przechodzi |
| Grzbiet (zamknięty, z tyłu) | 86 mm — tu bok zostaje ciągły na całej wysokości |
| Wysokość wrębu | 18,1 mm (grubość półki + luz 0,1 mm) |
| Ząb (między wrębami) | 378,4 mm wys. × 310 mm gł. × 18 mm gr., 5 szt. |
| Grzbiet | 2000 mm wys. × 86 mm gł. × 18 mm gr., 1 szt. |

Efekt: bok = grzebień — ciągły grzbiet z 5 zębami wystającymi we frontową
strefę między kolejnymi wrębami. W modelu to 6 osobnych brył (`Part`) pod
wspólnym `qty_group="vertical-L-gable"`, ale **fizycznie to jedna sztuka
materiału**, wycinana jako jeden kształt grzebienia — kolejna runda (DXF) musi
to zapisać jako jeden flat pattern, nie sześć osobnych części.

Test kolizji (`checks.py`) potwierdza zero przenikań między grzbietem/zębami
a sześcioma scalonymi płytami — konstrukcja domyka się geometrycznie.

**Konkretne milimetry (310/86) to mój dobór inżynierski, nie decyzja klienta
podana wprost — wymaga zatwierdzenia przez joinery-specialist przed cięciem.**
86 mm grzbietu to niewiele materiału na wysokości 2000 mm; warto sprawdzić
sztywność na skręcanie, zwłaszcza że złącze plyta↔wrąb nie ma na razie żadnego
mocowania (patrz niżej).

### Mocowanie w złączu wrąb ↔ płyta — nierozstrzygnięte

Płyta siedzi w wrębie na wcisk. Sam wrąb ją pozycjonuje, ale nic jej nie
przytrzymuje przy wielokrotnym montażu/demontażu (CLAUDE.md wymaga montażu
rozbieralnego). Do rozstrzygnięcia w rundzie dokumentacji: śruby retencyjne
przez grzbiet w mimośród w krawędzi płyty (analogicznie do złącza z sekcji 1),
czy samo tarcie wystarczy przy tej głębokości wrębu.

## 3. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Piony (mid-1, mid-2, R-side) | wzdłużne (Z) | nośność na wyboczenie |
| Lewy bok (grzbiet + zęby) | wzdłużne (Z) | jak pozostałe piony |
| Półki (przęsło 1, 2) | wzdłużne (X) | sztywność na rozpiętości 526 mm |
| Nos + półka (przęsło 0, scalone) | dowolne | złożony obrys |
| Plecy | wzdłużne (Z) | usztywnienie na skręcanie |

Każdy element ma zadeklarowany `grain_direction` w modelu — sprawdzane automatycznie.

## 4. Do rozstrzygnięcia

1. **Wrąb w lewym boku** — moje rozwinięcie decyzji „wręby przelotowe" (sekcja 2).
   Wymaga przeglądu joinery-specialist/qa-inspector przed cięciem.
2. **Mocowanie złącza wrąb ↔ płyta** — obecnie czysty wcisk, bez śrub. Dodać
   retencję czy polegać na tarciu?
3. **60 śrub M6** (po usunięciu 12 przy lewym boku) to nadal sporo jak na
   samodzielny montaż. Zejście do 1 na złącze dałoby 30; czopy i tak przenoszą
   ścinanie, śruba pracuje głównie na wyrywanie.
4. **Cokół** — pominięty, dno leży na podłodze.
5. **Masa 101 kg** (same płyty, bez okuć; spadła ze 107 kg po usunięciu
   poszycia i 5 żeber) — montaż w dwie osoby, do zapisania w instrukcji.
