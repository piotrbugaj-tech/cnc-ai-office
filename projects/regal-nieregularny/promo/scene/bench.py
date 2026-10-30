"""Benchmark renderu: czas/klatkę dla kilku ustawień (Cycles CPU/GPU, opcjonalnie EEVEE).

Użycie:
  python3 scene/bench.py -- [--shot hero] [--res 1920x1080] [--quick] [--eevee] [--device METAL]
Wynik: PROMO_DIR/renders/bench/bench.json + PNG każdego wariantu (do porównania szumu).

Mierzone warianty (Cycles, OIDN z albedo+normal, adaptive sampling):
  s32_t05, s64_t03, s128_t015, s64_t03_lowbounce (mniej odbić), s64_t03_noPD (bez persistent data),
  oraz 2. klatka animacji (ruch szuflady) z persistent data – czas "ciepłej" klatki sekwencji.
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

import build_scene as B  # noqa: E402

args = B.script_args()


def arg(name, default=None, cast=str):
    return cast(args[args.index(name) + 1]) if name in args else default


res = tuple(int(v) for v in arg("--res", "1920x1080").split("x"))
out = Path(arg("--out", str(B.RENDERS_DIR / "bench")))
out.mkdir(parents=True, exist_ok=True)

t0 = time.time()
B.build_all(look="window")
t_build = time.time() - t0
W = B.S.W
cam = B.make_camera("CAM_bench", (-1.05, -3.95, 1.02), (W * 0.56, 0.2, 1.02), lens=35, fstop=5.6,
                    focus=(W * 0.35, 0.0, 1.1), shift=(0.0, 0.035))
bpy.context.scene.camera = cam
# krótka animacja szuflady do testu klatek sekwencji
B.animate_drawer_open("S06", 2, dur_s=0.6)

variants = [
    ("s32_t05", dict(preset="draft", samples=32, threshold=0.05)),
    ("s64_t03", dict(preset="draft", samples=64, threshold=0.03)),
    ("s128_t015", dict(preset="final", samples=128, threshold=0.015)),
    ("s64_t03_lowbounce", dict(preset="preview", samples=64, threshold=0.03)),
]
if "--quick" in args:
    variants = variants[:2]
results = []


def run(name, kw, frame=1, persistent=True):
    info = B.render_settings(res=res, persistent=persistent, **kw)
    bpy.context.scene.frame_set(frame)
    p = out / f"bench_{name}.png"
    t = time.time()
    B.render_still(p, cam)
    dt = time.time() - t
    r = dict(name=name, seconds=round(dt, 1), frame=frame, persistent=persistent, res=res, **info)
    print("[bench]", r)
    results.append(r)
    return dt


for name, kw in variants:
    run(name, kw)
# persistent data: kolejne klatki tej samej sesji (BVH/shadery już zbudowane)
run("s64_t03_PD_frame2", dict(preset="draft", samples=64, threshold=0.03), frame=8, persistent=True)
run("s64_t03_PD_frame3", dict(preset="draft", samples=64, threshold=0.03), frame=12, persistent=True)
run("s64_t03_noPD_frame4", dict(preset="draft", samples=64, threshold=0.03), frame=14, persistent=False)

if "--eevee" in args:
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            if eng not in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]:
                continue
            info = B.render_settings(engine=eng, res=res, samples=64)
            t = time.time()
            B.render_still(out / "bench_eevee.png", cam)
            results.append(dict(name="eevee", engine=eng, seconds=round(time.time() - t, 1)))
        except Exception as e:  # brak GPU/kontekstu GL
            results.append(dict(name="eevee", engine=eng, error=str(e)[:300]))
        break

(out / "bench.json").write_text(json.dumps(dict(build_s=round(t_build, 1), cpu_threads=os.cpu_count(),
                                                blender=bpy.app.version_string, results=results), indent=1))
print("[bench] zapisano", out / "bench.json")
