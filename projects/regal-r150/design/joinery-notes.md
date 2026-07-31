# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
Runda 5: cokół cofnięty jednolicie na wszystkich bokach + dno/wieniec jako
jedna płyta pełnej szerokości. Wymiary otworów wchodzą do DXF w kolejnej
rundzie.

## Status

Bryła czeka na akceptację. Stolarka poniżej jest zamodelowana i przetestowana
geometrycznie (19/19 testów w `checks.py`, w tym zero kolizji na 62
elementach, bez żadnych wyjątków w teście kolizji), ale **nie została jeszcze
zwalidowana przez `qa-inspector` ani `safety-officer`**.

**Sekcje 1, 2, 3 i 4 wymagają przeglądu przed cięciem** — konkretne wymiary
(głębokość wrębu oporowego 5 mm; otwarcie 310 mm / grzbiet 86 mm w lewym
boku i teraz też w mid-1/mid-2 na dwóch poziomach; szerokość ramy cokołu
70 mm) to moje techniczne rozwinięcie decyzji klienta, nie jego dosłowna
specyfikacja w milimetrach. **Sekcja 3 ma dodatkowo nierozwiązany problem
konstrukcyjny — rama cokołu jest dziś bryłą pełną, nie realnymi płytami
18 mm — patrz niżej. Sekcja 1 ma nierozwiązany BLOKER — łeb śruby M6 nie ma
gdzie usiąść na 32 z 44 śrub.**

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

### BLOKER — łeb śruby nie ma gdzie usiąść na pionach pośrednich

Wyszło przy próbie narysowania detalu złącza w powiększeniu (prośba klienta
o „zbliżenie na mocowanie śrubowe"). Dotychczasowe widoki to elewacje całej
wysokości albo mapa rozmieszczenia — w tej skali problem był niewidoczny.

Przekrój poziomy przez pion pośredni **na wysokości wrębu** (X od lewego do
prawego lica, 18 mm):

| Zakres X (lokalnie) | Co tam jest |
|---|---|
| 0–5 mm | wpust półki **lewego** przęsła (wrąb 5 mm) |
| 5–13 mm | rdzeń pionu (8 mm) |
| 13–18 mm | wpust półki **prawego** przęsła (wrąb 5 mm) |

Obie półki leżą na **tym samym poziomie** i biegną na **pełnej głębokości**
0–396 mm, więc oba lica rdzenia są zakryte wpustami na całej długości złącza.
Śruba M6 ma iść „przez pion w mimośród osadzony w czole półki", ale na tej
wysokości **nie ma dostępnego lica, na którym mógłby usiąść łeb** — startuje
albo wewnątrz wpustu półki lewej, albo wewnątrz prawej. Różne Y (140/200 dla
`+x`, 320/380 dla `-x`) rozwiązują kolizję śruba–śruba, ale nie dają dostępu
dla łba.

**Skala (po rundzie 5):** 32 z 44 śrub (piony `mid-1` i `mid-2`, po 8 na
poziom × 4 **środkowe** poziomy). Dno i wieniec (poziom 0 i 5) nie mają już
w ogóle śrub na `mid-1`/`mid-2` — runda 5 zmieniła tam złącze na wrąb
przelotowy stop-notch (jak lewy bok), więc problem zniknął razem z rabetem
na tych dwóch poziomach (16 śrub mniej). Pozostałe 12 (prawy bok, po 2 na
poziom, wszystkie 6 poziomów) są **czyste** — wrąb jest tam tylko na licu
wewnętrznym, rdzeń ma 13 mm, a lico zewnętrzne zostaje płaskie na całej
wysokości, więc łeb siada na nim normalnie. Uwaga eksploatacyjna: to lico
stoi przy ścianie, więc demontaż wymaga wcześniejszego odsunięcia regału.

Model geometryczny jest **poprawny** — `bolt_positions()` zwraca same osie
(linie środkowe), nie bryły łbów, więc `checks.py` nie miało czego wykryć.
To luka w specyfikacji okucia, nie błąd w bryle.

**Kierunki do rozstrzygnięcia przez joinery-specialist** (żaden nie jest
jeszcze wybrany — to nie jest decyzja do podjęcia przy rysowaniu):

1. **Łeb stożkowy licowany w dnie wrębu** — łeb wpuszczony w rdzeń, zakryty
   wpustem sąsiedniej półki. Montaż idzie kolejno lewa→prawa. Do sprawdzenia:
   DIN 7991 M6 ma łeb Ø12 × 3,3 mm, a pasmo wrębu ma tylko 18,1 mm wysokości
   (zostaje ~3 mm z każdej strony) i rdzeń tylko 8 mm (zostaje 4,7 mm).
   Gniazdo walcowe pod łeb imbusowy (Ø11 × 6 mm) odpada — w 8 mm rdzenia
   zostałyby 2 mm.
2. **Jedna śruba przelotowa na dwa mimośrody** — jedna M6 przez rdzeń,
   z mimośrodem w czole obu sąsiadujących półek.
3. **Odwrócenie złącza** — mimośród w pionie, śruba przez półkę.
4. **Zmiana geometrii wrębu** — np. wrąb krótszy niż pełna głębokość, żeby
   odsłonić lico rdzenia w strefie śruby.

Każdy z tych wariantów zmienia albo okucie, albo geometrię wrębu, albo
kolejność montażu — czyli wykracza poza „dorysowanie detalu".

**Runda 5 pokazuje, że wariant 4 (wrąb przelotowy zamiast oporowego) jest
wykonalny w praktyce** — to dokładnie ta sama zmiana, zastosowana na dnie
i wieńcu z innego powodu (usztywnienie, patrz sekcja 4). Nie rozstrzyga to
jednak czterech środkowych poziomów: tam wrąb oporowy nadal jest potrzebny,
bo półki tam pozostają osobnymi płytami na przęsło (klient nie prosił o ich
scalenie), a wrąb przelotowy działa tylko wtedy, gdy przez pion przechodzi
jedna ciągła płyta.

### Wymiary okucia, których nadal nie ma w modelu

Niezależnie od powyższego, detal złącza wymaga liczb, których `PARAMS` nie
zawiera i których nikt jeszcze nie ustalił:

| Wielkość | Status |
|---|---|
| Odsunięcie osi mimośrodu od czoła półki | **brak** — decyduje o długości śruby i o wytrzymałości czoła na wyrwanie |
| Otwór przelotowy pod M6 w pionie | **brak** (typowo Ø6,5) |
| Długość mimośrodu / czy otwór Ø10 jest przelotowy | **brak** — Ø10 w półce 18 mm zostawia po 4 mm materiału nad i pod otworem |
| Rodzaj łba (stożkowy / walcowy / z podkładką) | **brak** — patrz punkt 1 wyżej |
| Długość śruby M6 | **brak** — wynika z dwóch pierwszych pozycji |

Dopóki te pozycje nie są ustalone, rysunek detalu w powiększeniu byłby
rysunkiem wymyślonych wymiarów, nie dokumentacją.

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

**Runda 5 — klient poprosił o jednolite cofnięcie 22 mm na wszystkich
czterech bokach** (zamiast asymetrii z rundy 4: 0 mm z przodu/lewej, tylko
20 mm z tyłu/prawej). 22 mm > `SKIRTING_DEPTH` (20 mm), więc rama nadal
omija listwę przypodłogową — 2 mm zapasu (sprawdzane automatycznie,
`checks.py`).

Cokół to **rama, nie pełna płyta** — obrys w rzucie z góry (`PLINTH_INSET`
= 22 mm cofnięcia, `PLINTH_FRAME_W` = 70 mm szerokości szyn):

| Element | Zasięg (X, Y) mm | Funkcja |
|---|---|---|
| `plinth-left` | 22–92, 150–378 | szyna pod lewym bokiem/nosem |
| `plinth-back` | 22–1778, 308–378 | szyna pod tylną ścianą |
| `plinth-right` | 1708–1778, 22–308 | szyna pod prawym bokiem |
| `plinth-front` | 150–1708, 22–92 | szyna pod frontem |
| `plinth-corner` | łuk R128 → R58 | narożnik, wspólśrodkowy z korpusem, pomniejszony o 22 mm |

**Narożnik musi podążać za łukiem R150 (pomniejszonym o cofnięcie), nie może
być prostokątny** — sprawdzone wprost: róg prostokątnej ramy (punkt (0,0))
leżałby 212 mm od środka łuku (150, 150), czyli poza promieniem R150 korpusu
powyżej. Prostokątny narożnik wystawałby więc poza zaokrąglony nawis
korpusu. Rozwiązanie: `plinth-corner` to wycinek pierścienia między
R150 − 22 = R128 (ten sam środek co łuk korpusu, pomniejszony o cofnięcie) a
R128 − 70 = R58, więc cokół nigdzie nie wychodzi poza obrys korpusu.
Sprawdzane automatycznie (`checks.py`: „cokół mieści się pod łukiem R150").

**Szerokość ramy (70 mm, `PLINTH_FRAME_W`) to mój dobór inżynierski** — nie
została podana wprost przez klienta. Typowy zakres dla cokołu meblowego to
50–100 mm; 70 mm wybrane jako środek tego zakresu. Wymaga potwierdzenia.
Samo cofnięcie (22 mm, `PLINTH_INSET`) to natomiast wprost decyzja klienta.

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
   zewnętrzne x = 1782–1800) stoi 4 mm na zewnątrz od krawędzi `plinth-right`
   (kończy się na x = 1778 po rundzie 5) — cały jego przekrój (18 mm) nie ma
   nic bezpośrednio pod spodem na całej głębokości 396 mm, bo rama jest tu
   cofnięta pod listwę. Obciążenie musi się przenieść bokiem, przez płytę
   dna (od rundy 5 — dna, patrz sekcja 4), do miejsca, gdzie rama faktycznie
   podpiera. Przy tym niewielkim wysięgu (18–22 mm) to prawdopodobnie bez
   znaczenia, ale wymaga potwierdzenia przez joinery-specialist/qa-inspector,
   nie założenia.
3. **Korpus nie jest niczym przypięty do cokołu** — dziś tylko siada na górnej
   krawędzi ramy (sprawdzone automatycznie: brak szczeliny). Analogicznie do
   złącza wrąb ↔ płyta z sekcji 2: sam ciężar czy dodać śruby/kołki
   pozycjonujące między dnem korpusu a ramą?

## 4. Dno i wieniec — runda 5: jedna płyta pełnej szerokości

Klient: **górna i dolna półka mają być po całej szerokości jednym kawałkiem
płyty**, żeby usztywnić konstrukcję (dziś rozwiązane tak samo jak w środku
regału — osobne półki na przęsło).

### Mechanizm — ponowne użycie wrębu przelotowego z sekcji 2

Żeby jedna płyta 1800 mm mogła przejść przez **oba** piony pośrednie
(`mid-1`, `mid-2`), każdy z nich dostaje na poziomie 0 (dno) i poziomie 5
(wieniec) **dokładnie ten sam wrąb przelotowy stop-notch**, co lewy bok
(sekcja 2): otwarty na `NOTCH_DEPTH` = 310 mm od frontu (płyta przechodzi
swobodnie), zamknięty grzbietem 86 mm z tyłu (pion zostaje ciągły na tym
poziomie). Na pozostałych czterech poziomach `mid-1`/`mid-2` **bez zmian** —
nadal wrąb oporowy z obu stron (sekcja 1), bo tam półki zostają osobnymi
płytami na przęsło (klient nie prosił o ich scalenie).

Płyta dna/wieńca ma więc teraz **trzy** wcięcia zamiast jednego (lewy bok +
mid-1 + mid-2), i kończy się normalnie w jednostronnym wrębie oporowym
prawego boku — bez zmian względem pozostałych czterech poziomów.

| Element | Wartość |
|---|---|
| Wcięcia w płycie dna/wieńca | 3 (lewy bok, mid-1, mid-2), ten sam wzór co w sekcji 2 |
| Zakończenie po prawej | wrąb oporowy prawego boku, jak reszta poziomów |
| Materiał w `mid-1`/`mid-2` na tych 2 poziomach | grzbiet 86 mm gł. (bez zmian w rdzeniu poza tym) |

### Skutek uboczny — 16 śrub mniej, blokada z sekcji 1 częściowo złagodzona

Skoro `mid-1`/`mid-2` mają teraz na tych dwóch poziomach złącze wrębowe (nie
skręcane, jak lewy bok), znikają tam śruby: **60 → 44 śruby M6** (4 na
złącze × 2 piony × 2 poziomy = 16 mniej). To automatycznie usuwa 16 z 48
przypadków bloku „łeb nie ma gdzie usiąść" opisanego w sekcji 1 — pozostałe
32 (cztery środkowe poziomy) są nadal nierozstrzygnięte.

**To wykonuje wprost decyzję klienta** (jedna płyta pełnej szerokości) —
sam mechanizm (stop-notch) to ponowne użycie już zaakceptowanej/wymagającej
przeglądu techniki z sekcji 2, nie nowy wybór inżynierski. Nowy jest zakres
zastosowania (teraz też `mid-1`/`mid-2`, nie tylko lewy bok) — wymaga tego
samego przeglądu co reszta wrębu przelotowego.

## 5. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Piony (mid-1, mid-2, R-side) | wzdłużne (Z) | nośność na wyboczenie |
| Lewy bok (grzbiet + zęby) | wzdłużne (Z) | jak pozostałe piony |
| Półki (przęsło 1, 2 — cztery środkowe poziomy) | wzdłużne (X) | sztywność na rozpiętości 526 mm |
| Nos + półka (przęsło 0, scalone) | dowolne | złożony obrys |
| Dno / wieniec (pełna szerokość, runda 5) | dowolne | złożony obrys (3 wcięcia + łuk) |
| Plecy | wzdłużne (Z) | usztywnienie na skręcanie |
| Cokół (szyny proste) | wzdłużne | jak pozostałe piony/ramy |
| Cokół (narożnik) | dowolne | złożony obrys (łuk) |

Każdy element ma zadeklarowany `grain_direction` w modelu — sprawdzane automatycznie.

## 6. Do rozstrzygnięcia

**PIERWSZEŃSTWO — bloker rysunku detalu:** łeb śruby M6 nie ma dostępnego lica
na pionach pośrednich, **32 z 44 śrub** (cztery środkowe poziomy — dno/wieniec
już rozwiązane rundą 5, patrz sekcja 4) oraz brak pięciu wymiarów okucia
(odsunięcie mimośrodu, otwór przelotowy, długość mimośrodu, rodzaj łba,
długość śruby). Patrz sekcja 1. Blokuje wykonanie zbliżenia na mocowanie
śrubowe, a tym samym wiercenia w DXF.

1. **Głębokość wrębu oporowego (5 mm)** — mój dobór inżynierski, nie decyzja
   klienta podana wprost (sekcja 1). Wymaga przeglądu joinery-specialist przed
   cięciem — zwłaszcza rdzeń pionów pośrednich (8 mm) na wysokości wrębu.
2. **Wrąb w lewym boku, teraz też w mid-1/mid-2 na 2 poziomach** — moje
   rozwinięcie decyzji „wręby przelotowe" (sekcja 2), zastosowane ponownie
   w rundzie 5 (sekcja 4). Wymaga przeglądu joinery-specialist/qa-inspector
   przed cięciem.
3. **Mocowanie złącza wrąb ↔ płyta (nos, mid-1, mid-2)** — obecnie czysty
   wcisk, bez śrub, na wszystkich wrębach przelotowych. Dodać retencję czy
   polegać na tarciu?
4. **44 śruby M6** — 2 na złącze, na czterech środkowych poziomach
   (piony pośrednie i prawy bok; dno/wieniec bez śrub na piony pośrednie —
   runda 5). Skoro wrąb oporowy przenosi teraz ciężar, można rozważyć
   zejście do 1 śruby na złącze (docisk/wyrywanie nie wymaga dwóch), ale to
   zmniejsza odporność na skręcanie — do potwierdzenia razem z przeglądem
   wrębu.
5. **Konstrukcja ramy cokołu** — dziś bryła pełna, nie płyty 18 mm.
   Wymaga rozstrzygnięcia przed cięciem/nestingiem — patrz sekcja 3.
6. **Prawy bok bez oparcia na cokole** — wysięg 18–22 mm bez
   podparcia bezpośredniego, patrz sekcja 3.
7. **Mocowanie korpus ↔ cokół** — dziś sam docisk ciężarem, bez
   żadnych śrub/kołków pozycjonujących. Patrz sekcja 3.
8. **Szerokość ramy cokołu (70 mm)** — mój dobór inżynierski, nie
   decyzja klienta. Patrz sekcja 3.
9. **Masa 104,3 kg** (same płyty, bez okuć — i bez uwzględnienia docelowej
   konstrukcji cokołu, patrz punkt 5; 107 → 101 → 102 → 104,6 → 104,3 kg
   w kolejnych rundach) — montaż w dwie osoby, do zapisania w instrukcji.
