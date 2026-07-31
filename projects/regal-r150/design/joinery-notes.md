# Regał R150 — decyzje stolarskie

Zgodnie z CLAUDE.md § 9 — dokumentacja decyzji technicznych.
Runda 6: rozstrzygnięcie wszystkich otwartych punktów.

## Status

Bryła czeka na akceptację. Stolarka jest zamodelowana i przetestowana
geometrycznie (**20/20 testów** w `checks.py`, zero kolizji na 57 elementach,
bez wyjątków), ale **nie została jeszcze zwalidowana przez `qa-inspector`
ani `safety-officer`**.

**Blokada z rundy 4/5 (łeb śruby nie ma gdzie usiąść) jest zamknięta.**
Otwarty pozostaje **jeden** punkt: proporcja wrębu przelotowego 310/86 mm
(§ 2) — patrz § 6.

---

## 1. Złącze półka ↔ pion — runda 6: koniec wrębu dwustronnego

### Co było nie tak (dwa niezależne problemy, jedno rozwiązanie)

**Problem A — reguła 1/3.** Piony pośrednie (`mid-1`, `mid-2`) miały wrąb
oporowy 5 mm na **obu** licach, na tej samej wysokości. Praktyka warsztatowa
dla wrębu/dado: głębokość **≤ 1/3 grubości** materiału, i **nigdy więcej niż
1/2 łącznie** — powyżej tego płyta traci integralność strukturalną. Nasz
przypadek: 5 + 5 = 10 mm z 18 mm = **56 % usuniętego materiału**, rdzeń 8 mm.
Poza limitem. To był realny błąd konstrukcyjny, niezależny od okucia.

**Problem B — łeb śruby.** Przekrój przez pion na wysokości wrębu: 0–5 mm
wpust półki lewej, 5–13 mm rdzeń, 13–18 mm wpust półki prawej. Obie półki
biegły na pełnej głębokości, więc **oba lica rdzenia były zakryte** — łeb M6
nie miał na czym usiąść. Dotyczyło 32 z 44 śrub. Kolejność montażu też się
nie domykała: żeby dokręcić śrubę półki prawej, trzeba dostępu do lica
lewego, które zasłaniała już zamontowana półka lewa.

### Rozwiązanie

**Piony pośrednie nie mają już wrębu oporowego w ogóle** — na każdym z 6
poziomów mają **wrąb przelotowy** (stopped housed dado), dokładnie ten sam,
który od rundy 2 ma lewy bok. Konsekwencje:

| | przed (runda 5) | po (runda 6) |
|---|---|---|
| Rdzeń `mid-1`/`mid-2` na wysokości półki | 8 mm (56 % usunięte) | pełne 18 mm, brak ścieniania |
| Śruby M6 | 44, z czego 32 bez dostępu do łba | 12, wszystkie z dostępem |
| Półki | 3 osobne na poziom (4 poziomy) + 2 pełne | 6 × jedna płyta 1800 mm |

Sprawdzane automatycznie: test „żaden pion nie traci > 1/2 grubości na
wysokości wrębu".

### Gdzie zostały śruby

Tylko **prawy bok**: wrąb oporowy 5 mm na licu wewnętrznym (rdzeń 13 mm —
28 % usunięte, mieści się w regule 1/3), lico zewnętrzne płaskie na całej
wysokości. Łeb siada na nim normalnie. **12 śrub M6** (2 na poziom × 6).

Uwaga eksploatacyjna: to lico stoi przy ścianie, więc demontaż wymaga
wcześniejszego odsunięcia regału.

### Wymiary okucia — rozstrzygnięte

Brakujące pozycje z rundy 4, ustalone na podstawie handlowego standardu M6
(mimośród beczkowy Ø10 × 12–13 mm, gwint wewnętrzny Ø5,35):

| Wielkość | Wartość | Uzasadnienie |
|---|---|---|
| Mimośród beczkowy | **Ø10 × 13 mm** | standard handlowy M6 |
| Otwór pod mimośród w półce | **Ø10, ślepy, 13 mm** | w płycie 18 mm zostaje 5 mm materiału — nie wiercić na wylot |
| Odsunięcie osi mimośrodu od czoła półki | **35 mm** | ≥ 3 × Ø otworu od czoła, żeby nie wyrwać czoła sklejki |
| Otwór przelotowy pod M6 w pionie | **Ø6,5** | luz montażowy 0,5 mm na M6 |
| Rodzaj łba | **walcowy z gniazdem imbusowym, na licu** | lico prawego boku jest wolne — nie trzeba pogłębiacza ani łba stożkowego |
| Długość śruby M6 | **45 mm** | 18 (pion) + 35 (do osi mimośrodu) − 8 (połowa Ø10) ≈ 45 |

### Rozważone i odrzucone warianty (dla protokołu)

- **Łeb stożkowy wpuszczony w dno wrębu** — DIN 7991 M6 ma łeb Ø12 × 3,3 mm;
  w rdzeniu 8 mm zostawałoby 4,7 mm, a pasmo wrębu ma tylko 18,1 mm wysokości.
  Odrzucone: nie rozwiązuje kolejności montażu (żeby dokręcić, i tak trzeba
  dostępu do lica).
- **Gniazdo walcowe pod łeb imbusowy (Ø11 × 6 mm)** — w rdzeniu 8 mm
  zostają 2 mm. Odrzucone jako niewykonalne.
- **Jedna śruba przelotowa na dwa mimośrody** — działa mechanicznie, ale
  wymaga dokręcania przez obracanie mimośrodów, co jest niepewne w montażu
  DIY. Odrzucone na rzecz prostszego rozwiązania.
- **Odwrócenie złącza (mimośród w pionie)** — insert M6 ma ~12 mm, a rdzeń
  miał 8 mm; insert przebiłby na drugą stronę. Odrzucone.

---

## 2. Nos zaoblony i wrąb przelotowy — runda 2, rozszerzony w rundzie 6

Runda 1 miała 11 żeber owiniętych sklejką giętą 4 mm; klient poprosił o
usunięcie poszycia i żeber bez odpowiednika. Diagnoza: rozstaw żeber był
dokładnie połową rozstawu półek — 5 z 11 siedziało na wysokościach
pośrednich bez odpowiednika. Usunięte; pozostałe wyprowadzone wprost z
`level_z`, więc nie mogą się już rozjechać.

Łuk **R150**, środek (150, 150), styczny do frontu w x = 150 i do lewego
boku w y = 150 — przechodzi w płaszczyzny bez załamania. Sprawdzane
automatycznie.

### Wrąb przelotowy (stopped housed dado)

Klient wybrał „wręby przelotowe, bok zostaje jedną płytą" zamiast „5 osobnych
słupków". Płyta biegnie na pełnej głębokości (0–396 mm), więc wrąb otwarty na
całą głębokość przeciąłby pion na wylot — geometrycznie to byłyby osobne
słupki. Dlatego wrąb jest **zamknięty od tyłu**:

| Element | Wartość |
|---|---|
| Otwarcie wrębu (od frontu) | 310 mm — tu płyta swobodnie przechodzi |
| Grzbiet (zamknięty, z tyłu) | 86 mm — tu pion zostaje ciągły |
| Wysokość wrębu | 18,1 mm (grubość płyty + luz 0,1 mm) |
| Ząb (między wrębami) | 358,4 × 310 × 18 mm, 5 szt. na pion |
| Grzbiet | 1900 × 86 × 18 mm, 1 szt. na pion |

**Od rundy 6 ten sam wrąb mają wszystkie cztery piony** (lewy bok + mid-1 +
mid-2 na wszystkich poziomach; prawy bok pozostaje na wrębie oporowym).

Każdy pion to w modelu 6 brył pod wspólnym `qty_group`, ale **fizycznie to
jedna sztuka materiału** wycinana jako jeden grzebień — runda DXF musi to
zapisać jako jeden flat pattern, nie sześć części.

### Mocowanie w złączu wrąb ↔ płyta — rozstrzygnięte

Płyta siedzi w wrębie na wcisk; wrąb ją pozycjonuje i przenosi ciężar. Przed
wysunięciem do przodu trzyma ją **plecy** (sklejka 4 mm, przykręcane do
grzbietów wszystkich pionów) — grzbiet ma 86 mm głębokości, czyli
wystarczająco dużo lica do przykręcenia pleców. To wystarczy: płyta nie ma
jak wyjść do przodu, dopóki plecy są na miejscu, a plecy są i tak wymagane
do usztywnienia na skręcanie. **Bez dodatkowych śrub retencyjnych.**

---

## 3. Cokół — runda 4–6

Regał stoi **tyłem i prawym bokiem do ściany**, gdzie biegnie listwa
przypodłogowa 85 mm wys. × 20 mm gł. Bez cokołu korpus oparłby się o listwę.

### Decyzje klienta

1. **Budżet wysokości** — korpus kurczy się, żeby korpus + cokół = dokładnie
   2000 mm. Korpus 2000 → **1900 mm**; światło międzypółkowe 378,4 → **358,4 mm**.
2. **Wysokość cokołu** — 85 mm listwy + 15 mm luzu = **100 mm**.
3. **Cofnięcie** — **22 mm** jednolicie na wszystkich czterech bokach.
   22 > 20 mm listwy, więc przy ścianach nadal ją omija (2 mm zapasu,
   sprawdzane automatycznie).

### Konstrukcja — runda 6: realne płyty zamiast bryły

Do rundy 5 szyny cokołu były w modelu **litymi klockami 70 × 100 mm** —
żaden z trzech wymiarów nie odpowiadał grubości sklejki, więc nie dało się
tego wyciąć z płyty. To był placeholder obrysu, nie konstrukcja. Teraz:

| Element | Konstrukcja |
|---|---|
| Szyna przednia / tylna / lewa / prawa | płyta **18 mm ustawiona na rąb**, 100 mm wysokości |
| Narożnik | pas **18 mm** między R128 a R110 (ten sam środek co łuk korpusu) |
| Żebra poprzeczne | **3 szt.**, 18 mm, pod lewym bokiem, mid-1 i mid-2 |

Żebra są konieczne: bez nich płyta dna przenosiłaby obciążenie pionów na
zginanie w świetle między szynami (do 526 mm). Z żebrami każdy pion stoi
nad materiałem cokołu.

**Narożnik nie może być prostokątny** — róg prostokątnej ramy (0,0) leżałby
212 mm od środka łuku, czyli poza R150 korpusu. Dlatego jest to pas
współśrodkowy z łukiem korpusu, pomniejszony o cofnięcie: R150 − 22 = **R128**
zewnętrznie, R128 − 18 = **R110** wewnętrznie. Sprawdzane automatycznie.

*Uwaga wykonawcza:* pas 18 mm na łuku R128 wykonać jako kilka prostych cięciw
albo nacinany (kerf-bent) — przy 100 mm wysokości i cofnięciu 22 mm różnica
jest niewidoczna w cieniu pod korpusem.

### Kotwienie korpusu do cokołu — rozstrzygnięte

Do rundy 5 korpus **tylko stał** na cokole własnym ciężarem. Przy cofnięciu
22 mm i bocznym pchnięciu to za mało. Teraz: **10 kotew M6** — śruba
pionowo przez płytę dna (Ø6,5 przelotowy) w mimośród beczkowy osadzony w
szynie cokołu (Ø10 × 13 mm ślepy, wiercony od górnej krawędzi szyny).
Rozmieszczenie: 3 na szynie przedniej, 3 na tylnej, po 2 na bocznych.
Sprawdzane automatycznie („każda kotwa trafia w materiał ramy").

### Nawis prawego boku — rozstrzygnięte, bez zmian

Prawy pion (lico zewnętrzne x = 1782–1800) stoi 4 mm za krawędzią szyny
prawej (x = 1778), więc jego przekrój 18 mm nawisa nad pustką. **Nawis
22 mm w płycie 18 mm to zagadnienie pomijalne** — moment zginający na takim
wysięgu jest o rząd wielkości poniżej wytrzymałości sklejki, a płyta dna
jest tu ciągła (od rundy 5/6 to jedna płyta 1800 mm, nie osobna półka
przęsła). Zamykam bez zmiany konstrukcji.

---

## 4. Słoje

| Grupa | Kierunek | Uzasadnienie |
|---|---|---|
| Piony (lewy bok, mid-1, mid-2, prawy bok) | wzdłużne (Z) | nośność na wyboczenie |
| Poziomy (6 × płyta pełnej szerokości) | dowolne | złożony obrys (łuk + 3 wcięcia) |
| Plecy | wzdłużne (Z) | usztywnienie na skręcanie |
| Cokół — szyny i żebra | wzdłużne | jak pozostałe elementy ramowe |
| Cokół — narożnik | dowolne | złożony obrys (łuk) |

Każdy element ma zadeklarowany `grain_direction` — sprawdzane automatycznie.

---

## 5. Reguła 1/3 — obowiązująca kontrola

Po rundzie 6 model jest zgodny z regułą warsztatową na całej długości:

| Element | Usunięte | % grubości | Werdykt |
|---|---|---|---|
| Prawy bok (wrąb oporowy jednostronny) | 5 mm | 28 % | ✅ ≤ 1/3 |
| Lewy bok, mid-1, mid-2 (wrąb przelotowy) | — | 0 % | ✅ brak ścieniania |

`checks.py` zawiera test, który to egzekwuje — gdyby ktoś w przyszłości
pogłębił wrąb powyżej połowy grubości, testy nie przejdą.

---

## 6. Do rozstrzygnięcia

**Jeden punkt otwarty:**

1. **Proporcja wrębu przelotowego 310 / 86 mm** — to nadal mój dobór
   inżynierski, nie specyfikacja klienta. Po rundzie 6 argument za jest
   mocniejszy niż wcześniej: grzbiet jest podparty płytą co ~376 mm na całej
   wysokości (dawniej tylko na 2 poziomach), więc wyboczenie 86 mm × 18 mm
   przestaje być realnym ryzykiem. **Do potwierdzenia przez
   joinery-specialist przed cięciem.**

**Zamknięte w rundzie 6:** dostęp dla łba śruby (§ 1), wymiary okucia (§ 1),
głębokość wrębu oporowego (§ 1, § 5), liczba śrub (§ 1), mocowanie złącza
wrąb ↔ płyta (§ 2), konstrukcja ramy cokołu (§ 3), kotwienie korpus ↔ cokół
(§ 3), nawis prawego boku (§ 3), szerokość ramy cokołu (§ 3 — pojęcie
zniknęło, rama to teraz płyta 18 mm).

**Do zapisania w instrukcji montażu:** masa netto **105 kg** (same płyty,
bez okuć). Konstrukcja kratowa składa się na płasko, ale gotowy korpus jest
sztywny i ciężki — montaż w dwie osoby, docelowo na miejscu ustawienia.
