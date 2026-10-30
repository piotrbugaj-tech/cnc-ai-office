"""Benchmark renderu na prawdziwych ujęciach filmu (film.py): czas/klatkę dla kilku ustawień.

Użycie:  python3.13 scene/bench.py -- [--quick] [--device METAL] [--eevee]
Wynik:   PROMO_DIR/renders/bench/bench.json + PNG każdego wariantu (porównanie szumu).

Warianty (Cycles, OIDN albedo+normal, adaptive sampling, light tree, odbicia 4/3/2 jak w briefie 9.1):
  B_S02_1440_s36   – "B" z briefu: S02 f120, 2560×1440, 36 spp, próg 0,035 (zimna klatka: BVH + shadery)
  S02_1440_s36_PD  – ta sama sesja, następna klatka (persistent data – czas "ciepłej" klatki sekwencji)
  S02_1440_s64 / s128 – więcej sampli
  S02_1080_s36     – 1920×1080
  S06_1440_s45     – makro (S06 f382)
  S08_1440_s27_MB  – montaż z motion blur 0,4 (S08 f540)
  eevee            – próba EEVEE (headless bez GPU zwykle niedostępne)
"""
from __future__ import annotations

import json
import os
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

import build_scene as B  # noqa: E402
import film as F  # noqa: E402

args = B.script_args()
device = args[args.index("--device") + 1] if "--device" in args else None
out = B.RENDERS_DIR / "bench"
out.mkdir(parents=True, exist_ok=True)

t0 = time.time()
cams = F.build_film()
t_build = time.time() - t0
sc = bpy.context.scene
results = []


ONLY = args[args.index("--only") + 1].split(",") if "--only" in args else None
JSON = out / (args[args.index("--json") + 1] if "--json" in args else "bench.json")


def run(name, sid, frame, res, spp, thr, mb=False, persistent=True):
    if ONLY and name not in ONLY:
        return
    F.set_shot_render(sid, "final", res, spp, device, thr=thr)
    sc.render.use_persistent_data = persistent
    sc.render.use_motion_blur = mb
    sc.render.motion_blur_shutter = 0.4
    sc.render.image_settings.color_depth = "8"
    sc.frame_set(frame)
    p = out / f"bench_{name}.png"
    sc.render.filepath = str(p)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    r = dict(name=name, shot=sid, frame=frame, res=list(res), spp=spp, threshold=thr, motion_blur=mb,
             persistent=persistent, seconds=round(dt, 1))
    print("[bench]", r, flush=True)
    results.append(r)
    JSON.write_text(json.dumps(dict(build_s=round(t_build, 1), cpu_threads=os.cpu_count(),
                                    blender=bpy.app.version_string, results=results), indent=1))


R1440, R1080 = (2560, 1440), (1920, 1080)
run("B_S02_1440_s36", "S02", 120, R1440, 36, 0.035)
run("S02_1440_s1", "S02", 121, R1440, 1, 0.5)            # stały narzut (synchronizacja, OIDN, zapis)
if "--quick" not in args:
    if "--full" in args:
        run("S02_1440_s64", "S02", 122, R1440, 64, 0.02)
        run("S02_1440_s128", "S02", 123, R1440, 128, 0.01)
    run("S02_1080_s36", "S02", 124, R1080, 36, 0.035)
    run("S06_1440_s45", "S06", 382, R1440, 45, 0.03)
    run("S08_1440_s27_MB", "S08", 540, R1440, 27, 0.05, mb=True)
if "--eevee" in args:   # headless bez GPU/EGL kończy proces (brak libEGL) – tylko na żądanie
    try:
        B.render_settings(engine="BLENDER_EEVEE", res=(640, 360), samples=16)
        sc.render.filepath = str(out / "bench_eevee.png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        results.append(dict(name="eevee_640x360_s16", seconds=round(time.time() - t, 1)))
    except Exception as e:
        results.append(dict(name="eevee", error=str(e)[:300]))
    (out / "bench.json").write_text(json.dumps(dict(build_s=round(t_build, 1), cpu_threads=os.cpu_count(),
                                                    blender=bpy.app.version_string, results=results), indent=1))
print("[bench] zapisano", out / "bench.json")
