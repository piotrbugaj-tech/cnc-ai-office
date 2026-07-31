# Regał R150 — brief

**Klient:** wewnętrzny / własny
**Runda:** 6 — rozstrzygnięcie wszystkich otwartych decyzji
**Data:** 2026-07-31
**Status:** czeka na akceptację bryły. Blokada z łbami śrub zamknięta; otwarty jeden punkt (proporcja wrębu 310/86) — patrz §5

## 1. Zakres

Regał ze sklejki brzozowej 18 mm, cięty na gotowo na CNC, do samodzielnego montażu
przez klienta.

| Parametr | Wartość |
|---|---|
| Szerokość | 1800 mm |
| Wysokość | 2000 mm (korpus 1900 + cokół 100) |
| Głębokość | 400 mm |
| Materiał nośny | sklejka brzozowa 18 mm |
| Zaoblenie | przedni lewy narożnik, R150, cała wysokość (korpus i cokół) |
| Cokół | 100 mm, cofnięty 22 mm od krawędzi korpusu na wszystkich czterech bokach |
| Poziomy | 6 × jedna płyta pełnej szerokości 1800 mm (krata — runda 6) |
| Montaż | rozbieralny na śruby (bez kleju) |

## 2. Decyzje klienta

Trzy kwestie rozstrzygnięte przed projektowaniem:

1. **Geometria zaoblenia** — zaokrąglony jest *przedni lewy narożnik*, nie całe lewe
   zakończenie. Łuk owija front na lewy bok; lewa ścianka boczna pozostaje płaska.
2. **Montaż** — rozbieralny na śruby. Od rundy 3: wrąb oporowy pozycjonuje i
   przenosi ciężar, śruby M6 z mimośrodem beczkowym (gwint żeński, nie wkręt)
   dociskają i przenoszą wyrywanie. Regał można rozłożyć i złożyć wielokrotnie.
3. **Kolejność prac** — najpierw bryła do obejrzenia i oceny, dokumentacja
   produkcyjna dopiero po akceptacji.

## 3. Ograniczenie środowiska

Pierwotnie zakładano uruchomienie Blendera na Mac mini przez computer use i pracę
przez jego MCP. **Z sesji, w której powstał ten projekt, było to niewykonalne:**

- sesja działała w zdalnym kontenerze Linux, nie na Mac mini,
- w sesji nie było narzędzia computer use,
- wśród podłączonych konektorów MCP (Gmail, Google Calendar, Google Drive,
  Higgsfield, Spotify) nie było Blendera,
- kontener nie miał binarki `blender` ani modułu `bpy`.

Dlatego model 3D dostarczono jako **skrypt `bpy` do uruchomienia po stronie
użytkownika** (`design/build_shelf_blender.py`), a do natychmiastowej oceny —
samodzielny podgląd HTML generowany bez Blendera (`design/preview.html`).

## 4. Rozwiązanie

Konstrukcja kratowa (od rundy 6):

- **Cztery piony** pełnej wysokości, wszystkie jako grzebienie: lewy bok,
  mid-1, mid-2 mają wrąb przelotowy na każdym z 6 poziomów (grzbiet 86 mm
  z tyłu + zęby od frontu). Prawy bok jako jedyny ma wrąb oporowy 5 mm na
  licu wewnętrznym — jego lico zewnętrzne zostaje wolne pod łby śrub.
- **Sześć poziomów, każdy jako jedna ciągła płyta 1800 mm** przechodząca
  przez wszystkie trzy piony pośrednie. Światło międzypółkowe 358,4 mm.
- **Trzy przęsła po 526 mm** światła — bezpieczna rozpiętość dla 18 mm.
- **Nos zaoblony** scalony z płytą poziomu, pełny promień R150, bez żeber
  i bez poszycia giętego (usunięte w rundzie 2).
- **Plecy** ze sklejki 4 mm — przykręcane do grzbietów pionów, trzymają
  płyty przed wysunięciem do przodu.
- **Cokół** 100 mm z płyt 18 mm na rąb, cofnięty 22 mm ze wszystkich stron,
  z 3 żebrami poprzecznymi, przykręcony do dna 10 kotwami M6.
- **Okucia:** 12 śrub M6 (prawy bok) + 10 kotew M6 (korpus↔cokół), wszystkie
  w mimośrody beczkowe Ø10 × 13 mm — gwint żeński, nie wkręt.

Szczegóły stolarki: `design/joinery-notes.md`.

## 5. Otwarte kwestie

Runda 6 zamknęła wszystkie punkty poza jednym.

1. **Proporcja wrębu przelotowego 310 / 86 mm** — mój dobór inżynierski, nie
   specyfikacja klienta. Do potwierdzenia przez joinery-specialist przed
   cięciem. Patrz `design/joinery-notes.md` §6.

**Zamknięte w rundzie 6:** dostęp dla łba śruby M6 (był blokerem), pięć
brakujących wymiarów okucia, głębokość wrębu oporowego, liczba śrub,
mocowanie złącza wrąb↔płyta, konstrukcja ramy cokołu, kotwienie
korpus↔cokół, nawis prawego boku nad cokołem. Szczegóły z uzasadnieniem:
`design/joinery-notes.md`.

## 6. Poza zakresem rundy 1–6

DXF z warstwami wg CLAUDE.md, cut-list CSV, BOM, nesting z kontrolą waste < 12 %,
G-code, instrukcja montażu, karta produktu.

## 7. Runda 2 — uproszczenie nosa

Klient poprosił o usunięcie poszycia giętego i żeber nosa bez odpowiednika
w reszcie regału.

**Diagnoza:** `N_RIBS=11` dawało rozstaw żeber dokładnie o połowę mniejszy niż
rozstaw półek — 6 z 11 żeber leżało dokładnie na wysokości prawdziwych półek,
5 siedziało na wysokościach pośrednich bez żadnego odpowiednika. Usunięto te 5,
a pozostałe 6 przebudowano tak, by wynikały wprost z poziomów półek (nie z
osobnego rozstawu), co eliminuje możliwość ponownego rozjechania się w
przyszłości.

**Decyzje klienta** (`AskUserQuestion`):

1. Bez poszycia żebra rozciągnięte do pełnego R150 (były cofnięte o 4 mm pod
   poszycie).
2. Żebro nosa i sąsiadująca półka przęsła 0 scalone w jeden element na każdym
   z 6 poziomów.
3. Lewy bok zostaje jedną, ciągłą płytą z wrębami przelotowymi, przez które
   przechodzi scalona płyta (nie rozpada się na 5 osobnych słupków).

**Rozwiązanie mechaniczne wrębu — wyprowadzone przeze mnie, nie zadane wprost:**
scalona płyta zajmuje pełną głębokość (0–396 mm), więc wrąb otwarty na całej
głębokości fizycznie przecina bok na wylot — nie różniłoby się to geometrycznie
od „5 słupków". Żeby bok faktycznie pozostał jedną sztuką materiału, wrąb jest
**zamknięty od tyłu**: otwarty od frontu na 310 mm, zamknięty na tylnych 86 mm
ciągłym grzbietem. Bok = 1 grzbiet (pełna wysokość, 86 mm głęboki) + 5 „zębów"
między wrębami (378,4 mm wysokości każdy, 310 mm głęboki). Test kolizji
potwierdza zero przenikań między grzbietem/zębami a sześcioma scalonymi płytami.

**To wymaga przeglądu przed cięciem** — konkretne milimetry (310/86) i brak
mocowania w złączu wrąb↔płyta (obecnie czysty wcisk, bez śrub) to moje
techniczne rozwinięcie decyzji klienta, nie jego dosłowna specyfikacja.
Szczegóły: `design/joinery-notes.md`.

**Środowisko (potwierdzone ponownie w rundzie 2):** użytkownik wskazał, że
w innej sesji (aplikacja desktopowa na Macu) Blender MCP działa i jest
włączony. To nie zmienia sytuacji w tej sesji — `hostname vm`, `Linux`,
port 9876 nieosiągalny, żadne narzędzie blenderowe nie ładuje się przez
`ToolSearch`. Dwie sesje pod tym samym kontem mają rozłączne zestawy narzędzi.
Model nadal dostarczany jako `design/build_shelf_blender.py` do wklejenia.

**Wynik:** 91 elementów (było 110), 60 śrub M6 (było 72), masa netto 101 kg
(było 107 kg). 16/16 testów geometrii przechodzi, w tym zero kolizji.

## 8. Runda 3 — złącza półka↔pion bez czopów

Po wyjaśnieniu, jak działa złącze czop/gniazdo + śruba (raport w rozmowie),
klient zdecydował o dalszym uproszczeniu: zrezygnować z czopa na rzecz
najprostszego rozwiązania — pod warunkiem, że da się je wywiercić w tym samym
ustawieniu co cięcie konturu na CNC, i że jest DIY-friendly (cel całego
projektu to własnoręczne złożenie regału).

**Kluczowe zastrzeżenie klienta:** żadnych wkrętów wkręcających się
bezpośrednio w płytę — mają ścierać się przy wielokrotnym montażu/demontażu.
Śruba ma wkręcać się w osadzony **gwint żeński** (mimośród beczkowy), nie
w drewno. To zresztą już było zamodelowane od rundy 1 — mimośród beczkowy
zawsze był metalową tuleją z gwintem, nie wkrętem.

**Konsekwencja, którą trzeba było rozwiązać:** czysty styk płaski (bez czopa)
przenosi cały ciężar półki przez same 2 śruby i sklejkę wokół otworów, a nie
przez drewno na drewnie jak przy czopie. Klient wybrał (`AskUserQuestion`)
dodanie **płytkiego wrębu oporowego** (5 mm) zamiast akceptować to ryzyko
wprost — prosty rowek frezowany na całą głębokość pionu, bez kieszeni, bez
dog-bone'ów (nie ma wewnętrznych narożników do obejścia).

Piony pośrednie mają wrąb na obu licach (rdzeń 8 mm na wysokości wrębu); prawy
bok tylko na licu wewnętrznym (rdzeń 13 mm), zewnętrzne lico zostaje płaskie
na całej wysokości. Każdy pion to w modelu seria brył — pełna grubość między
półkami, zredukowana na wysokości każdej półki — fizycznie jedna deska.

**Środowisko:** bez zmian względem rundy 2 — nadal skrypt do wklejenia,
Blender MCP nadal nieosiągalny z tej sesji.

**Wynik:** 61 elementów weryfikacyjnych (31 rzeczywistych sztuk + rozkład
pionów na bryły kontrolne), 60 śrub M6 (bez zmian), masa netto 102 kg
(nieznaczny wzrost — półki sięgają teraz 5 mm dalej w każdy wrąb). 13/13 testów
przechodzi, w tym zero kolizji **bez żadnych wyjątków** (dawniej czop/gniazdo
były jawnie pomijane w teście jako "z założenia wspólne" — teraz nic nie jest
pomijane, to prawdziwa weryfikacja dopasowania wrębu).

## 9. Runda 4 — rysunek rozmieszczenia śrub i cokół pod ścianę

Klient poprosił o dwie rzeczy: (A) rysunek techniczny pokazujący, gdzie
faktycznie są śruby — żaden z dotychczasowych widoków nie pokazywał ich
pozycji X/Z na całym korpusie; (B) cokół — regał stoi tyłem i prawym bokiem
do ściany, gdzie biegnie listwa przypodłogowa 85 mm wys. × 20 mm gł.
(odstaje od ściany o tyle); cokół ma podnieść cały regał, żeby dało się go
dosunąć do ściany mimo listwy.

### A. Rysunek rozmieszczenia śrub

Nowy widok „Rozmieszczenie śrub" — rzut z przodu, każdy odrębny klaster
(X, Z) oznaczony kółkiem z liczbą śrub w tym miejscu. Piony pośrednie: **4**
śruby na złącze (wrąb dwustronny, patrz `design/joinery-notes.md` §1); prawy
bok: **2** śruby na złącze (wrąb jednostronny). Lewy bok/nos nie ma śrub w
ogóle — to złącze wrębowe (grzebień), nie skręcane.

### B. Cokół

**Decyzje klienta (`AskUserQuestion`):**

1. Budżet wysokości — korpus kurczy się, żeby korpus + cokół = dokładnie
   2000 mm (nie: cokół dokładany na 2000 mm korpusu → 2100 mm całości).
   Korpus: 2000 → **1900 mm**.
2. Wysokość cokołu — 85 mm listwy + 15 mm luzu = **100 mm**.

Cokół to rama (nie pełna płyta), cofnięta 20 mm od tylnej i prawej ściany pod
listwę przypodłogową. Przedni-lewy narożnik podąża za tym samym łukiem R150
co korpus powyżej — sprawdzone wprost, że prostokątny narożnik wystawałby
62 mm poza promień R150 (róg (0,0) leży 212 mm od środka łuku, przy R = 150).

**To wymaga przeglądu przed cięciem** — trzy rzeczy w szczególności:
szerokość ramy (70 mm) to mój dobór inżynierski, nie decyzja klienta; rama
jest dziś zamodelowana jako bryła pełna, nie jako realne płyty 18 mm (żaden
z trzech wymiarów szyny nie odpowiada grubości sklejki — do rozstrzygnięcia,
jaka to ma być konstrukcja); prawy bok korpusu wisi nad cokołem bez
bezpośredniego oparcia na całej głębokości (cofnięcie pod listwę zostawia
18–20 mm wysięgu). Szczegóły: `design/joinery-notes.md` §3.

**Środowisko:** bez zmian — nadal skrypt `build_shelf_blender.py` do
wklejenia, Blender MCP nadal nieosiągalny z tej sesji.

**Wynik:** 66 elementów, 60 śrub M6 (bez zmian), masa netto 104,6 kg. Korpus
1900 mm (było 2000), światło międzypółkowe 358,4 mm (było 378,4 mm). 16/16
testów geometrii przechodzi, w tym dwa nowe testy specyficzne dla cokołu
(narożnik mieści się pod łukiem R150; korpus siada dokładnie na górze cokołu
bez szczeliny).

## 10. Runda 5 — cokół cofnięty jednolicie + dno/wieniec pełnej szerokości

Dwa niezależne życzenia klienta: (A) cokół cofnięty 22 mm od krawędzi
regału **z każdej strony** (poprawka literówki — pierwsza wiadomość mówiła
o 220 mm, co przy głębokości 400 mm było niewykonalne; klient potwierdził
22 mm); (B) górna i dolna półka mają być jednym kawałkiem płyty na całą
szerokość, żeby usztywnić konstrukcję (dziś rozwiązane tak samo jak w
środku regału — osobne półki na przęsło).

### A. Cokół cofnięty jednolicie 22 mm

Zastępuje asymetrię z rundy 4 (0 mm z przodu/lewej, 20 mm z tyłu/prawej pod
listwę) jednym cofnięciem na wszystkich czterech bokach. 22 mm > 20 mm
listwy przypodłogowej, więc rama nadal ją omija (2 mm zapasu — sprawdzane
automatycznie). Narożnik pod noskiem podąża za tym samym łukiem co korpus,
tylko wspólśrodkowo pomniejszonym o 22 mm (R150 → R128 zewnętrzny promień
ramy). Szerokość samych szyn (70 mm) bez zmian — to mój dobór inżynierski
z rundy 4, nadal wymaga przeglądu.

### B. Dno i wieniec — jedna płyta pełnej szerokości

Mechanizm: oba piony pośrednie (mid-1, mid-2) dostają na poziomie dna i
wieńca **ten sam wrąb przelotowy stop-notch**, co lewy bok (runda 2) —
otwarty na 310 mm od frontu, zamknięty grzbietem 86 mm z tyłu. Na czterech
środkowych poziomach — bez zmian, nadal wrąb oporowy i osobne półki na
przęsło (klient nie prosił o ich scalenie). Płyta dna/wieńca ma teraz trzy
wcięcia (lewy bok + mid-1 + mid-2) i kończy się normalnie w wrębie
prawego boku.

**Skutek uboczny — 16 śrub mniej, blokada z rundy 4 częściowo złagodzona:**
mid-1/mid-2 nie mają już śrub na poziomie dna/wieńca (złącze wrębowe, nie
skręcane, jak lewy bok) — **60 → 44 śruby M6**. To usuwa 16 z 48
przypadków „łeb śruby nie ma gdzie usiąść" zgłoszonych w rundzie 4;
pozostałe **32 (cztery środkowe poziomy) nadal czekają na decyzję
joinery-specialist** — patrz `design/joinery-notes.md` §1 i §6, pkt 0.

**Środowisko:** bez zmian — nadal skrypt `build_shelf_blender.py` do
wklejenia, Blender MCP nadal nieosiągalny z tej sesji.

**Wynik:** 62 elementy (było 66), 44 śruby M6 (było 60), masa netto 104,3 kg
(było 104,6 kg — lekki spadek mimo cokolu, bo wręby przelotowe w dnie/wieńcu
nie mają materiału tam, gdzie dawniej był pełny próg wrębu oporowego). 19/19
testów geometrii przechodzi, w tym dwa nowe: dno/wieniec poprawnie omijają
grzbiety wszystkich trzech pionów pośrednich; brak srub na mid-1/mid-2 przy
dnie/wieńcu z poprawną łączną liczbą 44.

## 11. Runda 6 — rozstrzygnięcie wszystkich otwartych decyzji

Klient: „znajdź odpowiedzi na wszystkie decyzje do rozstrzygnięcia".

### Kluczowe odkrycie — wrąb dwustronny łamał regułę warsztatową

Piony pośrednie miały wrąb oporowy 5 mm z **obu** stron na tej samej
wysokości: 10 z 18 mm = **56 % usuniętego materiału**, rdzeń 8 mm. Praktyka
warsztatowa dla wrębu/dado dopuszcza ≤ 1/3 grubości na stronę i **nigdy
więcej niż 1/2 łącznie**. To był realny błąd konstrukcyjny — niezależny od
zgłoszonego wcześniej problemu z łbem śruby, ale z tym samym rozwiązaniem.

### Rozwiązanie — wrąb przelotowy na wszystkich pionach

Piony pośrednie nie mają już wrębu oporowego: na każdym z 6 poziomów mają
wrąb przelotowy (ten sam, co lewy bok od rundy 2). W konsekwencji **każdy
poziom to jedna ciągła płyta 1800 mm** — rozszerzenie tego, o co klient
poprosił dla dna i wieńca w rundzie 5. Konstrukcja jest teraz kratą:
4 grzebienie pionowe + 6 ciągłych płyt.

Efekty: zero ścieniania pionów pośrednich; śruby **60 → 12** (zostały tylko
na prawym boku, gdzie lico zewnętrzne jest wolne i łeb ma na czym usiąść);
blokada z rundy 4/5 zamknięta w całości.

### Cokół — z bryły na realną konstrukcję

Szyny były modelowane jako lite klocki 70 × 100 mm, których nie dało się
wyciąć z płyty. Teraz: rama z płyt **18 mm na rąb**, 100 mm wysokości, plus
**3 żebra poprzeczne** pod lewym bokiem, mid-1 i mid-2 (bez nich płyta dna
pracowałaby na zginanie w świetle do 526 mm). Narożnik to pas 18 mm
współśrodkowy z łukiem korpusu (R128 → R110). Korpus **przykręcony** do
cokołu — 10 kotew M6 w mimośrody osadzone w szynach.

### Wymiary okucia — ustalone

Mimośród beczkowy M6 to standard **Ø10 × 13 mm**, więc otwór w płycie 18 mm
jest **ślepy** (zostaje 5 mm), nie przelotowy. Oś mimośrodu 35 mm od czoła
płyty, otwór przelotowy pod M6 Ø6,5, łeb walcowy imbusowy na licu, śruba
M6 × 45 mm.

**Wynik:** 57 elementów (było 62), 12 śrub M6 + 10 kotew do cokołu (było 44),
masa netto 105,2 kg. **20/20 testów** geometrii, w tym nowy test egzekwujący
regułę 1/3 i test trafiania kotew w materiał ramy cokołu.
