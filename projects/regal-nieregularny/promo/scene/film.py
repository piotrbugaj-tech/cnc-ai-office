"""film.py – film "RYTM" (research-brief.md): ujęcia S01–S09 na jednej osi czasu f 0…749 (25 fps).

Użycie (python3.13 lub blender -b -P scene/film.py -- …):
  --build-only                      zbuduj scenę + events.json (bez renderu)
  --blend                           zapisz scenę do PROMO_DIR/frames/rytm_film.blend
  --stills S02:179,S06:382,S03:224  klatki stylu (domyślnie --preset final, --res 1920x1080)
  --animatic                        cały film 640×360, 8 spp, kamery z markerów + nakładka ID/klatka → MP4
  --shot S03 [--preset final] [--res 2560x1440] [--spp N]   render ujęcia (zakładki ±3 kl., S09 +10) do frames/S03
  --device CPU|METAL|OPTIX|CUDA     (lub RENDER_DEVICE)
Układ: pozycje z briefu (mm, model.json) → świat: P(x, y, z) = (x, y, z + 15) / 1000 m (podłoga z = 0).
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

def _scene_dir():
    """Katalog scene/ także przy Run Script w GUI Blendera (__file__ bywa wtedy samą nazwą tekstu)."""
    cands = []
    if "__file__" in globals():
        cands.append(Path(__file__).resolve().parent)
    if os.environ.get("PROMO_DIR"):
        cands.append(Path(os.environ["PROMO_DIR"]).expanduser() / "scene")
    try:
        import bpy as _bpy
        cands += [Path(_bpy.path.abspath(t.filepath)).parent for t in _bpy.data.texts if t.filepath]
    except Exception:
        pass
    cands += [Path(os.getcwd()) / "scene", Path(os.getcwd())]
    return next((c for c in cands if (c / "build_scene.py").exists()), cands[0])


_here = _scene_dir()
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

import build_scene as B  # noqa: E402
import flatpack as FP  # noqa: E402
import materials as M  # noqa: E402

MM = 0.001
FPS = 25


def P(x, y, z):
    """Punkt z briefu (mm, układ model.json, Z = 0 spód P000) → świat (m, podłoga z = 0)."""
    return Vector((x * MM, y * MM, (z + 15.0) * MM))


SHOTS = {
    # f = [start, koniec) ; spp/thr – budżet z briefu (9.2) dla 2560×1440
    "S01": dict(f=(0, 60), lens=50, fstop=4.0, ev=-0.3, spp=45, thr=0.03, name="RYTM"),
    "S02": dict(f=(60, 180), lens=35, fstop=5.6, ev=0.0, spp=36, thr=0.035, name="Bez boków"),
    "S03": dict(f=(180, 225), lens=60, fstop=4.0, ev=-0.5, spp=36, thr=0.035, name="Pełny wysuw"),   # brief +0,1
    "S04": dict(f=(225, 300), lens=50, fstop=5.6, ev=0.0, spp=27, thr=0.04, name="Cichy domyk",
                holds=[(225, 249), (286, 299)]),
    "S05": dict(f=(300, 345), lens=50, fstop=4.0, ev=0.0, spp=36, thr=0.035, name="Domyka się sam"),
    "S06": dict(f=(345, 420), lens=100, fstop=5.6, ev=-0.8, spp=45, thr=0.03, name="2 mm"),   # brief: +0,2 (look-dev: −0,8)
    "S07": dict(f=(420, 480), lens=35, fstop=8.0, ev=0.1, spp=27, thr=0.05, name="140 elementów"),
    "S08": dict(f=(480, 600), lens=35, fstop=8.0, ev=0.0, spp=27, thr=0.05, name="Z płaskiego", mb=0.4),
    "S09": dict(f=(600, 660), lens=50, fstop=5.6, ev=-0.1, spp=36, thr=0.035, name="Hero", tail=10),
}
OVERLAP = 3
EV_OFFSET = -0.3   # globalna korekta ekspozycji pod Khronos PBR Neutral (brief liczył EV pod AgX)
F_SHEETS, F_ASSEMBLED, F_HERO = 420, 600, 600


# =========================================================================== pomocnicze
def cam(name, C, T, lens, fstop, focus=None, topdown=False):
    sid = name
    c = B.make_camera(f"CAM_{sid}", C, T, lens=lens, fstop=fstop, focus=focus if focus is not None else T)
    c.data.sensor_width = 36.0
    c.data.clip_end = 30.0
    if topdown:
        c.constraints.remove(c.constraints[0])
        c.rotation_mode = "XYZ"
        c.rotation_euler = (0.0, 0.0, 0.0)
    return c


def key_cam(c, frame, loc=None, tgt=None, foc=None, interp="LINEAR"):
    keys = dict(frame=frame)
    if loc is not None:
        keys["loc"] = tuple(loc)
    if tgt is not None:
        keys["target"] = tuple(tgt)
    if foc is not None:
        keys["focus"] = tuple(foc)
    B.animate_camera(c, [keys], interpolation=interp)


def energy_window(light_ob, f0, f1, energy):
    """Światło pomocnicze włączone tylko w zakresie [f0, f1] (klucze CONSTANT)."""
    with B._ConstKeys():
        L = light_ob.data
        L.energy = 0.0
        L.keyframe_insert("energy", frame=-10)
        L.energy = energy
        L.keyframe_insert("energy", frame=f0)
        L.energy = 0.0
        L.keyframe_insert("energy", frame=f1 + 1)
    B.set_interp(light_ob.data, "CONSTANT")


def aux_light(name, C, T, size, energy, kelvin, f0, f1, size_y=None):
    lo = B.area(name, B.coll("SWIATLA_okno"), C, T, size, size_y, energy=energy, kelvin=kelvin, spread=120)
    lo.visible_glossy = False
    energy_window(lo, f0, f1, energy)
    return lo


def ev(etype, frame, target="", **meta):
    return B.log_event(etype, frame, target, **meta)


# =========================================================================== ujęcia
def shot_S01():
    s = SHOTS["S01"]
    Zk = lambda f: 9 + 26.667 * f  # noqa: E731
    c = cam("S01", P(-520, -300, Zk(0)), P(0, 120, Zk(0)), s["lens"], s["fstop"], focus=P(0, 100, Zk(0)))
    for f in (-OVERLAP, 60 + OVERLAP):
        key_cam(c, f, P(-520, -300, Zk(f)), P(0, 120, Zk(f)), P(0, 100, Zk(f)), interp="LINEAR")
    k = aux_light("S01_kicker", P(-1100, -500, Zk(0)), P(0, 150, Zk(0)), 0.6, 15.0, 4500, -OVERLAP, 60 + OVERLAP)
    for f in (-OVERLAP, 60 + OVERLAP):
        k.location = P(-1100, -500, Zk(f))
        k.keyframe_insert("location", frame=f)
    B.set_interp(k, "LINEAR", path="location")
    notes = [("P000", 0, "F3"), ("P030", 11.25, "A3"), ("P060", 22.5, "C4"), ("P070a", 26.25, "D4"),
             ("P090", 33.75, "F4"), ("P120a", 45, "G4"), ("P140a", 52.5, "A4"), ("P150a", 56.25, "C5")]
    for pid, f, note in notes:
        zc = 9 + 26.667 * f            # czoło półki mija środek kadru – punkt: lewy narożnik czoła (0, 0, Z)
        ev("shelf_pass", f, pid, note=note, shot="S01", pos=[0.0, 0.0, round((zc + 15) / 1000, 4)])
    return c


def shot_S02():
    s = SHOTS["S02"]
    Pc = (950, 200, 1000)
    c = cam("S02", P(-3460, -2556, 1200), P(*Pc), s["lens"], s["fstop"], focus=P(*Pc))
    for f in range(60 - OVERLAP, 180 + OVERLAP):
        u = min(1.0, max(0.0, (f - 60) / 120.0))
        e = B.ease_in_out_sine(u)
        a = math.radians(58 + (34 - 58) * e)
        R = 5200 + (5000 - 5200) * e
        Z = 1200 + (1100 - 1200) * e
        key_cam(c, f, P(950 - R * math.sin(a), 200 - R * math.cos(a), Z), interp="LINEAR")
    # słońce pełznie o −1° azymutu przez całe ujęcie
    sun = B.S.lights["OKNO_sun"]
    for f, az in ((60, 0.0), (179, -1.0)):
        B.apply_light_preset("poranek", azimuth_deg=az)
        with B._LinearKeys():
            sun.keyframe_insert("rotation_quaternion", frame=f)
    B.apply_light_preset("poranek", azimuth_deg=0.0)
    sun.keyframe_insert("rotation_quaternion", frame=180)
    B.set_interp(sun, "LINEAR", 60, 179, path="rotation_quaternion")
    B.set_interp(sun, "CONSTANT", 180, 180, path="rotation_quaternion")
    ev("reveal", 60, "regal", shot="S02", note="sub + pad Fmaj9")
    ev("caption", 96, "Bez boków.", end=176)
    return c


def shot_S03():
    s = SHOTS["S03"]
    c = cam("S03", P(1010, -215, 830), P(900, -15, 809), s["lens"], s["fstop"])
    # f180–188 jak w briefie (makro gałki); od f199 kamera obchodzi front z prawej i w f210–225 staje ZA płaszczyzną
    # wysuniętego frontu – widać bok skrzynki z prowadnicą KA 4532 (zmiana zaakceptowana przez CEO)
    keys = [(180, (1010, -215, 830), (900, -15, 809)), (188, (1015, -225, 832), (900, -15, 809)),
            (199, (1250, -560, 980), (1000, -220, 805)), (210, (1520, -470, 1060), (1110, -170, 800)),
            (225, (1700, -480, 1150), (1080, -150, 800))]
    for f, C, T in keys:
        key_cam(c, f, P(*C), P(*T), interp="BEZIER")
    # ostrość = gałka S09 (empty jedzie z szufladą)
    d = B.S.drawers["S09"]
    foc = bpy.data.objects["FOC_CAM_S03"]
    if foc.animation_data:
        foc.animation_data_clear()
    foc.parent = d.rig
    foc.matrix_parent_inverse = Matrix.Identity(4)
    inv = B.rest_F(d.rig).inverted()
    for f, pF in ((188, (0.900, -0.019, 0.809)), (195, (0.900, -0.019, 0.809)),     # gałka
                  (208, (1.186, 0.150, 0.809))):                                    # prowadnica (bok skrzynki)
        foc.matrix_basis = inv @ Matrix.Translation(pF)
        foc.keyframe_insert("location", frame=f)
    B.set_interp(foc, "BEZIER")
    # S09: Hermite 0 → 352 mm (v1 = 3 mm/kl), uderzenie w ogranicznik f210, odbicie do 350 w f213
    B.hold_state("drawer", "S09", -10, 0.0)
    B.hold_state("drawer", "S09", 187, 0.0)
    sm = B.hermite_samples(188, 210, 0.0, 352.0, 0.0, 3.0)
    sm += [(211, 351.2), (212, 350.4), (213, 350.0)]
    B.key_drawer_curve("S09", sm)
    B.hold_state("drawer", "S09", 214, 350.0)
    B.hold_state("drawer", "S09", 229, 0.0)
    aux_light("S03_blenda", P(1300, -500, 600), P(900, -200, 800), 0.4, 6.0, 5500, 180 - OVERLAP, 225 + OVERLAP)
    ev("drawer_roll", 188, "S09", end=210, direction="open")
    ev("drawer_stop", 210, "S09", note="ogranicznik pełnego wysuwu")
    ev("cloth_rustle", 211, "S09", end=220)
    ev("caption", 196, "Pełny wysuw.", end=224)
    return c


def shot_S04():
    s = SHOTS["S04"]
    c = cam("S04", P(1650, -190, 1900), P(1650, -190, 0), s["lens"], s["fstop"], focus=P(1650, -190, 860),
            topdown=True)
    B.hold_state("drawer", "S10", -10, 0.0)
    B.hold_state("drawer", "S10", 225, 350.0)
    sm = B.hermite_samples(250, 262, 350.0, 40.0, 0.0, -5.2)
    sm += [(262 + i, 40.0 * (1 - i / 23) ** 3) for i in range(1, 24)]
    B.hold_state("drawer", "S10", 249, 350.0)
    B.key_drawer_curve("S10", sm)
    B.hold_state("drawer", "S10", 286, 0.0)
    aux_light("S04_softbox", P(1650, -190, 2600), P(1650, -190, 0), 0.8, 25.0, 5000, 225 - OVERLAP, 300 + OVERLAP)
    ev("drawer_roll", 250, "S10", end=262, direction="close")
    ev("softclose_catch", 262, "S10")
    ev("softclose_contact", 285, "S10")
    ev("caption", 262, "Cichy domyk.", end=296)
    return c


def shot_S05():
    s = SHOTS["S05"]
    c = cam("S05", P(900, -1250, 1150), P(1500, -80, 1060), s["lens"], s["fstop"], focus=P(1450, 0, 1059))
    for f in range(300 - OVERLAP, 345 + OVERLAP + 1):
        u = min(1.0, max(0.0, (f - 300) / 45.0))
        e = B.ease_out_cubic(u)
        C = Vector((900, -1250, 1150)).lerp(Vector((960, -1150, 1130)), e)
        key_cam(c, f, P(*C), interp="LINEAR")
    B.hold_state("door", "DZ02", -10, 0.0)
    sm = B.hermite_samples(300, 318, 80.0, 14.0, -3.6, -3.5)
    sm += [(318 + i, 14.0 * (1 - i / 12) ** 3) for i in range(1, 13)]
    B.hold_state("door", "DZ02", 299, 0.0)
    B.key_door_curve("DZ02", sm)
    B.hold_state("door", "DZ02", 331, 0.0)
    ev("door_swing", 300, "DZ02", end=318, direction="close")
    ev("door_catch", 318, "DZ02")
    ev("door_contact", 330, "DZ02")
    return c


CALLOUTS = {"A_18mm": [(1591, 0, 570), (1609, 0, 570)], "B_2mm": [(1560, 0, 598), (1560, 0, 600)],
            "C_13warstw": [(1650, 0, 609)]}


def shot_S06():
    s = SHOTS["S06"]
    # kadr obniżony o 15 mm względem briefu (górna 1/3 była pustą, ciemną wnęką – uwaga CEO)
    c = cam("S06", P(1540, -430, 595), P(1570, 0, 585), s["lens"], s["fstop"], focus=P(1570, 0, 585))
    for f in range(345 - OVERLAP, 420 + OVERLAP + 1):
        u = min(1.0, max(0.0, (f - 345) / 75.0))
        sm = u * u * (3 - 2 * u)
        key_cam(c, f, P(1540 + 80 * sm, -430, 595), P(1570 + 80 * sm, 0, 585), P(1570 + 80 * sm, 0, 585))
    aux_light("S06_pasek", P(1900, -120, 600), P(1500, -120, 600), 0.1, 4.0, 4500, 345 - OVERLAP, 420 + OVERLAP,
              size_y=0.6)
    for f, nm, note in ((360, "A_18mm", "F6"), (375, "B_2mm", "A6"), (390, "C_13warstw", "C7")):
        ev("callout", f, nm, note=note)
    return c


def shot_S07(layout):
    s = SHOTS["S07"]
    c = cam("S07", P(-200, -3525, 3600), P(-200, -3525, 0), s["lens"], s["fstop"], focus=P(-200, -3525, -15),
            topdown=True)
    for f in range(420 - OVERLAP, 480 + OVERLAP + 1):
        u = min(1.0, max(0.0, (f - 420) / 60.0))
        e = 1 - (1 - u) ** 2
        c.location = P(-200, -3525, 3600 + 5000 * e)
        c.rotation_euler = (0, 0, math.radians(3.0 * e))
        c.keyframe_insert("location", frame=f)
        c.keyframe_insert("rotation_euler", frame=f)
    B.set_interp(c, "LINEAR")
    ev("riser", 420, "", end=474)
    ev("caption", 428, "140 elementów. 8 arkuszy.", end=474)
    ev("silence", 474, "", end=480)
    return c


def shot_S08():
    s = SHOTS["S08"]
    C0, T0 = Vector((1800, -7600, 5200)), Vector((-200, -3300, 0))
    C1, T1 = Vector((3450, -5750, 1250)), Vector((950, 200, 1000))
    c = cam("S08", P(*C0), P(*T0), s["lens"], s["fstop"])
    c.data.dof.focus_object = None
    c.data.dof.focus_distance = 6.2
    bulge = Vector((600, 400, 500))
    for f in range(480 - OVERLAP, 600 + OVERLAP + 1):
        if f <= 585:
            u = min(1.0, max(0.0, (f - 480) / 105.0))
            e = 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
            C = C0.lerp(C1, e) + bulge * math.sin(math.pi * e)
            T = T0.lerp(T1, e)
        else:
            u = min(1.0, (f - 585) / 15.0)
            e = B.ease_in_out_sine(u)
            dirv = (T1 - C1).normalized()
            C = C1 + dirv * 80 * e
            T = T1
        key_cam(c, f, P(*C), P(*T), interp="LINEAR")
    # słońce ×1,15 w f585–600
    sun = B.S.lights["OKNO_sun"]
    e = bpy.context.preferences.edit
    old = e.keyframe_new_interpolation_type
    e.keyframe_new_interpolation_type = "BEZIER"
    base = B.LIGHT_PRESETS["poranek"]["sun"]
    sun.data.energy = base
    sun.data.keyframe_insert("energy", frame=585)
    sun.data.energy = base * 1.15
    sun.data.keyframe_insert("energy", frame=600)
    e.keyframe_new_interpolation_type = old
    return c


def shot_S09():
    s = SHOTS["S09"]
    c = cam("S09", P(950, -6600, 1060), P(950, 0, 1060), s["lens"], s["fstop"], focus=P(950, 0, 1060))
    for f in range(600 - OVERLAP, 660 + 10 + 1):
        u = min(1.0, max(0.0, (f - 600) / 60.0))
        e = math.sin(u * math.pi / 2)
        key_cam(c, f, P(950, -6600 + 350 * e, 1060), interp="LINEAR")
    B.apply_light_preset("zlota", frame=600)
    B.hold_state("drawer", "S03", 599, 0.0)
    sm = B.hermite_samples(600, 612, 220.0, 40.0, -12.0, -6.67)
    sm += [(612 + i, 40.0 * (1 - i / 18) ** 3) for i in range(1, 19)]
    B.key_drawer_curve("S03", sm)
    B.hold_state("drawer", "S03", 631, 0.0)
    ev("drawer_roll", 600, "S03", end=612, direction="close")
    ev("softclose_catch", 612, "S03")
    ev("softclose_contact", 630, "S03", note="logo dźwiękowe cz. 1")
    ev("crossfade", 660, "", end=670)
    ev("sting", 660, "RYTM", notes="F4 f660 · A4 f671.25 · C5 f682.5 · D5 f686.25 · F5 f693.75")
    return c


# =========================================================================== montaż S07/S08
FRONT_SLOTS = [(558.75, ["S01", "S02"], "D4"), (562.5, ["S05", "S07"], "F4"), (566.25, ["S03", "DZ03"], "A4"),
               (570.0, ["S08", "S04", "S09"], "C5"), (573.75, ["S06", "DZ06"], "E5"),
               (577.5, ["DZ01", "DZ05", "S10"], "F5"), (581.25, ["DZ04", "DZ02"], "A5"),
               (585.0, ["DZ08", "DZ07", "DZ09"], "F5+A5+C6")]
STEP_NOTES = ["F3", "A3", "C4", "D4", "D4", "F4", "G4", "G4", "A4", "A4", "C5", "C5", "D5", "F5"]


def assembly(layout):
    S = B.S
    parts = layout["parts"]
    center = P(-200, -3525, 0)
    maxd = max((parts[pid]["M"].translation.xy - center.xy).length for pid in S.parts if pid in parts)
    land, kinds = {}, {}
    # korpus: kroki z model.json → steps
    for k, st in enumerate(S.data["steps"]):
        f_sh = 555.0 if st["shelf"] == "P200" else 502.5 + 3.75 * k
        land[st["shelf"]] = f_sh
        kinds[st["shelf"]] = ("land", STEP_NOTES[k] + (" + sub" if st["shelf"] == "P200" else ""))
        for dpid in st.get("up", []):
            land[dpid] = f_sh + 2
            kinds[dpid] = ("divider_tick", None)
    for pid, p in S.part_info.items():
        if p["group"] == "plecy":
            land[pid] = 551.25
            kinds[pid] = ("back_land", None)
    front_land = {}
    for f, codes, note in FRONT_SLOTS:
        for i, code in enumerate(codes):
            pid = code if code.startswith("DZ") else f"{code}-F"
            land[pid] = f
            front_land[code] = f
            kinds[pid] = ("front_land", note if i == 0 else None)
    for d in S.data["drawers"]:
        fl = front_land[d["code"]]
        for j, pid in enumerate(d["parts"][1:]):
            land[pid] = max(545.0, min(575.0, fl - 10 - (4 - j) * 0.75))
            kinds[pid] = ("box_land", None)
    # klucze
    rnd_bob = {}
    for pid, ob in S.parts.items():
        if pid not in parts or pid not in land:
            continue
        Ms = parts[pid]["M"]
        Mr = FP.part_world_rest(ob)
        dist = (Ms.translation.xy - center.xy).length / maxd
        dl = 4.0 * dist
        fl = int(round(land[pid]))
        fs = fl - 14
        FP.key_part_world(ob, F_SHEETS - 1, Mr, "CONSTANT")
        FP.key_part_world(ob, F_SHEETS, Ms, "CONSTANT")
        # pop f465–471 (+30 mm, ease-out cubic 6 kl., opóźnienie radialne 0–4 kl.)
        p0 = 465 + dl
        FP.key_part_world(ob, int(math.floor(p0)), Ms, "LINEAR")
        for i in range(1, 7):
            f = int(math.floor(p0)) + i
            FP.key_part_world(ob, f, FP.lifted(Ms, 0.030 * B.ease_out_cubic(min(1.0, (f - p0) / 6.0))), "LINEAR")
        Mp = FP.lifted(Ms, 0.030)
        FP.key_part_world(ob, 479, Mp, "LINEAR")
        # lewitacja f480–488 → +300 mm (ease-out quint), potem bujanie ±5 mm 0,8 Hz do startu lotu
        l0 = 480 + dl
        phase = (hash(pid) % 628) / 100.0
        f = 480
        while f < fs:
            if f <= l0 + 8:
                z = 0.030 + 0.270 * B.ease_out_quint(max(0.0, min(1.0, (f - l0) / 8.0)))
            else:
                z = 0.300 + 0.005 * math.sin(2 * math.pi * 0.8 * (f - l0 - 8) / FPS + phase) * \
                    min(1.0, (f - l0 - 8) / 6.0)
            FP.key_part_world(ob, f, FP.lifted(Ms, z), "LINEAR")
            f += 1
        z_start = 0.300 if fs > l0 + 8 else 0.030 + 0.270 * B.ease_out_quint(max(0.0, min(1.0, (fs - l0) / 8.0)))
        M0 = FP.lifted(Ms, z_start)
        kind = kinds[pid][0]
        if kind == "back_land":
            samples = FP.flight_samples(M0, Mr, fs, 14, lift=0.9, lead=(0.0, 0.0, 0.9))
        else:
            samples = FP.flight_samples(M0, Mr, fs, 14, lift=0.9, lead=(0.0, -0.9, 0.0))
        for f, Mw in samples:
            FP.key_part_world(ob, f, Mw, "LINEAR")
        B.set_interp(ob, "LINEAR")
        B.set_interp(ob, "CONSTANT", F_SHEETS - 1, F_SHEETS)
        etype, note = kinds[pid]
        meta = dict(kind=S.part_info[pid]["meta"].get("kind"))
        if note:
            meta["note"] = note
        ev(etype, land[pid], pid, frame_land_rounded=fl, **meta)
        ev("pop", p0, pid, shot="S07")
    ev("levitate", 480, "all", end=488)
    ev("chord", 585, "", note="F5+A5+C6 + F2")
    # okucia: pojawiają się przy lądowaniu (prowadnice z korpusem skrzynki, zawiasy z drzwiami), gałki +2 kl.
    for ob in bpy.data.objects:
        n = ob.name
        if n.startswith("prowadnica_"):
            code = n.split("_")[1]
            fl = int(round(front_land[code] - 12))
        elif n.startswith("zawias_"):
            code = n.split("_")[1]
            fl = int(round(front_land[code] - 1))
        elif n.startswith("galka_"):
            code = n.split("_", 1)[1].replace("-F", "")
            fl = int(round(front_land[code] + 2))
            ev("knob_pop", fl, code)
        else:
            continue
        FP.key_scale_pop(ob, fl, 4, hide_before=F_SHEETS)
    return land


# =========================================================================== widoczność
def visibility(sheet_objs):
    for ob in sheet_objs:
        FP.key_hide(ob, [(-10, True), (F_SHEETS, False), (F_HERO, True)])
    for ob in B.S.props:
        FP.key_hide(ob, [(-10, False), (F_SHEETS, True), (F_HERO, False)])


def exposure_keys():
    sc = bpy.context.scene
    with B._ConstKeys():
        for sid, s in SHOTS.items():
            sc.view_settings.exposure = s["ev"] + EV_OFFSET
            sc.view_settings.keyframe_insert("exposure", frame=s["f"][0] if sid != "S01" else -10)
    B.set_interp(sc, "CONSTANT")


def markers(cams):
    sc = bpy.context.scene
    sc.timeline_markers.clear()
    for sid, c in cams.items():
        m = sc.timeline_markers.new(sid, frame=SHOTS[sid]["f"][0])
        m.camera = c


# =========================================================================== eksport zdarzeń
def shot_of(frame):
    for sid, s in SHOTS.items():
        if s["f"][0] <= frame < s["f"][1]:
            return sid
    return "S09"


def export_events(cams, path=None):
    sc = bpy.context.scene
    # pozycja x w kadrze (do panoramy) dla zdarzeń z celem-obiektem
    for e in sorted(B.S.events, key=lambda e: e["frame"]):
        sid = shot_of(e["frame"])
        e["shot"] = sid
        tgt = e.get("target", "")
        ob = bpy.data.objects.get(tgt) or bpy.data.objects.get(f"{tgt}-F") or \
            (bpy.data.objects.get(f"DRW_{tgt}") if tgt.startswith("S") else None)
        pos = e.get("meta", {}).get("pos")
        if (ob is None and pos is None) or sid not in cams:
            continue
        sc.frame_set(e["frame"])
        if pos is not None:
            wp = Vector(pos)
        elif ob.type == "MESH":
            bb = [Vector(c) for c in ob.bound_box]
            wp = ob.matrix_world @ (sum(bb, Vector()) / 8.0)       # środek bryły (nie origin w narożniku)
        else:
            wp = ob.matrix_world.translation
        co = world_to_camera_view(sc, cams[sid], wp)
        e["x_frame"] = round(co.x, 4)
        e["y_frame"] = round(1 - co.y, 4)
    # napisy CAD S06: pozycje 2D w każdej klatce
    callouts = {}
    for f in range(345, 420):
        sc.frame_set(f)
        for nm, pts in CALLOUTS.items():
            xy = []
            for p in pts:
                co = world_to_camera_view(sc, cams["S06"], P(*p))
                xy.append([round(co.x, 5), round(1 - co.y, 5)])
            callouts.setdefault(nm, []).append(dict(frame=f, pts=xy))
    extra = dict(bpm=100, shots={k: dict(frames=list(v["f"]), name=v["name"]) for k, v in SHOTS.items()},
                 callouts_S06=callouts,
                 note="Klatki globalne 0–749 (t = f/25). x_frame/y_frame: położenie celu w kadrze 0–1 (lewy‑górny róg). "
                      "curves: wysuw szuflad [mm] / kąt drzwi [deg] i prędkość na klatkę.")
    sc.frame_start, sc.frame_end = 0, 749
    return B.export_events(path or (B.RENDERS_DIR / "events.json"), extra=extra)


# =========================================================================== budowa
def build_film(props=True):
    t0 = time.time()
    B.clean_scene(FPS)
    B.load_model()
    B.build_furniture()
    B.build_room("scandi")
    B.light_rig_window(side="right", preset="poranek")
    B.apply_light_preset("poranek", frame=-10)
    if props:
        B.build_props()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 0, 749
    B.render_settings("preview", res=(640, 360))
    cams = {}
    cams["S01"] = shot_S01()
    cams["S02"] = shot_S02()
    cams["S03"] = shot_S03()
    cams["S04"] = shot_S04()
    cams["S05"] = shot_S05()
    cams["S06"] = shot_S06()
    layout = FP.sheet_layout()
    sheet_objs = FP.build_sheets(layout)
    cams["S07"] = shot_S07(layout)
    cams["S08"] = shot_S08()
    assembly(layout)
    cams["S09"] = shot_S09()
    visibility(sheet_objs)
    exposure_keys()
    markers(cams)
    B.S.film_cams = cams
    print(f"[film] scena zbudowana w {time.time() - t0:.1f} s, obiektów {len(bpy.data.objects)}")
    return cams


class no_marker_cams:
    """Na czas renderu jednego ujęcia/klatki odpina kamery od markerów (inaczej Blender przy frame_set i renderze
    przełącza kamerę wg markerów – zakładki ±3 kl. dostałyby kamerę sąsiedniego ujęcia)."""

    def __enter__(self):
        self.saved = [(m, m.camera) for m in bpy.context.scene.timeline_markers]
        for m, _ in self.saved:
            m.camera = None
        return self

    def __exit__(self, *a):
        for m, c in self.saved:
            m.camera = c


def set_shot_render(sid, preset="final", res=(2560, 1440), spp=None, device=None, animatic=False, thr=None):
    s = SHOTS[sid]
    sc = bpy.context.scene
    info = B.render_settings(preset, res=res, samples=spp or s["spp"], threshold=thr or s["thr"], device=device,
                             motion_blur=bool(s.get("mb")) and not animatic, shutter=s.get("mb", 0.5))
    sc.camera = B.S.film_cams[sid]
    # stała ekspozycja ujęcia (klucze ekspozycji służą tylko animatikowi – w renderze ujęcia je zdejmujemy)
    if sc.animation_data:
        sc.animation_data_clear()
    sc.view_settings.exposure = s["ev"] + EV_OFFSET
    cy = sc.cycles
    cy.use_animated_seed = False
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces = 4, 3, 2
    cy.transmission_bounces, cy.transparent_max_bounces = 2, 4
    cy.sample_clamp_indirect = 5.0
    cy.blur_glossy = 1.0
    sc.render.filter_size = 1.5
    sc.render.image_settings.color_depth = "16"
    return info


def render_stills(spec, preset, res, out, spp=None, device=None, thr=None, suffix=""):
    sc = bpy.context.scene
    rep = []
    for item in spec.split(","):
        sid, f = item.split(":")
        f = int(f)
        info = set_shot_render(sid, preset, res, spp, device, thr=thr)
        sc.view_settings.exposure = SHOTS[sid]["ev"] + EV_OFFSET
        path = Path(out) / f"{sid}_f{f:03d}{suffix}.png"
        t = time.time()
        sc.render.filepath = str(path)
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_depth = "8"
        with no_marker_cams():
            sc.frame_set(f)
            sc.camera = B.S.film_cams[sid]
            bpy.ops.render.render(write_still=True)
        dt = time.time() - t
        print(f"[film] {sid} f{f}: {dt:.1f} s → {path}")
        rep.append(dict(shot=sid, frame=f, file=str(path), seconds=round(dt, 1), **info))
    return rep


def render_shot(sid, preset="final", res=(2560, 1440), spp=None, device=None, out_root=None):
    s = SHOTS[sid]
    sc = bpy.context.scene
    set_shot_render(sid, preset, res, spp, device)
    f0 = s["f"][0] - OVERLAP
    f1 = s["f"][1] - 1 + OVERLAP + s.get("tail", 0)
    out = Path(out_root or B.FRAMES_DIR) / sid
    out.mkdir(parents=True, exist_ok=True)
    holds = s.get("holds", [])
    sc.render.image_settings.file_format = "PNG"
    sc.render.use_overwrite = False
    with no_marker_cams():
        _render_range(sid, sc, out, f0, f1, holds)


def _render_range(sid, sc, out, f0, f1, holds):
    for f in range(f0, f1 + 1):
        dst = out / f"f_{f:04d}.png"
        if dst.exists():
            continue
        hold = next(((a, b) for a, b in holds if a <= f <= b), None)
        if hold and f != hold[0]:
            src = out / f"f_{hold[0]:04d}.png"
            if src.exists():
                shutil.copyfile(src, dst)
                continue
        sc.frame_set(f)
        sc.camera = B.S.film_cams[sid]
        sc.render.filepath = str(dst)
        bpy.ops.render.render(write_still=True)


def animatic(out_dir=None, res=(640, 360), spp=6):
    """Cały film w niskiej jakości do sprawdzenia timingu: Cycles, `spp` sampli + OIDN, 2 odbicia, Fast GI,
    kamery z markerów, klatki S04 "trzymane" renderowane raz i kopiowane; wznawialne (pomija istniejące)."""
    sc = bpy.context.scene
    out = Path(out_dir or (B.FRAMES_DIR / "animatic"))
    out.mkdir(parents=True, exist_ok=True)
    B.render_settings("preview", res=res, samples=spp, threshold=0.1)
    cy = sc.cycles
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 2, 1, 1, 1
    try:
        cy.use_fast_gi = True
        cy.fast_gi_method = "REPLACE"
        cy.ao_bounces_render = 1
        sc.world.light_settings.distance = 1.0
    except Exception:
        pass
    cy.use_animated_seed = False
    sc.render.use_motion_blur = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    holds = [h for s in SHOTS.values() for h in s.get("holds", [])]
    t = time.time()
    n = 0
    for f in range(0, 660):
        dst = out / f"f_{f:04d}.png"
        if dst.exists():
            continue
        hold = next(((a, b) for a, b in holds if a <= f <= b), None)
        if hold and f != hold[0] and (out / f"f_{hold[0]:04d}.png").exists():
            shutil.copyfile(out / f"f_{hold[0]:04d}.png", dst)
            continue
        sc.frame_set(f)
        sc.camera = B.S.film_cams[shot_of(f)]
        sc.render.filepath = str(dst)
        bpy.ops.render.render(write_still=True)
        n += 1
        if n % 25 == 0:
            print(f"[film] animatik f{f}: {(time.time() - t) / n:.1f} s/kl.", flush=True)
    print(f"[film] animatik 3D: {time.time() - t:.0f} s, wyrenderowano {n} kl.", flush=True)
    return out


def finish_animatic(frames_dir, mp4=None):
    """Nakładka (ID ujęcia, klatka, timecode) + karta S10 (Pillow, jeśli dostępny) + MP4 (ffmpeg)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("[film] brak Pillow – pomijam nakładkę")
        return None
    frames_dir = Path(frames_dir)
    tmp = frames_dir.parent / "animatic_burn"
    tmp.mkdir(exist_ok=True)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf", 14)
        big = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf", 54)
    except Exception:
        font = big = ImageFont.load_default()
    size = None
    for f in range(0, 750):
        src = frames_dir / f"f_{f:04d}.png"
        if f < 660 and src.exists():
            im = Image.open(src).convert("RGB")
            size = im.size
        else:
            im = Image.new("RGB", size or (640, 360), (0xEF, 0xEA, 0xE2))
            d = ImageDraw.Draw(im)
            d.text((im.size[0] / 2, im.size[1] * 0.55), "RYTM", fill=(0x24, 0x21, 0x1E), font=big, anchor="mm")
        d = ImageDraw.Draw(im)
        sid = shot_of(f) if f < 660 else "S10"
        lab = f"{sid} {SHOTS[sid]['name'] if sid in SHOTS else 'Plansza'}   f{f:03d}   {f / FPS:05.2f}s"
        d.rectangle((0, 0, im.size[0], 20), fill=(0, 0, 0))
        d.text((6, 2), lab, fill=(255, 255, 255), font=font)
        im.save(tmp / f"b_{f:04d}.png")
    mp4 = Path(mp4 or (B.RENDERS_DIR / "animatic" / "RYTM_animatic_640x360.mp4"))
    mp4.parent.mkdir(parents=True, exist_ok=True)
    ff = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "b_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(mp4)],
                   check=True)
    return mp4


def main():
    args = B.script_args()

    def arg(n, d=None, cast=str):
        return cast(args[args.index(n) + 1]) if n in args else d

    cams = build_film(props="--no-props" not in args)
    ep = export_events(cams)
    print("[film] events.json →", ep, "zdarzeń:", len(B.S.events))
    if "--blend" in args:
        B.save_blend(B.FRAMES_DIR / "rytm_film.blend")
    device = arg("--device")
    res = tuple(int(v) for v in arg("--res", "1920x1080").split("x"))
    if "--stills" in args:
        out = Path(arg("--out", str(B.RENDERS_DIR / "lookdev")))
        rep = render_stills(arg("--stills"), arg("--preset", "final"), res, out, arg("--spp", None, int), device,
                            arg("--thr", None, float), arg("--suffix", ""))
        (out / f"stills_times{arg('--suffix', '')}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    if "--shot" in args:
        res = tuple(int(v) for v in arg("--res", "2560x1440").split("x"))
        for sid in arg("--shot").split(","):
            render_shot(sid, arg("--preset", "final"), res, arg("--spp", None, int), device)
    if "--animatic" in args:
        fr = animatic(res=tuple(int(v) for v in arg("--ares", "640x360").split("x")), spp=arg("--aspp", 6, int))
        mp4 = finish_animatic(fr)
        print("[film] animatik →", mp4)


if __name__ == "__main__":
    main()
