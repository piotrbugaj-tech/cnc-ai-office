# Regał R150 — brief

**Klient:** wewnętrzny / własny
**Runda:** 1 — bryła do oceny
**Data:** 2026-07-29
**Status:** czeka na akceptację bryły

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
2. **Montaż** — rozbieralny na śruby. Czopy pozycjonują, śruby M6 z mimośrodem
   beczkowym skręcają. Regał można rozłożyć i złożyć wielokrotnie.
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

## 6. Poza zakresem rundy 1

DXF z warstwami wg CLAUDE.md, cut-list CSV, BOM, nesting z kontrolą waste < 12 %,
G-code, instrukcja montażu, karta produktu.
