# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
Runda 4: cokół pod ścianę z listwą przypodłogową. Wymiary otworów wchodzą do
DXF w kolejnej rundzie.

## Status

Bryła czeka na akceptację. Stolarka poniżej jest zamodelowana i przetestowana
geometrycznie (16/16 testów w `checks.py`, w tym zero kolizji na 66
elementach, bez żadnych wyjątków w teście kolizji), ale **nie została jeszcze
zwalidowana przez `qa-inspector` ani `safety-officer`**.

**Sekcje 1, 2 i 3 wymagają przeglądu przed cięciem** — konkretne wymiary
(głębokość wrębu oporowego 5 mm; otwarcie 310 mm / grzbiet 86 mm w lewym
boku; szerokość ramy cokołu 70 mm) to moje techniczne rozwinięcie decyzji
klienta, nie jego dosłowna specyfikacja w milimetrach. **Sekcja 3 ma
dodatkowo nierozwiązany problem konstrukcyjny — rama cokołu jest dziś bryłą
pełną, nie realnymi płytami 18 mm — patrz niżej.**

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
| Ząb (między wrębami) | 358,4 mm wys. × 310 mm gł. × 18 mm gr., 5 szt. |
| Grzbiet | 1900 mm wys. (wysokość korpusu — runda 4) × 86 mm gł. × 18 mm gr., 1 szt. |

Efekt: bok = grzebień — ciągły grzbiet z 5 zębami wystającymi we frontową
strefę między kolejnymi wrębami. W modelu to 6 osobnych brył (`Part`) pod
wspólnym `qty_group="vertical-L-gable"`, ale **fizycznie to jedna sztuka
materiału**, wycinana jako jeden kształt grzebienia — kolejna runda (DXF) musi
to zapisać jako jeden flat pattern, nie sześć osobnych części.

Test kolizji (`checks.py`) potwierdza zero przenikań między grzbietem/zębami
a sześcioma scalonymi płytami — konstrukcja domyka się geometrycznie.

**Konkretne milimetry (310/86) to mój dobór inżynierski, nie decyzja klienta
podana wprost — wymaga zatwierdzenia przez joinery-specialist przed cięciem.**
86 mm grzbietu to niewiele materiału na wysokości 1900 mm korpusu; warto sprawdzić
sztywność na skręcanie, zwłaszcza że złącze plyta↔wrąb nie ma na razie żadnego
mocowania (patrz niżej).

### Mocowanie w złączu wrąb ↔ płyta — nierozstrzygnięte

Płyta siedzi w wrębie na wcisk. Sam wrąb ją pozycjonuje, ale nic jej nie
przytrzymuje przy wielokrotnym montażu/demontażu (CLAUDE.md wymaga montażu
rozbieralnego). Do rozstrzygnięcia w rundzie dokumentacji: śruby retencyjne
przez grzbiet w mimośród w krawędzi płyty (analogicznie do złącza z sekcji 1),
czy samo tarcie wystarczy przy tej głębokości wrębu.

## 3. Cokół — runda 4: podniesienie nad listwę przypodłogową

Klient: regał stoi **tyłem i prawym bokiem do ściany**. Przy podłodze biegnie
listwa przypodłogowa 85 mm wysokości, 20 mm grubości (o tyle odstaje od
ściany). Bez cokołu korpus oparłby się o listwę zamiast przylegać do ściany.

### Decyzje klienta (`AskUserQuestion`)

1. **Budżet wysokości** — korpus **kurczy się**, żeby korpus + cokół dały
   dokładnie 2000 mm (a nie: cokół dokładany na dotychczasowe 2000 mm korpusu,
   co dałoby 2100 mm całości). Korpus: 2000 → **1900 mm**; światło
   międzypółkowe: 378,4 → **358,4 mm** (wciąż bezpieczna rozpiętość, patrz
   `brief.md`).
2. **Wysokość cokołu** — 85 mm listwy + 15 mm luzu na nierówności podłogi =
   **100 mm**.

### Geometria ramy

Cokół to **rama, nie pełna płyta** — obrys w rzucie z góry:

| Element | Zasięg (X, Y) mm | Funkcja |
|---|---|---|
| `plinth-left` | 0–70, 150–310 | szyna pod lewym bokiem/nosem |
| `plinth-back` | 0–1780, 310–380 | szyna pod tylną ścianą — cofnięta 20 mm od ściany |
| `plinth-right` | 1710–1780, 0–310 | szyna pod prawym bokiem — cofnięta 20 mm od ściany |
| `plinth-front` | 150–1710, 0–70 | szyna pod frontem |
| `plinth-corner` | łuk R150 → R80 | narożnik, ten sam promień co korpus powyżej |

Przy ścianach (tył, prawy bok) rama jest cofnięta o `SKIRTING_DEPTH` = 20 mm,
żeby ominąć listwę.

**Narożnik musi podążać za łukiem R150, nie może być prostokątny** —
sprawdzone wprost: róg prostokątnej ramy (punkt (0,0)) leżałby 212 mm od
środka łuku (150, 150), czyli 62 mm poza promieniem R150 korpusu powyżej.
Prostokątny narożnik wystawałby więc poza zaokrąglony nawis korpusu.
Rozwiązanie: `plinth-corner` to wycinek pierścienia między R150 (ten sam łuk
co korpus) a R150 − 70 = R80, więc cokół nigdzie nie wychodzi poza obrys
korpusu. Sprawdzane automatycznie (`checks.py`: „cokół mieści się pod łukiem
R150").

**Szerokość ramy (70 mm, `PLINTH_FRAME_W`) to mój dobór inżynierski** — nie
została podana wprost przez klienta. Typowy zakres dla cokołu meblowego to
50–100 mm; 70 mm wybrane jako środek tego zakresu. Wymaga potwierdzenia.

### Nierozwiązane — wymaga przeglądu joinery-specialist przed cięciem

1. **Rama cokołu jest dziś bryłą pełną, nie płytami 18 mm.** Każda szyna
   (`plinth-left/back/right/front`) jest w modelu prostokątnym klockiem
   wypełniającym całą szerokość 70 mm × wysokość 100 mm — żaden z trzech
   wymiarów bryły nie odpowiada grubości sklejki (18 mm), więc **nie da się
   tego wyciąć z pojedynczej płyty tak, jak jest narysowane**. To placeholder
   obrysu (poprawny do oceny wizualnej: głębokość cofnięcia, wysokość,
   zgodność łuku z narożnikiem korpusu), nie gotowa konstrukcja. Do wyboru
   przed cięciem: (a) pojedyncza ścianka 18 mm stojąca na rąb w obrębie pasma
   70 mm — najlżejsza, ale sprawdzić ugięcie dna korpusu opartego wtedy tylko
   na wąskiej krawędzi; (b) skrzynka skrętna — dwie ścianki 18 mm
   (zewnętrzna + wewnętrzna) plus żebra poprzeczne; (c) inna konstrukcja.
   Masa cokołu w bieżącym podsumowaniu (`summary()`) jest orientacyjna —
   liczona tą samą heurystyką „grubość = najmniejszy z trzech wymiarów", co
   przy bryle pełnej nie odpowiada żadnej z tych realnych konstrukcji.
2. **Prawy bok wisi nad cokołem bez oparcia.** Prawy pion (`R-side`, lico
   zewnętrzne x = 1782–1800) stoi 2 mm na zewnątrz od krawędzi `plinth-right`
   (kończy się na x = 1780) — cały jego przekrój (18 mm) nie ma nic
   bezpośrednio pod spodem na całej głębokości 396 mm, bo rama jest tu cofnięta
   pod listwę. Obciążenie musi się przenieść bokiem, przez płytę dna, do
   miejsca, gdzie rama faktycznie podpiera. Przy tym niewielkim wysięgu
   (18–20 mm) to prawdopodobnie bez znaczenia, ale wymaga potwierdzenia przez
   joinery-specialist/qa-inspector, nie założenia.
3. **Korpus nie jest niczym przypięty do cokołu** — dziś tylko siada na górnej
   krawędzi ramy (sprawdzone automatycznie: brak szczeliny). Analogicznie do
   złącza wrąb ↔ płyta z sekcji 2: sam ciężar czy dodać śruby/kołki
   pozycjonujące między dnem korpusu a ramą?

## 4. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Piony (mid-1, mid-2, R-side) | wzdłużne (Z) | nośność na wyboczenie |
| Lewy bok (grzbiet + zęby) | wzdłużne (Z) | jak pozostałe piony |
| Półki (przęsło 1, 2) | wzdłużne (X) | sztywność na rozpiętości 526 mm |
| Nos + półka (przęsło 0, scalone) | dowolne | złożony obrys |
| Plecy | wzdłużne (Z) | usztywnienie na skręcanie |
| Cokół (szyny proste) | wzdłużne | jak pozostałe piony/ramy |
| Cokół (narożnik) | dowolne | złożony obrys (łuk) |

Każdy element ma zadeklarowany `grain_direction` w modelu — sprawdzane automatycznie.

## 5. Do rozstrzygnięcia

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
5. **Konstrukcja ramy cokołu (runda 4)** — dziś bryła pełna, nie płyty 18 mm.
   Wymaga rozstrzygnięcia przed cięciem/nestingiem — patrz sekcja 3.
6. **Prawy bok bez oparcia na cokole (runda 4)** — wysięg 18–20 mm bez
   podparcia bezpośredniego, patrz sekcja 3.
7. **Mocowanie korpus ↔ cokół (runda 4)** — dziś sam docisk ciężarem, bez
   żadnych śrub/kołków pozycjonujących. Patrz sekcja 3.
8. **Szerokość ramy cokołu (70 mm, runda 4)** — mój dobór inżynierski, nie
   decyzja klienta. Patrz sekcja 3.
9. **Masa 104,6 kg** (same płyty, bez okuć — i bez uwzględnienia docelowej
   konstrukcji cokołu, patrz punkt 5; 107 → 101 → 102 → 104,6 kg w kolejnych
   rundach) — montaż w dwie osoby, do zapisania w instrukcji.
