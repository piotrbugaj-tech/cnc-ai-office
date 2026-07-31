# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
Runda 3: bez czopów. Wymiary otworów wchodzą do DXF w kolejnej rundzie.

## Status

Bryła czeka na akceptację. Stolarka poniżej jest zamodelowana i przetestowana
geometrycznie (13/13 testów w `checks.py`, w tym zero kolizji na 61 elementach,
bez żadnych wyjątków w teście kolizji — dawniej czop/gniazdo był jawnie pomijany
jako "z założenia wspólny", teraz nic nie jest pomijane), ale **nie została
jeszcze zwalidowana przez `qa-inspector` ani `safety-officer`**.

**Sekcja 1 (wrąb oporowy) i sekcja 2 (wrąb w lewym boku) wymagają przeglądu
przed cięciem** — konkretne wymiary (głębokość wrębu oporowego 5 mm; otwarcie
310 mm / grzbiet 86 mm w lewym boku) to moje techniczne rozwinięcie decyzji
klienta, nie jego dosłowna specyfikacja w milimetrach.

## 1. Złącze półka ↔ pion (piony pośrednie i prawy bok) — runda 3: bez czopów

Podstawowe złącze konstrukcji, powtarzalne dla **30 końców półek** (przęsła 1
i 2 na obu pionach pośrednich + prawy bok; przęsło 0 przy nosie łączy się z
lewym bokiem przez wrąb przelotowy — patrz sekcja 2, inne złącze).

### Dlaczego zrezygnowaliśmy z czopa

Klient poprosił o najprostsze możliwe rozwiązanie: **żadnych wkrętów
wkręcających się bezpośrednio w płytę** (ścierają gniazdo przy wielokrotnym
montażu/demontażu), tylko śruby maszynowe w osadzony gwint żeński, i wszystko
ma dać się zrobić jako wiercenie w tym samym ustawieniu co cięcie konturu —
zero frezowania kieszeni, zero profilowania krawędzi pod czop. To wyklucza
czop/gniazdo/dog-bone (frezowana kieszeń z poprawką na promień freza) na rzecz
czystych, wierconych otworów.

**Konsekwencja, którą trzeba było rozwiązać:** bez czopa półka opierałaby się
o pion tylko płasko, na styk — cały ciężar tego, co stoi na półce, przenosiłyby
same 2 śruby i sklejka wokół otworów, zamiast drewna na drewnie jak przy czopie.
Klient wybrał dodanie **płytkiego wrębu oporowego** zamiast akceptować to
ryzyko wprost.

### Złącze — dwa elementy, dwie funkcje

| Element | Funkcja | Wartość |
|---|---|---|
| Wrąb oporowy | przenosi **ciężar** (ścinanie pionowe) przez bezpośrednie oparcie | głębokość 5 mm, wysokość 18,1 mm (grubość półki + luz) |
| Śruba M6 + mimośród beczkowy | przenosi **docisk i wyrywanie** | 2 szt. na złącze, w mimośród (gwint żeński — nie wkręt, można rozkręcać bez końca) |
| Pozycje śrub (Y) | — | złącze lewe 140 i 200 mm, prawe 320 i 380 mm |

Wrąb jest **otwartym rowkiem na całą głębokość** (0–396 mm), frezowanym w
jednej prostej operacji wzdłuż całego pionu — bez kieszeni, bez wewnętrznych
narożników, więc **bez dog-bone'ów**: prosty rowek otwarty na obu krawędziach
nie ma gdzie ich potrzebować.

### Piony pośrednie: wrąb z obu stron; prawy bok: z jednej

- **Piony pośrednie (mid-1, mid-2)** mają wrąb 5 mm na **obu** licach — z
  każdej strony wchodzi w niego inna półka. Rdzeń pionu na wysokości wrębu:
  18 − 5 − 5 = **8 mm**.
- **Prawy bok** ma wrąb tylko na licu wewnętrznym (od strony przęsła 3) — lico
  zewnętrzne (widoczne z zewnątrz mebla) zostaje płaskie, pełnej grubości na
  całej wysokości. Rdzeń na wysokości wrębu: 18 − 5 = **13 mm**.

W modelu każdy z tych pionów to seria naprzemiennych brył — pełna grubość
między półkami, zredukowana grubość na wysokości każdej z 6 półek — pod
wspólnym `qty_group` (fizycznie jedna deska, tak jak grzebień lewego boku
w sekcji 2). Test kolizji potwierdza dokładne dopasowanie: półka sięga
dokładnie do dna wrębu, bez szczeliny i bez zakładki.

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

1. **Głębokość wrębu oporowego (5 mm)** — mój dobór inżynierski, nie decyzja
   klienta podana wprost (sekcja 1). Wymaga przeglądu joinery-specialist przed
   cięciem — zwłaszcza rdzeń pionów pośrednich (8 mm) na wysokości wrębu.
2. **Wrąb w lewym boku** — moje rozwinięcie decyzji „wręby przelotowe" (sekcja 2).
   Wymaga przeglądu joinery-specialist/qa-inspector przed cięciem.
3. **Mocowanie złącza wrąb ↔ płyta (nos)** — obecnie czysty wcisk, bez śrub.
   Dodać retencję czy polegać na tarciu?
4. **60 śrub M6** — 2 na złącze, 30 złączy (piony pośrednie i prawy bok).
   Skoro wrąb oporowy przenosi teraz ciężar, można rozważyć zejście do 1 śruby
   na złącze (docisk/wyrywanie nie wymaga dwóch), ale to zmniejsza odporność
   na skręcanie — do potwierdzenia razem z przeglądem wrębu.
5. **Cokół** — pominięty, dno leży na podłodze.
6. **Masa 102 kg** (same płyty, bez okuć; 107 kg → 101 kg → 102 kg w kolejnych
   rundach) — montaż w dwie osoby, do zapisania w instrukcji.
