"""Look-dev (ETAP 1): 3 klatki referencyjne wyrenderowane z filmu – te same kamery, światło i materiały co w finale.

  a) hero 3/4 całego regału w świetle okna, z rekwizytami  → S02 f179 (koniec łuku kamery, rig "Poranek")
  b) makro krawędzi sklejki i szczeliny 2 mm (płytka GO)    → S06 f382 (front S06 / P060 / D160-030, 100 mm f/5.6)
  c) szuflada w pełnym wysuwie: prowadnica + wnętrze        → S03 f224 (S09 wysunięta 350 mm, tkaniny w środku);
     kamera look-devu z boku (kamera z briefu nie pokazuje prowadnicy – opcja --brief-cam-c renderuje oryginalną)

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

_here = Path(__file__).resolve().parent if "__file__" in globals() else Path(os.getcwd())
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
    if "c" in keys and "--brief-cam-c" not in args:
        # Kamera z briefu (S03, f210–225) stoi przed płaszczyzną frontu, więc prowadnica schowana za frontem
        # jest niewidoczna. Do look-devu (c) – kamera z prawej, z góry, za płaszczyzną frontu: bok skrzynki S09
        # z członami KA 4532 (wewnętrzny + środkowy) i wnętrze z tkaninami.
        cam = B.make_camera("CAM_LD_szuflada", F.P(1500, -255, 1090), F.P(1140, -175, 790), lens=40, fstop=4.0,
                            focus=F.P(1186, -190, 809))
        F.B.S.film_cams["S03"] = cam
    spec = ",".join(LOOKDEV[k][1] for k in keys)
    rep = F.render_stills(spec, "final", res, out, arg("--spp", 128, int), arg("--device"), arg("--thr", 0.01, float))
    for k, r in zip(keys, rep):
        dst = out / f"{LOOKDEV[k][0]}.png"
        shutil.copyfile(r["file"], dst)
        r["lookdev"] = str(dst)
    (out / "lookdev_times.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
