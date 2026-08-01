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
    # runda 7: zero wrebow. Piony stoja miedzy dolna a gorna plyta, polki
    # srodkowe leza na kolkach - patrz joinery-notes.md sekcja 1.
    "BOLT_Y": (120.0, 300.0),   # osie srub pion <-> plyta, w glab
    "BOLT_D": 6.0,          # M6
    "DOWEL_D": 10.0,        # mimosrod beczkowy (gwint zenski, nie wkret)
    "PIN_D": 5.0,           # kolek polkowy
    "PIN_Y": (60.0, 340.0), # osie kolkow polkowych, w glab
    "NOSE_CORNER_BOLT_Y": (60.0, 300.0),  # runda 8 - sruby poleczek naroznika
    "BACK_GROOVE_W": 4.0,   # wpust pod plecki w tylnych krawedziach
    "BACK_GROOVE_D": 8.0,
    # --- wyposazenie komor: opcje wlaczane parametrem (runda 7) ---
    # klucz to (poziom, przeslo). Poziom 0 = komora tuz nad dolna plyta.
    "DRAWER_CELLS": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    "DOOR_CELLS": {(2, 0): "L", (2, 2): "R"},
    "DRAWER_GAP": 3.0,      # szczelina wokol frontu
    "DRAWER_DEPTH": 350.0,
    "DRAWER_BOX_H": 220.0,
    "DRAWER_BOX_Z": 30.0,   # dol korpusu szuflady nad plyta
    # runda 9 - prowadnice Blum TANDEM 562H (bez BLUMOTION, wariant
    # ekonomiczny wg klienta - patrz joinery-notes.md sekcja 6):
    #   system 16 mm - max grubosc boku szuflady 16 mm (stad DRAWER_SIDE_T
    #   nizsza od T=18 uzywanego wszedzie indziej), luz systemowy 13 mm na
    #   strone (RUNNER_CLEAR - to jest oficjalna wartosc Blum, nie zmieniona
    #   z rundy 7, tam bylo to juz zgadniete poprawnie), NL 350 mm dobrane
    #   do DRAWER_DEPTH, nosnosc statyczna ~45 kg na pare.
    "DRAWER_SIDE_T": 16.0,
    "RUNNER_CLEAR": 13.0,   # luz na prowadnice kulkowa (Blum TANDEM), na strone
    "RUNNER_NL": 350.0,     # dlugosc nominalna prowadnicy (Blum TANDEM 562H)
    "RUNNER_LOAD_KG": 45.0,  # nosnosc statyczna na pare (Blum TANDEM 562H)
    "RUNNER_SCREW_Y": (18.0, 280.0, 342.0),  # osie wkretow mocujacych, w glab
    # cokol - runda 4: tyl i prawy bok przylegaja do sciany, listwa
    # przypodlogowa 85 mm wys. x 20 mm gl. (odstaje od sciany)
    "PLINTH_H": 100.0,      # 85 mm listwa + 15 mm przeswitu na nierownosci
    "SKIRTING_H": 85.0,     # wysokosc listwy przypodlogowej (dane wejsciowe)
    "SKIRTING_DEPTH": 20.0, # o tyle listwa odstaje od sciany
    "PLINTH_INSET": 22.0,   # runda 5: cokol cofniety o tyle od krawedzi
                            # korpusu na WSZYSTKICH czterech bokach (klient) -
                            # > SKIRTING_DEPTH, wiec nadal omija listwe (2 mm
                            # zapasu), zastepuje dawna asymetrie (0 mm z
                            # przodu/lewej, 20 mm z tylu/prawej)
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

def full_plate_profile(p=PARAMS, d=DERIVED):
    """Obrys dolnej i gornej plyty (runda 7) - jeden kawalek na pelne
    1800 mm, bez zadnych wciec. Piony staja MIEDZY plytami, wiec nic przez
    nie nie przechodzi i wreby przelotowe zniknely z calego mebla.

    Zaokraglony przedni lewy naroznik R150 przechodzi wprost w prosta
    krawedz frontu i lewego boku (styczny w x=150 i y=150).
    """
    cx, cy = d["arc_center"]
    fd = d["frame_depth"]
    pts = arc_points(cx, cy, p["R"], 270.0, 180.0, p["ARC_SEGMENTS"])  # (150,0)->(0,150)
    pts.append((0.0, fd))
    pts.append((p["W"], fd))
    pts.append((p["W"], 0.0))
    return pts


def nose_corner_profile(p=PARAMS, d=DERIVED):
    """Obrys malej zaokraglonej poleczki w rogu nosa (runda 8).

    Runda 7 usunela wrab przelotowy, wiec plyty srodkowych poziomow koncza
    sie teraz na licu lewego boku (x=150) - strefa zaokraglonego naroznika
    (0-150 mm) zrobila sie pusta na 4 srodkowych wysokosciach (dolna i gorna
    plyta ja nadal obejmuja, bo uzywaja full_plate_profile). Klient chce te
    poleczki z powrotem - wracaja jako osobne, male czesci wspornikowo
    skrecone do lica lewego boku (ktore jest teraz odslonietym plaskim
    licem, bo nie ma juz grzebienia/wrebu - wystarcza 2 sruby M6).
    """
    cx, cy = d["arc_center"]
    fd = d["frame_depth"]
    pts = arc_points(cx, cy, p["R"], 270.0, 180.0, p["ARC_SEGMENTS"])  # (150,0)->(0,150)
    pts.append((0.0, fd))
    pts.append((p["R"], fd))
    return pts


def plinth_corner_profile(p=PARAMS, d=DERIVED):
    """Obrys zaokraglonego naroznika ramy cokolowej - piescien wspolsrodkowy
    z lukiem R150 korpusu, ale pomniejszony o PLINTH_INSET (runda 5 - cokol
    cofniety rownomiernie na wszystkich czterech bokach, nie tylko przy
    scianach). Promien zewnetrzny = R - PLINTH_INSET, wewnetrzny = to minus
    PLINTH_FRAME_W. Ten sam srodek co luk korpusu gwarantuje rownomierne
    cofniecie az do samego naroznika (bez tego prostokatny czy niewspolsrodkowy
    naroznik wystawalby poza zaokraglony nawis korpusu w tym rogu).
    """
    cx, cy = d["arc_center"]
    r_out = p["R"] - p["PLINTH_INSET"]
    r_in = r_out - p["T"]
    outer = arc_points(cx, cy, r_out, 270.0, 180.0, p["ARC_SEGMENTS"])   # (150,0) -> (0,150)
    inner = arc_points(cx, cy, r_in, 180.0, 270.0, p["ARC_SEGMENTS"])     # (70,150) -> (150,70)
    return outer + inner


# ---------------------------------------------------------------- budowa

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
    """Cokol - rama (nie plyta pelna), z=0..PLINTH_H, cofnieta o PLINTH_INSET
    od zewnetrznego obrysu korpusu na WSZYSTKICH czterech bokach (runda 5 -
    jednolite 22 mm, zastepuje dawna asymetrie z rundy 4: 0 mm z przodu/lewej,
    tylko SKIRTING_DEPTH=20 mm z tylu/prawej). PLINTH_INSET > SKIRTING_DEPTH,
    wiec przy scianach nadal omija listwe przypodlogowa (2 mm zapasu - patrz
    checks.py). Przedni-lewy naroznik podaza za tym samym lukiem co korpus,
    tylko wspolsrodkowo pomniejszonym o PLINTH_INSET (patrz
    plinth_corner_profile). Piec brol, jedna fizyczna rama - patrz
    joinery-notes.md."""
    T = p["T"]
    ph = p["PLINTH_H"]
    inset = p["PLINTH_INSET"]
    W, Dp, R = p["W"], p["D"], p["R"]
    x0, y0 = inset, inset
    x1, y1 = W - inset, Dp - inset

    mat, grain = "sklejka brzozowa 18", "longitudinal"
    parts = [
        Part("plinth-left", "plinth",
             {"type": "box", "bounds": (x0, R, 0.0, x0 + T, y1 - T, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-back", "plinth",
             {"type": "box", "bounds": (x0, y1 - T, 0.0, x1, y1, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-right", "plinth",
             {"type": "box", "bounds": (x1 - T, y0, 0.0, x1, y1 - T, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-front", "plinth",
             {"type": "box", "bounds": (R, y0, 0.0, x1 - T, y0 + T, ph)},
             T, mat, grain, "plinth"),
        Part("plinth-corner", "plinth",
             {"type": "prism_z", "profile": plinth_corner_profile(p, d), "z0": 0.0, "z1": ph},
             T, mat, "free", "plinth"),
    ]
    # zebra poprzeczne pod kazdym pionem, ktory trafia w swiatlo ramy -
    # bez nich plyta dna przenosilaby cale obciazenie pionu na zginanie
    # miedzy szynami (runda 6, patrz joinery-notes.md sekcja 3)
    for i, x in enumerate(d["vertical_x"][:3]):
        parts.append(Part(
            "plinth-rib-%d" % i, "plinth",
            {"type": "box", "bounds": (x, y0 + T, 0.0, x + T, y1 - T, ph)},
            T, mat, grain, "plinth-rib"))
    return parts


def build_parts(p=PARAMS, d=DERIVED):
    """Korpus (zbudowany lokalnie, z=0 na jego dole) przesuniety na cokol
    (z=0..PLINTH_H) - patrz docstring modulu i _build_plinth."""
    return _translate_z(_build_corpus(p, d), p["PLINTH_H"]) + _build_plinth(p, d)


def hinge_positions(p=PARAMS, d=DERIVED):
    """Puszki zawiasow Ø35 w licu wewnetrznym drzwi (runda 7).

    Jedyne miejsce, w ktorym strona zawiasow ('L'/'R') w ogole cokolwiek
    zmienia - sama plyta drzwi jest w obu wariantach identyczna, wiec
    przelozenie zawiasow na druga strone nie rusza listy ciec.
    """
    T, g = p["T"], p["DRAWER_GAP"]
    z_off = p["PLINTH_H"]
    out = []
    for (li, b), side in sorted(p["DOOR_CELLS"].items()):
        x0, x1, z0, z1 = _cell_opening(li, b, p, d)
        xh = (x0 + g + 22.5) if side == "L" else (x1 - g - 22.5)
        for z in (z0 + g + 100.0, z1 - g - 100.0):
            out.append((xh, T, z + z_off, side))
    return out


def _build_corpus(p=PARAMS, d=DERIVED):
    """Korpus (runda 7): dolna i gorna plyta na pelne 1800 mm, cztery piony
    stojace MIEDZY nimi, polki srodkowe na kolkach. Zero wrebow."""
    parts = []
    xs = d["vertical_x"]
    fd = d["frame_depth"]
    T = p["T"]
    H = p["H"]
    mat = "sklejka brzozowa 18"
    prof = full_plate_profile(p, d)

    # --- dolna i gorna plyta: jeden kawalek, z zaokraglonym naroznikiem ---
    parts.append(Part("plate-bottom", "shelf",
                      {"type": "prism_z", "profile": prof, "z0": 0.0, "z1": T},
                      T, mat, "free", "plate"))
    parts.append(Part("plate-top", "shelf",
                      {"type": "prism_z", "profile": prof, "z0": H - T, "z1": H},
                      T, mat, "free", "plate"))

    # --- piony miedzy plytami: pelna grubosc, bez wrebow i bez czopow.
    # Skrecane pionowo przez plyte w mimosrod w czole pionu - lico czolowe
    # plyty jest wolne z gory i z dolu, wiec leb ma na czym usiasc ---
    names = ("vertical-L-gable", "vertical-mid-1", "vertical-mid-2", "vertical-R-side")
    groups = ("vertical-L-gable", "vertical-mid", "vertical-mid", "vertical-R-side")
    for name, group, x in zip(names, groups, xs):
        parts.append(Part(name, "vertical",
                          {"type": "box", "bounds": (x, 0.0, T, x + T, fd, H - T)},
                          T, mat, "longitudinal", group))

    # --- polki srodkowe: leza na kolkach (Ø5), nie sa niczym skrecone.
    # Dzieki temu sa przestawialne i wyjmowalne - a przy przesle z szuflada
    # lub drzwiczkami mozna je po prostu pominac ---
    for li in range(1, p["N_LEVELS"] - 1):
        z = d["level_z"][li]
        for b in range(p["N_BAYS"]):
            if (li, b) in p["DRAWER_CELLS"]:
                continue
            parts.append(Part(
                "shelf-L%d-B%d" % (li, b), "shelf",
                {"type": "box", "bounds": (xs[b] + T, 0.0, z, xs[b + 1], fd, z + T)},
                T, mat, "longitudinal", "shelf-bay"))

    # --- male zaokraglone poleczki w rogu nosa (runda 8) - runda 7
    # zostawila te strefe pusta, klient poprosil o przywrocenie. Wraca jako
    # osobna czesc na kazdym z 4 srodkowych poziomow, wspornikowo skrecona
    # do lica lewego boku (patrz joinery-notes.md) ---
    prof_corner = nose_corner_profile(p, d)
    for li in range(1, p["N_LEVELS"] - 1):
        z = d["level_z"][li]
        parts.append(Part(
            "nose-corner-L%d" % li, "shelf",
            {"type": "prism_z", "profile": prof_corner, "z0": z, "z1": z + T},
            T, mat, "free", "nose-corner"))

    # --- plecy: nos + po jednej plycie na przeslo, wsuwane we wpust
    # 4 x 8 mm w tylnych krawedziach (patrz joinery-notes.md) ---
    y0b, y1b = fd, p["D"]
    parts.append(Part("back-nose", "back",
                      {"type": "box", "bounds": (0.0, y0b, 0.0, p["R"], y1b, H)},
                      p["BACK"], "sklejka brzozowa 4", "longitudinal", "back-nose"))
    edges = [p["R"]] + [x + T / 2.0 for x in xs[1:-1]] + [p["W"]]
    for b in range(p["N_BAYS"]):
        parts.append(Part("back-B%d" % b, "back",
                          {"type": "box", "bounds": (edges[b], y0b, 0.0, edges[b + 1], y1b, H)},
                          p["BACK"], "sklejka brzozowa 4", "longitudinal", "back-bay"))

    parts += _build_drawers(p, d)
    parts += _build_doors(p, d)
    return parts


def _cell_opening(li, b, p, d):
    """Swiatlo komory (li, b): x miedzy licami pionow, z miedzy plytami."""
    xs, T = d["vertical_x"], p["T"]
    z0 = d["level_z"][li] + T
    z1 = d["level_z"][li + 1]
    return xs[b] + T, xs[b + 1], z0, z1


def _build_drawers(p=PARAMS, d=DERIVED):
    """Szuflady - opcja wlaczana przez PARAMS['DRAWER_CELLS'] (runda 7),
    dopasowane do prowadnic Blum TANDEM 562H (runda 9).

    Kazda szuflada to 5 elementow: front nakladany w swietle komory (18 mm,
    jak drzwiczki) + korpus (2 boki, tyl, dno 4 mm). Boki/tyl korpusu maja
    DRAWER_SIDE_T = 16 mm, nie T = 18 mm jak reszta mebla - to maksymalna
    grubosc boku dla systemu Blum TANDEM 562H (16 mm). Prowadnice kulkowe
    boczne, NL 350 mm, po RUNNER_CLEAR mm luzu na strone.
    """
    T, ST, B = p["T"], p["DRAWER_SIDE_T"], p["BACK"]
    g, run = p["DRAWER_GAP"], p["RUNNER_CLEAR"]
    out = []
    for li, b in sorted(p["DRAWER_CELLS"]):
        x0, x1, z0, z1 = _cell_opening(li, b, p, d)
        # front nakladany w swietle, z rowna szczelina dookola - grubosc T,
        # zgodnie z drzwiczkami (nie jest czescia zlacza z prowadnica)
        out.append(Part("drawer-%d%d-front" % (li, b), "drawer",
                        {"type": "box", "bounds": (x0 + g, 0.0, z0 + g, x1 - g, T, z1 - g)},
                        T, "sklejka brzozowa 18", "longitudinal", "drawer-front"))
        # korpus szuflady - grubosc ST (16 mm, limit systemu Blum)
        bx0, bx1 = x0 + run, x1 - run
        by0, by1 = T, T + p["DRAWER_DEPTH"]
        bz0 = z0 + p["DRAWER_BOX_Z"]
        bz1 = bz0 + p["DRAWER_BOX_H"]
        out.append(Part("drawer-%d%d-side-L" % (li, b), "drawer",
                        {"type": "box", "bounds": (bx0, by0, bz0, bx0 + ST, by1, bz1)},
                        ST, "sklejka brzozowa 16", "longitudinal", "drawer-side"))
        out.append(Part("drawer-%d%d-side-R" % (li, b), "drawer",
                        {"type": "box", "bounds": (bx1 - ST, by0, bz0, bx1, by1, bz1)},
                        ST, "sklejka brzozowa 16", "longitudinal", "drawer-side"))
        out.append(Part("drawer-%d%d-back" % (li, b), "drawer",
                        {"type": "box", "bounds": (bx0 + ST, by1 - ST, bz0, bx1 - ST, by1, bz1)},
                        ST, "sklejka brzozowa 16", "longitudinal", "drawer-back"))
        out.append(Part("drawer-%d%d-bottom" % (li, b), "drawer",
                        {"type": "box", "bounds": (bx0 + ST, by0, bz0, bx1 - ST, by1 - ST, bz0 + B)},
                        B, "sklejka brzozowa 4", "free", "drawer-bottom"))
    return out


def runner_positions(p=PARAMS, d=DERIVED):
    """Osie wkretow mocujacych prowadnice Blum TANDEM 562H (runda 9) -
    po jednej lisciwe na kazdym boku komory z szuflada: do lica pionu
    (strona korpusu) i do lica boku szuflady (strona ruchoma). Nie
    generuje geometrii samej prowadnicy (kupowane okucie, nie plyta) -
    tylko punkty pod wiercenie, jak bolt_positions()/hinge_positions().

    Zwraca (x, y, z, strona) w globalnym Z; strona = 'corpus' albo 'drawer'.
    """
    T, ST = p["T"], p["DRAWER_SIDE_T"]
    z_off = p["PLINTH_H"]
    out = []
    for li, b in sorted(p["DRAWER_CELLS"]):
        x0, x1, z0, z1 = _cell_opening(li, b, p, d)
        zc = z0 + p["DRAWER_BOX_Z"] + p["DRAWER_BOX_H"] / 2.0 + z_off
        for y in p["RUNNER_SCREW_Y"]:
            out.append((x0, y, zc, "corpus"))          # lico prawe lewego pionu
            out.append((x1, y, zc, "corpus"))           # lico lewe prawego pionu
            out.append((x0 + p["RUNNER_CLEAR"], y, zc, "drawer"))
            out.append((x1 - p["RUNNER_CLEAR"], y, zc, "drawer"))
    return out


def _build_doors(p=PARAMS, d=DERIVED):
    """Drzwiczki - opcja wlaczana przez PARAMS['DOOR_CELLS'] (runda 7).

    Wartosc w slowniku to strona zawiasow: 'L' albo 'R'. Sama plyta drzwi
    jest identyczna w obu wariantach - roznica siedzi wylacznie w pozycjach
    puszek zawiasow (Ø35), patrz hinge_positions(). Dzieki temu zmiana
    strony otwierania nie zmienia listy ciec, tylko wiercenia.
    """
    T, g = p["T"], p["DRAWER_GAP"]
    out = []
    for (li, b), side in sorted(p["DOOR_CELLS"].items()):
        x0, x1, z0, z1 = _cell_opening(li, b, p, d)
        out.append(Part("door-%d%d-%s" % (li, b, side), "door",
                        {"type": "box", "bounds": (x0 + g, 0.0, z0 + g, x1 - g, T, z1 - g)},
                        T, "sklejka brzozowa 18", "longitudinal", "door"))
    return out


def bolt_positions(p=PARAMS, d=DERIVED):
    """Osie srub M6 laczacych piony z dolna i gorna plyta (runda 7).

    Sruba idzie PIONOWO przez plyte w mimosrod beczkowy osadzony w czole
    pionu. Lico plyty jest wolne z gory (wieniec) i od spodu (dno, nad
    cokolem), wiec leb ma na czym usiasc - to bylo nierozwiazywalne, dopoki
    piony biegly ciagle, a polki wchodzily w nie wrebem z obu stron.

    Zwraca (x, y, z, kierunek) w globalnym Z (korpus stoi na cokole).
    """
    out = []
    T = p["T"]
    z_off = p["PLINTH_H"]
    H = p["H"]
    for x in d["vertical_x"]:
        xc = x + T / 2.0
        for y in p["BOLT_Y"]:
            out.append((xc, y, z_off, "+z"))          # przez dno
            out.append((xc, y, z_off + H, "-z"))      # przez wieniec
    return out


def nose_corner_bolt_positions(p=PARAMS, d=DERIVED):
    """Osie srub M6 mocujacych male poleczki naroznika do lica lewego boku
    (runda 8) - poziomo, przez lico pionu (x=R) w mimosrod w krawedzi
    poleczki. 2 sruby na poleczke, na 4 srodkowych poziomach.
    """
    out = []
    T = p["T"]
    z_off = p["PLINTH_H"]
    for li in range(1, p["N_LEVELS"] - 1):
        zc = d["level_z"][li] + T / 2.0 + z_off
        for y in p["NOSE_CORNER_BOLT_Y"]:
            out.append((p["R"], y, zc, "-x"))
    return out


def shelf_pin_positions(p=PARAMS, d=DERIVED):
    """Otwory Ø5 pod kolki polkowe - w licach pionow, po obu stronach kazdego
    przesla, na kazdej z 4 srodkowych wysokosci (runda 7). Polki srodkowe
    leza na kolkach, nie sa skrecane, wiec sa przestawialne i wyjmowalne.
    """
    out = []
    T = p["T"]
    z_off = p["PLINTH_H"]
    xs = d["vertical_x"]
    for li in range(1, p["N_LEVELS"] - 1):
        z = d["level_z"][li] + z_off
        for b in range(p["N_BAYS"]):
            for y in p["PIN_Y"]:
                out.append((xs[b] + T, y, z, "+x"))       # lico prawe lewego pionu
                out.append((xs[b + 1], y, z, "-x"))       # lico lewe prawego pionu
    return out


def plinth_bolt_positions(p=PARAMS, d=DERIVED):
    """Kotwienie korpusu do cokolu (runda 6) - sruba M6 pionowo przez plyte
    dna w mimosrod osadzony w szynie cokolu. Wczesniej korpus tylko stal na
    cokole wlasnym ciezarem; przy 22 mm cofnieciu i przechyle bocznym to za
    malo. Otwor Ø6,5 przelotowy przez dno + Ø10 x 13 mm ślepy w szynie.

    Zwraca (x, y, z, kierunek) - z na gornej krawedzi cokolu.
    """
    inset, T = p["PLINTH_INSET"], p["T"]
    W, Dp = p["W"], p["D"]
    z = p["PLINTH_H"]
    x0, y0 = inset + T / 2.0, inset + T / 2.0
    x1, y1 = W - inset - T / 2.0, Dp - inset - T / 2.0
    out = []
    for x in (400.0, 900.0, 1400.0):          # szyna przednia i tylna
        out.append((x, y0, z, "-z"))
        out.append((x, y1, z, "-z"))
    for y in (150.0, 300.0):                  # szyna lewa i prawa
        out.append((x0, y, z, "-z"))
        out.append((x1, y, z, "-z"))
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
        "n_bolts": len(bolt_positions(p, d)) + len(nose_corner_bolt_positions(p, d)),
        "bay_clear": d["bay_clear"],
        "shelf_clear": d["shelf_clear"],
        "level_z": d["level_z"],
        "vertical_x": d["vertical_x"],
    }
