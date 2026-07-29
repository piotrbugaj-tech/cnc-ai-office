# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
Runda 1: geometria. Wymiary gniazd i dog-bone'ów wchodzą do DXF w rundzie 2.

## Status

Bryła czeka na akceptację. Stolarka poniżej jest zamodelowana i przetestowana
geometrycznie (16/16 testów w `checks.py`), ale nie została jeszcze zwalidowana
przez `qa-inspector` ani `safety-officer`.

## 1. Złącze półka ↔ pion

Podstawowe złącze konstrukcji, powtarzalne dla wszystkich **36 końców półek**.

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
Stąd trzy przypadki:

- **Lewy bok (x = 150)** — czop przelotowy 18 mm, licuje z lewym licem pionu.
  Zakończenie ukryte w zamkniętej komorze nosa, więc nie musi być estetyczne.
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

## 2. Nos zaoblony

| Element | Wartość |
|---|---|
| Promień zewnętrzny | R150, środek (150, 150) |
| Promień profilu żebra | R146 (= R150 − grubość poszycia) |
| Żebra | 11 szt., rozstaw 198,2 mm |
| Poszycie | sklejka gięta 4 mm, rozwinięcie 482 × 2000 mm |

Łuk jest **styczny** do frontu w x = 150 i do lewego boku w y = 150 — przechodzi
w płaszczyzny bez załamania. Sprawdzane automatycznie.

Lewy bok konstrukcyjny stoi dokładnie w punkcie styczności, więc pas poszycia kończy
się na arrisie x = 150, y = 0, licując z frontem pionu. Styk czyta się jako jedna
linia, nie jako nakładka.

### Żebra są pełne, nie odciążone

W planie były wstęgi ~50 mm wzdłuż profilu. Odrzucone: 11 pełnych żeber to 0,58 m²
sklejki i ~7 kg, odciążenie oszczędziłoby ~4 kg na regale ważącym 107 kg, a zabrałoby
powierzchnię do wkręcania poszycia. Żebra są niewidoczne i mieszczą się w odpadach
z innych elementów, więc pełny profil jest tańszy w robocie i lepszy konstrukcyjnie.

### Kierunek gięcia

Poszycie gnie się wokół osi pionowej, więc **słoje lica muszą biec pionowo**.
Zwykła brzoza 4 mm na R146 jest na granicy pękania — zakładamy flexi-ply.
**Do potwierdzenia z materials-managerem.**

## 3. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Piony | wzdłużne (Z) | nośność na wyboczenie |
| Półki | wzdłużne (X) | sztywność na rozpiętości 526 mm |
| Żebra nosa | dowolne | element ukryty, obciążenie znikome |
| Poszycie | wzdłużne (Z) | oś gięcia = Z |
| Plecy | wzdłużne (Z) | usztywnienie na skręcanie |

Każdy element ma zadeklarowany `grain_direction` w modelu — sprawdzane automatycznie.

## 4. Do rozstrzygnięcia

1. **Montaż nosa** — 11 żeber + poszycie skręcane przez klienta (~40 wkrętów) czy
   moduł zmontowany fabrycznie? Wariant fabryczny psuje flat-pack.
2. **72 śruby M6** to dużo jak na samodzielny montaż. Zejście do 2 na złącze daje 36;
   czopy i tak przenoszą ścinanie, śruba pracuje głównie na wyrywanie.
3. **Cokół** — pominięty, dno leży na podłodze.
4. **Masa 107 kg** (same płyty, bez okuć) — montaż w dwie osoby, do zapisania
   w instrukcji.
