"""Szybki test shadera sklejki: zbliżenia krawędzi i lica (bez całego oświetlenia sceny).
python3.13 scene/shader_test.py -- --suffix _a"""
import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import build_scene as B

args = B.script_args()
suf = args[args.index("--suffix") + 1] if "--suffix" in args else ""
B.clean_scene()
B.load_model()
B.build_furniture(screws=True)
B.build_room("scandi")
B.light_rig_window()
out = B.RENDERS_DIR / "lookdev" / "tmp"
# 1) krawędź półki P090 + przegrody, 100 mm z 0,16 m (pole ~55 mm)
c1 = B.make_camera("T_edge", (0.585, -0.16, 0.93), (0.605, 0.0, 0.905), lens=100, fstop=None)
# 2) lico frontu S09 + gałka (pole ~ 0,35 m)
c2 = B.make_camera("T_face", (0.80, -0.55, 0.86), (0.80, 0.0, 0.81), lens=60, fstop=None)
# 3) narożnik z wysięgiem półki (koniec półki, czoło + lico)
c3 = B.make_camera("T_end", (-0.25, -0.30, 1.05), (0.03, 0.10, 0.905), lens=60, fstop=None)
B.render_settings("preview", res=(800, 450), samples=32)
for nm, c in (("edge", c1), ("face", c2), ("end", c3)):
    t = time.time()
    B.render_still(out / f"st_{nm}{suf}.png", c)
    print("[st]", nm, round(time.time() - t, 1))
