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
    # nose_bay_profile obejmuje tez prawa krawedz przesla (xr, 0) - stad
    # min() zamiast all(), zeby wylapac wlasciwy punkt stycznosci luku
    prof = m.nose_bay_profile(p, d)
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

    # --- 5. polka siada plasko na progu wrebu oporowego, bez szczeliny ----
    xs = d["vertical_x"]
    rd = p["RABBET_DEPTH"]
    by_name = {q.name: q for q in parts}
    gaps = []
    for li in range(p["N_LEVELS"]):
        for b in range(p["N_BAYS"]):
            shelf = by_name["shelf-L%d-B%d" % (li, b)]
            xl, xr = shelf.bbox()[0], shelf.bbox()[3]
            if b > 0 and abs(xl - (xs[b] + p["T"] - rd)) > TOL:
                gaps.append(("shelf-L%d-B%d" % (li, b), "L", xl))
            if abs(xr - (xs[b + 1] + rd)) > TOL:
                gaps.append(("shelf-L%d-B%d" % (li, b), "R", xr))
    r.check("polki siadaja na progu wrebu bez szczeliny", not gaps,
            "wszystkie krawedzie na spodziewanym X" if not gaps else str(gaps[:3]))

    # --- 6. sruby w granicach glebokosci polki --------------------------
    bad_y = [y for y in list(p["BOLT_Y_LEFT"]) + list(p["BOLT_Y_RIGHT"])
             if not (0 < y < d["frame_depth"])]
    r.check("sruby M6 w granicach glebokosci polki", not bad_y,
            "4 sruby na zlacze, y = %s" % (list(p["BOLT_Y_LEFT"]) + list(p["BOLT_Y_RIGHT"]))
            if not bad_y else str(bad_y))

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
    print()
    print("masa netto (bez okuc): %.1f kg" % s["mass_kg"])
    print("elementow: %d, srub M6: %d" % (len(s["parts"]), s["n_bolts"]))
    sys.exit(1 if res.report() else 0)
