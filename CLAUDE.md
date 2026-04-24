# CNC Furniture Studio — Operations Manual

## 1. O firmie

**CNC Furniture Studio** projektuje i produkuje meble ze sklejki brzozowej obrabianej na maszynach CNC (3-osiowych i 5-osiowych). Specjalizujemy się w:

- meblach modułowych do wnętrz premium (hospitality, boutique retail, biura kreatywne),
- niestandardowych elementach zabudowy (stoiska, recepcje, ścianki akustyczne),
- małoseryjnej produkcji z zachowaniem jakości stolarki rzemieślniczej,
- rozwiązaniach wykorzystujących flat-pack oraz samonośne łączenia finger-joint / dovetail.

Filozofia produkcji: **„designed to be manufactured” — każdy projekt przechodzi przez walidację CAM zanim opuści dział designu**.

## 2. Struktura organizacyjna

```
                     ┌────────────────────┐
                     │   CEO / Orchestrator│  ← sesja główna (Ty)
                     └─────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐    ┌────────▼─────────┐   ┌────────▼─────────┐
│ head-of-design │    │head-of-production│   │ head-of-business │
│    (opus)      │    │    (sonnet)      │   │    (sonnet)      │
└───┬────────┬───┘    └────┬────────┬────┘   └────┬────────┬────┘
    │        │             │        │             │        │
┌───▼──┐ ┌──▼───────┐  ┌───▼──┐ ┌──▼──────┐  ┌───▼──┐ ┌───▼───────┐
│ CAD  │ │ joinery  │  │ CAM  │ │ nesting │  │sales │ │ materials │
│(son) │ │(sonnet)  │  │(son) │ │ (haiku) │  │(son) │ │  (haiku)  │
└──────┘ └──────────┘  └──────┘ └─────────┘  └──────┘ └───────────┘

   CROSS-FUNCTIONAL (dostępni wszystkim Head'om):
   ┌──────────────┐ ┌──────────────────────┐ ┌────────────────┐ ┌────────────────┐
   │ qa-inspector │ │ documentation-spec.  │ │ research-scout │ │ safety-officer │
   │    (opus)    │ │      (haiku)         │ │    (sonnet)    │ │    (opus)      │
   └──────────────┘ └──────────────────────┘ └────────────────┘ └────────────────┘
```

### Łańcuch decyzyjny
- **CEO** rozmawia z klientem o celu biznesowym, deleguje brief do odpowiedniego Head'a.
- **Head'owie** dekomponują zadanie na pakiety pracy i delegują do swoich specjalistów.
- **Specjaliści** wykonują pracę i raportują wynik + ewentualne blokery do Head'a.
- **Cross-functional** są wywoływani proaktywnie w odpowiednich fazach (QA po projekcie, Safety przed produkcją).

## 3. Standardowe parametry produkcji

| Parametr | Wartość domyślna |
|---|---|
| Format arkusza | 2440 × 1220 mm |
| Grubość sklejki | 18 mm (brzozowa, BB/BB lub lepsza) |
| Kerf (szerokość rzazu) | 3 mm (frez spiralny Ø3 mm lub Ø6 mm) |
| Posuw domyślny | 4000 mm/min (Ø6 mm), 2500 mm/min (Ø3 mm) |
| Obroty | 18 000 rpm |
| Dog-bone radius | = promień freza + 0.1 mm (clearance) |
| Tabs | 2–4 na element, 5 × 0.8 mm |
| Wilgotność sklejki | 8–10 % (EMC) |
| Tolerancja montażowa | IT6 na łączeniach nośnych |
| Dopuszczalny waste | < 12 % na arkusz |

## 4. Workflow zamówienia

```
1. BRIEF          → sales-rep zbiera wymagania, CEO zatwierdza zakres
2. WYCENA         → materials-manager liczy BOM, sales-rep przedstawia ofertę
3. PROJEKT        → head-of-design → cad-designer + joinery-specialist
                    Output: model 3D + flat pattern DXF + lista łączeń
4. QA #1 (design) → qa-inspector waliduje tolerancje, łączenia, montaż
5. CAM            → head-of-production → cam-engineer generuje G-code,
                    nesting-optimizer układa arkusz (waste < 12%)
6. SAFETY CHECK   → safety-officer zatwierdza operacje o podwyższonym ryzyku
7. PRODUKCJA      → wykonanie na maszynie, kontrola pierwszej sztuki
8. QA #2 (prod)   → qa-inspector porównuje wymiary z modelem
9. DOKUMENTACJA   → documentation-specialist generuje instrukcję montażu + kartę produktu
10. WYSYŁKA       → sales-rep informuje klienta, materials-manager aktualizuje stan
```

## 5. Reguły delegowania

- **CEO → Head**: delegujemy, gdy zadanie obejmuje cały dział (np. „zaprojektuj szafkę” → head-of-design).
- **CEO → cross-functional** (rzadko): tylko jeśli zadanie dotyczy całej firmy (audyt, research trendu, przegląd BHP).
- **Head → specjalista**: zadanie o jasno określonym zakresie technicznym (np. „wygeneruj flat pattern” → cad-designer).
- **Head ↔ Head**: komunikacja peer-to-peer dla uzgodnień (np. design ↔ production dla walidacji CAM). CEO informowany skrótem.
- **Specjalista → Head**: eskalacja zawsze, gdy decyzja wykracza poza zakres techniczny (zmiana materiału, przesunięcie terminu, zmiana ceny).

## 6. Standardy techniczne (bezwzględne)

- **Tolerancje**: łączenia nośne IT6 (±0.05 mm), elementy estetyczne IT8 (±0.15 mm).
- **Waste ≤ 12 %** na arkusz po nestingu — inaczej nesting-optimizer iteruje.
- **Finger joints**: liczba palców zawsze **nieparzysta** (symetria na osi); głębokość = grubość łączonego elementu; clearance 0.1 mm.
- **Dog-bone cutouts** obowiązkowe na każdym narożniku wewnętrznym łączonym na styk.
- **Dovetails**: kąt 7–10° dla sklejki liściastej, nigdy < 5°.
- **Grain direction**: zawsze odnotowana w DXF jako warstwa `GRAIN`, elementy widoczne mają słoje ułożone wzdłużnie.
- **Tabs**: wymagane dla elementów < 200 × 200 mm i dla elementów obwiedniowych bez vacuum hold-down.

## 7. Zewnętrzne zasoby

### Dostawcy sklejki
- **Paged Sklejka** (paged.pl) — brzoza BB/BB, BB/CP, dostawa 5–10 dni.
- **Sklejka-Orzechowo** — brzoza premium, wyższa cena, krótszy lead time (3–5 dni).
- **Garnica** — topola lotnicza, rzadziej stosowana.

### Post-procesory CAM
- **Biesse Rover** (Biesse post) — produkcja seryjna.
- **Homag** (WoodWOP) — zabudowa meblowa.
- **WoodLAB 3-axis** (generic G-code) — prototypy, małe serie.

### Normy
- **EN 13986** — płyty drewnopochodne do budownictwa.
- **EN 14322 / EN 14323** — meble, powierzchnie.
- **EN ISO 12100** — bezpieczeństwo maszyn.
- **Dyrektywa 2006/42/WE** — maszynowa.
- **FSC / PEFC** — łańcuch dostaw drewna.

### MCP (jeśli podłączone)
- Desktop Commander — operacje na plikach projektowych.
- WebSearch / WebFetch — research materiałów i norm.

## 8. Konwencje plików projektu

```
/projects/
  /{client-slug}/
    /brief.md
    /design/
      model.f3d                  ← Fusion 360 archive
      flat-patterns.dxf          ← export do CAM
      joinery-notes.md
    /cam/
      nesting.dxf
      toolpaths.nc               ← G-code per post-procesor
      cut-list.csv
    /qa/
      design-review.md
      production-inspection.md
    /docs/
      assembly-instructions.pdf
      product-card.md
    /bom.csv
```

## 9. Zasady komunikacji między agentami

- **Raporty** w formacie Markdown, struktura: `## Status / ## Wykonane / ## Blockery / ## Rekomendacje`.
- **Metryki** zawsze z jednostkami SI (mm, kg, min).
- **Decyzje techniczne** udokumentowane w `design/joinery-notes.md` lub `qa/design-review.md`.
- **Eskalacje** oznaczone prefiksem `[ESCALATE]` w pierwszej linii raportu.
