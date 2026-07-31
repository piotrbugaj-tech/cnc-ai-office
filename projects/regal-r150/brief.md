# Regał R150 — brief

**Klient:** wewnętrzny / własny
**Runda:** 4 — rysunek rozmieszczenia śrub + cokół pod ścianę
**Data:** 2026-07-31
**Status:** czeka na akceptację bryły i przegląd wrębów oraz konstrukcji cokołu (joinery-specialist / qa-inspector)

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
| Cokół | 100 mm, cofnięty 20 mm od tylnej/prawej ściany pod listwę przypodłogową |
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

- **Cztery piony** pełnej wysokości: lewy bok to grzebień (grzbiet + 5 zębów,
  wrąb przelotowy — patrz runda 2), dalej dwa piony pośrednie i prawy bok
  (oba na wrębie oporowym pod półkami — patrz runda 3).
- **Trzy przęsła po 526 mm** światła — bezpieczna rozpiętość dla półki 18 mm o
  głębokości 400 mm.
- **Sześć poziomów** (dno, 4 półki, wieniec), światło międzypółkowe 358,4 mm
  (korpus 1900 mm — patrz runda 4).
- **Nos zaoblony** — scalony z półką przęsła 0 na każdym poziomie, pełny
  promień R150, bez żeber i bez poszycia giętego (usunięte w rundzie 2).
- **Plecy** ze sklejki 4 mm, cztery płyty (nos + trzy przęsła).
- **Cokół** 100 mm, cofnięty pod listwę przypodłogową przy tylnej i prawej
  ścianie — patrz runda 4.

Szczegóły stolarki: `design/joinery-notes.md`.

## 5. Otwarte kwestie

Zaktualizowane po rundzie 4 — poprzednie punkty tej sekcji dotyczyły żeber
nosa i poszycia giętego usuniętych w rundzie 2 (nieaktualne) albo zostały
rozstrzygnięte w kolejnych rundach (liczba śrub: 60 szt., 2 na złącze;
cokół: dodany w rundzie 4). Aktualne otwarte punkty:

1. **Konstrukcja ramy cokołu** — dziś bryła pełna w modelu, nie realne płyty
   18 mm. Patrz `design/joinery-notes.md` §3, pkt 1.
2. **Oparcie prawego boku na cokole** — wysięg 18–20 mm bez podparcia
   bezpośredniego. Patrz `design/joinery-notes.md` §3, pkt 2.
3. **Mocowanie korpus ↔ cokół** — dziś sam docisk ciężarem, bez śrub/kołków.
   Patrz `design/joinery-notes.md` §3, pkt 3.
4. **Mocowanie złącza wrąb ↔ płyta (nos)** — czysty wcisk, bez śrub
   retencyjnych. Patrz `design/joinery-notes.md` §2.
5. **[BLOKER] Dostęp dla łba śruby na pionach pośrednich** — wyszło przy
   próbie wykonania zbliżenia na mocowanie śrubowe (prośba klienta po
   rundzie 4). Na wysokości wrębu oba lica rdzenia pionu są zakryte wpustami
   sąsiednich półek, więc łeb M6 nie ma na czym usiąść — dotyczy 48 z 60
   śrub. Dodatkowo brakuje pięciu wymiarów okucia, których `PARAMS` nigdy
   nie zawierał. Patrz `design/joinery-notes.md` §1. Wstrzymuje rysunek
   detalu złącza i wiercenia w DXF.

## 6. Poza zakresem rundy 1–4

DXF z warstwami wg CLAUDE.md, cut-list CSV, BOM, nesting z kontrolą waste < 12 %,
G-code, instrukcja montażu, karta produktu. Dotyczy też docelowej konstrukcji
ramy cokołu (patrz `design/joinery-notes.md` §3, pkt 1) — obecna bryła jest
placeholderem obrysu, nie gotowym do wycięcia kształtem.

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
