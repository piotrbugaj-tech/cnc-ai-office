# Regał R150 — brief

**Klient:** wewnętrzny / własny
**Runda:** 3 — złącza półka↔pion bez czopów
**Data:** 2026-07-29
**Status:** czeka na akceptację bryły i przegląd wrębów (joinery-specialist / qa-inspector)

## 1. Zakres

Regał ze sklejki brzozowej 18 mm, cięty na gotowo na CNC, do samodzielnego montażu
przez klienta.

| Parametr | Wartość |
|---|---|
| Szerokość | 1800 mm |
| Wysokość | 2000 mm |
| Głębokość | 400 mm |
| Materiał nośny | sklejka brzozowa 18 mm |
| Zaoblenie | przedni lewy narożnik, R150, cała wysokość |
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

- **Cztery piony** pełnej wysokości: lewy bok konstrukcyjny stoi dokładnie w punkcie
  styczności łuku (x = 150), dalej dwa piony pośrednie i prawy bok.
- **Trzy przęsła po 526 mm** światła — bezpieczna rozpiętość dla półki 18 mm o
  głębokości 400 mm.
- **Sześć poziomów** (dno, 4 półki, wieniec), światło międzypółkowe 378,4 mm.
- **Nos zaoblony** — 11 żeber profilowych w rozstawie ~198 mm, owiniętych pasem
  sklejki giętej 4 mm. Strefa zamknięta, czyta się jako lite zaokrąglone zakończenie.
- **Plecy** ze sklejki 4 mm, cztery płyty (nos + trzy przęsła).

Szczegóły stolarki: `design/joinery-notes.md`.

## 5. Otwarte kwestie

Wymagają decyzji przed uruchomieniem dokumentacji:

1. **Montaż nosa** — 11 żeber i poszycie skręcane przez klienta (~40 wkrętów, żmudne)
   czy moduł zmontowany fabrycznie (lepszy montaż, paczka przestaje być płaska)?
2. **Liczba śrub** — 72 szt. (4 na złącze) czy 36 szt. (2 na złącze)?
3. **Cokół** — brak (dno na podłodze) czy cofnięty ~80 mm?
4. **Sklejka gięta** — poszycie na R146 wymaga flexi-ply; do potwierdzenia
   dostępności i ceny z materials-managerem.

## 6. Poza zakresem rundy 1–3

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
