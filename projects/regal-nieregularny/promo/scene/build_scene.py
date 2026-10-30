"""build_scene.py – biblioteka sceny promo regału ze sklejki (Blender 5.x, Cycles/EEVEE).

Działa:  * jako moduł `bpy` (python3 skrypt.py),
         * w Blenderze bez GUI:  blender -b -P scene/lookdev.py -- --shot hero
         * w Blenderze z GUI (Scripting → Run Script) – nie resetuje preferencji (czyści tylko dane sceny).

Ścieżki (zmienne środowiskowe):
  CNC_REPO          repo produktu (domyślnie /home/user/cnc); model: $CNC_REPO/output/model.json
  PROMO_DIR         katalog promo (domyślnie katalog nadrzędny względem scene/)
  REGAL_MODEL_JSON  jawna ścieżka do model.json (gdy brak – CNC_REPO, a potem snapshot PROMO_DIR/data/model.json)
  RENDER_DEVICE     CPU | METAL | OPTIX | CUDA | HIP | ONEAPI (domyślnie CPU)

Układ współrzędnych (jak w model.json, ale w metrach):  X = szerokość (0..1,9 m, od lewej),
Y = głębokość (0 = lico frontów, +Y = do ściany), Z = do góry. Regał stoi na stopkach – podłoga z = 0,
korzeń mebla `REGAL` w z = FOOT_H.

Hierarchia mebla (każdy element = obiekt o nazwie z model.json):
  REGAL (empty, korzeń)
   ├─ ASM_<pid>   (empty – jednostka montażu flat‑pack; półki, przegrody, plecy)  → <pid> (mesh) → wkręty
   ├─ ASM_<Sxx>   → DRW_<Sxx> (empty, pivot wysuwu, oś −Y)  → Sxx-F, -BF, -BB, -L, -R, -DNO, gałka, człon szufl.
   │              → DRW_MID_<Sxx> (człon środkowy prowadnicy, połowa wysuwu)  + człon korpusowy (stały)
   └─ ASM_<DZxx>  → DOOR_<DZxx> (empty na osi zawiasu)  → DZxx (mesh), gałka, puszki zawiasów
                  + prowadniki i ramiona zawiasów (stałe)

Główne API (szczegóły w docstringach):
  build_all(...)                    – wszystko naraz (mebel + otoczenie + rekwizyty + światło)
  load_model(), clean_scene(), build_furniture(front_grain="model"), build_room("scandi"|"studio"), build_props(),
  light_rig_window(side="right", preset="poranek"), apply_light_preset("poranek"|"zlota", frame=None),
  light_rig_studio(), set_look("window"|"studio")
  set_drawer(code, frac), set_door(code, angle_deg), reset_rigs(), rest_F(obj)
  animate_drawer_open/close(...), animate_door_open/close(...)   – gotowe krzywe soft‑close + zdarzenia
  key_drawer_curve(code, [(f, mm)]), key_door_curve(code, [(f, deg)]), hermite_samples(...), hold_state(...)
                                    – dowolne krzywe (np. dokładnie z briefu) z zapisem prędkości do events.json
  assembly_units(), assembly_start(mode), set_assembly(name, t), animate_assembly(...)  (montaż jednostkami;
                                      montaż formatkami z prawdziwego rozkroju – flatpack.py)
  make_camera(...), animate_camera(...), camera_path(...)
  render_settings(preset, ...), setup_device(), render_still(...), render_animation(...), save_blend(...)
  log_event(), export_events(path), clear_events(), set_interp(idb, "LINEAR"|"CONSTANT"|"BEZIER", f0, f1)
Film (10 ujęć wg research-brief.md): film.py; look-dev: lookdev.py; benchmark: bench.py.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector

try:
    from . import materials as M  # type: ignore
except Exception:  # uruchomienie jako skrypt / z blender -P
    _d = str(Path(__file__).resolve().parent) if "__file__" in globals() else os.getcwd()
    if _d not in sys.path:
        sys.path.insert(0, _d)
    import materials as M  # noqa: E402

# =========================================================================== ścieżki
MM = 0.001


def _scene_dir() -> Path:
    if "__file__" in globals() and __file__:
        return Path(__file__).resolve().parent
    return Path(os.getcwd())


SCENE_DIR = _scene_dir()
PROMO_DIR = Path(os.environ.get("PROMO_DIR", SCENE_DIR.parent)).expanduser()
CNC_REPO = Path(os.environ.get("CNC_REPO", "/home/user/cnc")).expanduser()
RENDERS_DIR = PROMO_DIR / "renders"
FRAMES_DIR = PROMO_DIR / "frames"


def model_json_path() -> Path:
    env = os.environ.get("REGAL_MODEL_JSON")
    if env:
        return Path(env).expanduser()
    p = CNC_REPO / "output" / "model.json"
    if p.exists():
        return p
    return PROMO_DIR / "data" / "model.json"


def script_args(argv=None):
    """Argumenty po '--' (blender -b -P skrypt.py -- --shot hero)."""
    argv = sys.argv if argv is None else argv
    return argv[argv.index("--") + 1:] if "--" in argv else []


# =========================================================================== stan
FOOT_H = 0.015          # wysokość stopek (regulacja 12–25 mm)
WALL_GAP = 0.003        # szczelina plecy – ściana

S = SimpleNamespace(
    data=None, layout=None, fps=25, root=None, parts={}, part_info={}, drawers={}, doors={}, asm={},
    rest={}, mats={}, colls={}, events=[], props=[], lights={}, cams={}, W=1.9, H=2.018, D=0.4, curves={},
)


def rest_F(ob):
    """Macierz spoczynkowa obiektu w układzie mebla (REGAL) – iloczyn macierzy spoczynkowych w łańcuchu rodziców."""
    M4 = Matrix.Identity(4)
    chain = []
    o = ob
    while o is not None and o is not S.root:
        chain.append(o)
        o = o.parent
    for o in reversed(chain):
        M4 = M4 @ S.rest.get(o.name, o.matrix_basis)
    return M4


S.rest_F = rest_F


# =========================================================================== narzędzia ogólne
def clean_scene(fps=25):
    """Usuwa wszystkie dane sceny (bez resetu preferencji – bezpieczne w GUI)."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves,
                bpy.data.node_groups, bpy.data.actions, bpy.data.worlds, bpy.data.images, bpy.data.textures):
        for d in list(blk):
            try:
                blk.remove(d)
            except Exception:
                pass
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.length_unit = "MILLIMETERS"
    sc.render.fps = fps
    sc.render.fps_base = 1.0
    S.fps = fps
    S.parts, S.part_info, S.drawers, S.doors, S.asm, S.rest = {}, {}, {}, {}, {}, {}
    S.mats, S.colls, S.events, S.props, S.lights, S.cams = {}, {}, [], [], {}, {}
    S.curves = {}
    return sc


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    S.colls[name] = c
    return c


def new_obj(name, data, collection, parent=None, local=None):
    ob = bpy.data.objects.new(name, data)
    collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
        ob.matrix_parent_inverse = Matrix.Identity(4)
    if local is not None:
        ob.matrix_basis = local
    return ob


def empty(name, collection, parent=None, local=None, size=0.05, kind="PLAIN_AXES"):
    ob = new_obj(name, None, collection, parent, local)
    ob.empty_display_type = kind
    ob.empty_display_size = size
    return ob


def look_at(loc, target, up="Y"):
    d = Vector(target) - Vector(loc)
    return d.to_track_quat("-Z", up)


def _mesh_from_bm(name, bm, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


def box_mesh(name, sx, sy, sz, center=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return _mesh_from_bm(name, bm)


def cyl_mesh(name, r, h, segments=48, axis="Z", center=(0, 0, 0), r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r, radius2=r if r2 is None else r2,
                          depth=h)
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    elif axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    me = _mesh_from_bm(name, bm)
    return me


def add_bevel(ob, width, segments=3, angle=35, harden=True):
    mod = ob.modifiers.new("faza", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle)
    mod.profile = 0.5
    try:
        mod.harden_normals = harden
    except Exception:
        pass
    me = ob.data
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return mod


def spin_mesh(name, profile, segments=64, close_top=False):
    """Bryła obrotowa z profilu [(r, z), ...] (r w metrach) wokół osi Z."""
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360),
                   steps=segments, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh_from_bm(name, bm, smooth=True)


# =========================================================================== model
def load_model(path=None):
    p = Path(path) if path else model_json_path()
    S.data = json.loads(p.read_text(encoding="utf-8"))
    lp = PROMO_DIR / "data" / "layout.json"
    S.layout = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else None
    cfg = S.data["cfg"]
    S.W, S.H, S.D = cfg["width"] * MM, cfg["height"] * MM, cfg["depth"] * MM
    S.model_path = str(p)
    return S.data


def part_matrix(p):
    eu, ev, ew, o = (Vector(p[k]) for k in ("eu", "ev", "ew", "origin"))
    return Matrix(((eu.x, ev.x, ew.x, o.x * MM),
                   (eu.y, ev.y, ew.y, o.y * MM),
                   (eu.z, ev.z, ew.z, o.z * MM),
                   (0, 0, 0, 1)))


def _hash01(s):
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def part_mesh(p, grain_local=(1, 0, 0), world_uv_axes=None, uv_offset=(0.0, 0.0)):
    """Siatka elementu: obrys (u, v) wyciągnięty na grubość t wzdłuż lokalnego +Z.
    UV (metry): U = wzdłuż usłojenia, V = w poprzek. `world_uv_axes=(g, c)` – UV z położenia w świecie
    (ciągłe usłojenie przez sąsiednie fronty)."""
    t = p["t"] * MM
    bm = bmesh.new()
    verts = [bm.verts.new((u * MM, v * MM, 0.0)) for u, v in p["outline"]]
    f = bm.faces.new(verts)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    if f.normal.z > 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=(0, 0, t))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uvl = bm.loops.layers.uv.new("UVMap")
    g = Vector(grain_local)
    c = Vector((0, 0, 1)).cross(g)
    Mw = part_matrix(p)
    for face in bm.faces:
        for lp in face.loops:
            co = lp.vert.co
            if world_uv_axes:
                pw = Mw @ co
                lp[uvl].uv = (pw.dot(world_uv_axes[0]) + uv_offset[0], pw.dot(world_uv_axes[1]) + uv_offset[1])
            else:
                lp[uvl].uv = (co.dot(g) + uv_offset[0], co.dot(c) + uv_offset[1])
    return _mesh_from_bm(p["pid"], bm)


def _bbox_world(p):
    Mw = part_matrix(p)
    t = p["t"] * MM
    pts = [Mw @ Vector((u * MM, v * MM, w)) for u, v in p["outline"] for w in (0.0, t)]
    lo = Vector((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
    hi = Vector((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
    return lo, hi


# =========================================================================== mebel
def make_materials():
    m = S.mats
    m["ply"] = M.plywood("Sklejka_brzoza_18_korpus")
    m["front"] = M.plywood("Sklejka_brzoza_18_front", tint=(1.01, 1.0, 0.985), variation=0.35,
                           per_object_pattern=False)
    m["box"] = M.plywood("Sklejka_brzoza_18_szuflada", tint=(1.0, 0.99, 0.97), variation=0.8)
    m["thin"] = M.plywood("Sklejka_brzoza_6.5_BBCP", t_mm=6.5, plies=5, tint=(0.98, 0.96, 0.93), grade="CP")
    m["zinc"] = M.metal("Ocynk_prowadnice", (0.80, 0.82, 0.85), rough=0.34, rough_var=0.02)
    m["nickel"] = M.metal("Nikiel_zawiasy", (0.80, 0.79, 0.76), rough=0.18)
    m["steel_a2"] = M.metal("Stal_A2_wkrety", (0.66, 0.66, 0.67), rough=0.30)
    m["knob"] = M.knob_pla()
    m["plastic_dark"] = M.plastic("Tworzywo_czarne", (0.02, 0.02, 0.022), rough=0.45)
    m["plastic_grey"] = M.plastic("Tworzywo_szare", (0.18, 0.18, 0.19), rough=0.5)
    m["csink"] = M.plastic("Pogłębienie_cien", M.hex_lin("6E5233")[:3], rough=0.7)
    return m


def _axis_abs(v):
    """Wektor osi z dodatnią największą składową (spójne UV dla elementów o przeciwnym zwrocie eu)."""
    v = Vector(v)
    i = max(range(3), key=lambda k: abs(v[k]))
    return v if v[i] >= 0 else -v


def _grain_for(p, front_grain):
    """Zwraca (grain_local, world_uv_axes) dla elementu.
    Fronty: UV w układzie świata (ciągła figura przez wszystkie fronty, jak z jednego arkusza);
    kierunek wg model.json (grain="u" → oś eu, czyli poziomo) albo wymuszony "vertical"."""
    if p["group"] == "front":
        if front_grain == "vertical":
            return None, (Vector((0, 0, 1)), Vector((1, 0, 0)))
        gw = _axis_abs(p["eu"] if p.get("grain", "u") != "v" else p["ev"])
        cw = _axis_abs(p["ev"] if p.get("grain", "u") != "v" else p["eu"])
        return None, (gw, cw)
    gr = p.get("grain")
    if gr == "v":
        return (0, 1, 0), None
    return (1, 0, 0), None


def build_furniture(data=None, bevel_mm=0.7, screws=True, hardware=True, front_grain="model", cups=True):
    """Buduje mebel z model.json. `front_grain`: "model" (domyślnie: jak w model.json i rozkroju – grain="u",
    czyli słoje poziomo) albo "vertical" (wymuszone pionowo). Zwraca S."""
    data = data or S.data or load_model()
    mats = make_materials()
    root_c = coll("REGAL")
    cc = {g: coll(f"regal_{g}", root_c) for g in ("korpus", "front", "szuflada", "plecy", "okucia", "wkrety",
                                                    "rig")}
    cut_c = coll("_wycinaki", root_c)
    cut_c.hide_render = True
    cut_c.hide_viewport = True
    root = empty("REGAL", cc["rig"], local=Matrix.Translation((0, 0, FOOT_H)), size=0.3, kind="ARROWS")
    S.root = root
    parts = {p["pid"]: p for p in data["parts"] if p["group"] in ("korpus", "front", "szuflada", "plecy")}
    S.part_info = parts
    drawer_of = {pid: d["code"] for d in data["drawers"] for pid in d["parts"]}
    door_codes = {d["code"] for d in data["doors"]}

    # --- obiekty elementów (najpierw bez rodziców, w układzie mebla)
    Fm = {}
    for pid, p in parts.items():
        gl, wuv = _grain_for(p, front_grain)
        off = (0.0, 0.0) if wuv else (_hash01(pid) * 2.3, _hash01(pid + "v") * 1.1)
        me = part_mesh(p, gl or (1, 0, 0), wuv, off)
        if p["group"] == "front":
            mat = mats["front"]
        elif p["t"] < 10:
            mat = mats["thin"]
        elif p["group"] == "szuflada":
            mat = mats["box"]
        else:
            mat = mats["ply"]
        me.materials.append(mat)
        ob = bpy.data.objects.new(pid, me)
        cc[p["group"]].objects.link(ob)
        ob["pid"] = pid
        ob["nazwa"] = p["name"]
        ob["grupa"] = p["group"]
        S.parts[pid] = ob
        Fm[pid] = part_matrix(p)
        if cups and p["group"] == "front":
            for h in p["holes"]:
                if h["kind"] != "cup":
                    continue
                dep = (h["depth"] + 1.0) * MM
                cme = cyl_mesh(f"puszka_{pid}", h["d"] / 2 * MM, dep, 48)
                cut = new_obj(f"cut_{pid}_{int(h['v'])}", cme, cut_c, ob,
                              Matrix.Translation((h["u"] * MM, h["v"] * MM, p["t"] * MM - dep / 2 + 0.5 * MM)))
                cut.hide_render = True
                mod = ob.modifiers.new("puszka", "BOOLEAN")
                mod.object = cut
                mod.operation = "DIFFERENCE"
                try:
                    mod.solver = "EXACT"
                except Exception:
                    pass
        bw = (0.45 if p["t"] < 10 else bevel_mm) * MM
        if bevel_mm > 0:
            add_bevel(ob, bw)

    def attach(child, parent, childF, parentF):
        child.parent = parent
        child.matrix_parent_inverse = Matrix.Identity(4)
        child.matrix_basis = parentF.inverted() @ childF
        S.rest[child.name] = child.matrix_basis.copy()

    ident = Matrix.Identity(4)

    # --- jednostki montażu: półki, przegrody, plecy
    for pid, p in parts.items():
        if pid in drawer_of or pid in door_codes:
            continue
        lo, hi = _bbox_world(p)
        cF = Matrix.Translation((lo + hi) / 2)
        a = empty(f"ASM_{pid}", cc["rig"], root, cF, 0.03)
        a.rotation_mode = "QUATERNION"
        S.rest[a.name] = cF.copy()
        S.asm[pid] = a
        attach(S.parts[pid], a, Fm[pid], cF)

    # --- szuflady
    t = data["cfg"]["t"] * MM
    for d in data["drawers"]:
        code = d["code"]
        fx, fz, fw, fh = (v * MM for v in d["front"])
        bx, by, bz, Wb, Lb, Hb = (v * MM for v in d["box"])
        cF = Matrix.Translation((fx + fw / 2, (by + Lb / 2) / 2, fz + fh / 2))
        a = empty(f"ASM_{code}", cc["rig"], root, cF, 0.03)
        a.rotation_mode = "QUATERNION"
        S.rest[a.name] = cF.copy()
        S.asm[code] = a
        dF = Matrix.Translation((fx + fw / 2, 0.0, fz + fh / 2))
        drw = empty(f"DRW_{code}", cc["rig"], a, None, 0.08, "SINGLE_ARROW")
        attach(drw, a, dF, cF)
        mid = empty(f"DRW_MID_{code}", cc["rig"], a, None, 0.04)
        attach(mid, a, dF, cF)
        for pid in d["parts"]:
            attach(S.parts[pid], drw, Fm[pid], dF)
        S.drawers[code] = SimpleNamespace(code=code, rig=drw, mid=mid, asm=a, travel=d["NL"] * MM, frac=0.0,
                                          rest_y=S.rest[drw.name].translation.y,
                                          rest_mid_y=S.rest[mid.name].translation.y, box=(bx, by, bz, Wb, Lb, Hb),
                                          z_run=d["z_run"] * MM, F=dF, cF=cF, front_pid=d["parts"][0])
        if hardware:
            _build_slides(S.drawers[code], data, cc["okucia"], attach)

    # --- drzwiczki
    for dr in data["doors"]:
        code = dr["code"]
        p = parts[code]
        x_left, z_bot, Wd, Hd = dr["x_left"] * MM, dr["z_bot"] * MM, dr["W"] * MM, dr["H"] * MM
        ax = dr["axis_x"] * MM
        cF = Matrix.Translation((x_left + Wd / 2, 0.009, z_bot + Hd / 2))
        a = empty(f"ASM_{code}", cc["rig"], root, cF, 0.03)
        a.rotation_mode = "QUATERNION"
        S.rest[a.name] = cF.copy()
        S.asm[code] = a
        pF = Matrix.Translation((ax, 0.0, z_bot + Hd / 2))
        piv = empty(f"DOOR_{code}", cc["rig"], a, None, 0.06, "SINGLE_ARROW")
        attach(piv, a, pF, cF)
        attach(S.parts[code], piv, Fm[code], pF)
        sgn = -1.0 if dr["hinge"] == "L" else 1.0
        S.doors[code] = SimpleNamespace(code=code, rig=piv, asm=a, sign=sgn, angle=0.0, hinge=dr["hinge"],
                                        F=pF, cF=cF, axis_x=ax, hinges=[z * MM for z in dr["hinges"]],
                                        x_left=x_left, W=Wd)
        if hardware:
            _build_hinges(S.doors[code], data, cc["okucia"], attach)

    # --- gałki (kuliste, druk 3D) i stopki
    if hardware:
        knob_me = knob_mesh()
        knob_me.materials.append(mats["knob"])
        for h in data["hardware"]:
            if h["type"] == "knob":
                fp = h["front"]
                ob = S.parts.get(fp)
                if ob is None:
                    continue
                kF = Matrix.Translation((h["x"] * MM, 0.0, h["z"] * MM)) @ Matrix.Rotation(math.radians(90), 4, "X")
                k = bpy.data.objects.new(f"galka_{fp}", knob_me)
                cc["okucia"].objects.link(k)
                # rodzic: obiekt frontu (jego macierz w układzie mebla = Fm)
                attach(k, ob, kF, Fm[fp])
                k["typ"] = "galka"
            elif h["type"] == "foot":
                fme = foot_mesh()
                fme.materials.append(mats["plastic_dark"])
                fo = bpy.data.objects.new(f"stopka_{int(h['x'])}_{int(h['y'])}", fme)
                cc["okucia"].objects.link(fo)
                attach(fo, S.parts["P000"], Matrix.Translation((h["x"] * MM, h["y"] * MM, 0.0)), Fm["P000"])
    if screws:
        _build_screws(parts, Fm, cc["wkrety"], attach)
    return S


def knob_mesh(r=0.014, neck_r=0.0075, neck_l=0.006):
    """Gałka kulista Ø28 z szyjką Ø15 × 6 mm; oś lokalna +Z = od frontu na zewnątrz (oś druku 3D)."""
    zc = neck_l + r * 0.92
    prof = [(0.0, 0.0), (neck_r + 0.0006, 0.0), (neck_r + 0.0003, 0.0004), (neck_r, 0.001), (neck_r, neck_l * 0.6)]
    n = 40
    started = False
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        rr, zz = r * math.cos(a), zc + r * math.sin(a)
        if not started:
            if rr < neck_r:
                continue
            started = True
            prof.append((neck_r * 1.02, zz - 0.0008))
        prof.append((max(rr, 0.0), zz))
    prof[-1] = (0.0, prof[-1][1])
    return spin_mesh("galka_kula", prof, 64)


def foot_mesh():
    prof = [(0.0, -FOOT_H), (0.014, -FOOT_H), (0.015, -FOOT_H + 0.001), (0.015, -FOOT_H + 0.004),
            (0.009, -FOOT_H + 0.005), (0.009, -0.002), (0.016, -0.002), (0.016, 0.0), (0.0, 0.0)]
    return spin_mesh("stopka", prof, 32)


# --------------------------------------------------------------------------- prowadnice Hettich KA 4532
def _profile_mesh(name, pts_xz, y0, y1):
    """Profil 2D (x, z) wyciągnięty wzdłuż Y od y0 do y1."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y0, z)) for x, z in pts_xz]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    top = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=top, vec=(0, y1 - y0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh_from_bm(name, bm)


def _build_slides(dr, data, collection, attach):
    """Trzy człony prowadnicy kulkowej (korpusowy, środkowy, szufladowy) po obu stronach skrzynki.
    Profil uproszczony, ale w prawdziwej skali (wys. 45 mm, gr. 12,7 mm)."""
    bx, by, bz, Wb, Lb, Hb = dr.box
    z = dr.z_run
    L = Lb
    q = MM
    # profile w układzie: x=0 przy przegrodzie, x=12,7 przy skrzynce (strona lewa); z wokół 0
    outer = [(0, -22.5), (9.5, -22.5), (9.5, -18.5), (8.3, -18.5), (8.3, -21.3), (1.2, -21.3), (1.2, 21.3),
             (8.3, 21.3), (8.3, 18.5), (9.5, 18.5), (9.5, 22.5), (0, 22.5)]
    middle = [(2.6, -17.0), (10.6, -17.0), (10.6, -15.8), (3.8, -15.8), (3.8, 15.8), (10.6, 15.8), (10.6, 17.0),
              (2.6, 17.0)]
    inner = [(12.7, -12.5), (5.8, -12.5), (5.8, -11.3), (11.5, -11.3), (11.5, 11.3), (5.8, 11.3), (5.8, 12.5),
             (12.7, 12.5)]
    ss = data["cfg"]["slide_space"] * MM
    allow = 0.2 * MM
    for side in ("L", "R"):
        if side == "L":
            x_div = bx - allow - ss
            tf = lambda pts: [(x_div + px * q, z + pz * q) for px, pz in pts]  # noqa: E731
        else:
            x_div = bx + Wb + allow + ss
            tf = lambda pts: [(x_div - px * q, z + pz * q) for px, pz in pts]  # noqa: E731

        def mk(nm, pts, y0, y1, mat):
            pts2 = tf(pts)
            if side == "R":
                pts2 = list(reversed(pts2))
            me = _profile_mesh(nm, pts2, y0, y1)
            me.materials.append(mat)
            ob = bpy.data.objects.new(nm, me)
            collection.objects.link(ob)
            return ob

        o = mk(f"prowadnica_{dr.code}_{side}_korpus", outer, by, by + L, S.mats["zinc"])
        attach(o, dr.asm, Matrix.Identity(4), dr.cF)
        mi = mk(f"prowadnica_{dr.code}_{side}_srodek", middle, by + 6 * q, by + L - 4 * q, S.mats["zinc"])
        attach(mi, dr.mid, Matrix.Identity(4), dr.F)
        inn = mk(f"prowadnica_{dr.code}_{side}_szuflada", inner, by, by + L - 12 * q, S.mats["zinc"])
        attach(inn, dr.rig, Matrix.Identity(4), dr.F)
        # czarna dźwignia odczepiania z przodu członu szufladowego + tłumik Silent System z tyłu (szary)
        sx = 1 if side == "L" else -1
        xl = x_div + sx * 9.0 * q
        lev = bpy.data.objects.new(f"prowadnica_{dr.code}_{side}_dzwignia",
                                   box_mesh("dzwignia", 5.0 * q, 22 * q, 9 * q, (xl, by + 20 * q, z)))
        lev.data.materials.append(S.mats["plastic_dark"])
        collection.objects.link(lev)
        attach(lev, dr.rig, Matrix.Identity(4), dr.F)
        damp = bpy.data.objects.new(f"prowadnica_{dr.code}_{side}_tlumik",
                                    box_mesh("tlumik", 6.0 * q, 70 * q, 14 * q,
                                             (x_div + sx * 4.6 * q, by + L - 40 * q, z)))
        damp.data.materials.append(S.mats["plastic_grey"])
        collection.objects.link(damp)
        attach(damp, dr.asm, Matrix.Identity(4), dr.cF)


# --------------------------------------------------------------------------- zawiasy Blum CLIP top
def _build_hinges(door, data, collection, attach):
    """Puszka Ø35 w drzwiach + korpus zawiasu (ruchome), prowadnik + ramię na przegrodzie (stałe).
    Uproszczenie: oś obrotu na przedniej krawędzi przegrody (jak w model.json: axis_x, axis_y=0)."""
    q = MM
    s = 1.0 if door.hinge == "L" else -1.0       # kierunek "w głąb komórki" od osi
    ax = door.axis_x
    for i, zc in enumerate(door.hinges):
        # puszka (widoczna od wewnątrz drzwi) – pierścień niklowany
        cx = ax + s * (2.0 + 5.0 + 17.5) * q
        cup = bpy.data.objects.new(f"zawias_{door.code}_{i}_puszka",
                                   cyl_mesh("puszka", 17.8 * q, 1.2 * q, 48, "Y", (cx, 18.6 * q, zc)))
        cup.data.materials.append(S.mats["nickel"])
        collection.objects.link(cup)
        attach(cup, door.rig, Matrix.Identity(4), door.F)
        body = bpy.data.objects.new(f"zawias_{door.code}_{i}_korpus",
                                    box_mesh("zawias_korpus", 20 * q, 6 * q, 20 * q,
                                             (ax + s * 18 * q, 22.0 * q, zc)))
        body.data.materials.append(S.mats["nickel"])
        collection.objects.link(body)
        attach(body, door.rig, Matrix.Identity(4), door.F)
        # prowadnik krzyżakowy na przegrodzie + ramię
        plate = bpy.data.objects.new(f"zawias_{door.code}_{i}_prowadnik",
                                     box_mesh("prowadnik", 9 * q, 50 * q, 42 * q, (ax + s * 4.5 * q, 56.5 * q, zc)))
        plate.data.materials.append(S.mats["nickel"])
        collection.objects.link(plate)
        attach(plate, door.asm, Matrix.Identity(4), door.cF)
        arm = bpy.data.objects.new(f"zawias_{door.code}_{i}_ramie",
                                   box_mesh("ramie", 10 * q, 62 * q, 16 * q, (ax + s * 14.0 * q, 63 * q, zc)))
        arm.data.materials.append(S.mats["nickel"])
        collection.objects.link(arm)
        attach(arm, door.asm, Matrix.Identity(4), door.cF)
        # łącznik przegubu: od końca ramienia (stały) do korpusu w drzwiach (ruchomy) – STRETCH_TO
        p_arm = Vector((ax + s * 14.0 * q, 32.0 * q, zc))
        p_door = Vector((ax + s * 9.0 * q, 22.0 * q, zc))
        d0 = (p_door - p_arm).length
        tgt = empty(f"zawias_{door.code}_{i}_cel", collection, size=0.005)
        attach(tgt, door.rig, Matrix.Translation(p_door), door.F)
        lme = box_mesh("lacznik", 8 * q, d0, 12 * q, (0, d0 / 2, 0))
        lme.materials.append(S.mats["nickel"])
        link = bpy.data.objects.new(f"zawias_{door.code}_{i}_lacznik", lme)
        collection.objects.link(link)
        rot = (p_door - p_arm).to_track_quat("Y", "Z").to_matrix().to_4x4()
        attach(link, door.asm, Matrix.Translation(p_arm) @ rot, door.cF)
        con = link.constraints.new("STRETCH_TO")
        con.target = tgt
        con.rest_length = d0
        con.volume = "NO_VOLUME"
        con.keep_axis = "PLANE_Z"


# --------------------------------------------------------------------------- wkręty (łby widoczne)
def screw_head_mesh():
    """Łeb stożkowy Ø8 (SPAX A2, T20) zlicowany w pogłębieniu Ø9: lokalne +Z = na zewnątrz, z=0 = lico.
    Pierścień cienia pogłębienia (Ø9→Ø8), dysk łba, gniazdo T20 (gwiazda, ciemne)."""
    q = MM
    bm = bmesh.new()
    r1 = bmesh.ops.create_circle(bm, cap_ends=False, segments=40, radius=4.5 * q)["verts"]
    r2 = bmesh.ops.create_circle(bm, cap_ends=False, segments=40, radius=4.0 * q)["verts"]
    bmesh.ops.translate(bm, vec=(0, 0, 0.02 * q), verts=r1 + r2)
    res = bmesh.ops.bridge_loops(bm, edges=list(bm.edges))
    for f in res["faces"]:
        f.material_index = 0
    disc = bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=3.98 * q)
    bmesh.ops.translate(bm, vec=(0, 0, 0.035 * q), verts=disc["verts"])
    for f in {f for v in disc["verts"] for f in v.link_faces}:
        f.material_index = 1
    star = []
    for i in range(12):
        a = math.pi * 2 * i / 12
        rr = 1.95 * q if i % 2 == 0 else 1.35 * q
        star.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), 0.055 * q)))
    sf = bm.faces.new(star)
    sf.material_index = 2
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    me = _mesh_from_bm("leb_wkretu", bm)
    me.materials.append(S.mats["csink"])
    me.materials.append(S.mats["steel_a2"])
    me.materials.append(S.mats["plastic_dark"])
    return me


def _build_screws(parts, Fm, collection, attach):
    q = MM
    me = screw_head_mesh()
    shelves, dividers = [], []
    for pid, p in parts.items():
        k = p["meta"].get("kind")
        if k in ("shelf", "divider"):
            lo, hi = _bbox_world(p)
            (shelves if k == "shelf" else dividers).append((pid, lo, hi))
    ys = [0.040, 0.200, 0.360]
    n = 0

    def put(pid_host, loc, normal):
        nonlocal n
        rot = Vector((0, 0, 1)).rotation_difference(Vector(normal)).to_matrix().to_4x4()
        F = Matrix.Translation(loc) @ rot
        ob = bpy.data.objects.new(f"wkret_{pid_host}_{n:03d}", me)
        collection.objects.link(ob)
        attach(ob, S.parts[pid_host], F, Fm[pid_host])
        n += 1

    eps = 0.0006
    for dpid, dlo, dhi in dividers:
        xc = (dlo.x + dhi.x) / 2
        for spid, slo, shi in shelves:
            if not (slo.x < xc < shi.x):
                continue
            if abs(shi.z - dlo.z) < eps:       # przegroda stoi na półce → łby od spodu półki
                for y in ys:
                    put(spid, (xc, y, slo.z), (0, 0, -1))
            elif abs(slo.z - dhi.z) < eps:     # półka leży na przegrodzie → łby na wierzchu
                for y in ys:
                    put(spid, (xc, y, shi.z), (0, 0, 1))
    for spid, slo, shi in shelves:
        zc = (slo.z + shi.z) / 2
        for dpid, dlo, dhi in dividers:
            if not (dlo.z < zc < dhi.z):
                continue
            if abs(shi.x - dlo.x) < eps:       # półka kończy się na lewym licu przegrody → łby na prawym licu
                for y in ys:
                    put(dpid, (dhi.x, y, zc), (1, 0, 0))
            elif abs(slo.x - dhi.x) < eps:
                for y in ys:
                    put(dpid, (dlo.x, y, zc), (-1, 0, 0))
    S.n_screws = n
    return n


# =========================================================================== zdarzenia (dla dźwięku)
def log_event(etype, frame, target="", **meta):
    ev = dict(type=etype, frame=int(round(frame)), frame_exact=round(float(frame), 3),
              time_s=round((frame - bpy.context.scene.frame_start) / S.fps, 3), target=target)
    if meta:
        ev["meta"] = meta
    S.events.append(ev)
    return ev


def clear_events():
    S.events = []


def export_events(path=None, extra=None):
    """Zapisuje oś zdarzeń do JSON (posortowane po klatce). Domyślnie PROMO_DIR/renders/events.json."""
    sc = bpy.context.scene
    path = Path(path) if path else RENDERS_DIR / "events.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    out = dict(fps=S.fps, frame_start=sc.frame_start, frame_end=sc.frame_end,
               events=sorted(S.events, key=lambda e: (e["frame_exact"], e["type"])),
               curves=getattr(S, "curves", {}))
    if extra:
        out.update(extra)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    sc["events_json"] = json.dumps(out["events"])
    return path


# =========================================================================== krzywe ruchu
def hermite(u, m0=0.0, m1=0.0):
    """Krzywa 0→1 z zadanymi nachyleniami na początku/końcu (znormalizowanymi)."""
    u2, u3 = u * u, u * u * u
    return (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) + (u3 - u2) * m1


def ease_in_out_sine(u):
    return 0.5 - 0.5 * math.cos(math.pi * u)


def ease_out_cubic(u):
    return 1 - (1 - u) ** 3


def ease_out_quint(u):
    return 1 - (1 - u) ** 5


EASINGS = dict(linear=lambda u: u, sine=ease_in_out_sine, out_cubic=ease_out_cubic, out_quint=ease_out_quint,
               smooth=lambda u: hermite(u))


def fcurves_of(idb):
    """Wszystkie F-krzywe datablocku (obiekt, światło, kamera, scena, drzewo węzłów) – akcje warstwowe 4.4+/5.x
    i starsze `action.fcurves`."""
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action:
        return []
    act = ad.action
    out = []
    for layer in getattr(act, "layers", []):
        for st in layer.strips:
            for cb in getattr(st, "channelbags", []):
                out.extend(cb.fcurves)
    if not out and hasattr(act, "fcurves"):
        try:
            out = list(act.fcurves)
        except Exception:
            pass
    return out


def set_interp(idb, interp="LINEAR", f0=None, f1=None, path=None):
    """Ustawia interpolację kluczy w zakresie klatek [f0, f1] (opcjonalnie tylko kanał kończący się na `path`).
    Potrzebne, bo keyframe_insert w bpy nie zawsze respektuje preferencję interpolacji nowych kluczy."""
    for fc in fcurves_of(idb):
        if path and not fc.data_path.endswith(path):
            continue
        for k in fc.keyframe_points:
            x = k.co.x
            if (f0 is None or x >= f0 - 1e-4) and (f1 is None or x <= f1 + 1e-4):
                k.interpolation = interp
        fc.update()


class _LinearKeys:
    """Kontekst: nowe klucze z interpolacją LINEAR (gęste klucze co klatkę = dokładna krzywa)."""

    def __enter__(self):
        e = bpy.context.preferences.edit
        self.old = e.keyframe_new_interpolation_type
        e.keyframe_new_interpolation_type = "LINEAR"

    def __exit__(self, *a):
        bpy.context.preferences.edit.keyframe_new_interpolation_type = self.old


def _key_samples(samples, setter, keyer, idbs=(), interp="LINEAR"):
    """samples: [(frame, value)], setter(value) ustawia stan, keyer(frame) wstawia klucz;
    `idbs` – datablocki, którym ustawiamy interpolację wstawionych kluczy (domyślnie LINEAR)."""
    with _LinearKeys():
        for f, v in samples:
            setter(v)
            keyer(f)
    if samples:
        for idb in idbs:
            set_interp(idb, interp, samples[0][0], samples[-1][0])


def _sample(f0, dur_frames, fn):
    n = max(1, int(round(dur_frames)))
    return [(f0 + i, fn(i / n)) for i in range(n + 1)]


# =========================================================================== szuflady
def set_drawer(code, frac):
    """Ustawia wysuw szuflady: frac 0 = zamknięta, 1 = pełny wysuw (350 mm). Człon środkowy – połowa."""
    d = S.drawers[code]
    d.frac = frac
    d.rig.location.y = d.rest_y - frac * d.travel
    d.mid.location.y = d.rest_mid_y - frac * d.travel * 0.5


def key_drawer(code, frame):
    d = S.drawers[code]
    d.rig.keyframe_insert("location", index=1, frame=frame)
    d.mid.keyframe_insert("location", index=1, frame=frame)


def animate_drawer_open(code, f0, dur_s=0.9, frac_to=1.0, frac_from=0.0, events=True):
    """Otwarcie (pociągnięcie za gałkę): łagodny start, wyhamowanie na ogranicznik pełnego wysuwu."""
    n = dur_s * S.fps
    fn = lambda u: frac_from + (frac_to - frac_from) * hermite(u, 0.0, 0.35)  # noqa: E731
    d = S.drawers[code]
    _key_samples(_sample(f0, n, fn), lambda v: set_drawer(code, v), lambda f: key_drawer(code, f), (d.rig, d.mid))
    if events:
        log_event("drawer_open_start", f0, code, travel_mm=round((frac_to - frac_from) * d.travel * 1000))
        log_event("drawer_open_end", f0 + n, code, full_extension=frac_to >= 0.999)
    return f0 + n


def animate_drawer_close(code, f0, push_s=0.55, softclose_mm=12.0, softclose_s=0.42, frac_from=None,
                         events=True):
    """Zamknięcie z cichym domykiem: szybkie pchnięcie (z prędkością resztkową) do punktu zaczepu
    tłumika (`softclose_mm` przed końcem), potem tłumik wyhamowuje i dociąga ostatnie mm w `softclose_s`."""
    d = S.drawers[code]
    frac_from = d.frac if frac_from is None else frac_from
    x0 = frac_from * d.travel
    xe = min(softclose_mm * MM, x0)
    nA = max(1.0, push_s * S.fps)
    nB = softclose_s * S.fps
    m1 = 0.9  # nachylenie na końcu pchnięcia (prędkość resztkowa)
    vA_end = (x0 - xe) * m1 / push_s if x0 > xe else 0.0      # m/s
    samples = _sample(f0, nA, lambda u: (x0 - (x0 - xe) * hermite(u, 0.0, m1)) / d.travel)
    # faza tłumika: zaczep "łapie" szufladę – prędkość spada skokowo do ~35 % (słychać/widać miękki docisk)
    m0 = min(1.6, 0.35 * vA_end * softclose_s / xe) if xe > 0 else 0.0
    sB = _sample(f0 + nA, nB, lambda u: (xe - xe * hermite(u, m0, 0.0)) / d.travel)
    _key_samples(samples + sB[1:], lambda v: set_drawer(code, v), lambda f: key_drawer(code, f), (d.rig, d.mid))
    if events:
        log_event("drawer_close_start", f0, code)
        log_event("drawer_softclose_engage", f0 + nA, code, remaining_mm=softclose_mm,
                  speed_mm_s=round(vA_end * 1000))
        log_event("drawer_closed", f0 + nA + nB, code)
    return f0 + nA + nB


def key_drawer_curve(code, samples, log_curve=True):
    """Dowolna krzywa wysuwu: samples = [(klatka, wysuw_mm)] (wysuw ≥ 0 = na zewnątrz, w stronę −Y).
    Klucze LINEAR co klatkę. Krzywą (pozycja + prędkość mm/kl.) zapisuje do S.curves dla dźwięku."""
    d = S.drawers[code]
    _key_samples([(f, v / 1000.0 / d.travel) for f, v in samples], lambda v: set_drawer(code, v),
                 lambda f: key_drawer(code, f), (d.rig, d.mid))
    if log_curve:
        _log_curve(code, "drawer_mm", samples)


def _log_curve(target, kind, samples):
    cur = S.__dict__.setdefault("curves", {}).setdefault(target, dict(kind=kind, frames=[], value=[], speed=[]))
    for i, (f, v) in enumerate(samples):
        sp = 0.0 if i == 0 else v - samples[i - 1][1]
        cur["frames"].append(round(float(f), 3))
        cur["value"].append(round(float(v), 3))
        cur["speed"].append(round(float(sp), 3))


def hermite_samples(f0, f1, p0, p1, v0=0.0, v1=0.0):
    """Próbki Hermite co klatkę: p0→p1, prędkości v0/v1 w jednostkach/klatkę (jak w research-brief 5.3)."""
    n = f1 - f0
    out = []
    for i in range(int(round(n)) + 1):
        u = i / n
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        out.append((f0 + i, h00 * p0 + h10 * v0 * n + h01 * p1 + h11 * v1 * n))
    return out


# =========================================================================== drzwiczki
def set_door(code, angle_deg):
    """Kąt otwarcia drzwiczek w stopniach (0 = zamknięte; Blum CLIP top 110° → max ~105–110)."""
    d = S.doors[code]
    d.angle = angle_deg
    d.rig.rotation_euler = (0.0, 0.0, d.sign * math.radians(angle_deg))


def key_door(code, frame):
    S.doors[code].rig.keyframe_insert("rotation_euler", index=2, frame=frame)


def animate_door_open(code, f0, dur_s=1.0, angle_to=105.0, angle_from=0.0, events=True):
    n = dur_s * S.fps
    fn = lambda u: angle_from + (angle_to - angle_from) * hermite(u, 0.0, 0.25)  # noqa: E731
    _key_samples(_sample(f0, n, fn), lambda v: set_door(code, v), lambda f: key_door(code, f), (S.doors[code].rig,))
    if events:
        log_event("door_open_start", f0, code)
        log_event("door_open_end", f0 + n, code, angle_deg=angle_to)
    return f0 + n


def animate_door_close(code, f0, push_s=0.6, softclose_deg=8.0, softclose_s=0.45, angle_from=None,
                       events=True):
    """Zamknięcie z BLUMOTION: szybki ruch do ~`softclose_deg`, potem tłumik domyka ostatnie stopnie."""
    d = S.doors[code]
    a0 = d.angle if angle_from is None else angle_from
    ae = min(softclose_deg, a0)
    nA = max(1.0, push_s * S.fps)
    nB = softclose_s * S.fps
    m1 = 0.85
    vA = (a0 - ae) * m1 / push_s if a0 > ae else 0.0
    sA = _sample(f0, nA, lambda u: a0 - (a0 - ae) * hermite(u, 0.0, m1))
    m0 = min(1.6, 0.35 * vA * softclose_s / ae) if ae > 0 else 0.0
    sB = _sample(f0 + nA, nB, lambda u: ae - ae * hermite(u, m0, 0.0))
    _key_samples(sA + sB[1:], lambda v: set_door(code, v), lambda f: key_door(code, f), (d.rig,))
    if events:
        log_event("door_close_start", f0, code)
        log_event("door_softclose_engage", f0 + nA, code, remaining_deg=softclose_deg)
        log_event("door_close_click", f0 + nA + nB, code)
    return f0 + nA + nB


def key_door_curve(code, samples, log_curve=True):
    """Dowolna krzywa kąta drzwiczek: samples = [(klatka, kąt_deg)] (0 = zamknięte, + = otwarcie)."""
    _key_samples(samples, lambda v: set_door(code, v), lambda f: key_door(code, f), (S.doors[code].rig,))
    if log_curve:
        _log_curve(code, "door_deg", samples)


def hold_state(kind, code, frame, value):
    """Stan stały od klatki (klucz CONSTANT): kind = "drawer" (mm) | "door" (deg)."""
    with _ConstKeys():
        if kind == "drawer":
            set_drawer(code, value / 1000.0 / S.drawers[code].travel)
            key_drawer(code, frame)
            for idb in (S.drawers[code].rig, S.drawers[code].mid):
                set_interp(idb, "CONSTANT", frame, frame)
        else:
            set_door(code, value)
            key_door(code, frame)
            set_interp(S.doors[code].rig, "CONSTANT", frame, frame)


# =========================================================================== montaż flat-pack
def assembly_units():
    """Słownik nazwa → empty ASM_* (półki, przegrody, plecy, szuflady w całości, drzwiczki z zawiasami)."""
    return dict(S.asm)


def assembly_default_order():
    """Kolejność jak w instrukcji montażu (model.json → steps): poziomami od dołu, potem plecy, szuflady, drzwi."""
    order, seen = [], set()
    for st in S.data.get("steps", []):
        for pid in [st["shelf"]] + st.get("up", []) + st.get("down", []):
            if pid in S.asm and pid not in seen:
                order.append(pid)
                seen.add(pid)
    rest = sorted(S.asm, key=lambda n: (0 if n in S.part_info and S.part_info[n]["meta"].get("kind") in
                                        ("shelf", "divider") else
                                        1 if n.startswith("P") else 2 if n.startswith("S") else 3, n))
    for n in rest:
        if n not in seen:
            order.append(n)
            seen.add(n)
    return order


def assembly_start(mode="explode", amount=0.6, seed=7, spread_rot_deg=12.0):
    """Macierze startowe (w układzie REGAL) dla każdej jednostki:
      explode – odsunięcie promieniowe od środka mebla + do przodu, lekki losowy obrót,
      lift    – z góry (+Z o `amount`) z lekkim obrotem,
      front   – z przodu (−Y o `amount`), z wysokości podłogi rozłożone,
      flat    – płaskie elementy leżą na podłodze przed regałem w siatce (flat‑pack „rozłożony”)."""
    rnd = random.Random(seed)
    c = Vector((S.W / 2, S.D / 2, S.H / 2))
    starts = {}
    flat_x, flat_y, row_h = -0.3, -0.6, 0.0
    for name, a in S.asm.items():
        rest = S.rest[a.name]
        loc = rest.translation.copy()
        rq = rest.to_quaternion()
        if mode == "explode":
            dvec = (loc - c)
            dvec.y = -0.35 - rnd.random() * 0.5
            dvec.normalize()
            nl = loc + dvec * amount * (0.7 + 0.6 * rnd.random())
            e = [math.radians(rnd.uniform(-spread_rot_deg, spread_rot_deg)) for _ in range(3)]
            nq = Quaternion((1, 0, 0), e[0]) @ Quaternion((0, 1, 0), e[1]) @ Quaternion((0, 0, 1), e[2]) @ rq
        elif mode == "lift":
            nl = loc + Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.1, 0.0), amount * (0.8 + 0.4 * rnd.random())))
            nq = Quaternion((0, 0, 1), math.radians(rnd.uniform(-spread_rot_deg, spread_rot_deg))) @ rq
        elif mode == "front":
            nl = loc + Vector((0, -amount * (0.8 + 0.4 * rnd.random()), 0))
            nq = rq
        elif mode == "flat":
            p = S.part_info.get(name)
            if p is not None:
                lo, hi = _bbox_world(p)
                ext = sorted([hi.x - lo.x, hi.y - lo.y, hi.z - lo.z])
                w, l, th = ext[1], ext[2], ext[0]
            else:
                w, l, th = 0.4, 0.4, 0.3
            if flat_x + l > S.W + 0.6:
                flat_x, flat_y, row_h = -0.3, flat_y - row_h - 0.05, 0.0
            nl = Vector((flat_x + l / 2, flat_y - w / 2, -FOOT_H + th / 2))
            flat_x += l + 0.05
            row_h = max(row_h, w)
            # obrót: najdłuższa oś → X, najkrótsza → Z
            if p is not None:
                Mw = part_matrix(p).to_3x3()
                axes = [(abs(Mw.col[i].x), abs(Mw.col[i].y), abs(Mw.col[i].z)) for i in range(3)]
                tz = Mw.col[2]   # oś grubości elementu
                nq = tz.rotation_difference(Vector((0, 0, 1)))
            else:
                nq = rq
        else:
            raise ValueError(mode)
        starts[name] = Matrix.LocRotScale(nl, nq, Vector((1, 1, 1)))
    S.asm_starts = starts
    return starts


def set_assembly(name, t, start=None):
    """t = 0 → pozycja startowa, 1 → na miejscu."""
    a = S.asm[name]
    rest = S.rest[a.name]
    st = (start or S.asm_starts)[name]
    l0, q0 = st.translation, st.to_quaternion()
    l1, q1 = rest.translation, rest.to_quaternion()
    a.location = l0.lerp(l1, t)
    a.rotation_quaternion = q0.slerp(q1, t)


def key_assembly(name, frame):
    a = S.asm[name]
    a.keyframe_insert("location", frame=frame)
    a.keyframe_insert("rotation_quaternion", frame=frame)


def animate_assembly(order=None, f_start=1, stagger=4.0, dur_s=0.8, starts=None, ease="out_quint",
                     events=True, hold_start=True):
    """Każda jednostka wlatuje z pozycji startowej na miejsce (gęste klucze, krzywa `ease`);
    zdarzenie `part_landing` w klatce lądowania. Zwraca klatkę końca."""
    order = order or assembly_default_order()
    starts = starts or getattr(S, "asm_starts", None) or assembly_start()
    fn = EASINGS[ease] if isinstance(ease, str) else ease
    n = dur_s * S.fps
    end = f_start
    for i, name in enumerate(order):
        f0 = f_start + i * stagger
        if hold_start and f0 > bpy.context.scene.frame_start:
            set_assembly(name, 0.0, starts)
            with _LinearKeys():
                key_assembly(name, bpy.context.scene.frame_start)
        _key_samples(_sample(f0, n, fn), lambda v, nm=name: set_assembly(nm, v, starts),
                     lambda f, nm=name: key_assembly(nm, f), (S.asm[name],))
        if events:
            log_event("part_launch", f0, name)
            log_event("part_landing", f0 + n, name, kind=_unit_kind(name))
        end = max(end, f0 + n)
    return end


def _unit_kind(name):
    if name in S.drawers:
        return "drawer"
    if name in S.doors:
        return "door"
    p = S.part_info.get(name)
    return p["meta"].get("kind") if p else "unit"


def reset_rigs():
    for c in S.drawers:
        set_drawer(c, 0.0)
    for c in S.doors:
        set_door(c, 0.0)
    for name, a in S.asm.items():
        r = S.rest[a.name]
        a.location = r.translation
        a.rotation_quaternion = r.to_quaternion()


def clear_animation():
    for ob in bpy.data.objects:
        if ob.animation_data:
            ob.animation_data_clear()
    for cam in bpy.data.cameras:
        if cam.animation_data:
            cam.animation_data_clear()


# =========================================================================== otoczenie
def build_room(style="scandi", floor="microcement", wall_color="E9E4DB", floor_color="BDB4A8", side_wall=True,
               x_left=-6.0, x_right=3.8):
    """style: "scandi" – otwarty set (research-brief 3.1): ściana tylna z tynku (X −6…3,8 m, Z do 3,6 m),
    ściana boczna z oknem na X = 3,8 m (otwór Y −2,4…−0,4, Z 0,4…3,2 m model, rama grafitowa 60×120 mm,
    1 słupek + 1 ślemię na Z 2,2 m), podłoga mikrocement/dąb (X −6…3,8, Y −10…0,41).
    "studio" – ciemne tło typu cyc do detali. Przełączanie: set_look("window"|"studio")."""
    r = coll("OTOCZENIE")
    if style == "scandi":
        c = coll("otoczenie_scandi", r)
        wall_m = M.plaster("Sciana_tynk", wall_color, bump=0.10)
        fl_m = M.microcement(color=floor_color) if floor == "microcement" else M.oak_floor(color=floor_color)
        S.mats["wall"], S.mats["floor"] = wall_m, fl_m
        yw = S.D + S.data["cfg"]["back_t"] * MM + WALL_GAP
        S.wall_y = yw
        H = 3.6
        xr = x_right + 0.15
        wall = new_obj("sciana", box_mesh("sciana", xr - x_left, 0.12, H, ((x_left + xr) / 2, yw + 0.06, H / 2)), c)
        wall.data.materials.append(wall_m)
        flo = new_obj("podloga", box_mesh("podloga", xr - x_left, 10.5, 0.05, ((x_left + xr) / 2, yw + 0.1 - 5.25,
                                                                               -0.025)), c)
        flo.data.materials.append(fl_m)
        if side_wall:
            _side_wall_window(c, wall_m, x_right, yw, H)
        return c
    c = coll("otoczenie_studio", r)
    m = M.studio_backdrop()
    S.mats["studio_bg"] = m
    bm = bmesh.new()
    prof = []
    R, yb = 0.8, S.D + 0.6
    for i in range(17):
        a = math.pi / 2 * i / 16
        prof.append((yb - R + R * math.sin(a), R - R * math.cos(a)))
    pts = [(-3.0, 0.0)] + prof + [(yb, 4.0)]
    rows = [[bm.verts.new((x, y, z)) for y, z in pts] for x in (-2.5, S.W + 2.5)]
    for i in range(len(pts) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = _mesh_from_bm("studio_cyc", bm, smooth=True)
    me.materials.append(m)
    new_obj("studio_cyc", me, c)
    return c


def _side_wall_window(c, wall_m, xw, yw, H, y0=-9.0, t=0.15):
    """Ściana boczna (lico na X = xw, w stronę −X) z otworem okiennym i ramą (bez szyby)."""
    oy0, oy1 = -2.4, -0.4
    oz0, oz1 = 0.400 + FOOT_H, 3.200 + FOOT_H
    xc = xw + t / 2
    pieces = [((y0 + oy0) / 2, oy0 - y0, H / 2, H),                      # część przed oknem (−Y)
              ((oy1 + yw + 0.12) / 2, yw + 0.12 - oy1, H / 2, H),        # część przy narożniku
              ((oy0 + oy1) / 2, oy1 - oy0, oz0 / 2, oz0),               # podokienna
              ((oy0 + oy1) / 2, oy1 - oy0, (oz1 + H) / 2, H - oz1)]      # nadproże
    for i, (yc, ly, zc, lz) in enumerate(pieces):
        ob = new_obj(f"sciana_boczna_{i}", box_mesh("sciana_boczna", t, ly, lz, (xc, yc, zc)), c)
        ob.data.materials.append(wall_m)
    frame_m = M.plastic("Rama_okna_grafit", M.hex_lin("3A3733")[:3], rough=0.55)
    S.mats["window_frame"] = frame_m
    f, d = 0.060, 0.120
    xf = xw + 0.015 + d / 2
    bars = [((oy0 + oy1) / 2, oy1 - oy0, oz0 + f / 2, f),     # dół
            ((oy0 + oy1) / 2, oy1 - oy0, oz1 - f / 2, f),     # góra
            (oy0 + f / 2, f, (oz0 + oz1) / 2, oz1 - oz0),     # boki
            (oy1 - f / 2, f, (oz0 + oz1) / 2, oz1 - oz0),
            ((oy0 + oy1) / 2, f, (oz0 + oz1) / 2, oz1 - oz0),  # słupek
            ((oy0 + oy1) / 2, oy1 - oy0, 2.200 + FOOT_H, f)]  # ślemię
    for i, (yc, ly, zc, lz) in enumerate(bars):
        ob = new_obj(f"okno_rama_{i}", box_mesh("okno_rama", d, ly, lz, (xf, yc, zc)), c)
        ob.data.materials.append(frame_m)
    S.window = dict(x=xw, y=(oy0, oy1), z=(oz0, oz1))


def set_look(look="window"):
    """Przełącza otoczenie + światła: "window" (wnętrze scandi, światło okna) albo "studio" (ciemne tło, detal)."""
    for name, flag in (("otoczenie_scandi", look == "window"), ("otoczenie_studio", look == "studio"),
                       ("SWIATLA_okno", look == "window"), ("SWIATLA_studio", look == "studio")):
        c = bpy.data.collections.get(name)
        if c:
            c.hide_render = not flag
            c.hide_viewport = not flag
            for lc in bpy.context.view_layer.layer_collection.children:
                _set_exclude(lc, name, not flag)
    w = bpy.data.worlds.get("Swiat_okno" if look == "window" else "Swiat_studio")
    if w:
        bpy.context.scene.world = w
    S.look = look


def _set_exclude(lc, name, val):
    if lc.name == name:
        lc.exclude = val
        return True
    for ch in lc.children:
        if _set_exclude(ch, name, val):
            return True
    return False


# =========================================================================== światło
def area(name, collection, loc, target, size, size_y=None, energy=100.0, kelvin=5200, spread=180.0,
         visible=False, shape="RECTANGLE"):
    L = bpy.data.lights.new(name, "AREA")
    L.shape = shape
    L.size = size
    if size_y is not None:
        L.size_y = size_y
    L.energy = energy
    L.color = M.kelvin_rgb(kelvin)
    try:
        L.spread = math.radians(spread)
    except Exception:
        pass
    ob = new_obj(name, L, collection)
    ob.location = loc
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = look_at(loc, target, "Y")
    ob.visible_camera = visible
    ob.visible_glossy = True
    S.lights[name] = ob
    return ob


def world_simple(name, color, strength, camera_sky=None):
    """Świat: słaby ambient pokoju; `camera_sky` (siła) – jaśniejsze "niebo" widoczne tylko dla kamery
    (przez okno w ścianie bocznej), bez zalewania sceny światłem z otwartego setu."""
    w = bpy.data.worlds.get(name) or bpy.data.worlds.new(name)
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (*color[:3], 1)
    bg.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputWorld")
    if camera_sky:
        sky = nt.nodes.new("ShaderNodeBackground")
        sky.inputs[0].default_value = (*M.kelvin_rgb(7000), 1)
        sky.inputs[1].default_value = camera_sky
        lp = nt.nodes.new("ShaderNodeLightPath")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
        nt.links.new(bg.outputs[0], mx.inputs[1])
        nt.links.new(sky.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], o.inputs[0])
    else:
        nt.links.new(bg.outputs[0], o.inputs[0])
    return w


# Rigi światła wg research-brief.md 4 (kierunek promieni słońca d, temperatury, mnożniki).
# Energie skalibrowane w look-devie (cel: brzoza w słońcu ~0,80–0,85 wyświetlanej, w cieniu 0,45–0,55).
LIGHT_PRESETS = dict(
    poranek=dict(sun_dir=(-0.851, 0.300, -0.431), sun=2.4, sun_k=4600, key=1.0, key_k=5000, fill=1.0, fill_k=5600,
                 ceil=1.0, ceil_k=4300, world=1.0),
    zlota=dict(sun_dir=(-0.901, 0.240, -0.360), sun=2.75, sun_k=3800, key=0.8, key_k=4200, fill=0.7, fill_k=6500,
               ceil=0.8, ceil_k=4000, world=0.7),
)
BASE_ENERGY = dict(key=105.0, fill=16.0, ceil=12.0, world=0.05, sky=1.6)


def light_rig_window(side="right", preset="poranek", gobo=None, world_strength=None):
    """Rig A "Poranek" (domyślnie): okno w prawej ścianie (X = 3,8 m).
      OKNO_sun   – słońce, kąt 1,2°, przez fizyczne okno (rama rzuca cień podziałów); bez ściany bocznej
                   można włączyć maskownicę (gobo=True, cień tylko od słońca przez shadow linking),
      OKNO_key   – AREA 1,8 × 2,4 m w oknie (3,6; −1,25; 1,55) → (1,15; 0,15; 1,05),
      OKNO_fill  – AREA 3 × 2 m z lewej (odbicie od pokoju),  OKNO_sufit – AREA 3,5 × 2,5 m z góry.
    `side="left"` – lustrzane odbicie w X (bez ściany z oknem). Parametry: apply_light_preset()."""
    c = coll("SWIATLA_okno")
    W, H, D = S.W, S.H, S.D
    mir = (lambda x: x) if side == "right" else (lambda x: W - x)  # noqa: E731
    z = FOOT_H
    area("OKNO_key", c, (mir(3.6), -1.25, 1.55 + z), (mir(1.15), 0.15, 1.05 + z), 1.8, 2.4, energy=BASE_ENERGY["key"],
         spread=150)
    area("OKNO_fill", c, (mir(-2.6), -3.2, 1.6 + z), (W / 2, D / 2, H / 2), 3.0, 2.0, energy=BASE_ENERGY["fill"])
    area("OKNO_sufit", c, (0.95, -1.5, 3.0 + z), (0.95, -1.2, 0.0), 3.5, 2.5, energy=BASE_ENERGY["ceil"])
    for n in ("OKNO_key", "OKNO_fill", "OKNO_sufit"):
        S.lights[n].visible_glossy = False if n != "OKNO_key" else True
    Ls = bpy.data.lights.new("OKNO_sun", "SUN")
    Ls.angle = math.radians(1.2)
    so = new_obj("OKNO_sun", Ls, c)
    so.rotation_mode = "QUATERNION"
    S.lights["OKNO_sun"] = so
    S.rig_side = side
    world_simple("Swiat_okno", M.kelvin_rgb(6500), BASE_ENERGY["world"], camera_sky=BASE_ENERGY["sky"])
    bpy.context.scene.world = bpy.data.worlds["Swiat_okno"]
    apply_light_preset(preset)
    if gobo is None:
        gobo = side != "right" or not bpy.data.objects.get("sciana_boczna_0")
    if gobo:
        d = Vector(LIGHT_PRESETS[preset]["sun_dir"])
        if side != "right":
            d.x = -d.x
        g = _window_gobo(c, Vector((W / 2, D / 2, H * 0.48)) - d.normalized() * 2.2, d.normalized())
        _shadow_link_only(so, g, c)
    return c


def _sun_quat(d, side=None):
    d = Vector(d)
    if (side or getattr(S, "rig_side", "right")) != "right":
        d.x = -d.x
    return d.normalized().to_track_quat("-Z", "Y")


def apply_light_preset(name="poranek", frame=None, sun_mult=1.0, azimuth_deg=0.0):
    """Ustawia parametry rigu okna wg LIGHT_PRESETS (poranek / zlota); `frame` → wstawia klucze (CONSTANT
    przełączenie przy cięciu). `azimuth_deg` obraca kierunek słońca wokół Z (powolne pełzanie cieni)."""
    P = LIGHT_PRESETS[name]
    L = S.lights
    sun = L["OKNO_sun"]
    sun.data.energy = P["sun"] * sun_mult
    sun.data.color = M.kelvin_rgb(P["sun_k"])
    sun.rotation_quaternion = Quaternion((0, 0, 1), math.radians(azimuth_deg)) @ _sun_quat(P["sun_dir"])
    for key, n in (("key", "OKNO_key"), ("fill", "OKNO_fill"), ("ceil", "OKNO_sufit")):
        L[n].data.energy = BASE_ENERGY[key] * P[key]
        L[n].data.color = M.kelvin_rgb(P[key + "_k"])
    w = bpy.data.worlds.get("Swiat_okno")
    bg = w.node_tree.nodes.get("Background") if w else None
    if bg:
        bg.inputs[1].default_value = BASE_ENERGY["world"] * P["world"]
    if frame is not None:
        with _ConstKeys():
            sun.data.keyframe_insert("energy", frame=frame)
            sun.data.keyframe_insert("color", frame=frame)
            sun.keyframe_insert("rotation_quaternion", frame=frame)
            for n in ("OKNO_key", "OKNO_fill", "OKNO_sufit"):
                L[n].data.keyframe_insert("energy", frame=frame)
                L[n].data.keyframe_insert("color", frame=frame)
            if bg:
                bg.inputs[1].keyframe_insert("default_value", frame=frame)
        for idb in [sun, sun.data] + [L[n].data for n in ("OKNO_key", "OKNO_fill", "OKNO_sufit")] + \
                ([w.node_tree] if w else []):
            set_interp(idb, "CONSTANT", frame, frame)
    S.light_preset = name


class _ConstKeys(object):
    def __enter__(self):
        e = bpy.context.preferences.edit
        self.old = e.keyframe_new_interpolation_type
        e.keyframe_new_interpolation_type = "CONSTANT"

    def __exit__(self, *a):
        bpy.context.preferences.edit.keyframe_new_interpolation_type = self.old


def _window_gobo(collection, center, sun_dir, w=2.6, h=2.4, mullion=0.07, panes=(2, 3)):
    """Płaska rama okna z podziałami (otwory = szyby) prostopadła do kierunku słońca."""
    bm = bmesh.new()
    # pełna płyta z otworami: budujemy z prostokątów (ramka + szprosy)
    bars = []
    nx, nz = panes
    big = 3.0
    # obramowanie (duże pasy dookoła – blokują resztę słońca)
    bars.append((-w / 2 - big, -h / 2 - big, -w / 2, h / 2 + big))
    bars.append((w / 2, -h / 2 - big, w / 2 + big, h / 2 + big))
    bars.append((-w / 2, -h / 2 - big, w / 2, -h / 2))
    bars.append((-w / 2, h / 2, w / 2, h / 2 + big))
    for i in range(1, nx):
        x = -w / 2 + w * i / nx
        bars.append((x - mullion / 2, -h / 2, x + mullion / 2, h / 2))
    for j in range(1, nz):
        z = -h / 2 + h * j / nz
        bars.append((-w / 2, z - mullion / 3, w / 2, z + mullion / 3))
    for x0, z0, x1, z1 in bars:
        vs = [bm.verts.new((x0, z0, 0)), bm.verts.new((x1, z0, 0)), bm.verts.new((x1, z1, 0)),
              bm.verts.new((x0, z1, 0))]
        bm.faces.new(vs)
    me = _mesh_from_bm("okno_maskownica", bm)
    ob = new_obj("okno_maskownica", me, collection)
    ob.location = center
    ob.rotation_mode = "QUATERNION"
    # płaszczyzna XY obiektu prostopadła do słońca, oś lokalna Y ~ pionowo
    q = sun_dir.to_track_quat("Z", "Y")
    ob.rotation_quaternion = q @ Quaternion((0, 0, 1), math.radians(4))
    ob.visible_camera = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    ob.visible_transmission = False
    ob.visible_volume_scatter = False
    ob.visible_shadow = True
    return ob


def _shadow_link_only(light_ob, blocker, collection):
    """Maskownica blokuje tylko słońce (shadow linking Cycles 4.0+). Pozostałe światła ją ignorują."""
    try:
        for name, lo in S.lights.items():
            if lo is light_ob:
                continue
            ex = bpy.data.collections.new(f"_bez_maskownicy_{name}")
            ex.objects.link(blocker)
            lo.light_linking.blocker_collection = ex
            for item in ex.collection_objects:
                item.light_linking.link_state = "EXCLUDE"
        S.gobo = blocker
    except Exception as e:  # starszy Blender – maskownica blokuje wszystkie światła
        print("[build_scene] shadow linking niedostępny:", e)


def light_rig_studio(key=1.0, kelvin=4800, rim=1.0):
    """Wariant "studio detal": ciemne tło, miękki strip‑light z góry‑lewej, kontra z tyłu‑prawej, delikatne
    wypełnienie. Kolekcja SWIATLA_studio, świat Swiat_studio (prawie czarny)."""
    c = coll("SWIATLA_studio")
    W, H, D = S.W, S.H, S.D
    area("STUDIO_key", c, (-0.6, -1.3, 1.9), (0.5, 0.1, 0.9), 0.5, 2.0, energy=380.0 * key, kelvin=kelvin,
         spread=90)
    area("STUDIO_rim", c, (W + 0.5, 0.9, 1.8), (W / 2, 0.0, 0.9), 0.4, 1.8, energy=240.0 * rim, kelvin=5600,
         spread=70)
    area("STUDIO_fill", c, (W / 2 + 0.8, -2.5, 1.0), (W / 2, 0.2, 0.9), 2.0, 1.2, energy=45.0, kelvin=4500)
    world_simple("Swiat_studio", (0.02, 0.019, 0.018), 0.15)
    return c


# =========================================================================== rekwizyty
def build_props(seed=3, enabled=True):
    """Kuratorska, oszczędna stylizacja kilku otwartych wnęk (książki, kamionka, gałązka oliwki)."""
    if not enabled:
        return None
    try:
        import props as P  # noqa
    except Exception:
        sys.path.insert(0, str(SCENE_DIR))
        import props as P  # noqa
    return P.build(S, seed=seed)


# =========================================================================== kamera
def make_camera(name, loc, target, lens=50.0, fstop=None, focus=None, sensor=36.0, shift=(0.0, 0.0),
                clip=(0.01, 60.0), blades=7):
    """Kamera z celem (empty TGT_<name>, constraint Track To) i punktem ostrości (empty FOC_<name>).
    `focus`: punkt (x,y,z) / nazwa obiektu / None (= cel). `fstop`=None → bez DOF."""
    c = coll("KAMERY")
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = sensor
    cam.sensor_fit = "HORIZONTAL"
    cam.clip_start, cam.clip_end = clip
    cam.shift_x, cam.shift_y = shift
    ob = new_obj(name, cam, c)
    ob.location = loc
    tgt = empty(f"TGT_{name}", c, local=Matrix.Translation(target), size=0.05, kind="SPHERE")
    tc = ob.constraints.new("TRACK_TO")
    tc.target = tgt
    tc.track_axis = "TRACK_NEGATIVE_Z"
    tc.up_axis = "UP_Y"
    foc = empty(f"FOC_{name}", c, size=0.03, kind="CUBE")
    if focus is None:
        foc.location = target
    elif isinstance(focus, str):
        foc.location = bpy.data.objects[focus].matrix_world.translation
    else:
        foc.location = focus
    cam.dof.focus_object = foc
    cam.dof.use_dof = fstop is not None
    if fstop is not None:
        cam.dof.aperture_fstop = fstop
        cam.dof.aperture_blades = blades
        cam.dof.aperture_rotation = math.radians(12)
    S.cams[name] = ob
    return ob


def animate_camera(cam, keys, interpolation="BEZIER"):
    """keys: lista dict(frame, loc=(...), target=(...), focus=(...), lens=mm, fstop=f).
    Klucze Bezier z automatycznymi uchwytami (płynny ruch). Dla ruchu po ścieżce – camera_path()."""
    tgt = bpy.data.objects[f"TGT_{cam.name}"]
    foc = bpy.data.objects[f"FOC_{cam.name}"]
    e = bpy.context.preferences.edit
    old = e.keyframe_new_interpolation_type
    e.keyframe_new_interpolation_type = interpolation
    try:
        for k in keys:
            f = k["frame"]
            if "loc" in k:
                cam.location = k["loc"]
                cam.keyframe_insert("location", frame=f)
            if "target" in k:
                tgt.location = k["target"]
                tgt.keyframe_insert("location", frame=f)
            if "focus" in k:
                foc.location = k["focus"]
                foc.keyframe_insert("location", frame=f)
            if "lens" in k:
                cam.data.lens = k["lens"]
                cam.data.keyframe_insert("lens", frame=f)
            if "fstop" in k:
                cam.data.dof.aperture_fstop = k["fstop"]
                cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
            for idb in (cam, tgt, foc, cam.data):
                set_interp(idb, interpolation, f, f)
    finally:
        e.keyframe_new_interpolation_type = old


def camera_path(cam, points, f0, f1, ease="sine"):
    """Ruch kamery po krzywej (NURBS/Bezier przez punkty) – stała orientacja na cel TGT_.
    Prędkość z krzywą `ease` (gęste klucze offset_factor)."""
    c = coll("KAMERY")
    cu = bpy.data.curves.new(f"PATH_{cam.name}", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(points))
    path = new_obj(f"PATH_{cam.name}", cu, c)
    cam.location = (0, 0, 0)
    fp = cam.constraints.new("FOLLOW_PATH")
    fp.target = path
    fp.use_fixed_location = True
    # Track To musi być po Follow Path
    cons = cam.constraints
    try:
        cons.move(len(cons) - 1, 0)
    except Exception:
        pass
    fn = EASINGS[ease]
    _key_samples(_sample(f0, f1 - f0, fn), lambda v: setattr(fp, "offset_factor", v),
                 lambda f: fp.keyframe_insert("offset_factor", frame=f), (cam,))
    return path


# =========================================================================== render
def setup_device(device=None):
    """CPU (domyślnie) lub GPU: METAL (Mac), OPTIX/CUDA (NVIDIA), HIP (AMD), ONEAPI (Intel).
    Kolejność: argument → --device z linii poleceń → RENDER_DEVICE → CPU."""
    args = script_args()
    if device is None and "--device" in args:
        device = args[args.index("--device") + 1]
    device = (device or os.environ.get("RENDER_DEVICE", "CPU")).upper()
    sc = bpy.context.scene
    if device == "CPU":
        sc.cycles.device = "CPU"
        return "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = device
        prefs.get_devices()
        n = 0
        for d in prefs.devices:
            d.use = d.type != "CPU"
            n += d.use
        sc.cycles.device = "GPU" if n else "CPU"
        return f"{device} ({n} urz.)" if n else "CPU (brak GPU)"
    except Exception as e:
        print("[build_scene] GPU niedostępne:", e)
        sc.cycles.device = "CPU"
        return "CPU"


# Transformacja widoku. Pomiar w look-devie: AgX (też z lookiem Medium High Contrast) odsyca albedo brzozy
# #E0C59A do ~#C7BAA6 (szarawy "jesion/płyta"), Khronos PBR Neutral oddaje je wiernie (~#DDC49E) i łagodnie
# kompresuje światła → domyślnie PBR Neutral + balans bieli 5300 K. Nadpisanie: REGAL_VIEW="AgX" / view=...
VIEW_TRANSFORM = "Khronos PBR Neutral"
WHITE_BALANCE_K = 5300

PRESETS = dict(
    # samples, adaptive threshold, min samples, bounces (total, diffuse, glossy, transmission), clamp ind.
    preview=dict(samples=24, thr=0.05, min=0, b=(6, 3, 2, 4), clamp=8.0, quality="BALANCED"),
    draft=dict(samples=48, thr=0.03, min=0, b=(8, 3, 3, 6), clamp=10.0, quality="HIGH"),
    final=dict(samples=96, thr=0.015, min=16, b=(10, 4, 4, 8), clamp=10.0, quality="HIGH"),
    hero=dict(samples=256, thr=0.008, min=32, b=(12, 5, 5, 8), clamp=12.0, quality="HIGH"),
)


def render_settings(preset="final", res=(1920, 1080), engine="CYCLES", samples=None, threshold=None,
                    denoise=True, persistent=True, motion_blur=False, shutter=0.5, look="AgX - Medium High Contrast",
                    exposure=0.0, device=None, percentage=100, time_limit=0.0, light_tree=False, white_balance="auto",
                    view=None):  # white_balance=None → bez balansu bieli
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = percentage
    sc.render.film_transparent = False
    sc.render.use_persistent_data = persistent
    sc.render.use_motion_blur = motion_blur
    sc.render.motion_blur_shutter = shutter
    vs = sc.view_settings
    view = view or os.environ.get("REGAL_VIEW", VIEW_TRANSFORM)
    vs.view_transform = view
    try:
        vs.look = look if view == "AgX" else "None"
        want = vs.look
    except TypeError:
        want = "None"
        vs.look = want
    vs.exposure = exposure
    vs.gamma = 1.0
    # balans bieli "aparatu" (Blender 4.3+): światła 4600–5000 K bez niego przesuwały brzozę w łososiowy róż
    if white_balance == "auto":
        white_balance = WHITE_BALANCE_K if view == "Khronos PBR Neutral" else None
    if hasattr(vs, "use_white_balance"):
        vs.use_white_balance = white_balance is not None
        if white_balance:
            vs.white_balance_temperature = white_balance
            vs.white_balance_tint = 0.0
    sc.display_settings.display_device = "sRGB"
    out = {"engine": engine, "view": view, "look": want}
    if engine == "CYCLES":
        P = PRESETS[preset]
        cy = sc.cycles
        out["device"] = setup_device(device)
        cy.samples = samples or P["samples"]
        cy.use_adaptive_sampling = True
        cy.adaptive_threshold = threshold or P["thr"]
        cy.adaptive_min_samples = P["min"]
        cy.time_limit = time_limit
        cy.use_denoising = denoise
        if denoise:
            cy.denoiser = "OPENIMAGEDENOISE"
            cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
            cy.denoising_prefilter = "ACCURATE"
            try:
                cy.denoising_quality = P["quality"]
            except Exception:
                pass
            try:
                cy.denoising_use_gpu = sc.cycles.device == "GPU"
            except Exception:
                pass
        tot, dif, glo, tra = P["b"]
        cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = tot, dif, glo, tra
        cy.volume_bounces = 0
        cy.transparent_max_bounces = 8
        cy.sample_clamp_direct = 0.0
        cy.sample_clamp_indirect = P["clamp"]
        cy.blur_glossy = 0.5
        cy.caustics_reflective = False
        cy.caustics_refractive = False
        try:
            cy.use_light_tree = light_tree     # przy kilku światłach drzewo światła kosztuje ~17 % (pomiar)
        except Exception:
            pass
        sc.render.film_transparent = False
        out.update(samples=cy.samples, threshold=cy.adaptive_threshold)
    elif engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        ee = sc.eevee
        ee.taa_render_samples = samples or 64
        for attr, val in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2),
                          ("shadow_step_count", 8), ("use_fast_gi", False)):
            if hasattr(ee, attr):
                setattr(ee, attr, val)
        out.update(samples=ee.taa_render_samples)
    return out


def render_still(path, camera=None, frame=None):
    sc = bpy.context.scene
    if camera is not None:
        sc.camera = camera if not isinstance(camera, str) else bpy.data.objects[camera]
    if frame is not None:
        sc.frame_set(int(frame))
    sc.render.filepath = str(path)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.color_mode = "RGB"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    return path


def render_animation(out_dir, camera=None, f0=None, f1=None, fmt="PNG"):
    """Sekwencja klatek do out_dir (domyślnie PROMO_DIR/frames/<nazwa>/). Wznawialne: pomija istniejące."""
    sc = bpy.context.scene
    if camera is not None:
        sc.camera = camera if not isinstance(camera, str) else bpy.data.objects[camera]
    if f0 is not None:
        sc.frame_start = f0
    if f1 is not None:
        sc.frame_end = f1
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    sc.render.filepath = str(Path(out_dir) / "f_")
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    sc.render.image_settings.file_format = fmt
    bpy.ops.render.render(animation=True)


def save_blend(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True, relative_remap=True)
    return path


# =========================================================================== wszystko naraz
def build_all(look="window", props=True, screws=True, floor="microcement", front_grain="model", fps=25,
              studio=True, model_path=None, bevel_mm=0.7, side="right", preset="poranek"):
    """Wszystko naraz: mebel + otoczenie (scandi z oknem, opcjonalnie studio) + rekwizyty + światło."""
    clean_scene(fps)
    load_model(model_path)
    build_furniture(screws=screws, front_grain=front_grain, bevel_mm=bevel_mm)
    build_room("scandi", floor=floor, side_wall=(side == "right"))
    light_rig_window(side=side, preset=preset)
    if studio:
        build_room("studio")
        light_rig_studio()
    if props:
        build_props()
    set_look(look)
    reset_rigs()
    bpy.context.scene.frame_set(1)
    return S
