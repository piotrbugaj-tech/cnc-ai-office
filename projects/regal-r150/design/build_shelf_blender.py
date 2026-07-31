"""
Regal R150 - generator bryly w Blenderze.

PLIK WYGENEROWANY AUTOMATYCZNIE - nie edytuj recznie.
Zrodlo: shelf_model.py + blender_emit.py, sklejone przez make_blender_script.py

Jak uzyc na Mac mini:
  1. Blender -> zakladka Scripting -> New
  2. Wklej cala zawartosc tego pliku
  3. Run Script (Alt+P)

Bryla powstaje w kolekcji "Regal_R150". Skrypt jest idempotentny -
kolejne uruchomienie podmienia poprzednia wersje zamiast dokladac druga.

Scena przechodzi na jednostki milimetrowe, wiec panel N pokazuje wymiary w mm.
"""

# --------------------------------------------------------------------------
# czesc 1/2: model parametryczny (zrodlo: shelf_model.py)
# --------------------------------------------------------------------------

import math

# ---------------------------------------------------------------- parametry

PARAMS = {
    # gabaryty
    "W": 1800.0,            # szerokosc calkowita
    "H": 2000.0,            # wysokosc calkowita
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
    "TENON_W": 60.0,        # szerokosc czopa (wzdluz Y)
    "TENON_PROUD": 2.0,     # wystawanie czopa poza lico eksponowane
    "CLEARANCE": 0.1,       # luz gniazda wg CLAUDE.md par. 6
    "TOOL_D": 6.0,          # frez spiralny
    "NOTCH_DEPTH": 310.0,   # wrab w lewym boku: otwarty na ta glebokosc od frontu
    "TENON_Y": ((40.0, 100.0), (236.0, 296.0)),
    "BOLT_Y_LEFT": (140.0, 200.0),
    "BOLT_Y_RIGHT": (320.0, 380.0),
    "BOLT_D": 6.0,          # M6
    "DOWEL_D": 10.0,        # mimosrod beczkowy
    # rendering / material
    "ARC_SEGMENTS": 40,
    "PLY_DENSITY": 700.0,   # kg/m3
}

# gniazdo = czop + luz; dog-bone = promien freza + 0.1 (CLAUDE.md par. 6)
PARAMS["MORTISE_W"] = PARAMS["TENON_W"] + PARAMS["CLEARANCE"]
PARAMS["MORTISE_T"] = PARAMS["T"] + PARAMS["CLEARANCE"]
PARAMS["DOGBONE_R"] = PARAMS["TOOL_D"] / 2.0 + 0.1


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
        self.kind = kind                # vertical | shelf | tenon | back
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
    """
    cx, cy = d["arc_center"]
    fd = d["frame_depth"]
    gx0 = d["vertical_x"][0]
    gx1 = gx0 + p["T"]
    xr = d["vertical_x"][1]
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


# ---------------------------------------------------------------- budowa

def build_parts(p=PARAMS, d=DERIVED):
    parts = []
    xs = d["vertical_x"]
    fd = d["frame_depth"]
    T = p["T"]

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

    # --- pozostale piony (pelna wysokosc, sloje wzdluz wysokosci) ---
    labels = ["mid-1", "mid-2", "R-side"]
    for i, x in enumerate(xs[1:]):
        parts.append(Part(
            "vertical-%s" % labels[i], "vertical",
            {"type": "box", "bounds": (x, 0.0, 0.0, x + T, fd, p["H"])},
            T, "sklejka brzozowa 18", "longitudinal", "vertical"))

    # --- polki (3 na poziom) + czopy przelotowe ---
    # przeslo 0 (przy nosie): jedna scalona plyta nos+polka, zlacze z bokiem
    # to wrab (patrz sekcja pionow wyzej), bez czopow/srub na tej stronie
    prof0 = nose_bay_profile(p, d)
    for li, z in enumerate(d["level_z"]):
        for b in range(p["N_BAYS"]):
            if b == 0:
                parts.append(Part(
                    "shelf-L%d-B0" % li, "shelf",
                    {"type": "prism_z", "profile": prof0, "z0": z, "z1": z + T},
                    T, "sklejka brzozowa 18", "free", "shelf-B0"))
            else:
                xl = xs[b] + T          # lico prawe lewego pionu
                xr = xs[b + 1]          # lico lewe prawego pionu
                parts.append(Part(
                    "shelf-L%d-B%d" % (li, b), "shelf",
                    {"type": "box", "bounds": (xl, 0.0, z, xr, fd, z + T)},
                    T, "sklejka brzozowa 18", "longitudinal", "shelf-B%d" % b))

            # czopy: skrajne przechodza na wylot, srodkowe spotykaja sie w osi pionu
            for side in ("L", "R"):
                if side == "L":
                    if b == 0:
                        continue         # zlacze z bokiem to wrab, nie czop
                    vx = xs[b]
                    tx0 = vx + T / 2.0
                    tx1 = vx + T
                else:
                    vx = xs[b + 1]
                    tx0 = vx
                    # prawy bok jest eksponowany - czop wystaje 2 mm
                    tx1 = (vx + T + p["TENON_PROUD"]) if b == p["N_BAYS"] - 1 else vx + T / 2.0
                for k, (y0, y1) in enumerate(p["TENON_Y"]):
                    parts.append(Part(
                        "tenon-L%d-B%d-%s%d" % (li, b, side, k), "tenon",
                        {"type": "box", "bounds": (tx0, y0, z, tx1, y1, z + T)},
                        T, "sklejka brzozowa 18", "longitudinal", "tenon"))

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
    """Osie srub M6 (przez lico pionu w mimosrod beczkowy w czole polki).

    Zwraca (x, y, z, kierunek). Nie renderowane w 3D - dane pod wiercenia DXF.
    """
    out = []
    xs = d["vertical_x"]
    T = p["T"]
    for li, z in enumerate(d["level_z"]):
        zc = z + T / 2.0
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
    mass = sum(pt.area_m2() * pt.thickness / 1000.0 * p["PLY_DENSITY"]
               for pt in parts if pt.kind != "tenon")
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


# --------------------------------------------------------------------------
# czesc 2/2: emisja do Blendera (zrodlo: blender_emit.py)
# --------------------------------------------------------------------------


MM = 0.001                 # model liczony w mm, scena Blendera w metrach

COLLECTIONS = {
    "vertical": "01_Piony",
    "shelf": "02_Polki",
    "tenon": "03_Czopy",
    "back": "04_Plecy",
}

COLORS = {
    "vertical": (0.86, 0.72, 0.50, 1.0),
    "shelf": (0.90, 0.78, 0.57, 1.0),
    "tenon": (0.72, 0.55, 0.33, 1.0),
    "back": (0.62, 0.50, 0.35, 1.0),
}


def _material(bpy, kind):
    name = "regal_%s" % kind
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = COLORS[kind]
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.65
        mat.diffuse_color = COLORS[kind]        # kolor w trybie Solid
    return mat


def _collection(bpy, root, name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        root.children.link(col)
    return col


def clear_previous(bpy, root_name):
    """Usuwa poprzednia wersje regalu - skrypt jest idempotentny."""
    root = bpy.data.collections.get(root_name)
    if root is None:
        return
    stack = [root]
    seen = []
    while stack:
        col = stack.pop()
        seen.append(col)
        stack.extend(col.children)
    for col in seen:
        for obj in list(col.objects):
            bpy.data.meshes.remove(obj.data, do_unlink=True)
    for col in seen:
        bpy.data.collections.remove(col)


def build_scene(root_name="Regal_R150", with_tenons=True):
    import bpy               # dostepny tylko wewnatrz Blendera
    import bmesh

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"

    clear_previous(bpy, root_name)

    root = bpy.data.collections.new(root_name)
    scene.collection.children.link(root)

    parts = build_parts()
    made = 0
    for part in parts:
        if part.kind == "tenon" and not with_tenons:
            continue
        verts, faces = part.mesh()

        mesh = bpy.data.meshes.new(part.name)
        mesh.from_pydata([(x * MM, y * MM, z * MM) for x, y, z in verts], [], faces)
        mesh.validate()
        mesh.update()

        # scalenie pokrywajacych sie wierzcholkow na luku + gladkie normalne krawedzi
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(part.name, mesh)
        obj.data.materials.append(_material(bpy, part.kind))
        obj["kind"] = part.kind
        obj["grain"] = part.grain
        obj["material_spec"] = part.material
        obj["thickness_mm"] = part.thickness
        _collection(bpy, root, COLLECTIONS[part.kind]).objects.link(obj)
        made += 1

    return made


def main():
    s = summary()
    n = build_scene()
    p, d = PARAMS, DERIVED
    print("=" * 58)
    print("Regal R150  %.0f x %.0f x %.0f mm" % (p["W"], p["H"], p["D"]))
    print("=" * 58)
    print("  zaoblenie      R%.0f, przedni lewy narozik, cala wysokosc, bez poszycia" % p["R"])
    print("  przesla        %d x %.0f mm swiatla" % (p["N_BAYS"], d["bay_clear"]))
    print("  poziomy        %d, swiatlo miedzypolkowe %.1f mm"
          % (p["N_LEVELS"], d["shelf_clear"]))
    print("  nos + przeslo0 scalone w jedna plyte na kazdym z %d poziomow" % p["N_LEVELS"])
    print("  lewy bok       grzbiet + 5 zebow, wrab przelotowy w kazdym zlaczu")
    print("  obiektow       %d" % n)
    print("  srub M6        %d" % s["n_bolts"])
    print("  masa netto     %.1f kg" % s["mass_kg"])
    print("=" * 58)


if __name__ == "__main__":
    main()
