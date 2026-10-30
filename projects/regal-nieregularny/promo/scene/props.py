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


def _obj(S, name, me, loc=(0, 0, 0), rot=None, coll=None, parent=None):
    """Obiekt rekwizytu; `loc`/`rot` w układzie mebla (REGAL). `parent` = rig (np. DRW_S09) – obiekt jedzie
    z szufladą (macierz liczona z pozycji spoczynkowej rigu)."""
    ob = bpy.data.objects.new(name, me)
    (coll or S.colls["REKWIZYTY"]).objects.link(ob)
    mat = Matrix.Translation(loc)
    if rot is not None:
        mat = mat @ rot
    ob.parent = parent or S.root
    ob.matrix_parent_inverse = Matrix.Identity(4)
    if parent is not None:
        pF = S.rest_F(parent)
        mat = pF.inverted() @ mat
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
    S.mats["clay"] = cer_terra
    build_extra(S, rnd)
    n_shelf = len(S.props)
    S.contents = build_contents(S, rnd)
    S.n_props_shelf = n_shelf
    return S.props

# --------------------------------------------------------------------------- grupy G–K i zawartość mebli
def framed_print(S, name, loc, w=0.16, h=0.22, lean_deg=6.0, frame_w=0.012, depth=0.015):
    """Grafika w ramce (kremowy papier, koło terakota Ø70) oparta o ścianę. `loc` = środek dolnej tylnej krawędzi."""
    bm = bmesh.new()

    def bx(x0, x1, y0, y1, z0, z1, mi):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r["verts"]
        bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=vs)
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = mi

    fw = frame_w
    bx(-w / 2, w / 2, -depth, 0, 0, fw, 0)
    bx(-w / 2, w / 2, -depth, 0, h - fw, h, 0)
    bx(-w / 2, -w / 2 + fw, -depth, 0, fw, h - fw, 0)
    bx(w / 2 - fw, w / 2, -depth, 0, fw, h - fw, 0)
    bx(-w / 2 + fw, w / 2 - fw, -depth * 0.55, -depth * 0.45, fw, h - fw, 1)    # papier (passe-partout)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.ceramic("Rama_dab", "B89A72", rough=0.55, speckle=0.0, glaze=0.0))
    me.materials.append(print_material())
    rot = Matrix.Rotation(-math.radians(lean_deg), 4, "X")
    ob = _obj(S, name, me, loc, rot)
    mod = ob.modifiers.new("faza", "BEVEL")
    mod.width = 0.0008
    mod.segments = 2
    return ob


def print_material(name="Grafika_kolo_terakota"):
    """Papier kremowy z kołem terakota Ø70 mm (proceduralnie, współrzędne obiektu ramki)."""
    m, nt, nb = M.new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-800, 0))
    o = nb.separate(tc.outputs["Object"], (-600, 0))
    dx = nb.math("SUBTRACT", o[0], 0.0)
    dz = nb.math("SUBTRACT", o[2], 0.125)
    r = nb.math("SQRT", nb.math("ADD", nb.math("MULTIPLY", dx, dx), nb.math("MULTIPLY", dz, dz)))
    circ = nb.maprange(r, 0.0345, 0.0355, 1.0, 0.0, (-300, 0))
    grain = nb.noise(tc.outputs["Object"], scale=600.0, detail=2.0, loc=(-500, -250))
    paper = nb.mix(nb.maprange(grain.outputs["Fac"], 0.3, 0.7, 0.0, 0.08), M.hex_lin("F1EBDF"), M.hex_lin("D9CFBD"))
    col = nb.mix(circ, paper, M.hex_lin("B5593D"), (-100, 0))
    b = M.principled(nb)
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    M.out_node(nb, b.outputs[0])
    return m


def folded_cloth(S, name, loc, size=(0.16, 0.24, 0.048), color="E3D9C4", parent=None, rnd=None):
    """Złożona tkanina: 4 zaokrąglone warstwy z drobnymi przesunięciami (fałdy)."""
    rnd = rnd or random.Random(1)
    sx, sy, sz = size
    n = 4
    bm = bmesh.new()
    for i in range(n):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r["verts"]
        th = sz / n
        bmesh.ops.scale(bm, vec=(sx - rnd.uniform(0, 0.004), sy - rnd.uniform(0, 0.006), th * 0.98), verts=vs)
        bmesh.ops.translate(bm, vec=(rnd.uniform(-0.002, 0.002), rnd.uniform(-0.003, 0.003), th * (i + 0.5)),
                            verts=vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.cloth_cover(f"tkanina_{name}", color, rough=0.85))
    ob = _obj(S, name, me, loc, parent=parent)
    mod = ob.modifiers.new("faza", "BEVEL")
    mod.width = sz / n * 0.45
    mod.segments = 3
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return ob


def pencil(S, name, loc, length=0.175, d=0.007, color="B5593D", parent=None):
    """Ołówek sześciokątny wzdłuż X: lakierowany korpus + zatemperowany czubek (drewno + grafit)."""
    tip = 0.018
    body = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=d / 2, radius2=d / 2, depth=length - tip)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    for f in bm.faces:
        f.material_index = 0
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=d / 2, radius2=0.0006, depth=tip)
    bmesh.ops.rotate(bm, verts=r["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, verts=r["verts"], vec=((length - tip) / 2 + tip / 2, 0, 0))
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = 1
    bm.to_mesh(body)
    bm.free()
    body.materials.append(M.plastic(f"lakier_{name}", M.hex_lin(color)[:3], rough=0.35))
    body.materials.append(M.plastic("drewno_olowka", M.hex_lin("D8B88E")[:3], rough=0.7))
    rot = Matrix.Rotation(math.radians(30), 4, "X")
    return _obj(S, name, body, (loc[0], loc[1], loc[2] + d * 0.433), rot, parent=parent)


def build_extra(S, rnd):
    cer_terra = M.ceramic("Kamionka_terakota", "B5593D", rough=0.65, speckle=0.12, glaze=0.0)
    cer_sage = M.ceramic("Kamionka_szalwia", "7F8A6E", rough=0.6, speckle=0.3)
    cer_clay = S.mats.get("clay") or M.ceramic("Glina_terakota_2", "B07A5C", rough=0.75, speckle=0.15, glaze=0.0)
    # G: #08 – 5 albumów pionowo przy prawej przegrodzie
    xa, xb, za, zb = cell_box(70, 100, 30, 60)
    x = xb - 0.002
    cols = ["34404F", "D2C3A5", "7F8A6E", "3B3936", "E3D9C4"]
    for i, ccol in enumerate(cols):
        w = rnd.uniform(0.020, 0.030)
        h = min(zb - za - 0.014, rnd.uniform(0.245, 0.266))
        d = rnd.uniform(0.21, 0.25)
        _book(S, f"prop_album_G{i}", w, h, d, ccol, (x - w / 2, 0.06 + d / 2, za))
        x -= w + 0.0008
    # H: #15 – walcowy wazon terakota Ø90×200 + 2 książki płasko
    xa, xb, za, zb = cell_box(120, 150, 60, 90)
    cylinder_vase(S, "prop_wazon_H", (xa + 0.075, 0.21, za), r=0.045, h=0.20, mat=cer_terra)
    books_stack(S, rnd, (120, 150, 60, 90), n=2, x_left=xb - 0.205, y_c=0.2, prefix="H", rot_deg=[1, -3])
    # I: #26 – grafika w ramce oparta o ścianę
    xa, xb, za, zb = cell_box(110, 130, 90, 120)
    yw = getattr(S, "wall_y", S.D + 0.0095)
    lean = 6.0
    y_bottom = yw - 0.22 * math.sin(math.radians(lean)) - 0.0005
    framed_print(S, "prop_grafika_I", ((xa + xb) / 2, y_bottom, za), lean_deg=lean)
    # J: #31 – 4 paperbacki płasko + kubek szałwia
    xa, xb, za, zb = cell_box(70, 100, 120, 140)
    top = za
    pcols = ["E3D9C4", "B5593D", "D2C3A5", "34404F"]
    for i, ccol in enumerate(pcols):
        th = rnd.uniform(0.012, 0.02)
        L, D = 0.178 - i * 0.004, 0.11 - i * 0.002
        ang = math.radians(rnd.uniform(-5, 5))
        rot = Matrix.Rotation(ang, 4, "Z") @ Matrix.Rotation(math.radians(-90), 4, "Y")
        ob = _book(S, f"prop_paperback_J{i}", th, L, D, ccol, (0, 0, 0))
        ob.matrix_basis = Matrix.Translation((xa + 0.03 + L / 2, 0.2, top + th / 2)) @ rot @ \
            Matrix.Translation((0, 0, -L / 2))
        top += th
    cylinder_vase(S, "prop_kubek_J", (xb - 0.055, 0.17, za), r=0.034, h=0.085, mat=cer_sage)
    # K: #46 – mała misa terakota Ø120
    xa, xb, za, zb = cell_box(150, 170, 150, 170)
    bowl(S, "prop_misa_K", ((xa + xb) / 2, 0.2, za), r=0.06, h=0.045, foot=0.03, mat=cer_clay)


def build_contents(S, rnd):
    """Zawartość mebli do ujęć funkcyjnych: S09 tkaniny, S10 flat-lay, DZ02 misy + słoik (rodzic = rig)."""
    out = []
    # S09: 3 złożone tkaniny 240×160×(40–55) – krem, szałwia, terakota
    d = S.drawers.get("S09")
    if d:
        bx, by, bz, Wb, Lb, Hb = d.box
        zb = bz + 0.0165
        x0 = bx + 0.018 + 0.012
        for i, (ccol, hh) in enumerate((("E3D9C4", 0.050), ("7F8A6E", 0.044), ("B5593D", 0.054))):
            out.append(folded_cloth(S, f"prop_tkanina_S09_{i}", (x0 + 0.08 + i * 0.172, by + 0.018 + 0.135, zb),
                                    (0.16, 0.24, hh), ccol, parent=d.rig, rnd=rnd))
    # S10: notes A5 szałwia, 3 ołówki, linijka brzozowa – równolegle do X
    d = S.drawers.get("S10")
    if d:
        bx, by, bz, Wb, Lb, Hb = d.box
        zb = bz + 0.0165
        xi0 = bx + 0.018
        # notes A5 leży okładką do góry: książka (gr. 10, wys. 210, gł. 148) położona na boku, grzbiet wzdłuż Y
        me = book_mesh("prop_notes_S10", 0.010, 0.21, 0.148, stripe=(0.0, 1.0))
        me.materials.append(M.cloth_cover("okladka_notes", "7F8A6E", rough=0.8))
        me.materials.append(S.mats["paper"])
        me.materials.append(M.cloth_cover("gumka_notes", "3B3936", rough=0.5))
        cx, cy = xi0 + 0.012 + 0.074, by + 0.018 + 0.202
        rot = Matrix.Rotation(math.radians(90), 4, "Z") @ Matrix.Rotation(math.radians(-90), 4, "Y")
        mat = Matrix.Translation((cx, cy, zb + 0.005)) @ rot @ Matrix.Translation((0, 0, -0.105))
        ob = _obj(S, "prop_notes_S10", me, (0, 0, 0), parent=d.rig)
        ob.matrix_basis = S.rest_F(d.rig).inverted() @ mat
        out.append(ob)
        for i, ccol in enumerate(("B5593D", "3B3936", "D8B88E")):
            out.append(pencil(S, f"prop_olowek_S10_{i}", (xi0 + 0.022 + 0.0875, by + 0.018 + 0.017 + i * 0.015, zb),
                              color=ccol, parent=d.rig))
        rul = bpy.data.meshes.new("linijka")
        rbm = bmesh.new()
        rbm.loops.layers.uv.new("UVMap")
        bmesh.ops.create_cube(rbm, size=1.0, calc_uvs=True)
        bmesh.ops.scale(rbm, vec=(0.2, 0.025, 0.003), verts=rbm.verts)
        bmesh.ops.translate(rbm, vec=(0, 0, 0.0015), verts=rbm.verts)
        rbm.to_mesh(rul)
        rbm.free()
        rul.materials.append(S.mats.get("ruler") or M.plywood("Linijka_brzoza", t_mm=3.0, plies=1, edge_contrast=0.0))
        out.append(_obj(S, "prop_linijka_S10", rul, (xi0 + 0.0101 + 0.1, by + 0.018 + 0.072, zb), parent=d.rig))
    # DZ02: dwie misy szałwia jedna na drugiej + słoik terakota (szafka, za drzwiczkami)
    cer_sage = bpy.data.materials.get("Kamionka_szalwia") or M.ceramic("Kamionka_szalwia", "7F8A6E")
    cer_terra = bpy.data.materials.get("Kamionka_terakota") or M.ceramic("Kamionka_terakota", "B5593D")
    xa, xb, za, zb = cell_box(130, 170, 90, 120)
    out.append(bowl(S, "prop_misa_DZ02_a", (xa + 0.12, 0.2, za), r=0.085, h=0.05, foot=0.04, mat=cer_sage))
    out.append(bowl(S, "prop_misa_DZ02_b", (xa + 0.12, 0.2, za + 0.012), r=0.075, h=0.045, foot=0.035,
                    mat=cer_sage))
    out.append(cylinder_vase(S, "prop_sloik_DZ02", (xb - 0.09, 0.22, za), r=0.045, h=0.14, mat=cer_terra))
    return out
