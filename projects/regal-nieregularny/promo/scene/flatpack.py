"""flatpack.py – montaż "z płaskiego": arkusze z prawdziwego rozkroju (data/nesting.json) → lot formatek do mebla.

Używane przez film.py (ujęcia S07 "140 elementów" i S08 "Z płaskiego"), ale niezależne od choreografii:
  load_nesting()                       – JSON z export_nesting.py (regal.cnc.run_nesting z repo cnc)
  sheet_layout(grid=SHEET_GRID_MM)     – pid → macierz świata formatki leżącej w arkuszu na podłodze
  build_sheets(layout)                 – szkielety arkuszy (płyta z otworami po frezie Ø6 = kontur +3 mm),
                                         przymiary PRZ* (zostają w arkuszach)
  part_world_rest(pid) / to_parent_basis(ob, Mworld)
  key_part_world(ob, frame, Mworld)    – klucz położenia/obrotu obiektu z macierzy świata
  flight_samples(...)                  – Bezier P0 → P0+(0,0,h) → P1+lead → P1, obrót slerp, ease
Konwencja: formatka leży licem A do góry (obróbka jednostronna), oś u wzdłuż X arkusza (rot=False) albo
wzdłuż Y (rot=True, obrót 90° CCW), jak w regal.nesting.to_sheet().
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector, geometry

import build_scene as B
import materials as M

MM = 0.001

# Siatka arkuszy na podłodze (research-brief 5.7), mm w układzie modelu: (X0, Y0) = lewy‑dolny róg arkusza
SHEET_GRID_MM = {
    (18.0, 1): (-4100, -2750), (18.0, 2): (-1450, -2750), (18.0, 3): (1200, -2750),
    (18.0, 4): (-4100, -4150), (18.0, 5): (-1450, -4150), (18.0, 6): (1200, -4150),
    (6.5, 1): (-2625, -5550), (6.5, 2): (25, -5550),
}
KERF_MM = 3.0


def load_nesting(path=None):
    p = Path(path) if path else B.PROMO_DIR / "data" / "nesting.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _place_matrix(pl, X0, Y0):
    """Macierz świata (m) formatki leżącej na podłodze w arkuszu (lico A do góry)."""
    u0, v0, u1, v1 = pl["bbox"]
    if not pl["rot"]:
        R = Matrix(((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        o = (X0 + pl["x"] - u0, Y0 + pl["y"] - v0)
    else:
        R = Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))
        Hp = v1 - v0
        o = (X0 + pl["x"] + Hp + v0, Y0 + pl["y"] - u0)
    M4 = R.to_4x4()
    M4.translation = Vector((o[0] * MM, o[1] * MM, 0.0))
    return M4


def sheet_layout(nest=None, grid=None):
    nest = nest or load_nesting()
    grid = grid or SHEET_GRID_MM
    out, sheets = {}, []
    for sh in nest["sheets"]:
        X0, Y0 = grid[(float(sh["t"]), int(sh["index"]))]
        sheets.append(dict(sh, X0=X0, Y0=Y0))
        for pl in sh["placements"]:
            out[pl["pid"]] = dict(M=_place_matrix(pl, X0, Y0), pl=pl, sheet=(sh["t"], sh["index"]), X0=X0, Y0=Y0)
    return dict(parts=out, sheets=sheets)


def _offset_poly(pts, d):
    """Przesunięcie wielokąta prostego o d na zewnątrz (fazowanie "miter" – dokładne dla obrysów prostokątnych)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2
    sgn = 1.0 if area > 0 else -1.0       # CCW → normalna zewnętrzna = (dy, −dx)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e0, e1 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n0 = Vector((e0.y, -e0.x)) * sgn
        n1 = Vector((e1.y, -e1.x)) * sgn
        bis = (n0 + n1)
        if bis.length < 1e-9:
            out.append(tuple(p1 + n0 * d))
            continue
        bis.normalize()
        cosh = max(0.2, bis.dot(n0))
        out.append(tuple(p1 + bis * (d / cosh)))
    return out


def _to_sheet_pts(pl, outline):
    u0, v0, u1, v1 = pl["bbox"]
    res = []
    for u, v in outline:
        uu, vv = u - u0, v - v0
        if not pl["rot"]:
            res.append((pl["x"] + uu, pl["y"] + vv))
        else:
            res.append((pl["x"] + (v1 - v0 - vv), pl["y"] + uu))
    return res


def build_sheets(layout, collection_name="ARKUSZE", gauges=True):
    """Szkielety arkuszy (płyta 2500×1250 z otworami = kontur formatki + 3 mm) leżące na podłodze."""
    c = B.coll(collection_name)
    mats = {18.0: B.S.mats.get("ply") or M.plywood("Sklejka_brzoza_18_korpus"),
            6.5: B.S.mats.get("thin") or M.plywood("Sklejka_brzoza_6.5_BBCP", t_mm=6.5, plies=5, grade="CP")}
    objs = []
    for sh in layout["sheets"]:
        t = float(sh["t"]) * MM
        W, H = sh["W"], sh["H"]
        outer = [(0, 0), (W, 0), (W, H), (0, H)]
        holes = [_offset_poly(_to_sheet_pts(pl, pl["outline"]), KERF_MM) for pl in sh["placements"]]
        loops = [outer] + holes
        vloops = [[Vector((x, y, 0.0)) for x, y in lp] for lp in loops]
        tris = geometry.tessellate_polygon(vloops)
        flat = [v for lp in vloops for v in lp]
        bm = bmesh.new()
        bot = [bm.verts.new((v.x * MM, v.y * MM, 0.0)) for v in flat]
        top = [bm.verts.new((v.x * MM, v.y * MM, t)) for v in flat]
        for a, b_, c_ in tris:
            try:
                bm.faces.new((top[a], top[b_], top[c_]))
                bm.faces.new((bot[c_], bot[b_], bot[a]))
            except ValueError:
                pass
        k = 0
        for lp in vloops:
            n = len(lp)
            for i in range(n):
                i0, i1 = k + i, k + (i + 1) % n
                try:
                    bm.faces.new((bot[i0], bot[i1], top[i1], top[i0]))
                except ValueError:
                    pass
            k += n
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        uvl = bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x + sh["index"] * 0.7, lp.vert.co.y)
        me = bpy.data.meshes.new(f"arkusz_{sh['t']:g}_{sh['index']}")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mats[float(sh["t"])])
        ob = B.new_obj(f"ARKUSZ_{sh['t']:g}mm_{sh['index']}", me, c)
        ob.location = (sh["X0"] * MM, sh["Y0"] * MM, 0.0)
        objs.append(ob)
        if gauges:
            for pl in sh["placements"]:
                if pl["group"] != "pomoc":
                    continue
                p = dict(pid=pl["pid"], t=pl["t"], outline=pl["outline"], origin=[0, 0, 0], eu=[1, 0, 0], ev=[0, 1, 0],
                         ew=[0, 0, 1])
                gme = B.part_mesh(p, (1, 0, 0))
                gme.materials.append(mats[float(sh["t"])])
                g = B.new_obj(f"przymiar_{pl['pid']}", gme, c)
                g.matrix_world = layout["parts"][pl["pid"]]["M"]
                objs.append(g)
    return objs


# --------------------------------------------------------------------------- macierze
def root_world():
    return Matrix.Translation((0, 0, B.FOOT_H))


def part_world_rest(ob):
    return root_world() @ B.rest_F(ob)


def parent_world_rest(ob):
    return root_world() @ B.rest_F(ob.parent) if ob.parent is not None and ob.parent is not B.S.root else root_world()


def key_part_world(ob, frame, Mw, interp="LINEAR"):
    """Klucz obiektu z macierzy świata (rodzic w pozycji spoczynkowej)."""
    basis = parent_world_rest(ob).inverted() @ Mw
    loc, q, sc = basis.decompose()
    if ob.rotation_mode != "QUATERNION":
        ob.rotation_mode = "QUATERNION"
    ob.location = loc
    ob.rotation_quaternion = q
    e = bpy.context.preferences.edit
    old = e.keyframe_new_interpolation_type
    e.keyframe_new_interpolation_type = interp
    try:
        ob.keyframe_insert("location", frame=frame)
        ob.keyframe_insert("rotation_quaternion", frame=frame)
    finally:
        e.keyframe_new_interpolation_type = old


def bezier(p0, p1, p2, p3, u):
    a = 1 - u
    return p0 * a ** 3 + p1 * 3 * a * a * u + p2 * 3 * a * u * u + p3 * u ** 3


def flight_samples(M0, M1, f0, n=14, lift=0.9, lead=(0.0, -0.9, 0.0), rot_frac=0.75, ease=None, final_push=0.0):
    """Lot z M0 do M1: [(klatka, Mworld)]. Pozycja po Bezierze z łatwieniem ease (domyślnie ease-out cubic),
    obrót slerp na pierwszych `rot_frac` lotu. `final_push` (m) – ostatni odcinek prosto wzdłuż +Y ("wpięcie")."""
    ease = ease or B.ease_out_cubic
    p0, p3 = M0.translation.copy(), M1.translation.copy()
    p1 = p0 + Vector((0, 0, lift))
    p2 = p3 + Vector(lead)
    q0, q1 = M0.to_quaternion(), M1.to_quaternion()
    if q0.dot(q1) < 0:
        q1 = -q1
    out = []
    for i in range(int(n) + 1):
        tau = i / n
        u = ease(tau)
        pos = bezier(p0, p1, p2, p3, u)
        if final_push:
            pos = pos  # tor Beziera z lead (0, −0.9, 0) i tak dochodzi wzdłuż +Y
        s = min(1.0, tau / rot_frac)
        s = s * s * (3 - 2 * s)
        q = q0.slerp(q1, s)
        out.append((f0 + i, Matrix.LocRotScale(pos, q, Vector((1, 1, 1)))))
    return out


def lifted(Mw, dz):
    M2 = Mw.copy()
    M2.translation = Mw.translation + Vector((0, 0, dz))
    return M2


def key_scale_pop(ob, f_on, dur=4, hide_before=None, interp_after="LINEAR"):
    """Skala 0,001 → 1 w `dur` klatek od f_on (pojawienie się okucia/gałki)."""
    e = bpy.context.preferences.edit
    old = e.keyframe_new_interpolation_type
    try:
        e.keyframe_new_interpolation_type = "CONSTANT"
        if hide_before is not None:
            ob.scale = (1, 1, 1)
            ob.keyframe_insert("scale", frame=hide_before - 1)
            ob.scale = (0.001,) * 3
            ob.keyframe_insert("scale", frame=hide_before)
        e.keyframe_new_interpolation_type = "LINEAR"
        for i in range(dur + 1):
            s = max(0.001, B.ease_out_cubic(i / dur))
            ob.scale = (s, s, s)
            ob.keyframe_insert("scale", frame=f_on + i)
    finally:
        e.keyframe_new_interpolation_type = old
    B.set_interp(ob, "LINEAR", f_on, f_on + dur, path="scale")
    if hide_before is not None:
        B.set_interp(ob, "CONSTANT", hide_before - 1, hide_before, path="scale")


def key_hide(ob, frames_states):
    """hide_render/hide_viewport w klatkach: [(klatka, ukryty)] (CONSTANT)."""
    for f, h in frames_states:
        ob.hide_render = h
        ob.hide_viewport = h
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)
