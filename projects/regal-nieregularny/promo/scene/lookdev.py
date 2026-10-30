"""Look-dev (ETAP 1): 3 klatki referencyjne wyrenderowane z filmu – te same kamery, światło i materiały co w finale.

  a) hero 3/4 całego regału w świetle okna, z rekwizytami  → S02 f179 (koniec łuku kamery, rig "Poranek")
  b) makro krawędzi sklejki i szczeliny 2 mm (płytka GO)    → S06 f382 (front S06 / P060 / D160-030, 100 mm f/5.6)
  c) szuflada w pełnym wysuwie: prowadnica + wnętrze        → S03 f224 (S09 wysunięta 350 mm, tkaniny w środku;
     kamera S03 w f210–225 przesunięta za płaszczyznę frontu, żeby prowadnica była w kadrze)

Użycie:
  python3.13 scene/lookdev.py -- [--res 1920x1080] [--spp 128] [--thr 0.01] [--device METAL] [--only a,b]
  blender -b -P scene/lookdev.py -- --device METAL
Wynik: PROMO_DIR/renders/lookdev/{a_hero_34,b_makro_krawedz_szczelina,c_szuflada_wysuw}.png + lookdev_times.json
"""
from __future__ import annotations

import json
import os
import shutil
import sys
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

import build_scene as B  # noqa: E402
import film as F  # noqa: E402

LOOKDEV = {"a": ("a_hero_34", "S02:179"), "b": ("b_makro_krawedz_szczelina", "S06:382"),
           "c": ("c_szuflada_wysuw", "S03:224")}


def main():
    args = B.script_args()

    def arg(n, d=None, cast=str):
        return cast(args[args.index(n) + 1]) if n in args else d

    res = tuple(int(v) for v in arg("--res", "1920x1080").split("x"))
    out = Path(arg("--out", str(B.RENDERS_DIR / "lookdev")))
    keys = arg("--only", "a,b,c").split(",")
    F.build_film()
    spec = ",".join(LOOKDEV[k][1] for k in keys)
    rep = F.render_stills(spec, "final", res, out, arg("--spp", 128, int), arg("--device"), arg("--thr", 0.01, float))
    for k, r in zip(keys, rep):
        dst = out / f"{LOOKDEV[k][0]}.png"
        shutil.copyfile(r["file"], dst)
        r["lookdev"] = str(dst)
    (out / "lookdev_times.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
