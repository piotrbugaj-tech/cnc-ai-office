"""Eksport prawdziwego rozkroju (regal.cnc.run_nesting z repo produktu) do PROMO_DIR/data/nesting.json.

Uruchom raz (dowolny Python z zależnościami repo cnc: numpy, PyYAML, shapely, ezdxf, matplotlib):
  python3.13 scene/export_nesting.py
Blender (film.py, ujęcia S07/S08) czyta już tylko JSON – na Macu nie trzeba instalować zależności cnc.
Repo produktu tylko czytamy (CNC_REPO, domyślnie /home/user/cnc).
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMO_DIR = Path(os.environ.get("PROMO_DIR", HERE.parent))
CNC_REPO = Path(os.environ.get("CNC_REPO", "/home/user/cnc"))
sys.dont_write_bytecode = True   # nie zostawiamy __pycache__ w repo produktu (tylko odczyt)
sys.path.insert(0, str(CNC_REPO))

from regal import model as rmodel  # noqa: E402
from regal.cnc import run_nesting  # noqa: E402

m = rmodel.build()
sheets = run_nesting(m)
parts = {p.pid: p for p in m.parts}
out = dict(source=str(CNC_REPO), sheet_size=list(m.cfg["cnc"]["sheet"]), sheets=[])
for t, lst in sorted(sheets.items(), reverse=True):
    for sh in lst:
        pls = []
        for pl in sh.placements:
            p = parts[pl.pid]
            pls.append(dict(pid=pl.pid, x=pl.x, y=pl.y, rot=bool(pl.rot), w=pl.w, h=pl.h,
                            bbox=[float(v) for v in p.bbox], group=p.group, t=p.t,
                            outline=[[round(float(u), 2), round(float(v), 2)] for u, v in p.outline]))
        out["sheets"].append(dict(t=t, material=sh.material, index=sh.index, W=sh.W, H=sh.H, placements=pls))
p = PROMO_DIR / "data" / "nesting.json"
p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("zapisano", p, [(s["t"], s["index"], len(s["placements"])) for s in out["sheets"]])
