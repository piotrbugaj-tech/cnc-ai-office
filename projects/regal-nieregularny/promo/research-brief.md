# Regał „RYTM”: treatment, shot list i sound design (30 s, 16:9 + cutdown 9:16, 15 s)

## Status
Brief wykonawczy dla renderu (Blender 5.2, Cycles), montażu i dźwięku. **Produkt: finalna wersja regału wysłana do
wyceny** (repo `/home/user/cnc`: `design/layout.yaml`, `design/config.yaml`, `output/model.json`, `docs/OKUCIA.md`).
Brief **nie dotyczy** rev A z `design/uklad.json`; tamten układ jest nieaktualny.

Decyzje klienta: główna wersja 16:9, 30 s; pionowy cutdown 9:16, 15 s, **z tych samych renderów**; muzyka syntezowana
w Pythonie; nazwę produktu proponuje brief (sekcja 7.5).

Research zrobiłem przez WebSearch. WebFetch nie działał: domeny stashmedia.tv, behance.net, lbbonline.com,
andreaswannerstedt.se nie rozwiązują się w tej sesji. Wnioski opierają się na opisach z wyników wyszukiwania.
Samych filmów referencyjnych nie oglądałem.

---

## 0. Produkt w liczbach (źródło prawdy: `output/model.json`)

| | |
|---|---|
| Gabaryt | **1900 × 400 × 2018 mm** (szer. × gł. × wys.) + regulowane stopki ~12–25 mm (w scenie promo 15 mm) |
| Siatka | osiowa, moduł 100 mm; półki na poziomach 0/300/600/700/900/1200/1400/1500/1700/2000 mm, płyta 18 mm |
| Rzędy (światło) | R1 282 · R2 282 · R3 82 · R4 182 · R5 282 · R6 182 · R7 82 · R8 182 · R9 282 mm |
| **Brak boków** | 10 poziomów półek (14 płyt, półki dzielone a/b) biegnie przez całą szerokość 0–1900. Skrajne przegrody są cofnięte, a półki wystają za nie: |
| wysięg z lewej (R1→R9) | 91 · 291 · 91 · 191 · 291 · 91 · 191 · 91 · 191 mm |
| wysięg z prawej (R1→R9) | 191 · 291 · 191 · 91 · 191 · 291 · 91 · 191 · 91 mm |
| Przegrody | 41 szt. (`D<x cm>-<od cm>`, np. `D160-030`) |
| Fronty | 18 mm, **wpuszczane, zlicowane**, szczelina 2 mm; słoje frontów **poziomo** (grain = u, zgodnie z rozkrojem) |
| Drzwiczki | 9 szt. DZ01–DZ09, **17 zawiasów Blum CLIP top BLUMOTION 110°** (71B3750) wpuszczanych; DZ05 (278×78) na 1 zawiasie |
| Szuflady | 10 szt. S01–S10, skrzynki ze sklejki 18 mm, prowadnice boczne kulkowe **Hettich KA 4532 Silent System 350 mm** (pełny wysuw, cichy domyk, trzy człony teleskopu widoczne z boku) |
| Gałki | **białe, kuliste, druk 3D** (projekt właściciela); w scenie: kula Ø28 + szyjka Ø15 × 6 mm (`knob_mesh`) |
| Plecy | sklejka 6,5 mm za każdą szafką i szufladą (16 płyt); **otwarte komórki bez pleców, przez nie widać ścianę** |
| Łączenie | wkręty SPAX A2 4×50 w nawiertach CNC z fazą. **Łby są widoczne** (srebrne kropki Ø8) na półkach w otwartych komórkach |
| Materiał | **140 elementów** (55 korpus + 19 frontów + 50 części skrzynek + 16 pleców) z **8 arkuszy** 2500×1250 (6 × 18 mm + 2 × 6,5 mm), etykiety na elementach |

### Układ współrzędnych (wszystkie liczby w tym briefie)
**Układ `model.json`, mm:** X = szerokość 0 (lewy koniec półek) → 1900 (prawy), patrząc od frontu.
Y = głębokość: **0 = lico frontów i korpusu**, +Y w stronę ściany (tył korpusu 400, plecy 400–406,5, **ściana Y ≈ 409,5**).
Kamera stoi po stronie −Y. Z = wysokość: **0 = spód półki P000**, góra P200 = 2018, **podłoga Z = −15**.

> W `promo/scene/build_scene.py` podłoga leży na z = 0, a korzeń mebla na z = FOOT_H = 15 mm.
> **Przeliczenie: X_w = X/1000, Y_w = Y/1000, Z_w = (Z + 15)/1000 [m].** (`regal.blend` z repo cnc ma podłogę na −12 mm.)
> Czas: **25 fps**, numer klatki **f = 0…749 (globalny)**, t = f/25 s. W Blenderze używamy tych samych numerów klatek
> (klatka 0 jest dozwolona). Każde ujęcie renderujemy osobno z zakładkami ±3 kl.

### Mapa komórek (do celowania kamerą i rekwizytów)
Światło komórki w mm. #nr = indeks z `layout.yaml`; „koniec” oznacza strefę wysięgu bez przegrody na zewnątrz.

| Rząd (Z) | Od lewej do prawej |
|---|---|
| R9 1718–2000 | #48 koniec 0–191 · #49 open 209–591 · **DZ08** 611–989 (zawias L) · #51 open 1009–1391 · **DZ09** 1411–1789 (R) · #53 koniec 1809–1900 |
| R8 1518–1700 | #42 koniec 0–91 · **DZ06** 111–389 (L) · #44 open 409–791 · *(#38 wysoka 809–1091, Z 1418–1700)* · **DZ07** 1111–1489 (R) · #46 open 1509–1691 · #47 koniec 1709–1900 |
| R7 1418–1500 | #35 koniec 0–191 · #36 open 209–491 · **DZ05** 511–789 (L, 78 mm) · #38 · #39 open 1109–1391 · *(#33 wysoka)* · #40 open 1609–1791 · #41 koniec 1809–1900 |
| R6 1218–1400 | #29 koniec 0–91 · **DZ03** 111–289 (L) · *(#24)* · #31 open 709–991 · **DZ04** 1011–1389 (R) · *(#33 wysoka 1409–1591, Z 1218–1500)* · #34 koniec 1609–1900 |
| R5 918–1200 | #23 koniec 0–291 · *(#24 wysoka 309–691, Z 918–1400, 382×482)* · **DZ01** 711–1089 (L) · #26 open 1109–1291 · **DZ02** 1311–1689 (R) · #28 koniec 1709–1900 |
| R4 718–900 | #18 koniec 0–191 · #19 open 209–591 · **S09** 611–1189 · *(#15 wysoka 1209–1491, Z 618–900)* · **S10** 1511–1789 · #22 koniec 1809–1900 |
| R3 618–700 | #11 koniec 0–91 · **S07** 111–489 · #13 open 509–791 · **S08** 811–1189 · #15 · #16 open 1509–1691 · #17 koniec 1709–1900 |
| R2 318–600 | #06 koniec 0–291 · **S05** 311–689 · #08 open 709–991 · **S06** 1011–1589 · #10 koniec 1609–1900 |
| R1 18–300 | #00 koniec 0–91 · **S01** 111–389 · **S02** 411–789 · **S03** 811–1389 · **S04** 1411–1689 · #05 koniec 1709–1900 |

Pozycje frontów (lewa krawędź X, dół Z, szer. × wys.) i gałek są w `model.json` → `doors`, `drawers.front`, `hardware`.
Osie zawiasów: dla L `x_left − 2`, dla R `x_left + W + 2`. Drzwi otwierają się na zewnątrz, czyli w stronę −Y.

---

## 1. Koncepcja kreatywna

**„Regał, który ma rytm.”** Regał nie ma boków, więc jego sylwetkę tworzą półki. Wystają na 91, 191 i 291 mm, a
odstępy w pionie wynoszą 300/300/100/200/300/200/100/200/300 mm. To zapis rytmiczny na siatce 100 mm, a film go
**dosłownie odgrywa**. Tempo muzyki to **100 BPM**: przy 25 fps szesnastka trwa 3,75 kl., a ósemka 7,5 kl. Kamera
w otwierającym ujęciu jedzie w górę wzdłuż lewego końca z prędkością **100 mm na szesnastkę**. Każde czoło półki, które
mija środek kadru, wybrzmiewa jako nuta drewnianej marimby. Wzór (16-tki 0·3·6·7·9·12·14·15) wynika wprost z przekroju mebla
i staje się motywem dźwiękowym filmu. Wraca przy montażu, gdy płaskie formatki z 8 arkuszy lądują w meblu w tej samej kolejności wysokości dźwięków.
Zamyka film jako sygnał na planszy końcowej. Pomiędzy nimi pokazujemy jakość w zbliżeniach o podwyższonej
dosłowności („hyper‑real”): pełny wysuw na kulkach, cichy domyk szuflady i drzwiczek, szczelinę 2 mm, 13 warstw
sklejki i białą kulistą gałkę z druku 3D. Całość grają poranne światło z bocznego okna i cienie schodkowych półek na
ścianie. Ludzi nie ma, frontami porusza „niewidzialna ręka”.

- **Tagline (rekomendacja): „Precyzja w każdej warstwie.”** Łączy warstwy sklejki, warstwy druku 3D gałki i precyzję CNC.
- Alternatywy: **„Bez boków. Bez kompromisów.”** · **„Złożony z precyzji.”** · **„Wycięty co do milimetra. Złożony na lata.”**

### Mood i referencje (znalezione w researchu)
| Referencja | Co bierzemy |
|---|---|
| FRAME × USM Haller, brand film: montaż systemu z generatora w Houdini, sound design Nina Liv. [stashmedia](https://www.stashmedia.tv/frame-usm-haller-system/), [vimeo](https://vimeo.com/937659997); Soft Panel: [stashmedia](https://www.stashmedia.tv/soft-machine-frame-assemble-new-product-film-for-usm/) | proceduralny, „satysfakcjonujący” montaż; jeden system i jeden detal (u nich kula, u nas warstwa) jako bohater |
| Andreas Wannerstedt × Tylko (Moss Green, Black Friday 2025): materiał, proporcja, harmonia przestrzeni. [Moss Green](https://andreaswannerstedt.se/tylko-moss-green), [BF](https://andreaswannerstedt.se/tylko-black-friday-2025), [wywiad „oddly satisfying”](https://designwanted.com/andreas-wannerstedt-interview/) | pętle i miękkie zwalnianie, ruch „idealny”, czyste pastelowe światło |
| Tylko „Furniture that fits. For people that don't.” (Grey London + Studio Dumbar/DEPT, D&AD 2024 shortlist, motion design): [LBB](https://lbbonline.com/news/tylko-launches-new-campaign-to-stand-out-from-overly-commercialised-furniture), [D&AD](https://www.dandad.org/work/d-ad-awards-archive/tylko-furniture-that-fits-for-people-that-dont) | typografia jako system, bez „meblowego” kiczu |
| Tylko Matte Black (VVAND): minimalny design, jeden kolor marki, uwaga na meblu. [behance](https://behance.net/gallery/130490647/Tylko-Matte-Black) | powściągliwość grafiki |
| Tylko Original Classic: krawędzie sklejki zostawione na widoku i olejowane ręcznie. [tylko.com](https://tylko.com/en-ch/faq/articles/shelves/what-is-the-tylko-original-classic-made-of) | krawędź jako „podpis”, czyli macro warstw |
| Tylko „Truck” (Kijek/Adamski, Strange Beast): ujęcia robione w kamerze i na fizycznych obiektach. [strangebeast](https://strangebeast.tv/projects/tylko-truck) | polska marka, rzemiosło, ciepło |
| Vitsœ 606 „Tidy up your life” (2013). [catesthill](https://catesthill.com/2013/01/21/vitsoe-tidy-up-your-life) | spokój i ponadczasowość, długie ujęcia |
| Dan Hoopert „Playing in the Shadows” dla HAY: surowy, poetycki CG. [stashmedia](https://stashmedia.tv/?p=56272) | **cień jako bohater**, czyli cienie wysięgów na ścianie |
| Product reveal w stylu Apple: hero, detale, kontekst; kontra i światło na krawędziach; macro z dużą głębią ostrości. [Manfrotto](https://www.manfrotto.com/global-en/stories/how-to-shoot-cinematic-tech-videos-like-apple/) | struktura: hook, odsłona, detale, kulminacja, hero |
| Okno w kinie: światło z północy miękkie, słońce przez szybę rzuca plamę. [melies](https://melies.co/cinematic-techniques/lighting/window-light); niedoskonałości materiałów chronią minimalizm przed sterylnością. [threelight](https://www.threelight.studio/content/scandinavian-interior-netherlands) | tynk z fakturą, plama słońca z podziałem okna |
| ASMR/Foley w reklamie (IKEA: nagrania na replice planu, bliskie mikrofony). [LBB](https://lbbonline.com/news/the-extending-phenomena-of-asmr-and-foley-in-advertising), [IKEA](https://asmruniversity.com/2017/08/11/ikea-asmr-video-commercial-advertisement/), Pentagram × Tarkett: „dźwięk dotykowy”. [pentagram](https://www.pentagram.com/work/tarkett?setKey=4) | podwyższona dosłowność Foley, dźwięk jako dotyk |

Tempo montażu: przeciętna reklama ma ~1,4 s na ujęcie ([animaticmedia](https://animaticmedia.com/story-fitting-into-30-seconds))
i 15–20 ujęć na 30 s ([videomaker](https://www.videomaker.com/article/f11/3327-30-second-sensation/)).
**Celowo jesteśmy wolniej: 9 ujęć 3D + plansza, średnio ~3 s.** Spokój to cecha premium. Energię niesie ruch
w kadrze i kulminacja montażu, a nie częstotliwość cięć.

---

## 2. Specyfikacja techniczna

| | |
|---|---|
| Wersja główna | **16:9, 1920×1080, 25 fps progresywnie, 30,00 s = 750 kl.**, plansza końcowa wliczona w 30 s |
| **Rozdzielczość renderu** | **2560×1440** (PNG 16‑bit RGB). Downscale do 1080p daje supersampling, a 9:16 wycinamy jako 810×1440 → 1080×1920 (upscale tylko ×1,33). Sample skalujemy ×0,56, więc koszt jest taki sam jak dla 1080p (sekcja 9) |
| Cutdown | 9:16, 1080×1920, 15,00 s = 375 kl., wycinany z renderów 16:9 (sekcja 8) |
| Silnik | Cycles CPU (4 rdzenie), OIDN z albedo+normal, adaptive sampling, light tree, persistent data |
| Kolor | Widok **AgX**, look **„Medium High Contrast”** (nazwa enumu zależy od wersji, sprawdzić `view_settings.look` w 5.2), wyświetlacz sRGB, przestrzeń robocza Linear Rec.709 (domyślna). Filmic to rozwiązanie starsze, AgX łagodniej prowadzi światła okna i słońca na brzozie ([PR AgX](https://projects.blender.org/blender/blender/pulls/106355)). Na forach zgłaszano dryf odcieni w AgX, więc w lookdevie trzeba porównać brzozę i terakotę z HEX z sekcji 3.2 |
| Look | „Nordycki poranek”: ciepłe półtony, czernie lekko uniesione (~2%), miękkie zejście świateł, saturacja −8%, delikatne ziarno, winieta −8…10% |
| Master / dostawa | ProRes 422 HQ (`prores_ks -profile:v 3`) + H.264 High (`libx264 -crf 16 -preset slow -pix_fmt yuv420p -movflags +faststart`, tagi bt709), audio 48 kHz/24 bit → AAC 320 kb/s |
| Głośność | **−14 LUFS integrated, true peak ≤ −1,0 dBTP** po enkodzie (limiter −1,5 dBTP przed AAC) |

---

## 3. Scenografia

### 3.1 Wnętrze (otwarty set: 2 ściany + podłoga, bez sufitu, dzięki czemu GI szybko się zbiega)
- **Ściana tylna**: tynk wapienny, płaszczyzna Y = 409,5, X od −6000 do +3800, Z do 3600. `build_room` ma ścianę 9 m (X −3550…5450), więc **trzeba ją wydłużyć w lewo do −6000**, bo widać to w S02.
- **Ściana boczna z oknem (nowa, potrzebna w S02)**: płaszczyzna X = +3800 (lico w stronę −X), Y od −9000 do 409,5.
  Otwór okienny Y −2400…−400, Z 400…3200. Rama grafitowa: profil 60 mm, głębokość 120 mm, 1 słupek i 1 ślemię na Z 2200.
  Za oknem tylko świat (jasne „niebo”, które w AgX miękko się przepala). Bez szyby, bo transmisja jest droga.
- **Podłoga**: mikrocement, płaszczyzna Z = −15, X −6000…3800, Y −10000…409,5 (S07 i S08 potrzebują dużej podłogi).
- Styk ściana–podłoga ostry, bez listwy. Tył korpusu jest 9,5 mm od ściany (plecy 6,5 mm + szczelina 3 mm), kotwy pod P200
  w #49 i #51 (małe kątowniki, można pominąć).

### 3.2 Paleta (sRGB HEX)
| Rola | HEX | Uwagi |
|---|---|---|
| Ściana, tynk ciepła biel | `#E9E4DB` | jak `build_room` default; faktura bump 0,08–0,12 |
| Podłoga, mikrocement | `#BDB4A8` | **ciemniej niż default `CFC6B8`**, żeby brzoza odcinała się w S07/S08 |
| Sklejka, lico (olej) | `#E3CBA5` (słoje `#CFB083`) | kremowo-miodowa, roughness 0,40–0,55 |
| Sklejka, krawędź | jasna warstwa `#EAD8B9`, poprzeczna `#CDAE82`, klej `#7B5E43` | 13 warstw / 18 mm, 5 warstw / 6,5 mm |
| Gałka PLA | `#F3F1EC` | matowa, roughness 0,45, warstwy druku 0,2 mm |
| Stal (zawiasy, prowadnice, łby A2) | `#A9AAA6` | metallic 1, roughness 0,28 |
| Terakota (akcent) | `#B5593D` / glina `#B07A5C` | ceramika |
| Szałwia (akcent) | `#7F8A6E` | tekstylia, okładki |
| Grafit | `#3B3936` | ceramika, książki |
| Krem ceramika | `#E8E1D4` | |
| Atrament | `#34404F` | 1–2 grzbiety książek |
| Rama okna | `#3A3733` | |
| Typografia ciemna / jasna | `#24211E` / `#F6F2EA` | |
| Tło planszy końcowej | `#EFEAE2` | |

### 3.3 Materiały (implementacja: `promo/scene/materials.py`)
- **Sklejka** (`plywood(t_mm=18, plies=13)`). Każda formatka ma lokalną oś Z wzdłuż grubości (tak budują `part_mesh`
  i `model.json`). Warstwy liczymy jako `fract(Z_obj · plies / t)`. Warstwy są naprzemiennie jasne i poprzeczne, każda
  ma losowe ±5% jasności, a na granicy warstw rysujemy cienką linię kleju (~0,12 mm). O tym, gdzie jest lico, a gdzie
  krawędź, decyduje `|normal_obj.z| > 0,5`. Na krawędziach roughness 0,62 i pory w warstwach poprzecznych (bump).
  **Warstwy stopniowo wygaszamy z odległością:** `Camera Data → View Distance` 1,2 m → 2,8 m przechodzi z kontrastu
  100% do 25%, inaczej warstwy migają i dają moiré w szerokich ujęciach. Bevel geometryczny 0,7 mm
  (`build_furniture(bevel_mm=0.7)`) łapie światło w macro.
- **Słoje frontów: poziomo.** `model.json` ma grain = u, rozkrój też ma słoje wzdłuż szerokości frontu.
  `build_furniture()` domyślnie ma `front_grain="vertical"`. **Do zmiany: produkt ma słoje poziome.**
- **Gałka** (`knob_pla(layer_mm=0.2)`): biała. Warstwy druku to koncentryczne pierścienie wzdłuż osi gałki (oś Y),
  bump 0,15. Można dodać jeden pionowy „szew” druku. W macro (S03) warstwy 0,2 mm mają mieć ≥ 3 px przy 1440p.
- **Łby SPAX A2** (`screws=True`): metal, gniazdo Torx, zlicowane w fazie ~0,5 mm pod licem.
- **Prowadnice KA 4532**: 3 człony stalowe, widoczne z boku wysuniętej szuflady. Człon środkowy porusza się o połowę
  wysuwu (`DRW_MID_<Sxx>`).
- **Zawiasy CLIP top**: puszka Ø35 w drzwiach, ramię, prowadnik na przegrodzie (`_build_hinges`).
- Ceramika `ceramic()` (roughness 0,5–0,75, **bez wysokiego połysku**), książki `book_mesh` + `cloth_cover`, tynk
  `plaster`, podłoga `microcement(color="BDB4A8")`. **Zero szkła i zero SSS.**

### 3.4 Rekwizyty (≤ 15 grup, wszystkie proceduralne; `props.py`)
**Zasada nadrzędna: wszystkie strefy wysięgu („koniec”: #00 #05 #06 #10 #11 #17 #18 #22 #23 #28 #29 #34 #35 #41 #42
#47 #48 #53), niskie komórki 82 mm (#13 #16 #36 #39 #40) i #33 zostają PUSTE.** Schodkowa sylwetka ma być czysta, a
puste komórki dają oddech rytmowi.

| Grupa | Komórka | Obiekt | Stan w `props.py` |
|---|---|---|---|
| A | #49 (R9, 209–591) | rząd 7 książek od prawej, ostatnia pochylona + kubek piaskowy | jest |
| B | **#24 (wysoka 382×482)** | wazon butelkowy kremowy + gałązka oliwna + 2 książki na płasko, czyli „hero niche” | jest |
| C | #44 (R8, 409–791) | stos 3 książek + mała misa grafitowa | jest |
| D | #51 (R9, 1009–1391) | płaska misa kremowa Ø210 + wazonik terakota | jest |
| E | #38 (wysoka 282×282) | moon vase grafit Ø165 | jest |
| F | #19 (R4, 209–591) | stos 3 książek | jest |
| G | #08 (R2, 709–991) | 5 albumów pionowo, oparte o prawą przegrodę | **dodać** |
| H | #15 (wysoka 1209–1491, Z 618–900) | walcowy wazon terakota Ø90×200 + 2 książki na płasko. Widać go w S03 | **dodać** |
| I | #26 (182×282, między DZ01 i DZ02) | grafika w ramce oparta o ścianę, 160×220: kremowy papier, koło terakota Ø70 (tekstura z Pillow). Widać ją w S05 | **dodać** |
| J | #31 (R6, 709–991) | 4 paperbacki na płasko + mały kubek szałwia | **dodać** |
| K | #46 (182×182) | mała misa terakota Ø120 | opcjonalnie |

Rekwizyty w ujęciach funkcyjnych liczą się poza limitem i są tylko w środku mebla:
- **S09** (szuflada): 3 złożone tkaniny (krem, szałwia, terakota), 240×160×40–55 mm, materiał `cloth_cover`.
- **S10** (top‑down): notes A5 z okładką w kolorze szałwii, 3 ołówki sześciokątne Ø7×175 (terakota, grafit, natural)
  i linijka brzozowa 200×25×3, ułożone równolegle do X.
- **DZ02** (szafka): 2 misy jedna na drugiej (szałwia) + słoik terakota.

---

## 4. Oświetlenie

**Historia światła:** poranne słońce wpada przez okno w **prawej** ścianie. Promienie biegną od prawej do lewej, lekko
do ściany. Prawe końce mebla są oświetlone od czoła. Lewe końce dają **kontrę**, a półki rzucają na ścianę po lewej
długie, schodkowe pasy cienia. Lica frontów dostają światło **boczne, ślizgowe**, a kuliste gałki rzucają długie cienie
w lewo.

### Rig A „Poranek” (S01–S08): `light_rig_window(side="right")` z nadpisaniem kierunku słońca
| Światło | Typ / parametry | Pozycja (mm, model) | K |
|---|---|---|---|
| OKNO_sun | SUN, angle 1,2°, strength **2,6**, kierunek promieni **d = (−0,851, +0,300, −0,431)** (25,5° nad horyzontem) | — | **4600** |
| Maskownica okna | `_window_gobo` 2,6×2,4 m, szyby 2×3, szpros 70 mm, 2,2 m przed środkiem mebla wzdłuż −d, light linking: cień tylko od słońca | — | — |
| OKNO_key | AREA 1,8×2,4 m, 520 W, spread 150° | (3600, −1250, 1550) → (1150, 150, 1050) | 5000 |
| OKNO_fill | AREA 3,0×2,0 m, 90 W (odbicie od pokoju z lewej) | (−2600, −3200, 1600) → środek mebla | 5600 |
| OKNO_sufit | AREA 3,5×2,5 m, 70 W | (950, −1500, 3000) → w dół | 4300 |
| Świat | kolor 6500 K, strength 0,35 (widoczny przez okno jako niebo) | | |

### Rig B „Złota godzina” (S09)
Słońce **3800 K**, strength 3,0, **d = (−0,901, +0,240, −0,360)** (21° nad horyzontem, dłuższe cienie wysięgów).
OKNO_key 4200 K ×0,8, OKNO_fill 6500 K ×0,7 (chłodny kontrast w cieniach), świat 0,25.

### Dodatki per ujęcie
| Ujęcie | Dodatkowe światło |
|---|---|
| S01 | **kicker** AREA 600×600, 15 W, 4500 K, w (−1100, −500, Z_kam), celuje w (0, 150, Z_kam), **dziecko riga kamery** (jedzie z nią). Czytelność warstw na zacienionych czołach |
| S03 | blenda AREA 400×400, 10 W, 4800 K, (1300, −500, 600) → wnętrze szuflady |
| S04 | softbox AREA 800×800, 25 W, 5000 K, (1650, −190, 2600) → w dół (wnętrze szuflady, cienie ołówków zostają od słońca) |
| S06 | ślizgowy pasek AREA 100×600, 8 W, 3800 K, (1900, −120, 600) → −X (relief warstw) |
| S07 | przesunąć maskownicę tak, by plama okna leżała na rzędzie arkuszy bliżej ściany |
| S08 | słońce ×1,15 (rozjaśnienie) w f585–600, ease in/out |

Pomocnicze światła mają `visible_camera = False` i `visible_glossy = False`. Ekspozycja (Film → Exposure, EV):
S01 −0,3 · S02 0 · S03 +0,1 · S04 0 · S05 0 · S06 +0,2 · S07 +0,1 · S08 0 · S09 −0,1.
Cel w lookdevie: brzoza w słońcu ~0,80–0,85 wartości wyświetlanej, w cieniu 0,45–0,55, ściana w słońcu ≤ 0,95.

---

## 5. Shot list (30 s, 16:9)

Siatka muzyczna: **100 BPM**, takt = 60 kl. = 2,4 s, ćwierćnuta = 15 kl., ósemka = 7,5 kl., szesnastka = 3,75 kl.
**Każde cięcie wypada na uderzeniu.** Kamery mają matrycę 36 mm (sensor fit horizontal). Pozycje kamery C i celu T
podaję w mm w układzie modelu.

| # | Klatki / czas | Dł. | Ujęcie i akcja | Kamera (mm, ogniskowa) | Ruch | DOF | Animacja elementów | Przejście | Kluczowy dźwięk |
|---|---|---|---|---|---|---|---|---|---|
| **S01 „RYTM”** (hook) | 0–60 / 0,00–2,40 | 2,4 | Lewy, otwarty koniec regału z profilu 3/4. Kamera jedzie w górę od podłogi, czoła półek P000→P150 mijają środek kadru, każde jako nuta. Kontra, czoła warstw lśnią | 50 mm. C = (−520, −300, **9 + 26,667·f**), T = (0, 120, ten sam Z) | crane pionowy, **liniowy 667 mm/s** (100 mm na 16‑tkę), bez easingu | f/4, ostrość na empty (0, 100, Z_kam) | brak | cięcie na ruchu, f60 (raz taktu 2) | nuty marimby F3·A3·C4·D4·F4·G4·A4·C5 na f 0 / 11,25 / 22,5 / 26,25 / 33,75 / 45 / 52,5 / 56,25 |
| **S02 „Bez boków”** (odsłona) | 60–180 / 2,40–7,20 | 4,8 | Cały regał. Łuk od profilu lewego (okno w prawej części kadru, sylwetka i pasy cieni na ścianie) do 3/4 frontu | 35 mm. Łuk wokół P = (950, 200, 1000): α 58°→34°, R 5200→5000, Z 1200→1100; C = (950 − R·sinα, 200 − R·cosα, Z). Start ≈ (−3460, −2556, 1200), koniec ≈ (−1846, −3945, 1100). T = P | orbita, ease in-out sine | f/5,6, ostrość P | słońce: azymut −1,0° przez 120 kl. (cienie lekko pełzną) | cięcie f180 | f60: sub + pad Fmaj9. Napis „Bez boków.” f96–176 |
| **S03 „Pełny wysuw”** | 180–225 / 7,20–9,00 | 1,8 | Makro gałki S09, potem szuflada wyjeżdża na pełny wysuw, kamera cofa się razem z nią. Prowadnica KA 4532 lśni z boku | 60 mm. Klucze: f180 C(1010, −215, 830) T(900, −15, 809) · f188 C(1015, −225, 832) · f210 C(1350, −900, 1050) T(900, −330, 800) · f225 C(1380, −960, 1080) T(900, −320, 790) | dolly w tył i w górę, Bezier | f/4, ostrość = gałka S09 (empty jedzie z szufladą) | **S09**: f188→210 Hermite 0 → −352 mm (v0 = 0, v1 = −3 mm/kl), **f210 uderzenie w ogranicznik**, f210→213 odbicie do −350 | cięcie f225 | toczenie kulek f188–210, „tunk” f210 (3. ćwierćnuta taktu 4), szelest tkanin f211–220 |
| **S04 „Cichy domyk”** | 225–300 / 9,00–12,00 | 3,0 | Top‑down na wysuniętą S10 (flat‑lay: notes, ołówki, linijka). Niewidzialna ręka dopycha, a Silent System łapie i powoli domyka | 50 mm. C = (1650, −190, 1900), oś w dół (−Z), **góra kadru = +Y** | **zablokowana** | f/5,6, ostrość Z 860 | **S10**: f225–250 −350 (stoi) · f250→262 Hermite −350 → −40 (v1 = +5,2 mm/kl) · **f262 zatrzask** · f262→285 domyk p = −40·(1−u)³ · **f285 kontakt** | cięcie f300 | toczenie f250–262, „klik” f262, syk tłumika, **„thup” f285** (4. ćwierćnuta taktu 5). Napis „Cichy domyk.” f262–296 |
| **S05 „Domyka się sam”** | 300–345 / 12,00–13,80 | 1,8 | DZ02 (zawias R) w ruchu zamykania (cięcie na akcji). Odsłania wnętrze z plecami 6,5 mm i misami, potem BLUMOTION wyhamowuje. Słońce przesuwa się po licu, gdy drzwi się zamykają | 50 mm. C (900, −1250, 1150) → (960, −1150, 1130), T (1500, −80, 1060) | lekki dosuw, ease-out | f/4, ostrość (1450, 0, 1059) | **DZ02** θ (otwarcie +): f300 80° (już −3,6°/kl) · f300→318 Hermite 80° → 14° · **f318 zatrzask tłumika** · f318→330 θ = 14·(1−u)³ · **f330 kontakt** | cięcie f345 | szum powietrza f300–318, „tsk” f318, syk, **„tok” + klik zawiasu f330** (3. ćwierćnuta taktu 6) |
| **S06 „2 mm”** (makro) | 345–420 / 13,80–16,80 | 3,0 | Styk: prawy górny róg frontu S06, przegroda D160-030 (warstwy pionowo), półka P060 (warstwy poziomo), szczeliny 2 mm, z prawej nasłoneczniona strefa wysięgu #10. Napisy jak z rysunku CAD | 100 mm. C = (1540 + 80·s, −430, 610), T = (1570 + 80·s, 0, 600), s = smoothstep((f−345)/75) | slider w prawo o 80 mm | f/5,6, płaszczyzna Y = 0 | brak | cięcie f420 | tyknięcia „suwmiarki” F6·A6·C7 na f360/375/390 |
| **S07 „140 elementów”** | 420–480 / 16,80–19,20 | 2,4 | Top‑down: 8 arkuszy leży na podłodze, formatki w szkieletach po frezowaniu, małe etykiety. Kamera wznosi się. f465–471 wszystkie formatki „wyskakują” o 30 mm | 35 mm. C = (−200, −3525, Z), Z 3600→8600 (ease-out quad), oś w dół, góra = +Y, roll 0→3° | crane w górę | f/8 | pop: +30 mm, ease-out cubic 6 kl., opóźnienie radialne 0–4 kl. od środka kadru | cięcie f480 po 6 kl. ciszy | riser f420–474, 140 mikro‑tyknięć f465–471, **cisza f474–480**. Napis f428–474 |
| **S08 „Z płaskiego”** (montaż) | 480–600 / 19,20–24,00 | 4,8 | **Drop:** wszystkie formatki lewitują, potem rzędami wlatują w meble pod ścianą (kolejność montażu z `model.json → steps`), plecy, na końcu fronty falą po przekątnej | 35 mm. C0 (1800, −7600, 5200) T0 (−200, −3300, 0) → C1 (**3450, −5750, 1250**) T1 (950, 200, 1000) | crane w dół z odchyleniem f480–585 (ease in-out cubic), f585–600 dosuw 80 mm | f/8, ostrość 6,2 m | harmonogram w 5.8. **Motion blur ON** (shutter 0,4) | cięcie f600 | uderzenie f480, nuty lądowania półek (jak w hooku), tiki przegród, arpeggio frontów, akord f585 |
| **S09 „Hero”** | 600–660 / 24,00–26,40 | 2,4 | Front na wprost, złote światło, pasy cieni wysięgów na ścianie po lewej. Ostatnia szuflada S03 domyka się | 50 mm. C (950, −6600, 1060) → (950, −6250, 1060), T (950, 0, 1060), pitch 0 (pionowe krawędzie proste), shift 0 | dosuw ease-out sine | f/5,6, płaszczyzna Y = 0 | **S03**: f600 −220 (w ruchu) · f600→612 Hermite → −40 · f612 zatrzask · f612→630 domyk · **f630 kontakt** | przenikanie f660–670 | **„thup” f630 = logo dźwiękowe cz. 1**, pad B♭maj7 |
| **S10 Plansza końcowa** | 660–750 / 26,40–30,00 | 3,6 | Glif sylwetki rysuje się na tle `#EFEAE2`, potem nazwa RYTM, tagline, opis, marka | 2D (Pillow) | — | — | rysowanie glifu f662–692 | trzymać do f750 | sygnał RYTM f660 (16‑tki 0·3·6·7·9) + akord Fmaj9, wybrzmienie do ~f744 |

### 5.1 S01 „RYTM”: szczegóły
- Ujęcie zaczyna się prawie na podłodze: kamera jest na Z = 9, czyli 24 mm nad podłogą. Widać czoło P000 unoszące się
  15 mm na stopkach.
- Czoła półek przechodzą przez środek kadru dokładnie w f = (Z_półki_środek − 9)/26,667:
  P000 f0 · P030 f11,25 · P060 f22,5 · P070a f26,25 · P090 f33,75 · P120a f45 · P140a f52,5 · P150a f56,25
  (P170 wypadłaby w f63,75, już po cięciu). Na 16‑tkach daje to **X . . X . . X X . X . . X . X X**.
  Tak zapisany jest motyw RYTM.
- Kontrolne punkty kadru (x, y od lewego górnego rogu, 0–1): narożnik czoła (0, 0, Z) ≈ (0,72; 0,49), tylna krawędź
  czoła ≈ (0,14; 0,52). W głębi, poza ostrością, widać przegrody cofnięte o 91/191/291 mm i ścianę z plamą słońca.
- Wysokości nut odpowiadają półkom (tak samo w S08): P000 **F3** · P030 **A3** · P060 **C4** · P070 **D4** · P090 **F4** ·
  P120 **G4** · P140 **A4** · P150 **C5** · P170 **D5** · P200 **F5**.

### 5.2 S02 „Bez boków”
- Start: regał zajmuje x 0,42–0,61 i y 0,10–0,92, okno x ≈ 0,77–0,91 (jasne). Koniec: regał x 0,35–0,66, okno wychodzi
  z kadru w prawo.
- Pasy cieni wysięgów padają na ścianę na lewo od mebla, na pole od X ≈ −1400 do 0, gdzie plama słońca sięga do Z ≈ 1280.
  To kadr „Hoopert”: cień jako druga sylwetka.
- Napis „Bez boków.” stoi na ścianie po lewej (sekcja 7.3).

### 5.3 S03 „Pełny wysuw”: krzywe
- Hermite: p(u) = (2u³−3u²+1)·p0 + (u³−2u²+u)·m0 + (−2u³+3u²)·p1 + (u³−u²)·m1, gdzie m = prędkość [mm/kl] × czas trwania [kl].
  To samo daje `B.hermite(u, m0, m1)`.
- Człon środkowy prowadnicy (`DRW_MID_S09`) przesuwa się o połowę drogi szuflady.
- Kontrolne punkty kadru: w f180 gałka jest w środku (0,50; 0,50) i zajmuje ~19% szerokości kadru. W f210 gałka jest
  w (0,45; 0,50), a front w x 0,07–1,1 (prawa część przycięta celowo).

### 5.4 S04 „Cichy domyk”
- Wszystkie zatrzymane fragmenty renderujemy jako **1 klatkę** i trzymamy: f225–249 oraz f286–299. Kamera musi być
  absolutnie zablokowana.
- Kadr: skrzynka x 0,32–0,68, czoło P090 na górnej krawędzi (y 0,02). Szuflada wsuwa się pod półkę w górę kadru, pod
  spodem rozmyta podłoga.
- Na skali filmowej domyk jest celowo wydłużony (40 mm w 0,92 s). W API: `animate_drawer_close("S10", f0=250,
  push_s=0.48, softclose_mm=40, softclose_s=0.92, frac_from=1.0)`.

### 5.5 S05 „Domyka się sam”
- Oś drzwi DZ02: (1689…1691, 0, ·), obrót wokół Z, otwarcie +. W API: `animate_door_close("DZ02", f0=300,
  push_s=0.72, softclose_deg=14, softclose_s=0.48, angle_from=80)`.
- W kadrze: wolna krawędź otwartych drzwi x ≈ 0,80, oś zawiasu x ≈ 0,62, grafika w #26 po lewej. Widać zawiasy
  CLIP top na Z 976 i 1142.

### 5.6 S06 „2 mm”: napisy CAD
Pozycje 2D liczy Blender: `world_to_camera_view` dla każdej klatki, eksport do `events.json`, potem nakładka w poście.
| Napis | Punkty 3D (mm) | Wejście | Wyjście |
|---|---|---|---|
| A „18 mm”: wymiar poziomy przez czoło przegrody D160-030 | (1591, 0, 570) – (1609, 0, 570) | f360 | f408–416 |
| B „2 mm”: wymiar pionowy szczeliny front S06 / P060, strzałki na zewnątrz | (1560, 0, 598) – (1560, 0, 600) | f375 | f398–406 |
| C „13 warstw”: linia odniesienia do czoła P060 | (1650, 0, 609) | f390 | f408–416 |

Kontrolnie: w f360 A jest w x 0,58–0,70 (y 0,84), w f375 B w x 0,25 (y 0,50–0,52), w f390 C w x 0,68 (y 0,40).

### 5.7 S07 „140 elementów”
- Arkusze leżą na podłodze w siatce 3×3 bez jednego pola:

  | | kolumna X −4100…−1600 | kolumna X −1450…1050 | kolumna X 1200…3700 |
  |---|---|---|---|
  | rząd Y −2750…−1500 | 18 mm #1 | 18 mm #2 | 18 mm #3 |
  | rząd Y −4150…−2900 | 18 mm #4 | 18 mm #5 | 18 mm #6 |
  | rząd Y −5550…−4300 | 6,5 mm #1 (X −2625…−125) | 6,5 mm #2 (X 25…2525) | — |

- **Prawdziwy rozkrój:** `pip install -r /home/user/cnc/requirements.txt`, potem
  `m = regal.model.build(); sheets = regal.cnc.run_nesting(m)`. Wynik to `{grubość: [Sheet(placements=[Placement(pid,
  x, y, rot, w, h)])]}`, a `regal.nesting.to_sheet()` mapuje współrzędne. Podgląd: `output/cnc/podglad/*.png`.
- **Szkielet arkusza:** płyta 2500×1250 z otworami (boolean Manifold, kontur formatki +3 mm, bo frez Ø6) i formatki
  w otworach. Plan B: bez otworów, formatki na ciemnej płycie ofiarnej `#8C7A66`.
- Etykiety 70×37 (opcjonalnie): białe prostokąty z ID formatki (tekstura z Pillow).
- Kadr na końcu (Z 8600) obejmuje arkusze w x 0,06–0,94 i y 0,09–0,91.

### 5.8 S08 „Z płaskiego”: harmonogram montażu (`assembly_units()` / `animate_assembly(starts=…)`)
1. **f480–488 lewitacja**: wszystkie formatki unoszą się z pozycji po „pop” (+30 mm) na +300 mm (ease-out quint),
   opóźnienie radialne 0–4 kl. Bujanie ±5 mm (sinus 0,8 Hz) do startu lotu.
2. **Lot każdej formatki: 14 kl.** z pozycji zawieszenia do pozycji docelowej. Tor to krzywa Béziera P0 → P0 + (0, 0, 900)
   → P1 + (0, −900, 0) → P1. Obrót slerp na pierwszych 75% lotu, pozycja ease-out cubic (lądowanie „na zatrzask”).
   Start lotu = lądowanie − 14.
3. **Korpus**: 14 kroków na szesnastkach. Przegrody „up” z danego kroku lądują 2 kl. po swojej półce.

| k | Krok (półka + przegrody „up”) | Lądowanie półki f | Przegrody f | Nuta |
|---|---|---|---|---|
| 0 | P000 + D010-000, D040-000, D080-000, D140-000, D170-000 | 502,5 | 504,5 | F3 |
| 1 | P030 + D030-030, D070-030, D100-030, D160-030 | 506,25 | 508,25 | A3 |
| 2 | P060 + D010-060, D050-060, D080-060, D120-060, D150-060, D170-060 | 510 | 512 | C4 |
| 3 | P070a + D020-070, D060-070 | 513,75 | 515,75 | D4 |
| 4 | P070b + D180-070 | 517,5 | 519,5 | D4 |
| 5 | P090 + D030-090, D070-090, D110-090, D130-090, D170-090 | 521,25 | 523,25 | F4 |
| 6 | P120a + D010-120 | 525 | 527 | G4 |
| 7 | P120b + D100-120, D140-120, D160-120 | 528,75 | 530,75 | G4 |
| 8 | P140a + D020-140, D050-140, D080-140, D110-140 | 532,5 | 534,5 | A4 |
| 9 | P140b + D180-140 | 536,25 | 538,25 | A4 |
| 10 | P150a + D010-150, D040-150 | **540** (raz taktu 10) | 542 | C5 |
| 11 | P150b + D150-150, D170-150 | 543,75 | 545,75 | C5 |
| 12 | P170 + D020-170, D060-170, D100-170, D140-170, D180-170 | 547,5 | 549,5 | D5 |
| 13 | **P200** (wieniec) | **555** (2. ćwierćnuta) | — | **F5 + sub** |

Klatki ułamkowe zaokrąglamy do najbliższej całej. Dźwięk stawiamy w dokładnym czasie muzycznym; różnica ≤ 20 ms jest
niezauważalna.

4. **Plecy (16 szt.)** wsuwają się od góry za meblem, lądowanie razem w f551,25 (cichy „szuff”).
5. **Części skrzynek szuflad** wlatują do swoich komórek w f545–575. Są ukryte w ciemnym wnętrzu i lądują ~10 kl. przed
   swoim frontem, więc każdy element z arkusza trafia na miejsce.
6. **Fronty i drzwiczki: 8 slotów na szesnastkach, fala po przekątnej (X+Z):**
   f558,75 S01, S02 · f562,5 S05, S07 · f566,25 S03, DZ03 · f570 S08, S04, S09 · f573,75 S06, DZ06 ·
   f577,5 DZ01, DZ05, S10 · f581,25 DZ04, DZ02 · **f585 DZ08, DZ07, DZ09** (akord).
   Ostatnie 40 mm każdy front przejeżdża prosto wzdłuż +Y, „wpięcie” w lico. Gałka wskakuje (skala 0→1, 4 kl.)
   2 kl. po lądowaniu frontu.
7. Kontrolnie w kadrze końcowym (f585) regał zajmuje x 0,36–0,65 i y 0,21–0,80, więc **mieści się w kolumnie 9:16**.
   Kadr startowy: arkusze y 0,24–0,96, regał tuż nad górną krawędzią.

### 5.9 S09 „Hero”
- Regał zajmuje x 0,30–0,70, y 0,14–0,90 (start) i x 0,29–0,71 (koniec). Pasy cieni na ścianie widać w x ≈ 0,1–0,3.
- W API: `animate_drawer_close("S03", f0=600, push_s=0.48, softclose_mm=40, softclose_s=0.72, frac_from=220/350)`.

---

## 6. Sound design (synteza w Pythonie: numpy + scipy; `promo/audio_edit/dsp.py`, `sfx_synth.py`)

**Synchronizacja:** Blender eksportuje `events.json` przez `B.log_event(...)` / `B.export_events(...)`. Plik zawiera
klatkę, typ, cel, położenie x w kadrze (do panoramy) i krzywą prędkości szuflad/drzwi na każdą klatkę. Audio czyta
**wyłącznie** ten plik, z czasem = f/25. Proponowane typy zdarzeń: `shelf_pass`, `drawer_roll`, `drawer_stop`,
`softclose_catch`, `softclose_contact`, `door_catch`, `door_contact`, `callout`, `pop`, `levitate`, `land`, `front_land`.

### 6.1 Muzyka
- **100 BPM, F‑dur, 4/4**: minimal/ambient z pulsem „half‑time”. Brzmienie ma być ciepłe i drewniane, w stylu Nordic.
  Stockowe utwory „premium minimal” mają zwykle 100–118 BPM z marimbą, padami i pluckami
  ([przykład](https://motionarray.com/royalty-free-music/minimal-warm-ambient-66563/)).
- **Instrumenty (synteza):**
  - **Marimba (motyw RYTM, nuty półek)**: modalnie, partiale 1 : 3,99 : 10,0, amplitudy 1 / 0,25 / 0,06,
    τ ≈ 0,9·√(220/f) s / 0,09 s / 0,03 s, pałka = półsinus 1,5 ms + szum BP 2–4 kHz −18 dB, humanizacja ±5 ms i ±1,5 dB.
  - **Pad**: na każdą nutę akordu 3 piły PolyBLEP rozstrojone ±7 centów, LP 2‑biegunowy 1400 Hz ± 300 Hz (LFO 0,07 Hz),
    A 1,2 s / R 2,5 s, panorama głosów ±40%, chorus.
  - **Sub‑kick**: sinus z opadającą wysokością 110 → 46 Hz (τ 40 ms), amplituda τ 0,28 s, klik 2 ms (szum HP 2 kHz −24 dB).
  - **Wood clap / rim**: blok drewniany modalnie (900 Hz + 2,4 kHz, τ 25 ms) + szum BP 1,5 kHz 8 ms.
  - **Shaker**: szum HP 6 kHz, 25 ms, szesnastki z akcentami, −30 dB.
  - **Bas (drop)**: sinus + 2. harmoniczna −12 dB + nasycenie tanh, obwiednia A 5 ms, D 300 ms, S 0,6.
  - **Pogłos**: syntetyczna odpowiedź impulsowa, szum stereo zdekorelowany L/P. RT60 2,8 s (<500 Hz) / 2,2 s (0,5–2 kHz) /
    1,5 s (2–6 kHz) / 0,8 s (>6 kHz), predelay 20 ms, `scipy.signal.fftconvolve`.
  - **Klej premium**: nasycenie taśmowe (tanh, drive 1,2), półka −2 dB powyżej 12 kHz, kompresja szyny 1,5:1.
    Bas < 120 Hz w mono.
- **Struktura (takty po 2,4 s):**

| Takt | Klatki | Sekcja | Akord | Co gra |
|---|---|---|---|---|
| 1 | 0–60 | Hook | — (pad wchodzi od f30, −30 dB) | nuty półek (marimba, prawie sucha, pogłos 0,9 s), od f45 odwrócony pogłos akordu |
| 2–3 | 60–180 | Odsłona | Fmaj9 → Dm9 | **f60 sub + otwarcie pada**, motyw RYTM w takcie 3 (cicho, oktawę niżej) |
| 4–7 | 180–420 | Groove A | B♭maj7 → C(sus4→3) → Fmaj9 → Dm9 | kick na 1, wood clap na 3, shaker, motyw RYTM co takt; **ducking −4 dB pod Foley** |
| 8 | 420–480 | Breakdown | B♭maj7(#11) | pad + riser, bez perkusji, **cisza f474–480** |
| 9–10 | 480–600 | **Drop** | Fmaj9 → Dm9 | sub+kick f480, bas, **lądowania = melodia** (nuty z 5.8), fronty = arpeggio D4 F4 A4 C5 E5 F5 A5, **f585 akord F5+A5+C6 z F2** |
| 11 | 600–660 | Rozwiązanie | B♭maj7 | bez bębnów, rzadka marimba, „thup” f630 |
| 12 + ogon | 660–750 | Logo | Fmaj9 | **sygnał RYTM: F4 f660 · A4 f671,25 · C5 f682,5 · D5 f686,25 · F5 f693,75** + sub F1 + pełny pad; wybrzmienie, muzyka gaśnie do f744, ostatnie 6 kl. ciszy |

### 6.2 Foley i SFX: lista z czasem i recepturą
| Czas (s) / klatki | Zdarzenie | Receptura (warstwy) | Poziom szczytowy |
|---|---|---|---|
| cały film | room tone | szum różowy, LP 1,2 kHz | −48 dBFS |
| 0,00–2,40 | „powietrze” crane'a | szum LP narastający 150 → 600 Hz | −40 dB |
| 2,40 (f60) | odsłona | sub‑kick + otwarcie pada + szum powietrza | −10 dBFS |
| 2,4–7,2 i 24–26,4 (opcj.) | ptaki za oknem | ćwierkanie FM (nośna 3,2–5,5 kHz, mod. 15–40 Hz, 80–250 ms), 2–3 na sekundę, daleko | −42 dB |
| 7,52–8,40 (f188–210) | **toczenie kulek KA 4532** | A: impulsy Poissona, częstość 400 + 2500·v/v_max na s, każdy przez filtry BP 3,1 / 4,7 / 6,3 kHz (Q 12, zanik 4 ms), losowo ±40%. B: korpus skrzynki, szum różowy BP 120–450 Hz ∝ v^0,8 + mody 180/260/410 Hz (τ 60 ms). C: szelest szyny, szum HP 7 kHz ∝ v. Wszystkie filtry jaśnieją z prędkością | −16 dBFS |
| 8,40 (f210) | **ogranicznik pełnego wysuwu** | modalnie drewno 150/340/620 Hz (τ 50/35/20 ms) + klik metalu 2,8/5,6 kHz (τ 6 ms) + odbicie po 70 ms (−14 dB) | −12 dBFS |
| 8,44–8,80 | tkaniny w szufladzie | szum BP 2–6 kHz, 120 ms, miękka obwiednia | −34 dB |
| 10,00–10,48 (f250–262) | dopchnięcie S10 | toczenie jak wyżej (szybsze) + „whff” LP 800 Hz | −18 dBFS |
| 10,48 (f262) | **zatrzask Silent System** | impuls 1,5 ms przez BP 2,2 kHz (Q 4) + 3,6 kHz, plastikowy | −24 dBFS |
| 10,48–11,40 | tłumik | szum LP 900 Hz ∝ v (zanika) + olejowy syk BP 1,2–3 kHz | −34 dB |
| **11,40 (f285)** | **„thup” domyku** | (a) sinus 82 → 70 Hz, τ 90 ms; (b) mody panelu 190/360/590/1050/1900 Hz, amplitudy 1/0,55/0,35/0,2/0,08, τ 70/50/32/18/9 ms, wzbudzenie podniesionym kosinusem 5 ms (filcowy odbojnik); (c) podmuch, szum LP 500 Hz, 35 ms. **Miękko, nie klaśnięcie** | **−9 dBFS** |
| 12,00–12,72 (f300–318) | powietrze drzwi | szum BP 200–700 Hz ∝ prędkość kątowa, ruch w stereo | −38 dB |
| 12,72 (f318) | zatrzask BLUMOTION | mody metalu 2,35/4,8/7,9 kHz (τ 7 ms) + szum 3 ms | −28 dBFS |
| **13,20 (f330)** | **„tok” drzwiczek** | mody drzwi 150/300/510/860/1550 Hz (τ 80/55/35/20/10 ms) + uderzenie 65 Hz (τ 60 ms) + klik zawiasu 5 kHz 2 ms (−26 dB, +15 ms) | −11 dBFS |
| 14,40 / 15,00 / 15,60 | tyknięcia „suwmiarki” (napisy CAD) | klik 1 ms HP 3 kHz + ping sinus F6 / A6 / C7, τ 70 ms | −26 dBFS |
| 16,80–18,96 (f420–474) | riser | szum BP przemiatany wykładniczo 250 Hz → 7 kHz + odwrócona, pogłosowana marimba + sinus 220 → 440 Hz; crescendo −40 → −14 dB; **twarde cięcie f474** | −14 dBFS |
| 18,60–18,84 (f465–471) | **„pop” 140 formatek** | 140 mikro‑tyknięć modalnych (f0 losowo 1,6–3,4 kHz, τ 10 ms), czas radialnie od środka kadru | −30 dB każde |
| 18,96–19,20 | **próżnia** | całość ściszona do −60 dB w 80 ms | — |
| **19,20 (f480)** | drop i lewitacja | sub‑kick + kick + bas F + szum „uniesienia” (BP sweep w górę 0,32 s) | −8 dBFS |
| 20,10–22,20 | lądowania korpusu | na każdy krok: whoosh (szum BP 350 Hz → 2,2 kHz → 700 Hz w ciągu 0,56 s, szczyt przy 60%, −30 dB, **panorama = 2·(x_kadru − 0,5)·0,6**) + **nuta marimby** (wysokość z 5.8) zmieszana 60/40 z „tok” sklejki (mody jak „thup” ×1,2). Przegrody: tik drewna 1,1 + 2,7 kHz, τ 15 ms, −22 dB | −14 dBFS |
| 22,05 (f551) | plecy | „szuff”: szum BP 1–3 kHz, 150 ms | −30 dB |
| 22,20 (f555) | **P200** | nuta F5 + głębokie „tok” + sub | −10 dBFS |
| 22,35–23,40 | fronty | miękki „klik-in” (lżejszy „thup”) + nuty arpeggio, gałka: tik 4 kHz | −16 dBFS |
| **23,40 (f585)** | akord domknięcia | F5+A5+C6, F2, pogłos 2,8 s | −10 dBFS |
| 24,00–24,48 | dopchnięcie S03 | toczenie | −18 dBFS |
| **25,20 (f630)** | **„thup” = logo dźwiękowe cz. 1** | jak 11,40, +2 dB pogłosu pokoju | −9 dBFS |
| **26,40–27,75** | **sygnał RYTM** | 5 nut marimby (16‑tki 0·3·6·7·9) + sub F1 + pad Fmaj9 | −10 dBFS |

### 6.3 Miks
- Muzyka pod Foley ~−18 LUFS‑S. Bohaterskie zdarzenia Foley (thup, tok, ogranicznik) ~4 dB nad muzyką.
  Sidechain muzyki −4 dB (atak 10 ms, puszczenie 300 ms).
- Panorama Foley zgodna z położeniem w kadrze, maks. ±30%.
- Master: kompresja 1,5:1, limiter **−1,5 dBTP**, normalizacja **−14 LUFS** (dwuprzebiegowo,
  `ffmpeg … -af loudnorm=I=-14:TP=-1.5:LRA=9`), weryfikacja po AAC: `ebur128=peak=true`, true peak ≤ −1,0 dBTP.
  −14 LUFS to najczęstszy cel dla YouTube, Instagrama i TikToka ([loudfix](https://loudfix.pages.dev/presets),
  [vloggingpro](https://vloggingpro.com/tools/audio-loudness/)). Wersja −16 LUFS tylko na życzenie, pod Reels/TikTok
  ([APU](https://d1lex0gkhzvix9.cloudfront.net/tiktok-instagram-reels-loudness)).
- Uzasadnienie syntezy modalnej (uderzenia, kontakt): [SMC 2019](https://www.smc2019.uma.es/articles/P1/P1_05_SMC2019_paper.pdf),
  [FoleyAutomatic](https://www.cs.mcgill.ca/~kry/pubs/foleyautomatic/foleyautomatic.pdf).

---

## 7. Montaż i post

### 7.1 Rytm i przejścia
- Cięcia (f): 60 | 180 | 225 | 300 | 345 | 420 | 480 | 600, potem przenikanie 660–670.
- Długości ujęć: 2,4 · 4,8 · 1,8 · 3,0 · 1,8 · 3,0 · 2,4 · 4,8 · 2,4 · 3,6 s. Para krótkie–długie się kołysze, a mocne
  zmiany wypadają na raz taktu: 60, 180, 300, 420, 480, 600, 660
  ([zasada downbeatu](https://skills.sh/iart-ai/motion-design-skills/beat-sync-editing),
  [cięcie na beat](https://support.apple.com/en-gw/guide/final-cut-pro/ver65b55a2b7/mac)).
- Wszystkie cięcia są twarde i „na ruchu”. Wyjątki: przenikanie S09→S10 (10 kl.) i trzymanie planszy do końca.
  **Bez wejścia z czerni**, bo hook zaczyna się od pierwszej klatki.

### 7.2 Grading (ffmpeg albo numpy, na PNG 16‑bit po downscale)
- Krzywa S: (0; 0,02) (0,25; 0,235) (0,5; 0,5) (0,75; 0,77) (1; 0,98).
- Saturacja 0,92. Półtony R +2%, B −1,5%; cienie R −1%, B +1%.
- Winieta: rogi −8…10%, maska radialna z potęgą 2,5.
- Ziarno: tylko luminancja, σ ≈ 1,6/255, nowe na każdą klatkę (`noise=c0s=5:c0f=t+u` albo numpy z rozmyciem 0,6 px).
  Maskuje też resztki szumu po OIDN.
- Bez wyostrzania w 16:9. W 9:16 po upscalu ×1,33: `unsharp=5:5:0.4`.
- Downscale 2560 → 1920: Lanczos.

### 7.3 Typografia (napisy renderowane osobno w Pillow jako sekwencje RGBA i nakładane w poście)
- **Fonty (offline, SIL OFL 1.1, pełne polskie znaki):** **Inter Display** do tytułów i napisów
  (`/usr/share/fonts/opentype/inter/InterDisplay-Light.otf`, `-Medium.otf`), **Inter** do drobnego tekstu, **JetBrains
  Mono** do napisów CAD i wymiarów (`/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf`).
  Inter to neutralny neo‑grotesk w tonie skandynawskich marek (Tylko, HAY, Muuto). Mono daje warsztatowy, „CNC‑owy”
  akcent precyzji. DejaVu odpada: wygląda systemowo.
- **Napisy 16:9 (1920×1080):** Inter Display Light 60 px, tracking −1%, kolor `#24211E`, wyrównanie do lewej na
  x = 144 px. Animacja: wejście 10 kl. (fade + 12 px w górę, ease-out cubic), wyjście 8 kl. Bez cieni. Jeśli tło jest
  zbyt ruchliwe, dajemy miękką radialną poświatę `#EFEAE2` z kryciem 35%.

| Napis | Klatki | Pozycja (środek linii y) |
|---|---|---|
| „Bez boków.” | 96–176 | x 144, y 470 (ściana po lewej) |
| „Pełny wysuw.” | 196–224 | x 144, y 900 |
| „Cichy domyk.” | 262–296 | x 144, y 540 (lewe pole top‑down) |
| „18 mm” · „2 mm” · „13 warstw” | 360–416 | z projekcji 3D (5.6) |
| „140 elementów. 8 arkuszy.” | 428–474 | x 144, y 960, z poświatą |

- **Napisy CAD (S06):** JetBrains Mono Regular 26 px, linie 2 px `#24211E`. Linie wymiarowe zakończone
  **architektonicznymi kreskami 45°** (10 px), linie pomocnicze 2 px z przerwą 6 px od krawędzi. Animacja: linia rysuje
  się w 8 kl., tekst pojawia się w 4 kl. po linii.

### 7.4 Plansza końcowa (f660–750)
- Tło `#EFEAE2`, przenikanie z S09 w f660–670.
- **Glif = sylwetka regału z `model.json`:** każda półka to pozioma linia przez całą szerokość, każda przegroda to linia
  pionowa. Kreska 2 px `#24211E`, wysokość 240 px, środek (960, 380). Glif od razu pokazuje „bez boków” i schodki.
  Rysowanie f662–692: półki od dołu do góry, każda w 6 kl. od lewej do prawej, z opóźnieniem 3 kl. między półkami.
  Przegrody rosną w górę po 4 kl.
- **„RYTM”**: Inter Display Medium 120 px, tracking +24%, środek y 600, wejście f672–686.
- **„Precyzja w każdej warstwie.”**: Inter Display Light 44 px, y 690, wejście f684–698.
- **„Regał ze sklejki brzozowej · 190 × 202 × 40 cm”**: JetBrains Mono 22 px `#6E655B`, y 750, wejście f690–702.
- **„CNC Furniture Studio”**: Inter Medium 24 px, tracking +10%, y 980, wejście f696–708.
- Trzymać do f750, bez wyjścia w czerń. Pętla na webie wraca wtedy do hooka bez szwu.

### 7.5 Nazwa produktu: 3 opcje i rekomendacja
1. **RYTM** *(rekomendacja)*. Półki bez boków, z nieregularnymi odstępami 300/100/200, dosłownie tworzą rytm, a cały
   film (100 mm ↔ 100 BPM, motyw z przekroju) jest zbudowany na tej idei. Słowo jest krótkie, polskie i czytelne
   za granicą.
2. **WARSTWA**. Nawiązuje do warstw sklejki i warstw druku 3D gałki, rymuje się z taglinem. Gorzej się wymawia poza
   Polską.
3. **ARKUSZ**. Opowiada pochodzenie: płaski arkusz, CNC, mebel. Brzmi jednak bardziej technicznie niż „premium”.

Przed publikacją trzeba sprawdzić znak w UPRP i EUIPO.

---

## 8. Wersje pochodne

### 8.1 Pionowy cutdown 9:16, 15,00 s (375 kl.), wyłącznie z renderów 2560×1440
Kolumna wycinana z kadru 16:9 ma **810×1440 px** (31,6% szerokości, pełna wysokość) i jest skalowana do 1080×1920.
Środek wycinka `cx` (0–1) jest kluczowany per ujęcie. Ujęcia zaprojektowano tak, żeby akcja mieściła się w kolumnie.

| V | Czas (s) | Źródło | cx (start → koniec) | Uwagi |
|---|---|---|---|---|
| V1 | 0,0–2,4 | S01 f0–60 | 0,45 | wznoszące się czoła półek to naturalny pion. Napis „Bez boków.” 0,4–2,3 s |
| V2 | 2,4–4,2 | S03 f180–225 | 0,50 → 0,46 → 0,47 (f210) | ogranicznik na 3,6 s, czyli na uderzeniu. Napis „Pełny wysuw.” |
| V3 | 4,2–6,0 | S04 f255–300 | 0,50 | skrzynka S10 zajmuje 35% kadru, boki przycięte o ~2%, ruch szuflady pionowy na ekranie. „thup” na 5,4 s. Napis „Cichy domyk.” |
| V4 | 6,0–7,2 | S07 f450–480 | 0,50 | środkowa kolumna arkuszy (28% szerokości) mieści się cała, pop na 6,6 s. Napis „140 elementów.” |
| V5 | 7,2–12,0 | S08 f480–600 | 0,50 → 0,505 | regał w f585 zajmuje x 0,36–0,65, mieści się |
| V6 | 12,0–15,0 | plansza 9:16 | — | sygnał RYTM na 12,0 s |

- **Muzyka 15 s** to osobny render z tego samego silnika:
  takt 1 hook | 2,4–6,0 groove (1,5 taktu) | 6,0–7,2 breakdown z popami i ciszą od 6,96 s | 7,2–12,0 drop |
  12,0–15,0 sygnał i wybrzmienie.
  Zdarzenia z `events.json` przesuwamy o offset ujęcia, na przykład f480 = 7,2 s.
- **Napisy 9:16:** Inter Display Light 72 px, środek, y 300–520. **Krytyczny tekst tylko w strefie y 270–1250 i x 65–1015.**
  Dolne ~35% i prawa szyna to interfejs Reels/TikTok ([Hopper/Meta](https://www.hopperhq.com/blog/instagram-reel-size/)).
- **Plansza 9:16:** glif 400 px wysokości, środek y 560 · „RYTM” 140 px na y 900 · tagline 52 px na y 990 ·
  opis 26 px na y 1060 · marka 28 px na y 1180.
- Opcjonalnie wersja 16:9, 15 s: ta sama edycja bez kadrowania, z planszą 16:9.

### 8.2 Inne formaty (opcja)
4:5 (1080×1350) do feedu: kadr 1152×1440 z 2560×1440, skalowany ×0,94. Te same `cx`.

---

## 9. Budżet renderu (CPU, 4 rdzenie, 15 GB RAM)

### 9.1 Ustawienia Cycles (wspólne)
- `device CPU`, `threads_mode FIXED = 4`, rozdzielczość 2560×1440 100%.
- Light tree ON ([notatki 3.5](https://developer.blender.org/docs/release_notes/3.5/cycles/)).
- Odbicia: max 4 (diffuse 3, glossy 2, transmission 0, volume 0, transparent 4), **caustics OFF**, filter glossy 1,0,
  clamp indirect 5.
- OIDN, prefilter Accurate, przebiegi albedo i normal; jakość HIGH w makro, BALANCED w szerokich.
- Adaptive sampling ([Renderjuice](https://www.development.renderjuice.com/blog/how-to-render-faster-in-blender)).
- `use_persistent_data = True`, **`use_animated_seed = False`** (stabilny wzór szumu, mniej migotania OIDN).
- Pixel filter Blackman‑Harris 1,5 px.
- Wyjście: PNG 16 bit, `use_overwrite = False`, `use_placeholder = True`, żeby dało się wznowić po awarii.
- Modyfikatory boolean (puszki zawiasów, szkielety arkuszy) **zastosować przed renderem**: bez ponownego liczenia
  w każdej klatce.
- **Drogie efekty i zamienniki:**
  - motion blur tylko w S08; plan B to przebieg Vector + Vector Blur w kompozytorze;
  - volumetria to zero mgły, „promienie” najwyżej jako lekki gradient w poście;
  - szkło i kaustyki: nie używamy, okno bez szyby;
  - mocny połysk: ceramika matowa, metal w małych ilościach;
  - DOF w Cycles jest praktycznie darmowy, ale mocny bokeh potrzebuje trochę więcej sampli (makro);
  - emisyjne lampy: brak.

### 9.2 Klatki i sample (zakładki ±3 kl., S04 renderuje stałe fragmenty jako pojedyncze klatki, S09 +10 kl. na przenikanie)
B = zmierzony czas jednej klatki S02 w 2560×1440 przy 36 spp. **Szacuję ~36 s**: prosta otwarta scena, OIDN, CPU 4C.
Liczbę trzeba potwierdzić benchmarkiem `scene/bench.py`.

| Ujęcie | Klatki | spp max (1440p) | Próg szumu | Współczynnik | s/kl. (B = 36) | Czas |
|---|---|---|---|---|---|---|
| S01 makro | 66 | 45 | 0,03 | ×1,1 | ~50 | 55 min |
| S02 szerokie | 126 | 36 | 0,035 | ×1,0 | ~36 | 76 min |
| S03 | 51 | 36 | 0,035 | ×1,05 | ~38 | 32 min |
| S04 top‑down | 54 | 27 | 0,04 | ×0,8 | ~22 | 20 min |
| S05 | 51 | 36 | 0,035 | ×1,0 | ~36 | 31 min |
| S06 makro | 81 | 45 | 0,03 | ×1,1 | ~50 | 67 min |
| S07 top‑down | 66 | 27 | 0,05 | ×0,7 | ~19 | 21 min |
| S08 montaż + MB | 126 | 27 | 0,05 | ×1,3 | ~35 | 74 min |
| S09 hero | 73 | 36 | 0,035 | ×1,05 | ~38 | 46 min |
| **Razem** | **694** | | | | | **≈ 7,0 h** |

Wersja 9:16 nie kosztuje dodatkowych renderów. Plansze 2D, napisy, grading i enkodowanie zajmują poniżej 15 min.

### 9.3 Kolejność i podglądy
1. **Animatik**: Cycles 640×360, 8 spp, OIDN, bez MB, cały film w ~20–25 min. Zmiksowany z pierwszą wersją muzyki
   służy do akceptacji timingu i synchronizacji.
2. **Klatki stylu**: po 1 klatce na ujęcie w pełnej jakości (~10 min), akceptacja looku i palety.
3. **Podgląd 720p dla S08** (1280×720, 16 spp): kontrola choreografii montażu.
4. **Finał według priorytetu:** S08 → S01 → S02 → S09 → S06 → S03 → S04 → S05 → S07. Najmocniejsze ujęcia są gotowe
   pierwsze, więc w razie braku czasu montaż awaryjny jest możliwy.

### 9.4 Ryzyka i plan B
| Ryzyko | Plan B |
|---|---|
| B > 45 s/kl. (budżet > 9 h) | po kolei: (1) Fast GI (Replace, AO 1 odbicie, 1 m) w S02/S07/S08/S09; (2) max odbić 3; (3) próg 0,05 wszędzie; (4) render 2240×1260 (kolumna 9:16 ma wtedy 709 px, upscale ×1,52, nadal akceptowalnie); (5) ostatecznie 1920×1080 i 9:16 z upscalem ×1,78 |
| Migotanie OIDN przy niskim spp | stały seed, min samples 16, ziarno w poście; w statycznych fragmentach pojedyncza klatka |
| Moiré warstw i szczelin w szerokich | gaszenie warstw z odległością (3.3) + supersampling 1440p |
| Boolean szkieletów (140 cięć) zbyt wolny lub błędny | płyta ofiarna `#8C7A66` bez otworów |
| Light linking maskownicy nie działa w 5.2 | maskownica jako zwykła płaszczyzna z `visible_camera = False`, `visible_glossy = False` |
| Dryf odcieni w AgX (terakota, brzoza) | korekta base color o ±3% odcienia lub look „Base Contrast” + krzywa w poście |
| Koszt MB w S08 | Vector Blur w kompozytorze (Blender 5.x) albo krótszy shutter 0,25 |
| Rozjazd dźwięku | zdarzenia wyłącznie z `events.json`, audio 48 kHz, czas = f/25, muzyka kwantyzowana do siatki 100 BPM |
| Render przeniesiony na GPU Maca (`MAC_SETUP.md`) | budżet spada ~3–5×: można podnieść spp ×2 i zostawić MB wszędzie, gdzie jest ruch |

---

## 10. Oś czasu do automatyzacji (skrót)
```yaml
fps: 25
bpm: 100            # 15 kl./ćwierćnuta, 3.75 kl./16-tka
render_res: [2560, 1440]
shots:
  - {id: S01, f: [0, 60],    lens: 50,  fstop: 4.0}
  - {id: S02, f: [60, 180],  lens: 35,  fstop: 5.6}
  - {id: S03, f: [180, 225], lens: 60,  fstop: 4.0, drawer: S09}
  - {id: S04, f: [225, 300], lens: 50,  fstop: 5.6, drawer: S10, locked: true}
  - {id: S05, f: [300, 345], lens: 50,  fstop: 4.0, door: DZ02}
  - {id: S06, f: [345, 420], lens: 100, fstop: 5.6}
  - {id: S07, f: [420, 480], lens: 35,  fstop: 8.0}
  - {id: S08, f: [480, 600], lens: 35,  fstop: 8.0, motion_blur: 0.4}
  - {id: S09, f: [600, 660], lens: 50,  fstop: 5.6, drawer: S03, rig: golden}
  - {id: S10, f: [660, 750], type: endcard_2d}
vertical_15s:
  - {src: S01, f: [0, 60],    cx: 0.45}
  - {src: S03, f: [180, 225], cx: [0.50, 0.46, 0.47]}
  - {src: S04, f: [255, 300], cx: 0.50}
  - {src: S07, f: [450, 480], cx: 0.50}
  - {src: S08, f: [480, 600], cx: [0.50, 0.505]}
  - {src: endcard_9x16, dur_f: 75}
contacts: {S03_stop: 210, S10_catch: 262, S10_contact: 285, DZ02_catch: 318, DZ02_contact: 330,
           P200_land: 555, fronts_last: 585, S03_contact: 630, sting: 660}
```
