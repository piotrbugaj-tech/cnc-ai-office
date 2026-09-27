"""Rysuje widok z przodu regalu na podstawie uklad.json -> widok-przod.svg"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(os.path.join(HERE, "uklad.json"), encoding="utf-8"))
T = U["plyta"]
W, H = U["gabaryt"]["szerokosc"], U["gabaryt"]["wysokosc"]
M = 60                      # margines rysunku
S = 0.45                    # skala px/mm

def X(x): return M + x * S
def Y(y): return M + (H - y) * S

out = []
add = out.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S+2*M:.0f}" height="{H*S+2*M+40:.0f}" '
    f'viewBox="0 0 {W*S+2*M:.0f} {H*S+2*M+40:.0f}" font-family="Helvetica, Arial, sans-serif">')
add('<rect width="100%" height="100%" fill="#ffffff"/>')

rows = U["rzedy"]
KOL = {"szuflada": "#d9b98a", "drzwiczki": "#b8d0a8", "otwarta": "#f6f1e8"}

def comp_rect(od, do, y0, y1):
    return od + T, y0, do - od - T, y1 - y0        # swiatlo wneki w X modelu

# wneki
for w in U["wneki"]:
    y0, y1 = rows[w["rzad"]]
    x, y, ww, hh = comp_rect(w["od"], w["do"], y0, y1)
    add(f'<rect x="{X(x):.1f}" y="{Y(y+hh):.1f}" width="{ww*S:.1f}" height="{hh*S:.1f}" fill="#f6f1e8"/>')
    if w["typ"] != "otwarta":
        g = 2  # szczelina frontu
        add(f'<rect x="{X(x+g):.1f}" y="{Y(y+hh-g):.1f}" width="{(ww-2*g)*S:.1f}" height="{(hh-2*g)*S:.1f}" '
            f'fill="{KOL[w["typ"]]}" stroke="#6b5a45" stroke-width="0.8"/>')
        cx, cy = X(x + ww / 2), Y(y + hh / 2)
        lab = w["stare"].replace("Szuflada ", "S").replace("Drzwiczki ", "D")
        fs = 11 if hh > 100 else 9
        add(f'<text x="{cx:.1f}" y="{cy+4:.1f}" font-size="{fs}" text-anchor="middle" fill="#3a2f22">{lab}</text>')
        if w["typ"] == "drzwiczki":   # znacznik strony zawiasow
            zx = X(x + g + 4) if w["zawias"] == "L" else X(x + ww - g - 4)
            add(f'<line x1="{zx:.1f}" y1="{Y(y+hh-10):.1f}" x2="{zx:.1f}" y2="{Y(y+10):.1f}" stroke="#2e6b2e" stroke-width="2"/>')
    else:
        add(f'<text x="{X(x+ww/2):.1f}" y="{Y(y+hh/2)+4:.1f}" font-size="9" text-anchor="middle" fill="#a89a85">{ww:.0f}×{hh:.0f}</text>')
for t in U["wneki_wysokie"]:
    y0 = rows[t["rzedy"][0]][0]; y1 = rows[t["rzedy"][-1]][1]
    x, y, ww, hh = comp_rect(t["od"], t["do"], y0, y1)
    add(f'<rect x="{X(x):.1f}" y="{Y(y+hh):.1f}" width="{ww*S:.1f}" height="{hh*S:.1f}" fill="#efe6d6"/>')
    add(f'<text x="{X(x+ww/2):.1f}" y="{Y(y+hh/2)+4:.1f}" font-size="9" text-anchor="middle" fill="#a89a85">{ww:.0f}×{hh:.0f}</text>')

PLY = "#c9a66b"
# poziomy
for p in U["poziomy"]:
    y0, y1 = (p["y0"], p["y1"]) if "y0" in p else (p["os"] - T / 2, p["os"] + T / 2)
    for a, b in p["odcinki"]:
        add(f'<rect x="{X(a):.1f}" y="{Y(y1):.1f}" width="{(b-a)*S:.1f}" height="{T*S:.1f}" fill="{PLY}" stroke="#8a6d3b" stroke-width="0.5"/>')
    add(f'<text x="{X(W)+6:.1f}" y="{Y((y0+y1)/2)+4:.1f}" font-size="10" fill="#555">{p["id"]}</text>')
# przegrody
for q in U["przegrody"]:
    y0 = rows[q["rzedy"][0]][0]; y1 = rows[q["rzedy"][-1]][1]
    add(f'<rect x="{X(q["os_x"]):.1f}" y="{Y(y1):.1f}" width="{T*S:.1f}" height="{(y1-y0)*S:.1f}" fill="{PLY}" stroke="#8a6d3b" stroke-width="0.5"/>')
# wymiary gabarytowe
add(f'<text x="{X(W/2):.1f}" y="{M-8:.1f}" font-size="13" text-anchor="middle" fill="#333">{W} mm</text>')
add(f'<text x="{M-14:.1f}" y="{Y(H/2):.1f}" font-size="13" text-anchor="middle" fill="#333" transform="rotate(-90 {M-14:.1f} {Y(H/2):.1f})">{H} mm</text>')
add(f'<text x="{M:.1f}" y="{M-30:.1f}" font-size="11" fill="#555">S = szuflada, D = drzwiczki (numeracja ze starych plików), zielona kreska = strona zawiasów. Głębokość {U["gabaryt"]["glebokosc"]} mm.</text>')
add('</svg>')
open(os.path.join(HERE, "widok-przod.svg"), "w", encoding="utf-8").write("\n".join(out))
print("OK widok-przod.svg")
