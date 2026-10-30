"""Rekwizyty proceduralne: książki, kamionka, gałązka oliwki. Stonowana paleta japandi.

Rozmieszczenie w otwartych wnękach (współrzędne komórek z data/layout.json, cm osiowo):
  A [20,60]×[170,200]  rząd książek + jedna oparta
  B [30,70]×[90,140]   wysoka wnęka: butelkowy wazon + gałązka oliwki, 2 książki na płasko
  C [40,80]×[150,170]  stos 3 książek + mała misa
  D [100,140]×[170,200] płaska misa + mały wazonik
  E [80,110]×[140,170]  "moon vase" grafit
  F [20,60]×[70,90]    stos książek
Wszystkie obiekty: kolekcja REKWIZYTY, rodzic REGAL (ruszają się z meblem), nazwy prop_*.
"""
from __future__ import annotations

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import materials as M

MM = 0.001
T = 0.018  # grubość półki/przegrody

PALETTE_BOOKS = ["8A9A7B", "A9705A", "E3D9C4", "3E3C39", "6F8396", "C49A52", "D2C3A5", "5F6346", "8C5A3C",
                 "B9A58A", "7D6E62", "EFE9DD"]


def cell_box(x0, x1, y0, y1):
    """Wnętrze komórki (m, układ mebla): (xa, xb, za, zb)."""
    return x0 * 0.01 + T / 2, x1 * 0.01 - T / 2, y0 * 0.01 + T, y1 * 0.01


def _obj(S, name, me, loc=(0, 0, 0), rot=None, coll=None):
    ob = bpy.data.objects.new(name, me)
    (coll or S.colls["REKWIZYTY"]).objects.link(ob)
    ob.parent = S.root
    ob.matrix_parent_inverse = Matrix.Identity(4)
    mat = Matrix.Translation(loc)
    if rot is not None:
        mat = mat @ rot
    ob.matrix_basis = mat
    S.props.append(ob)
    return ob


# --------------------------------------------------------------------------- książki
def book_mesh(name, w, h, d, board=0.0022, inset=0.003, stripe=None):
    """Książka stojąca: grubość w (X), wysokość h (Z), głębokość d (Y); grzbiet z przodu (−Y).
    Początek: środek podstawy. Materiały: 0 okładka, 1 kartki, 2 pasek na grzbiecie."""
    bm = bmesh.new()

    def bx(x0, x1, y0, y1, z0, z1, mi):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r["verts"]
        bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=vs)
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = mi

    y_front, y_back = -d / 2, d / 2
    bx(-w / 2, -w / 2 + board, y_front, y_back, 0, h, 0)                # okładka tylna (lewa)
    bx(w / 2 - board, w / 2, y_front, y_back, 0, h, 0)                  # okładka przednia (prawa)
    bx(-w / 2, w / 2, y_front, y_front + board, 0, h, 0)                # grzbiet
    bx(-w / 2 + board, w / 2 - board, y_front + board, y_back - inset, inset, h - inset, 1)  # kartki
    if stripe:
        z0, z1 = stripe
        bx(-w / 2 + 0.0004, w / 2 - 0.0004, y_front - 0.00025, y_front + 0.0002, h * z0, h * z1, 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def _book(S, name, w, h, d, color, loc, rot=None, stripe=None, stripe_col="C9B27C"):
    me = book_mesh(name, w, h, d, stripe=stripe)
    me.materials.append(M.cloth_cover(f"okladka_{name}", color, rough=0.72))
    me.materials.append(S.mats["paper"])
    me.materials.append(M.cloth_cover(f"pasek_{name}", stripe_col, rough=0.5))
    ob = _obj(S, name, me, loc, rot)
    mod = ob.modifiers.new("faza", "BEVEL")
    mod.width = 0.0006
    mod.segments = 2
    mod.limit_method = "ANGLE"
    return ob


def books_row(S, rnd, cell, n=7, from_right=True, lean=True, y_spine=0.035, prefix="A", hmax=None):
    xa, xb, za, zb = cell_box(*cell)
    hmax = hmax or (zb - za - 0.03)
    x = xb - 0.002 if from_right else xa + 0.002
    cols = rnd.sample(PALETTE_BOOKS, k=min(n + 1, len(PALETTE_BOOKS)))
    last_face = None
    for i in range(n):
        w = rnd.uniform(0.016, 0.038)
        h = min(hmax, rnd.uniform(0.20, 0.255))
        d = rnd.uniform(0.15, 0.19)
        cx = x - w / 2 if from_right else x + w / 2
        stripe = (0.78, 0.82) if rnd.random() < 0.3 else None
        _book(S, f"prop_ksiazka_{prefix}{i}", w, h, d, cols[i], (cx, y_spine + d / 2, za), stripe=stripe)
        x = x - w - 0.0008 if from_right else x + w + 0.0008
        last_face = x
    if lean:
        w = rnd.uniform(0.02, 0.03)
        h = min(hmax, 0.24)
        d = 0.17
        th = math.radians(14)
        # obrót wokół dolnej krawędzi od strony rzędu, górny narożnik opiera się o ostatnią książkę
        sgn = 1 if from_right else -1
        xs = last_face + sgn * 0.0005
        xc = xs - sgn * h * math.sin(th)
        rot = Matrix.Rotation(sgn * th, 4, "Y")
        # w układzie książki pivot = dolny narożnik po stronie rzędu: przesuwamy siatkę
        me_name = f"prop_ksiazka_{prefix}_oparta"
        ob = _book(S, me_name, w, h, d, cols[n % len(cols)], (0, 0, 0))
        off = Matrix.Translation((-sgn * w / 2, 0, 0))
        ob.matrix_basis = Matrix.Translation((xc, y_spine + d / 2 + 0.01, za)) @ rot @ off
    return x


def books_stack(S, rnd, cell, n=3, x_left=None, y_c=0.2, prefix="C", rot_deg=None):
    xa, xb, za, zb = cell_box(*cell)
    z = za
    x0 = x_left if x_left is not None else xa + 0.03
    cols = rnd.sample(PALETTE_BOOKS, k=n)
    top = z
    for i in range(n):
        th = rnd.uniform(0.018, 0.034)
        L = rnd.uniform(0.22, 0.25) - i * 0.012
        D = rnd.uniform(0.16, 0.18) - i * 0.008
        ang = math.radians(rot_deg[i] if rot_deg else rnd.uniform(-4, 4))
        # książka leżąca: wysokość książki → X, grubość → Z
        rot = Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.radians(-90), 4, "Y")
        ob = _book(S, f"prop_ksiazka_{prefix}{i}", th, L, D, cols[i], (0, 0, 0))
        ob.matrix_basis = Matrix.Translation((x0 + L / 2, y_c, top + th / 2)) @ rot @ \
            Matrix.Translation((0, 0, -L / 2))
        top += th
    return top


# --------------------------------------------------------------------------- kamionka
def vessel_mesh(name, outer, wall=0.004, depth=None, segments=72):
    """Naczynie z profilu zewnętrznego [(r,z) od dna do krawędzi]; ścianka `wall`, wnętrze do `depth`."""
    rim_r, rim_z = outer[-1]
    inner = []
    depth = depth if depth is not None else rim_z - 0.006
    # zaokrąglona krawędź
    inner.append((rim_r - wall * 0.5, rim_z + wall * 0.25))
    inner.append((rim_r - wall, rim_z))
    for r, z in reversed(outer[:-1]):
        if z < rim_z - depth:
            break
        inner.append((max(0.0005, r - wall), z))
    inner.append((0.0, inner[-1][1] - wall * 0.5))
    prof = [(0.0, 0.0)] + outer + inner
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0.0, z)) for r, z in prof]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=segments,
                   use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


def smooth_profile(ctrl, n=40):
    """Gładki profil (Catmull-Rom) przez punkty kontrolne (r, z)."""
    pts = [Vector((r, z)) for r, z in ctrl]
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        steps = max(2, n // (len(pts) - 1))
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append((max(0.0, q.x), q.y))
    out.append((pts[-1].x, pts[-1].y))
    return out


def bottle_vase(S, name, loc, h=0.235, body_r=0.062, neck_r=0.016, mat=None):
    ctrl = [(0.040, 0.0), (body_r * 0.97, 0.03), (body_r, 0.09), (body_r * 0.88, 0.15), (neck_r * 1.6, 0.19),
            (neck_r, 0.205), (neck_r * 1.05, h - 0.004), (neck_r * 1.25, h)]
    me = vessel_mesh(name, [(0.036, 0.0005)] + smooth_profile(ctrl, 60), wall=0.0035, depth=0.05)
    me.materials.append(mat)
    return _obj(S, name, me, loc)


def moon_vase(S, name, loc, r=0.085, mat=None):
    ctrl = [(0.03, 0.0)]
    for i in range(1, 12):
        a = -math.pi / 2 + math.pi * i / 12
        ctrl.append((r * math.cos(a), r + r * math.sin(a)))
    ctrl += [(0.022, 2 * r + 0.004), (0.024, 2 * r + 0.016)]
    me = vessel_mesh(name, smooth_profile(ctrl, 60), wall=0.004, depth=0.04)
    me.materials.append(mat)
    return _obj(S, name, me, loc)


def bowl(S, name, loc, r=0.1, h=0.06, foot=0.045, mat=None):
    ctrl = [(foot, 0.0), (foot + 0.004, 0.006), (r * 0.8, h * 0.45), (r * 0.97, h * 0.85), (r, h)]
    me = vessel_mesh(name, smooth_profile(ctrl, 40), wall=0.005, depth=h)
    me.materials.append(mat)
    return _obj(S, name, me, loc)


def cylinder_vase(S, name, loc, r=0.035, h=0.13, mat=None):
    ctrl = [(r * 0.92, 0.0), (r, 0.006), (r, h * 0.7), (r * 0.96, h - 0.004), (r * 0.94, h)]
    me = vessel_mesh(name, smooth_profile(ctrl, 30), wall=0.004, depth=0.06)
    me.materials.append(mat)
    return _obj(S, name, me, loc)


# --------------------------------------------------------------------------- gałązka
def _leaf_geom(bm, M4, L=0.06, W=0.011, n=8, fold=0.25, droop=0.008):
    rows = []
    for i in range(n + 1):
        t = i / n
        w = W * (math.sin(math.pi * min(t * 1.08, 1.0)) ** 0.75) * 0.5
        x = L * t
        z = -droop * t * t
        row = [M4 @ Vector((x, -w, z - w * fold)), M4 @ Vector((x, 0.0, z)), M4 @ Vector((x, w, z - w * fold))]
        rows.append([bm.verts.new(p) for p in row])
    for i in range(n):
        a, b = rows[i], rows[i + 1]
        bm.faces.new((a[0], b[0], b[1], a[1]))
        bm.faces.new((a[1], b[1], b[2], a[2]))


def olive_branch(S, name, base, rnd, height=0.40, lean=(-0.10, 0.0), n_twigs=3, leaves_per=9):
    """Gałązka oliwki: łodygi = krzywe z fazą (zbieżne), liście = jedna siatka (wąskie, złożone wzdłuż nerwu)."""
    cu = bpy.data.curves.new(name + "_lodyga", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0022
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    base = Vector(base)
    stems = []

    def add_stem(p0, direction, length, r0, nseg=8, bend=0.25):
        sp = cu.splines.new("NURBS")
        sp.points.add(nseg)
        pts = []
        d = Vector(direction).normalized()
        side = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.0))
        p = Vector(p0)
        for i in range(nseg + 1):
            t = i / nseg
            pts.append(p.copy())
            dd = (d + side * bend * t).normalized()
            p = p + dd * (length / nseg)
        for sp_pt, q, i in zip(sp.points, pts, range(nseg + 1)):
            sp_pt.co = (*q, 1.0)
            sp_pt.radius = r0 * (1.0 - 0.75 * i / nseg)
        sp.order_u = 4
        sp.use_endpoint_u = True
        stems.append(pts)
        return pts

    main = add_stem(base, (lean[0], lean[1], 1.0), height, 1.0, 10, 0.35)
    for k in range(n_twigs):
        i0 = rnd.randint(3, 7)
        p0 = main[i0]
        dirn = Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.5, 0.2), rnd.uniform(0.5, 1.0)))
        add_stem(p0, dirn, height * rnd.uniform(0.3, 0.45), 0.6, 6, 0.4)
    # liście
    bm = bmesh.new()
    for pts in stems:
        for i in range(2, len(pts)):
            if rnd.random() > leaves_per / len(pts):
                continue
            p, tgt = pts[i], (pts[i] - pts[i - 1]).normalized()
            for s in (-1, 1):
                if rnd.random() < 0.2:
                    continue
                side = tgt.cross(Vector((0, 0, 1)))
                if side.length < 1e-3:
                    side = Vector((1, 0, 0))
                side.normalize()
                rr = Matrix.Rotation(rnd.uniform(0, 2 * math.pi), 3, tgt)
                side = rr @ side
                d = (tgt * 0.55 + side * s * 0.85).normalized()
                up = d.cross(side).normalized()
                yv = up.cross(d).normalized()
                M4 = Matrix((d, yv, up)).transposed().to_4x4()
                M4.translation = p
                _leaf_geom(bm, M4, L=rnd.uniform(0.045, 0.07), W=rnd.uniform(0.009, 0.013))
        # liście na końcu
        p, tgt = pts[-1], (pts[-1] - pts[-2]).normalized()
        side = tgt.orthogonal().normalized()
        up = tgt.cross(side).normalized()
        M4 = Matrix((tgt, side, up)).transposed().to_4x4()
        M4.translation = p
        _leaf_geom(bm, M4, L=0.05, W=0.01)
    me = bpy.data.meshes.new(name + "_liscie")
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.materials.append(S.mats["leaf"])
    lv = _obj(S, name + "_liscie", me)
    cu.materials.append(S.mats["bark"])
    st = _obj(S, name + "_lodyga", cu)
    return st, lv


# --------------------------------------------------------------------------- całość
def build(S, seed=3):
    c = bpy.data.collections.get("REKWIZYTY")
    if c is None:
        c = bpy.data.collections.new("REKWIZYTY")
        bpy.context.scene.collection.children.link(c)
    S.colls["REKWIZYTY"] = c
    rnd = random.Random(seed)
    S.mats["paper"] = M.paper_block()
    S.mats["leaf"] = M.leaf()
    S.mats["bark"] = M.bark()
    cer_white = M.ceramic("Kamionka_kremowa", "E8E1D4", rough=0.5, speckle=0.45)
    cer_char = M.ceramic("Kamionka_grafit", "3B3936", rough=0.62, speckle=0.25, speck_col="8A8378", glaze=0.05)
    cer_sand = M.ceramic("Kamionka_piaskowa", "CDB99A", rough=0.58, speckle=0.4)
    cer_terra = M.ceramic("Glina_terakota", "B07A5C", rough=0.75, speckle=0.15, glaze=0.0)

    # A: rząd książek w górnej wnęce (od prawej przegrody) + kubek
    books_row(S, rnd, (20, 60, 170, 200), n=7, from_right=True, lean=True, prefix="A")
    xa, xb, za, zb = cell_box(20, 60, 170, 200)
    cylinder_vase(S, "prop_kubek_A", (xa + 0.065, 0.20, za), r=0.038, h=0.095, mat=cer_sand)

    # B: wysoka wnęka – wazon + gałązka, dwie książki na płasko
    xa, xb, za, zb = cell_box(30, 70, 90, 140)
    vx, vy = xa + 0.13, 0.19
    bottle_vase(S, "prop_wazon_B", (vx, vy, za), mat=cer_white)
    olive_branch(S, "prop_galazka_B", (vx, vy, za + 0.20), rnd, height=0.21, lean=(0.25, -0.1, 0), n_twigs=3)
    books_stack(S, rnd, (30, 70, 90, 140), n=2, x_left=xb - 0.26, y_c=0.20, prefix="B", rot_deg=[2, -3])

    # C: stos trzech książek + mała misa na wierzchu
    top = books_stack(S, rnd, (40, 80, 150, 170), n=3, x_left=cell_box(40, 80, 150, 170)[0] + 0.03, y_c=0.21,
                      prefix="C", rot_deg=[0, 3, -2])
    xa, xb, za, zb = cell_box(40, 80, 150, 170)
    bowl(S, "prop_misa_C", (xa + 0.16, 0.21, top), r=0.055, h=0.035, foot=0.025, mat=cer_char)

    # D: płaska misa + wazonik
    xa, xb, za, zb = cell_box(100, 140, 170, 200)
    bowl(S, "prop_misa_D", (xa + 0.13, 0.20, za), r=0.105, h=0.055, foot=0.05, mat=cer_white)
    cylinder_vase(S, "prop_wazonik_D", (xb - 0.085, 0.22, za), r=0.03, h=0.16, mat=cer_terra)

    # E: moon vase
    xa, xb, za, zb = cell_box(80, 110, 140, 170)
    moon_vase(S, "prop_moon_E", ((xa + xb) / 2 + 0.01, 0.20, za), r=0.082, mat=cer_char)

    # F: stos książek w niskiej wnęce
    books_stack(S, rnd, (20, 60, 70, 90), n=3, x_left=cell_box(20, 60, 70, 90)[0] + 0.07, y_c=0.21, prefix="F",
                rot_deg=[-2, 1, 4])
    return S.props
