"""
Regal R150 - parametryczny model brylowy (czysty Python, bez bpy).

Jedyne zrodlo prawdy dla geometrii. Uzywany przez:
  - blender_emit.py     -> mesh w Blenderze
  - preview_gen.py      -> podglad HTML / rzuty SVG
  - (runda 2) dxf_gen   -> flat patterns

Uklad wspolrzednych (mm):
  X: 0 = lewa krawedz  -> 1800 = prawa
  Y: 0 = front         -> 400  = tyl
  Z: 0 = podloga       -> 2000 = gora calosci (korpus 1900 + cokol 100)

Zaoblenie: przedni lewy narozik, luk R150 o srodku (150, 150),
styczny do frontu (y=0) w x=150 i do lewego boku (x=0) w y=150.

Cokol (runda 4): regal stoi tylem i prawym bokiem do sciany, gdzie listwa
przypodlogowa (85 mm wys., 20 mm gl.) nie pozwala korpusowi dotknac sciany
na poziomie podlogi. Cokol podnosi korpus ponad listwe; przy scianach jest
cofniety o SKIRTING_DEPTH, zeby ja ominac. build_parts() buduje korpus w
lokalnych wspolrzednych (z=0 na dole korpusu) i przesuwa go w gore o
PLINTH_H, a cokol dokleja osobno na samym dole (z=0..PLINTH_H).
"""

import math

# ---------------------------------------------------------------- parametry

PARAMS = {
    # gabaryty calosci (korpus + cokol = 2000 mm - runda 4, na zyczenie klienta)
    "W": 1800.0,            # szerokosc calkowita
    "H": 1900.0,            # wysokosc samego korpusu (2000 - PLINTH_H)
    "D": 400.0,             # glebokosc calkowita
    # material
    "T": 18.0,              # sklejka brzozowa konstrukcyjna
    "BACK": 4.0,            # sklejka - plecy
    # zaoblenie
    "R": 150.0,             # promien zewnetrzny przedniego lewego naroznika
    # podzialy
    "N_LEVELS": 6,          # poziomy poziome: dno + 4 polki + wieniec
    "N_BAYS": 3,            # przesla miedzy pionami
    # stolarka
    "NOTCH_DEPTH": 310.0,   # wrab w lewym boku: otwarty na ta glebokosc od frontu
    "RABBET_DEPTH": 5.0,    # wrab oporowy pod polki - patrz joinery-notes.md sekcja 1
    "BOLT_Y_LEFT": (140.0, 200.0),
    "BOLT_Y_RIGHT": (320.0, 380.0),
    "BOLT_D": 6.0,          # M6
    "DOWEL_D": 10.0,        # mimosrod beczkowy (gwint zenski, nie wkret)
    # cokol - runda 4: tyl i prawy bok przylegaja do sciany, listwa
    # przypodlogowa 85 mm wys. x 20 mm gl. (odstaje od sciany)
    "PLINTH_H": 100.0,      # 85 mm listwa + 15 mm przeswitu na nierownosci
    "PLINTH_FRAME_W": 70.0, # szerokosc szyn ramy cokolowej
    "SKIRTING_H": 85.0,     # wysokosc listwy przypodlogowej (dane wejsciowe)
    "SKIRTING_DEPTH": 20.0, # o tyle listwa odstaje od sciany
    # rendering / material
    "ARC_SEGMENTS": 40,
    "PLY_DENSITY": 700.0,   # kg/m3
}


def derived(p=PARAMS):
    """Wielkosci pochodne - liczone raz, uzywane wszedzie."""
    d = {}
    d["frame_depth"] = p["D"] - p["BACK"]                 # 396 - glebokosc rusztu
    d["arc_center"] = (p["R"], p["R"])                    # (150, 150)

    # piony: lewy bok stoi dokladnie w punkcie stycznosci luku
    x0 = p["R"]
    x1 = p["W"] - p["T"]
    inner_span = x1 - x0 - p["T"]                         # swiatlo miedzy licami skrajnych pionow
    n_mid = p["N_BAYS"] - 1
    d["bay_clear"] = (inner_span - n_mid * p["T"]) / p["N_BAYS"]
    xs = [x0]
    cur = x0 + p["T"]
    for _ in range(n_mid):
        cur += d["bay_clear"]
        xs.append(cur)
        cur += p["T"]
    xs.append(x1)
    d["vertical_x"] = xs                                  # lewe lico kazdego pionu

    # poziomy
    d["level_pitch"] = (p["H"] - p["T"]) / (p["N_LEVELS"] - 1)
    d["level_z"] = [i * d["level_pitch"] for i in range(p["N_LEVELS"])]
    d["shelf_clear"] = d["level_pitch"] - p["T"]
    return d


DERIVED = derived()


# ---------------------------------------------------------------- pomocnicze

def arc_points(cx, cy, r, a0, a1, segments):
    """Punkty luku od kata a0 do a1 (stopnie, CCW dodatnio)."""
    pts = []
    for i in range(segments + 1):
        a = math.radians(a0 + (a1 - a0) * i / segments)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


class Part:
    """Element z geometria i metadanymi produkcyjnymi."""

    __slots__ = ("name", "kind", "geom", "thickness", "material", "grain",
                 "qty_group", "area_override")

    def __init__(self, name, kind, geom, thickness, material, grain,
                 qty_group=None, area_override=None):
        self.name = name
        self.kind = kind                # vertical | shelf | back | plinth
        self.geom = geom
        self.thickness = thickness
        self.material = material
        self.grain = grain              # longitudinal | crosswise | free
        self.qty_group = qty_group or name
        # elementy giete leza na arkuszu w rozwinieciu, nie w przekroju
        self.area_override = area_override

    # --- geometria ---------------------------------------------------

    def footprint(self):
        """Obrys XY jako lista punktow (do testow kolizji i rzutu z gory)."""
        g = self.geom
        if g["type"] == "box":
            x0, y0, _, x1, y1, _ = g["bounds"]
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return list(g["profile"])

    def z_range(self):
        g = self.geom
        if g["type"] == "box":
            return g["bounds"][2], g["bounds"][5]
        return g["z0"], g["z1"]

    def bbox(self):
        g = self.geom
        if g["type"] == "box":
            return g["bounds"]
        xs = [pt[0] for pt in g["profile"]]
        ys = [pt[1] for pt in g["profile"]]
        return (min(xs), min(ys), g["z0"], max(xs), max(ys), g["z1"])

    def area_m2(self):
        """Pole plyty (do BOM / masy)."""
        if self.area_override is not None:
            return self.area_override
        g = self.geom
        if g["type"] == "box":
            x0, y0, z0, x1, y1, z1 = g["bounds"]
            dims = sorted([x1 - x0, y1 - y0, z1 - z0])
            return dims[1] * dims[2] / 1e6
        return abs(polygon_area(g["profile"])) / 1e6

    def mesh(self, arc_segments=None):
        """(verts, faces) - n-gony, gotowe dla Blendera i rasteryzatora."""
        g = self.geom
        if g["type"] == "box":
            x0, y0, z0, x1, y1, z1 = g["bounds"]
            v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                 (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
            f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                 (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            return v, f
        prof = g["profile"]
        z0, z1 = g["z0"], g["z1"]
        n = len(prof)
        v = [(x, y, z0) for x, y in prof] + [(x, y, z1) for x, y in prof]
        f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        for i in range(n):
            j = (i + 1) % n
            f.append((i, j, j + n, i + n))
        return v, f

    def triangles(self):
        """(verts, tris) - siatka trojkatna dla rasteryzatora WebGL."""
        g = self.geom
        verts, faces = self.mesh()
        if g["type"] == "box":
            tris = []
            for f in faces:
                for i in range(1, len(f) - 1):
                    tris.append((f[0], f[i], f[i + 1]))
            return verts, tris

        # prism_z: pokrywy przez ear clipping (profil bywa wklesly), boki wachlarzem
        prof = g["profile"]
        n = len(prof)
        cap = triangulate_2d(prof)
        tris = [(a, b, c) for a, b, c in cap]
        tris += [(a + n, b + n, c + n) for a, b, c in cap]
        for i in range(n):
            j = (i + 1) % n
            tris.append((i, j, j + n))
            tris.append((i, j + n, i + n))
        return verts, tris


def polygon_area(poly):
    """Pole ze wzoru shoelace (dodatnie dla CCW)."""
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _in_triangle(p, a, b, c):
    d1 = _cross(a, b, p)
    d2 = _cross(b, c, p)
    d3 = _cross(c, a, p)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def triangulate_2d(poly):
    """Ear clipping - obsluguje wielokaty wklesle (pas poszycia).

    Zwraca liste trojek indeksow do 'poly'. Nawiniecie nie ma znaczenia:
    cieniowanie jest dwustronne, a widocznosc rozstrzyga bufor glebi.
    """
    n = len(poly)
    if n < 3:
        return []
    idx = list(range(n))
    if polygon_area(poly) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 4 * n * n:
        guard += 1
        clipped = False
        for i in range(len(idx)):
            a = idx[i - 1]
            b = idx[i]
            c = idx[(i + 1) % len(idx)]
            if _cross(poly[a], poly[b], poly[c]) <= 0:      # wierzcholek wklesly
                continue
            if any(_in_triangle(poly[j], poly[a], poly[b], poly[c])
                   for j in idx if j not in (a, b, c)):
                continue
            tris.append((a, b, c))
            del idx[i]
            clipped = True
            break
        if not clipped:                                     # degeneracja - konczymy wachlarzem
            break
    for i in range(1, len(idx) - 1):
        tris.append((idx[0], idx[i], idx[i + 1]))
    return tris


# ---------------------------------------------------------------- profile

def nose_bay_profile(p=PARAMS, d=DERIVED):
    """Obrys scalonej plyty nos + polka przeslo 0 (bez poszycia, runda 2).

    Zaokraglony front-lewy naroznik R150 przechodzi wprost w prostokatna
    czesc przeslau (bez cofniecia - poszycie gietego juz nie ma, wiec zebro
    samo jest licem zewnetrznym). Od strony boku wciecie na wrab przelotowy:
    otwarte od frontu na NOTCH_DEPTH, zamkniete na tyle grzbietem lewego boku.
    Prawa krawedz wchodzi w wrab oporowy pionu mid-1 (runda 3 - patrz
    joinery-notes.md sekcja 1), stad +RABBET_DEPTH.
    """
    cx, cy = d["arc_center"]
    fd = d["frame_depth"]
    gx0 = d["vertical_x"][0]
    gx1 = gx0 + p["T"]
    xr = d["vertical_x"][1] + p["RABBET_DEPTH"]
    nd = p["NOTCH_DEPTH"]
    pts = arc_points(cx, cy, p["R"], 270.0, 180.0, p["ARC_SEGMENTS"])   # (150,0) -> (0,150)
    pts.append((0.0, fd))
    pts.append((gx0, fd))
    pts.append((gx0, nd))       # wcina sie do wewnatrz - omija grzbiet boku
    pts.append((gx1, nd))
    pts.append((gx1, fd))       # wraca na krawedz tylna za grzbietem
    pts.append((xr, fd))
    pts.append((xr, 0.0))
    return pts


def plinth_corner_profile(p=PARAMS, d=DERIVED):
    """Obrys zaokraglonego naroznika ramy cokolowej - piescien miedzy R150
    (ten sam luk co korpus powyzej) a R150-PLINTH_FRAME_W. Prostokatna rama
    wystawalaby poza zaokraglony nawis korpusu w tym rogu; ten sam luk R150
    gwarantuje, ze cokol nigdzie nie wychodzi poza obrys korpusu.
    """
    cx, cy = d["arc_center"]
    r_in = p["R"] - p["PLINTH_FRAME_W"]
    outer = arc_points(cx, cy, p["R"], 270.0, 180.0, p["ARC_SEGMENTS"])   # (150,0) -> (0,150)
    inner = arc_points(cx, cy, r_in, 180.0, 270.0, p["ARC_SEGMENTS"])     # (70,150) -> (150,70)
    return outer + inner


# ---------------------------------------------------------------- budowa

def _rabbeted_vertical(name, x0, faces, p=PARAMS, d=DERIVED, qty_group=None):
    """Pion z plytkim wrebem oporowym na wysokosci kazdej polki (runda 3 -
    zamiast czopa: patrz joinery-notes.md sekcja 1). Miedzy polkami pion ma
    pelna grubosc T; na wysokosci kazdej polki grubosc jest zmniejszona o
    RABBET_DEPTH od strony/stron podanych w 'faces' ("L" i/lub "R") - tam
    siada krawedz polki, ktora przenosi na tym progu obciazenie pionowe.

    Zwraca liste Part - kilka brol na jeden fizyczny pion (jak grzebien
    lewego boku), pod wspolnym qty_group.
    """
    T = p["T"]
    fd = d["frame_depth"]
    rd = p["RABBET_DEPTH"]
    levels = d["level_z"]
    qg = qty_group or name
    xa = x0 + rd if "L" in faces else x0
    xb = x0 + T - rd if "R" in faces else x0 + T

    parts = [Part(
        "%s-gap-%d" % (name, i), "vertical",
        {"type": "box", "bounds": (x0, 0.0, levels[i] + T, x0 + T, fd, levels[i + 1])},
        T, "sklejka brzozowa 18", "longitudinal", qg)
        for i in range(len(levels) - 1)]
    parts += [Part(
        "%s-rabbet-%d" % (name, i), "vertical",
        {"type": "box", "bounds": (xa, 0.0, z, xb, fd, z + T)},
        T, "sklejka brzozowa 18", "longitudinal", qg)
        for i, z in enumerate(levels)]
    return parts


def _translate_z(parts, dz):
    """Kopiuje liste Part z geometria przesunieta o dz w Z - uzywane zeby
    zbudowac korpus w lokalnych wspolrzednych (z=0 na jego wlasnym dole),
    a potem postawic go na cokole bez przepisywania kazdej linii budowy."""
    out = []
    for pt in parts:
        g = pt.geom
        if g["type"] == "box":
            x0, y0, z0, x1, y1, z1 = g["bounds"]
            newg = {"type": "box", "bounds": (x0, y0, z0 + dz, x1, y1, z1 + dz)}
        else:
            newg = {"type": "prism_z", "profile": g["profile"],
                    "z0": g["z0"] + dz, "z1": g["z1"] + dz}
        out.append(Part(pt.name, pt.kind, newg, pt.thickness, pt.material,
                        pt.grain, pt.qty_group, pt.area_override))
    return out


def _build_plinth(p=PARAMS, d=DERIVED):
    """Cokol - rama (nie plyta pelna), z=0..PLINTH_H. Przy scianach (tyl,
    prawy bok) cofnieta o SKIRTING_DEPTH, zeby ominac listwe przypodlogowa;
    przedni-lewy naroznik podaza za lukiem R150 korpusu (patrz
    plinth_corner_profile). Piec brol, jedna fizyczna rama - patrz
    joinery-notes.md."""
    T = p["T"]
    ph = p["PLINTH_H"]
    fw = p["PLINTH_FRAME_W"]
    sd = p["SKIRTING_DEPTH"]
    W, Dp, R = p["W"], p["D"], p["R"]
    y_back = Dp - sd            # 380 - cofniete od tylnej sciany
    x_right = W - sd            # 1780 - cofniete od prawej sciany

    mat, grain = "sklejka brzozowa 18", "longitudinal"
    return [
        Part("plinth-left", "plinth",
             {"type": "box", "bounds": (0.0, R, 0.0, fw, y_back - fw, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-back", "plinth",
             {"type": "box", "bounds": (0.0, y_back - fw, 0.0, x_right, y_back, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-right", "plinth",
             {"type": "box", "bounds": (x_right - fw, 0.0, 0.0, x_right, y_back - fw, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-front", "plinth",
             {"type": "box", "bounds": (R, 0.0, 0.0, x_right - fw, fw, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-corner", "plinth",
             {"type": "prism_z", "profile": plinth_corner_profile(p, d), "z0": 0.0, "z1": ph},
             T, mat, "free", "plinth"),
    ]


def build_parts(p=PARAMS, d=DERIVED):
    """Korpus (zbudowany lokalnie, z=0 na jego dole) przesuniety na cokol
    (z=0..PLINTH_H) - patrz docstring modulu i _build_plinth."""
    return _translate_z(_build_corpus(p, d), p["PLINTH_H"]) + _build_plinth(p, d)


def _build_corpus(p=PARAMS, d=DERIVED):
    parts = []
    xs = d["vertical_x"]
    fd = d["frame_depth"]
    T = p["T"]
    rd = p["RABBET_DEPTH"]

    # --- lewy bok: grzbiet ciagly + 5 zebow miedzy wrebami (jedna sztuka
    # materialu, wycieta jako grzebien - por. joinery-notes.md) ---
    gx0, gx1 = xs[0], xs[0] + T
    nd = p["NOTCH_DEPTH"]
    parts.append(Part(
        "vertical-L-gable-spine", "vertical",
        {"type": "box", "bounds": (gx0, nd, 0.0, gx1, fd, p["H"])},
        T, "sklejka brzozowa 18", "longitudinal", "vertical-L-gable"))
    for i in range(p["N_LEVELS"] - 1):
        z0 = d["level_z"][i] + T
        z1 = d["level_z"][i + 1]
        parts.append(Part(
            "vertical-L-gable-tooth-%d" % i, "vertical",
            {"type": "box", "bounds": (gx0, 0.0, z0, gx1, nd, z1)},
            T, "sklejka brzozowa 18", "longitudinal", "vertical-L-gable"))

    # --- pozostale piony, z wrebem oporowym na kazda strone, ktora nosi polke.
    # mid-1 i mid-2 sa wymiarowo identyczne (wrab z obu stron) - wspolny
    # qty_group; R-side ma wrab tylko z lewej, wiec inny przekroj progu ---
    parts += _rabbeted_vertical("vertical-mid-1", xs[1], "LR", p, d, "vertical-mid")
    parts += _rabbeted_vertical("vertical-mid-2", xs[2], "LR", p, d, "vertical-mid")
    parts += _rabbeted_vertical("vertical-R-side", xs[3], "L", p, d)

    # --- polki (3 na poziom), oparte na wrebach, bez czopow ---
    # przeslo 0 (przy nosie): jedna scalona plyta nos+polka, zlacze z bokiem
    # to wrab przelotowy (patrz sekcja pionow wyzej), prawa strona wchodzi
    # w wrab oporowy mid-1 jak kazda inna polka
    prof0 = nose_bay_profile(p, d)
    for li, z in enumerate(d["level_z"]):
        for b in range(p["N_BAYS"]):
            if b == 0:
                parts.append(Part(
                    "shelf-L%d-B0" % li, "shelf",
                    {"type": "prism_z", "profile": prof0, "z0": z, "z1": z + T},
                    T, "sklejka brzozowa 18", "free", "shelf-B0"))
            else:
                xl = xs[b] + T - rd     # wchodzi w wrab oporowy lewego pionu
                xr = xs[b + 1] + rd     # wchodzi w wrab oporowy prawego pionu
                parts.append(Part(
                    "shelf-L%d-B%d" % (li, b), "shelf",
                    {"type": "box", "bounds": (xl, 0.0, z, xr, fd, z + T)},
                    T, "sklejka brzozowa 18", "longitudinal", "shelf-B%d" % b))

    # --- plecy: nos + po jednej plycie na przeslo, styk w osiach pionow ---
    y0b = fd
    y1b = p["D"]
    parts.append(Part(
        "back-nose", "back",
        {"type": "box", "bounds": (0.0, y0b, 0.0, p["R"], y1b, p["H"])},
        p["BACK"], "sklejka brzozowa 4", "longitudinal", "back-nose"))

    edges = [p["R"]] + [x + T / 2.0 for x in xs[1:-1]] + [p["W"]]
    for b in range(p["N_BAYS"]):
        parts.append(Part(
            "back-B%d" % b, "back",
            {"type": "box", "bounds": (edges[b], y0b, 0.0, edges[b + 1], y1b, p["H"])},
            p["BACK"], "sklejka brzozowa 4", "longitudinal", "back-bay"))

    return parts


# ---------------------------------------------------------------- okucia

def bolt_positions(p=PARAMS, d=DERIVED):
    """Osie srub M6 (przez lico pionu w mimosrod beczkowy - gwint zenski,
    nie wkret - osadzony w czole polki). Polka siedzi na wrebie oporowym
    (patrz _rabbeted_vertical); sruby przenosza docisk i wyrywanie, nie
    ciezar - ten bierze prog wrebu.

    Zwraca (x, y, z, kierunek) w globalnym Z (korpus stoi na cokole -
    patrz build_parts). Nie renderowane w 3D - dane pod wiercenia DXF.
    """
    out = []
    xs = d["vertical_x"]
    T = p["T"]
    z_off = p["PLINTH_H"]
    for li, z in enumerate(d["level_z"]):
        zc = z + T / 2.0 + z_off
        for b in range(p["N_BAYS"]):
            if b > 0:                   # b==0 lewa strona: wrab, nie sruba
                for y in p["BOLT_Y_LEFT"]:
                    out.append((xs[b] + T / 2.0, y, zc, "+x"))
            for y in p["BOLT_Y_RIGHT"]:
                out.append((xs[b + 1] + T / 2.0, y, zc, "-x"))
    return out


def summary(p=PARAMS, d=DERIVED):
    parts = build_parts(p, d)
    by_kind = {}
    for pt in parts:
        e = by_kind.setdefault(pt.kind, {"n": 0, "area": 0.0})
        e["n"] += 1
        e["area"] += pt.area_m2()
    mass = sum(pt.area_m2() * pt.thickness / 1000.0 * p["PLY_DENSITY"] for pt in parts)
    return {
        "parts": parts,
        "by_kind": by_kind,
        "mass_kg": mass,
        "n_bolts": len(bolt_positions(p, d)),
        "bay_clear": d["bay_clear"],
        "shelf_clear": d["shelf_clear"],
        "level_z": d["level_z"],
        "vertical_x": d["vertical_x"],
    }
