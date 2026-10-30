"""Look-dev: 3 klatki referencyjne (hero 3/4, makro krawędzi i szczeliny 2 mm, szuflada wysunięta).

Użycie:
  python3 scene/lookdev.py -- --shot all
  blender -b -P scene/lookdev.py -- --shot hero --preset final --device METAL
Opcje:
  --shot hero|macro|drawer|all   (domyślnie all)
  --preset preview|draft|final|hero   --samples N   --res 1920x1080   --pct 50 (procent rozdzielczości)
  --look window|studio  (wymusza plan dla wszystkich ujęć; domyślnie: hero/drawer = window, macro = window)
  --side left|right     (strona okna)   --floor microcement|oak   --no-props   --no-sun
  --out DIR (domyślnie PROMO_DIR/renders/lookdev)   --suffix TXT   --blend (zapis .blend sceny)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_here = Path(__file__).resolve().parent if "__file__" in globals() else Path(os.getcwd())
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_scene as B  # noqa: E402


def arg(args, name, default=None, cast=str):
    if name in args:
        return cast(args[args.index(name) + 1])
    return default


# --------------------------------------------------------------------------- ujęcia
def shot_hero():
    """3/4 całego regału, poziom kamery ~1,05 m, pionowe linie zachowane (shift zamiast pochylenia)."""
    W, H = B.S.W, B.S.H
    cz = 1.02
    cam = B.make_camera("CAM_hero", (-1.45, -4.6, cz), (W * 0.47, 0.2, cz), lens=40, fstop=5.6,
                        focus=(W * 0.35, 0.0, 1.1), shift=(0.0, 0.035))
    return cam, {}


def shot_macro():
    """Makro: narożnik frontu szuflady S09 pod półką P090 – szczelina 2 mm + krawędź sklejki półki i przegrody.
    Płytka GO (f/2.8 przy 100 mm)."""
    # S09: front x 611..1189, z 720..898; półka P090 z 900..918; przegroda D060-070 x 591..609 (lewa)
    fx, fz = 0.611, 0.898
    tgt = (fx + 0.004, 0.0, fz + 0.002)
    cam = B.make_camera("CAM_macro", (fx - 0.085, -0.33, fz + 0.095), tgt, lens=100, fstop=4.0,
                        focus=(fx + 0.003, -0.001, fz + 0.003))
    # "kicker" – wąski softbox z góry-lewej, muska krawędzie pod kątem (wydobywa fazę i warstwy)
    k = B.area("MACRO_kicker", B.coll("SWIATLA_okno"), (fx - 0.30, -0.22, fz + 0.32), (fx + 0.02, 0.0, fz),
               0.12, 0.5, energy=5.0, kelvin=5200, spread=60)
    return cam, {"kicker": k.name}


def shot_drawer():
    """Szuflada S06 (578 mm, z 320–598) w pełnym wysuwie: widać prowadnicę KA 4532 i wnętrze skrzynki."""
    d = B.S.drawers["S06"]
    B.set_drawer("S06", 1.0)
    bx, by, bz, Wb, Lb, Hb = d.box
    # kamera z przodu‑lewej, z góry; cel: lewy bok skrzynki w połowie wysuwu
    tgt = (bx + 0.10, -0.20, bz + 0.12)
    cam = B.make_camera("CAM_drawer", (bx - 0.62, -1.05, bz + 0.72), tgt, lens=45, fstop=4.0,
                        focus=(bx - 0.006, -0.17, B.S.drawers["S06"].z_run))
    return cam, {"drawer": "S06"}


SHOTS = dict(hero=("a_hero_34", shot_hero, "window"), macro=("b_makro_krawedz_szczelina", shot_macro, "window"),
             drawer=("c_szuflada_wysuw", shot_drawer, "window"))


def main():
    args = B.script_args()
    shot = arg(args, "--shot", "all")
    preset = arg(args, "--preset", "final")
    samples = arg(args, "--samples", None, int)
    res = tuple(int(v) for v in arg(args, "--res", "1920x1080").split("x"))
    pct = arg(args, "--pct", 100, int)
    look_force = arg(args, "--look", None)
    side = arg(args, "--side", "left")
    floor = arg(args, "--floor", "microcement")
    out = Path(arg(args, "--out", str(B.RENDERS_DIR / "lookdev")))
    suffix = arg(args, "--suffix", "")
    thr = arg(args, "--thr", None, float)

    t0 = time.time()
    B.clean_scene(25)
    B.load_model()
    B.build_furniture(screws="--no-screws" not in args)
    B.build_room("scandi", floor=floor)
    B.light_rig_window(sun="--no-sun" not in args, side=side,
                       key=arg(args, "--key", 1.0, float), sun_strength=arg(args, "--sunk", 1.8, float))
    B.build_room("studio")
    B.light_rig_studio()
    if "--no-props" not in args:
        B.build_props()
    t_build = time.time() - t0
    print(f"[lookdev] scena zbudowana w {t_build:.1f} s; elementów {len(B.S.parts)}, wkrętów "
          f"{getattr(B.S, 'n_screws', 0)}, rekwizytów {len(B.S.props)}")
    names = list(SHOTS) if shot == "all" else shot.split(",")
    report = []
    for nm in names:
        fname, fn, look = SHOTS[nm]
        B.reset_rigs()
        cam, meta = fn()
        B.set_look(look_force or look)
        info = B.render_settings(preset, res=res, samples=samples, percentage=pct, threshold=thr,
                                 exposure=arg(args, "--exp", 0.0, float))
        bpy.context.scene.frame_set(1)
        path = out / f"{fname}{suffix}.png"
        t1 = time.time()
        B.render_still(path, cam)
        dt = time.time() - t1
        print(f"[lookdev] {nm}: {dt:.1f} s → {path}")
        report.append(dict(shot=nm, file=str(path), seconds=round(dt, 1), **info, res=res, pct=pct,
                           plan=look_force or look))
    (out / f"lookdev_times{suffix}.json").write_text(json.dumps(dict(build_s=round(t_build, 1), shots=report),
                                                                 indent=1, ensure_ascii=False))
    if "--blend" in args:
        B.save_blend(B.PROMO_DIR / "scene" / "regal_promo_lookdev.blend")


main()
