"""
Testy geometrii regalu R150.

Uruchomienie:  python3 checks.py
Zwraca kod 1 gdy ktorykolwiek test nie przejdzie (nadaje sie do CI).
"""

import math
import sys

import shelf_model as m

EPS = 1e-6
TOL = 0.01          # tolerancja domykania lancucha wymiarowego [mm]
TOUCH = 1e-4        # ponizej tego uznajemy styk, nie przenikanie


# ---------------------------------------------------------------- geometria 2D

def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if v > EPS:
        return 1
    if v < -EPS:
        return -1
    return 0


def segments_properly_cross(a, b, c, d):
    """True tylko dla przeciecia w punkcie wewnetrznym obu odcinkow.

    Odcinki wspolliniowe / stykajace sie koncami -> False (to styk, nie kolizja).
    """
    o1, o2 = _orient(a, b, c), _orient(a, b, d)
    o3, o4 = _orient(c, d, a), _orient(c, d, b)
    return o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0 and o1 != o2 and o3 != o4


def point_in_poly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xi > x:
                inside = not inside
    return inside


def dist_to_boundary(pt, poly):
    x, y = pt
    best = float("inf")
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        best = min(best, math.hypot(x - (ax + t * dx), y - (ay + t * dy)))
    return best


def point_strictly_inside(pt, poly, eps=TOUCH):
    return point_in_poly(pt, poly) and dist_to_boundary(pt, poly) > eps


def polygons_overlap(pa, pb):
    """Przenikanie obrysow. Sam styk krawedzi / naroznikow nie liczy sie."""
    for pt in pa:
        if point_strictly_inside(pt, pb):
            return True
    for pt in pb:
        if point_strictly_inside(pt, pa):
            return True
    na, nb = len(pa), len(pb)
    for i in range(na):
        a, b = pa[i], pa[(i + 1) % na]
        for j in range(nb):
            c, d = pb[j], pb[(j + 1) % nb]
            if segments_properly_cross(a, b, c, d):
                return True
    return False


def ranges_overlap(r0, r1, s0, s1, eps=TOUCH):
    return min(r1, s1) - max(r0, s0) > eps


def point_in_bbox(pt, bbox, margin=0.0):
    """Runda 9.1 (NC-19, audyt qa-inspector) - klasa testow luzu okuc:
    czy punkt (np. leb sruby) wpada w bryle bbox innego elementu. Celowo
    proste (AABB, nie pelny CSG) - wystarcza do wykrycia dokladnie tego typu
    bledu, ktory audyt zlapal (NC-01/NC-02): punkt wiercenia bez sprawdzenia
    materialu, ktory tam juz stoi."""
    x, y, z = pt
    x0, y0, z0, x1, y1, z1 = bbox
    return (x0 - margin <= x <= x1 + margin and
            y0 - margin <= y <= y1 + margin and
            z0 - margin <= z <= z1 + margin)


# ---------------------------------------------------------------- testy

class Results:
    def __init__(self):
        self.rows = []

    def check(self, name, ok, detail=""):
        self.rows.append((name, bool(ok), detail))

    def report(self):
        width = max(len(r[0]) for r in self.rows)
        failed = 0
        for name, ok, detail in self.rows:
            tag = "PASS" if ok else "FAIL"
            if not ok:
                failed += 1
            print("[%s] %-*s  %s" % (tag, width, name, detail))
        print("\n%d/%d testow przeszlo" % (len(self.rows) - failed, len(self.rows)))
        return failed


def run():
    p, d = m.PARAMS, m.DERIVED
    parts = m.build_parts(p, d)
    r = Results()

    # --- 1. gabaryty ---------------------------------------------------
    # calkowita wysokosc = korpus (p["H"]) + cokol (p["PLINTH_H"]) = 2000
    total_h = p["H"] + p["PLINTH_H"]
    bxs = [q.bbox() for q in parts]
    bb = (min(b[0] for b in bxs), min(b[1] for b in bxs), min(b[2] for b in bxs),
          max(b[3] for b in bxs), max(b[4] for b in bxs), max(b[5] for b in bxs))
    r.check("bbox bryly = 1800 x 400 x 2000 (korpus+cokol)",
            abs(bb[3] - bb[0] - p["W"]) < TOL and abs(bb[4] - bb[1] - p["D"]) < TOL
            and abs(bb[5] - bb[2] - total_h) < TOL,
            "%.1f x %.1f x %.1f mm" % (bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]))

    r.check("korpus + cokol = 2000 mm dokladnie",
            abs(total_h - 2000.0) < TOL,
            "korpus %.0f + cokol %.0f = %.1f" % (p["H"], p["PLINTH_H"], total_h))

    # --- 2. stycznosc luku ---------------------------------------------
    # profil plyty obejmuje tez prosta krawedz frontu - stad min() zamiast
    # all(), zeby wylapac wlasciwy punkt stycznosci luku
    prof = m.full_plate_profile(p, d)
    at_front = [q for q in prof if abs(q[1]) < TOL]
    at_side = [q for q in prof if abs(q[0]) < TOL]
    front_x = min(q[0] for q in at_front) if at_front else None
    r.check("luk styczny do frontu w x=150",
            front_x is not None and abs(front_x - p["R"]) < TOL,
            "punkt stycznosci (%.1f, 0)" % front_x if front_x is not None else "brak")
    r.check("luk styczny do lewego boku w y=150",
            bool(at_side) and min(q[1] for q in at_side) - p["R"] > -TOL,
            "punkt stycznosci (0, %.1f)" % min(q[1] for q in at_side) if at_side else "brak")

    cx, cy = d["arc_center"]
    arc_pts = [q for q in prof
               if q[0] <= p["R"] + TOL and q[1] <= p["R"] + TOL
               and abs(math.hypot(q[0] - cx, q[1] - cy) - p["R"]) < TOL]
    r.check("lico zewnetrzne luku ma staly promien R150",
            len(arc_pts) >= p["ARC_SEGMENTS"],
            "%d punktow na R%.0f wzgledem srodka (%.0f, %.0f)"
            % (len(arc_pts), p["R"], cx, cy))

    # --- 3. lancuch wymiarowy ------------------------------------------
    horiz = p["R"] + len(d["vertical_x"]) * p["T"] + p["N_BAYS"] * d["bay_clear"]
    r.check("lancuch poziomy domyka sie do 1800",
            abs(horiz - p["W"]) < TOL,
            "150 nos + %d x 18 piony + %d x %.1f swiatlo = %.1f"
            % (len(d["vertical_x"]), p["N_BAYS"], d["bay_clear"], horiz))

    vert = (p["N_LEVELS"] - 1) * d["shelf_clear"] + p["N_LEVELS"] * p["T"]
    r.check("lancuch pionowy korpusu domyka sie do 1900",
            abs(vert - p["H"]) < TOL,
            "%d x %.1f swiatlo + %d x 18 poziomow = %.1f (+ cokol %.0f = 2000)"
            % (p["N_LEVELS"] - 1, d["shelf_clear"], p["N_LEVELS"], vert, p["PLINTH_H"]))

    # --- 4. przenikanie ------------------------------------------------
    # zaden legalny para elementow nie powinna sie juz przenikac - polka
    # siedzi we wrebie oporowym pionu (rowna sciezka co wczesniej wrab
    # noska), wiec brak wyjatkow: to jest prawdziwa weryfikacja dopasowania.
    collisions = []
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            a, b = parts[i], parts[j]
            az, bz = a.z_range(), b.z_range()
            if not ranges_overlap(az[0], az[1], bz[0], bz[1]):
                continue
            ab, bbx = a.bbox(), b.bbox()
            if not (ranges_overlap(ab[0], ab[3], bbx[0], bbx[3])
                    and ranges_overlap(ab[1], ab[4], bbx[1], bbx[4])):
                continue
            if polygons_overlap(a.footprint(), b.footprint()):
                collisions.append((a.name, b.name))
    r.check("brak przenikania miedzy elementami",
            not collisions,
            "0 kolizji na %d elementow" % len(parts) if not collisions
            else "%d kolizji, np. %s" % (len(collisions), collisions[:3]))

    # --- 5. dolna i gorna plyta to jeden kawalek na pelne 1800 mm ---------
    xs = d["vertical_x"]
    by_name = {q.name: q for q in parts}
    plate_bad = []
    for nm in ("plate-bottom", "plate-top"):
        q = by_name.get(nm)
        if q is None:
            plate_bad.append((nm, "brak"))
            continue
        bb = q.bbox()
        if abs((bb[3] - bb[0]) - p["W"]) > TOL:
            plate_bad.append((nm, "szerokosc %.1f" % (bb[3] - bb[0])))
    r.check("dolna i gorna plyta: jeden kawalek 1800 mm", not plate_bad,
            "2 plyty pelnej szerokosci, naroznik R150" if not plate_bad
            else str(plate_bad))

    # --- 5b. runda 7: zero wrebow - kazdy pion ma pelna grubosc T na calej
    # wysokosci. Wczesniejsze rundy scieniały piony posrednie o 2 x 5 mm
    # (56% grubosci), co lamalo regule "nigdy wiecej niz 1/2 lacznie". ---
    thin = []
    for q in parts:
        if q.kind != "vertical":
            continue
        bb = q.bbox()
        if abs((bb[3] - bb[0]) - p["T"]) > TOL:
            thin.append((q.name, round(bb[3] - bb[0], 1)))
    r.check("zaden pion nie jest scieniany (zero wrebow)", not thin,
            "%d pionow, kazdy pelne %.0f mm" % (
                sum(1 for q in parts if q.kind == "vertical"), p["T"])
            if not thin else str(thin[:3]))

    # --- 5c. piony stoja MIEDZY plytami, nie przez nie -------------------
    T = p["T"]
    span = []
    for q in parts:
        if q.kind != "vertical":
            continue
        z0, z1 = q.z_range()
        if abs(z0 - (p["PLINTH_H"] + T)) > TOL or abs(z1 - (p["PLINTH_H"] + p["H"] - T)) > TOL:
            span.append((q.name, round(z0, 1), round(z1, 1)))
    r.check("piony stoja miedzy plytami (%.0f mm wysokosci)" % (p["H"] - 2 * T),
            not span,
            "wszystkie 4 piony od z=%.0f do z=%.0f" % (
                p["PLINTH_H"] + T, p["PLINTH_H"] + p["H"] - T)
            if not span else str(span[:3]))

    # --- 6. sruby pion <-> plyta: pionowe, lico plyty wolne --------------
    bolts = m.bolt_positions(p, d)
    bad_y = [y for y in p["BOLT_Y"] if not (0 < y < d["frame_depth"])]
    expect = len(xs) * len(p["BOLT_Y"]) * 2
    r.check("%d srub M6 pion-plyta, wszystkie pionowe" % expect,
            not bad_y and len(bolts) == expect
            and all(bt[3] in ("+z", "-z") for bt in bolts),
            "%d srub, 2 na czolo pionu, y = %s" % (len(bolts), list(p["BOLT_Y"]))
            if not bad_y else str(bad_y))

    # --- 6b. kolki polkowe trafiaja w lica pionow ------------------------
    pins = m.shelf_pin_positions(p, d)
    faces = set()
    for x in xs:
        faces.add(round(x, 3))
        faces.add(round(x + T, 3))
    off = [q for q in pins if round(q[0], 3) not in faces]
    # fizycznych polek (jednostek do wyjecia), NIE licznik Part - runda 9.1
    # rozbila polki przesla 0 na kilka sklejonych kawalkow (luz pod leb sruby
    # NC-02), wiec sum(qty_group=="shelf-bay") liczylby CNC-kawalki, nie
    # polki - myllace w tym konkretnym opisie testu (patrz preview_gen.py o
    # tej samej roznicy dla vertical-L-gable)
    n_shelves = (p["N_LEVELS"] - 2) * p["N_BAYS"]
    r.check("kolki Ø5 w licach pionow, %d polek przestawialnych" % n_shelves,
            not off,
            "%d otworow, wszystkie na licu pionu" % len(pins) if not off
            else str(off[:3]))

    # --- 6f. male poleczki naroznika (runda 8) obecne na 4 srodkowych
    # poziomach, skrecone do lica lewego boku (x=R) ------------------------
    corners = [q for q in parts if q.qty_group == "nose-corner"]
    cbolts = m.nose_corner_bolt_positions(p, d)
    bad_cb = [b for b in cbolts if abs(b[0] - p["R"]) > TOL]
    r.check("4 poleczki naroznika, %d srub mocujacych do lica pionu"
            % len(cbolts),
            len(corners) == p["N_LEVELS"] - 2 and not bad_cb,
            "%d poleczek, %d srub na x=%.0f" % (len(corners), len(cbolts), p["R"])
            if not bad_cb else str(bad_cb[:3]))

    # --- 6g. boki/tyl szuflady w oficjalnym zakresie grubosci Blum TANDEM
    # (1/2"-3/4" = 12.7-19.0 mm - blum.com/us/en/products/runnersystems/
    # tandem, runda 9 poprawka) - dawniej test wymuszal max 16 mm mysznie
    # biorac punkt odniesienia wzoru na luz za twardy limit gornej granicy
    BLUM_MIN, BLUM_MAX = 12.7, 19.0
    off_spec = [q for q in parts
                if q.qty_group in ("drawer-side", "drawer-back")
                and not (BLUM_MIN - TOL <= q.thickness <= BLUM_MAX + TOL)]
    r.check("boki/tyl szuflad w zakresie Blum TANDEM %.1f-%.1f mm" % (BLUM_MIN, BLUM_MAX),
            not off_spec,
            "wszystkie %d elementow w zakresie" % sum(
                1 for q in parts if q.qty_group in ("drawer-side", "drawer-back"))
            if not off_spec else str([q.name for q in off_spec][:3]))

    # NC-17 (audyt qa-inspector): RUNNER_NL byl niesprawdzonym parametrem -
    # docstring twierdzil "dobrane do DRAWER_DEPTH" ale nic tego nie
    # egzekwowalo. Teraz przynajmniej ta jedna relacja jest pilnowana.
    r.check("RUNNER_NL zgodne z DRAWER_DEPTH (wg dokumentacji)",
            abs(p["RUNNER_NL"] - p["DRAWER_DEPTH"]) < TOL,
            "RUNNER_NL=%.0f, DRAWER_DEPTH=%.0f" % (p["RUNNER_NL"], p["DRAWER_DEPTH"]))

    # --- 6h. otwory pod prowadnice trafiaja w lico pionu / boku szuflady -
    runs = m.runner_positions(p, d)
    faces = {round(v, 3) for v in xs} | {round(v + p["T"], 3) for v in xs}
    run_bad = []
    for x, y, z, side in runs:
        if side == "corpus" and round(x, 3) not in faces:
            run_bad.append((x, y, z, side))
    r.check("%d wkretow prowadnic Blum na %d parach szuflad"
            % (len(runs), len(p["DRAWER_CELLS"])),
            not run_bad,
            "wszystkie na licach pionow" if not run_bad else str(run_bad[:3]))

    # --- 6m. runda 9.2 (klient: "nie widze zadnego rowka ani polaczen dla
    # spodu szuflady") - rowek pod dno musi zostawic sensowna sciankie w
    # bokach/tyle, a kolki naroznikowe musza trafiac w realny material ----
    core_wall = p["T"] - p["DRAWER_GROOVE_DEPTH"]
    r.check("rowek dna szuflady zostawia scianke >= 10 mm w boku/tyle",
            core_wall >= 10.0,
            "T=%.0f - DRAWER_GROOVE_DEPTH=%.0f = %.0f mm" %
            (p["T"], p["DRAWER_GROOVE_DEPTH"], core_wall))

    # boki/tyl szuflady sa poklejone na 3 pasma (rowek) - Part.area_m2()
    # domyslnie zaklada, ze najmniejszy z 3 wymiarow to grubosc, co dla
    # waskich pasm (wysokosc pasma < T) jest falszywe (ta sama kategoria
    # bledu co NC-16 z audytu) - kazdy bok/tyl ma jawny area_override;
    # sprawdzamy, ze suma pasm nadal daje pole calego, niescienionego panelu
    box_h = p["DRAWER_BOX_H"]
    depth = p["DRAWER_DEPTH"]
    x0_00, x1_00, _, _ = m._cell_opening(0, 0, p, d)
    width_00 = (x1_00 - p["RUNNER_CLEAR"]) - (x0_00 + p["RUNNER_CLEAR"]) - 2 * T
    by_group = {}
    for q in parts:
        if q.qty_group in ("drawer-side", "drawer-back") and q.name.startswith("drawer-00-"):
            key = q.name.rsplit("-", 1)[0]
            by_group[key] = by_group.get(key, 0.0) + q.area_m2()
    bad_area = []
    for k, v in by_group.items():
        exp = (depth if "side" in k else width_00) * box_h / 1e6
        if abs(v - exp) > 1e-4:
            bad_area.append((k, round(v, 4), round(exp, 4)))
    r.check("pasma boku/tylu szuflady sumuja sie do pola pelnego panelu",
            not bad_area,
            "wszystkie %d grup zgodne" % len(by_group) if not bad_area
            else str(bad_area[:3]))

    drawer_bb = [q.bbox() for q in parts if q.kind == "drawer"]
    corner_dowels = m.drawer_corner_dowel_positions(p, d)
    front_dowels = m.drawer_front_dowel_positions(p, d)
    miss_corner = [(round(x), round(y), round(z)) for x, y, z, side in corner_dowels
                   if not any(point_in_bbox((x, y, z), bb, margin=1.0) for bb in drawer_bb)]
    miss_front = [(round(x), round(y), round(z)) for x, y, z, side in front_dowels
                  if not any(point_in_bbox((x, y, z), bb, margin=1.0) for bb in drawer_bb)]
    r.check("%d kolkow naroznika bok<->tyl trafia w material szuflady" % len(corner_dowels),
            not miss_corner, "wszystkie trafiaja" if not miss_corner
            else "%d chybia: %s" % (len(miss_corner), miss_corner[:3]))
    r.check("%d kolkow front<->bok trafia w material szuflady" % len(front_dowels),
            not miss_front, "wszystkie trafiaja" if not miss_front
            else "%d chybia: %s" % (len(miss_front), miss_front[:3]))

    # --- 6c. kotwy korpus <-> cokol trafiaja w szyny/zebra ramy ----------
    anchors = m.plinth_bolt_positions(p, d)
    plinth_fp = [q.footprint() for q in parts if q.kind == "plinth"]
    missed = []
    for ax, ay, _, _ in anchors:
        if not any(point_in_poly((ax, ay), fp) for fp in plinth_fp):
            missed.append((round(ax), round(ay)))
    r.check("kazda kotwa korpus-cokol trafia w material ramy", not missed,
            "%d kotew M6 w szynach/zebrach" % len(anchors) if not missed
            else "%d chybia: %s" % (len(missed), missed[:3]))

    # --- 6i. NC-19 (audyt qa-inspector): klasa testow luzu okuc - lby srub
    # sprawdzone wprost przeciwko materialowi, nie tylko "0 kolizji plyta-
    # plyta" jak test 1. To ta klasa testow, ktorej brak pozwolil NC-01/02/08
    # przejsc niezauwazonym w rundzie 9 mimo 26/26 -----------------------
    ribs_bb = [q.bbox() for q in parts if q.qty_group == "plinth-rib"]
    bolts_bottom = [b for b in m.bolt_positions(p, d) if b[3] == "+z"]
    crushed = [(round(x), round(y)) for x, y, z, _ in bolts_bottom
               if any(point_in_bbox((x, y, z - 1.0), rb) for rb in ribs_bb)]
    r.check("leb sruby dno<->pion ma luz od zebra cokolu (NC-01)", not crushed,
            "wszystkie %d wolne" % len(bolts_bottom) if not crushed
            else "%d zderzen: %s" % (len(crushed), crushed[:3]))

    shelf_b0 = [q.bbox() for q in parts if q.qty_group == "shelf-bay" and "-B0-" in q.name]
    head_x = p["R"] + T
    crushed2 = [(round(y), round(z)) for x, y, z, _ in cbolts
                if any(point_in_bbox((head_x, y, z), sb) for sb in shelf_b0)]
    r.check("leb sruby poleczki naroznika ma luz od polki B0 (NC-02)", not crushed2,
            "wszystkie %d wolne" % len(cbolts) if not crushed2
            else "%d zderzen: %s" % (len(crushed2), crushed2[:3]))

    EDGE_MIN = 8.0
    close_edge = []
    for ax, ay, _, _ in anchors:
        for fp in plinth_fp:
            if point_in_poly((ax, ay), fp) and dist_to_boundary((ax, ay), fp) < EDGE_MIN:
                close_edge.append((round(ax), round(ay)))
    r.check("kotwy korpus-cokol maja luz >= %.0f mm od krawedzi ramy (NC-08)" % EDGE_MIN,
            not close_edge, "wszystkie %d z luzem" % len(anchors) if not close_edge
            else "%d za blisko: %s" % (len(close_edge), close_edge[:3]))

    core = T - 2 * p["PIN_DEPTH"]
    r.check("kolki polkowe: 2x PIN_DEPTH zostawia rdzen w pionie (NC-07)",
            core > TOL,
            "rdzen %.1f mm (T=%.0f mm, PIN_DEPTH=%.1f mm x2 strony)" % (core, T, p["PIN_DEPTH"]))

    # --- 6d. wyposazenie komor miesci sie w swietle, nic sie nie dubluje --
    cells_dr = set(p["DRAWER_CELLS"])
    cells_do = set(p["DOOR_CELLS"])
    clash = cells_dr & cells_do
    oversize = []
    for q in parts:
        if q.kind not in ("drawer", "door"):
            continue
        bb = q.bbox()
        if bb[0] < -TOL or bb[3] > p["W"] + TOL:
            oversize.append(q.name)
    r.check("szuflady i drzwiczki: %d + %d komor, bez kolizji zakresu"
            % (len(cells_dr), len(cells_do)),
            not clash and not oversize,
            "%d szuflad, %d drzwi (zawiasy %s)" % (
                len(cells_dr), len(cells_do),
                "/".join(sorted(set(p["DOOR_CELLS"].values()))))
            if not clash else "ta sama komora ma szuflade i drzwi: %s" % sorted(clash))

    # --- 6e. zawiasy siedza przy wlasciwej krawedzi drzwi ----------------
    hinges = m.hinge_positions(p, d)
    hin_bad = []
    for (li, b), side in p["DOOR_CELLS"].items():
        x0, x1, _, _ = m._cell_opening(li, b, p, d)
        mine = [h for h in hinges if h[3] == side
                and x0 - TOL <= h[0] <= x1 + TOL]
        for h in mine:
            near_left = abs(h[0] - x0) < (x1 - x0) / 2.0
            if (side == "L") != near_left:
                hin_bad.append((li, b, side, round(h[0])))
    r.check("puszki zawiasow Ø35 po zadanej stronie drzwi", not hin_bad,
            "%d puszek, strona wg DOOR_CELLS" % len(hinges) if not hin_bad
            else str(hin_bad[:3]))

    # --- 7. wymogi CLAUDE.md -------------------------------------------
    ok_grain = [q for q in parts if q.grain not in ("longitudinal", "crosswise", "free")]
    r.check("kazdy element ma zadeklarowane sloje", not ok_grain,
            "%d elementow" % len(parts) if not ok_grain else str(ok_grain[:3]))

    # --- 8. elementy miesza sie na arkuszu 2440 x 1220 ------------------
    over = []
    for q in parts:
        b = q.bbox()
        dims = sorted([b[3] - b[0], b[4] - b[1], b[5] - b[2]])[1:]
        if dims[0] > 1220 - 20 or dims[1] > 2440 - 20:
            over.append((q.name, round(dims[0], 1), round(dims[1], 1)))
    r.check("kazdy element miesci sie na arkuszu 2440 x 1220", not over,
            "najwiekszy: %s" % max(
                (sorted([b[3] - b[0], b[4] - b[1], b[5] - b[2]])[1:], q.name)
                for q in parts)[1]
            if not over else str(over[:3]))

    # --- 9. triangulacja pokrywa profil bez dziur i zakladek ------------
    worst = 0.0
    worst_name = ""
    for q in parts:
        if q.geom["type"] != "prism_z":
            continue
        prof = q.geom["profile"]
        target = abs(m.polygon_area(prof))
        got = sum(abs(m._cross(prof[a], prof[b], prof[c])) / 2.0
                  for a, b, c in m.triangulate_2d(prof))
        rel = abs(got - target) / target
        if rel > worst:
            worst, worst_name = rel, q.name
    r.check("triangulacja odtwarza pole profilu", worst < 1e-9,
            "max blad %.2e (%s)" % (worst, worst_name or "-"))

    # --- 10. rozpietosc polki ------------------------------------------
    r.check("rozpietosc polki <= 800 mm (sklejka 18, gl. 400)",
            d["bay_clear"] <= 800.0,
            "swiatlo przesla %.0f mm" % d["bay_clear"])

    # --- 10b. dno szuflady - grubosc minimalna wg limitu ugiecia (NC-04,
    # audyt qa-inspector) - 4 mm (jak plecy) dawalo ugiecie znacznie ponad
    # L/300 pod obciazeniem ocenianym na nosnosc prowadnicy Blum; szczegoly
    # rachunku w joinery-notes.md sekcja 3 -------------------------------
    MIN_BOTTOM_T = 8.0
    r.check("dno szuflady >= %.0f mm (limit ugiecia L/300, NC-04)" % MIN_BOTTOM_T,
            p["DRAWER_BOTTOM_T"] >= MIN_BOTTOM_T,
            "DRAWER_BOTTOM_T = %.0f mm" % p["DRAWER_BOTTOM_T"])

    # --- 11. cokol nigdzie nie wychodzi poza zaokraglony nawis korpusu --
    cx, cy = d["arc_center"]
    corner = next((q for q in parts if q.name == "plinth-corner"), None)
    over_r = []
    if corner:
        for x, y in corner.geom["profile"]:
            dist = math.hypot(x - cx, y - cy)
            if dist > p["R"] + TOL:
                over_r.append((x, y, dist))
    r.check("cokol miesci sie pod lukiem R150 (zaden punkt > R od srodka)",
            not over_r,
            "wszystkie punkty naroznika <= R%.0f" % p["R"]
            if not over_r else "wystaje %d punktow, np. %s" % (len(over_r), over_r[:2]))

    # --- 11b. cofniecie cokolu (runda 5) omija listwe przypodlogowa -------
    margin = p["PLINTH_INSET"] - p["SKIRTING_DEPTH"]
    r.check("cofniecie cokolu (%.0f mm) >= glebokosc listwy (%.0f mm)"
            % (p["PLINTH_INSET"], p["SKIRTING_DEPTH"]),
            margin >= 0,
            "%.0f mm zapasu" % margin if margin >= 0 else "%.0f mm za malo" % -margin)

    # --- 12. korpus siada dokladnie na gorze cokolu, bez szczeliny -------
    plinth_top = p["PLINTH_H"]
    corpus_bottom = min(q.z_range()[0] for q in parts if q.kind != "plinth")
    r.check("korpus siada dokladnie na gorze cokolu (bez szczeliny)",
            abs(corpus_bottom - plinth_top) < TOL,
            "spod korpusu przy z=%.1f mm, gora cokolu z=%.1f mm"
            % (corpus_bottom, plinth_top))

    return r


if __name__ == "__main__":
    res = run()
    s = m.summary()
    runners = m.runner_positions()
    n_runner_pairs = len(m.PARAMS["DRAWER_CELLS"])
    n_screws = len(runners)
    print()
    print("masa netto (bez okuc): %.1f kg" % s["mass_kg"])
    print("elementow: %d, srub M6: %d, prowadnice Blum TANDEM 562H: %d par (%d wkretow)"
          % (len(s["parts"]), s["n_bolts"], n_runner_pairs, n_screws))
    print()
    print("BOM - takie same elementy x ilosc:")
    groups = {}
    for pt in s["parts"]:
        e = groups.setdefault(pt.qty_group, {"n": 0, "mat": pt.material})
        e["n"] += 1
    for name, e in sorted(groups.items()):
        print("  %-16s %2d szt.  (%s)" % (name, e["n"], e["mat"]))
    print()
    print("uwaga: plinth-rib i shelf-bay licza kawalki CNC, nie fizyczne")
    print("jednostki po montazu - runda 9.1 rozbila zebra cokolu i polki")
    print("przesla 0 na kilka sklejonych kawalkow (luz pod leb sruby,")
    print("NC-01/NC-02) - fizycznie to nadal 3 zebra i 12 polek, jak w")
    print("nazwach 'plinth-rib-<i>-<j>' / 'shelf-L<li>-B0-strip-<j>'.")
    sys.exit(1 if res.report() else 0)
