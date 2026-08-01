"""
Generator podgladu regalu R150 -> preview.html

Samodzielna strona (bez zasobow zewnetrznych - CSP artefaktu):
  - podglad 3D w WebGL 2 (bufor glebi, plaskie cieniowanie, orbita mysza)
  - trzy rzuty ortogonalne SVG z wymiarami
  - tabela specyfikacji

Uruchomienie:  python3 preview_gen.py
"""

import json
import math
import os

import checks
import shelf_model as m

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview.html")

P, D = m.PARAMS, m.DERIVED


# ================================================================ dane 3D

def parts_payload():
    """Jedna siatka na rodzaj elementu - toggle warstwy = pominiecie draw calla."""
    buckets = {}
    for part in m.build_parts():
        verts, tris = part.triangles()
        b = buckets.setdefault(part.kind, {"v": [], "t": []})
        base = len(b["v"]) // 3
        for x, y, z in verts:
            b["v"] += [round(x, 1), round(y, 1), round(z, 1)]
        for a, c, d in tris:
            b["t"] += [base + a, base + c, base + d]
    return buckets


# ================================================================ SVG

PLY = "var(--ply)"
PLY_D = "var(--ply-dark)"
CAV = "var(--cavity)"
RULE = "var(--rule)"
DIM = "var(--dim)"
ACC = "var(--accent)"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def poly(pts, fill, stroke=RULE, sw=1.4, extra=""):
    d = " ".join("%.2f,%.2f" % (x, y) for x, y in pts)
    return ('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%.1f" '
            'vector-effect="non-scaling-stroke" %s/>' % (d, fill, stroke, sw, extra))


def rect(x0, y0, x1, y1, fill, stroke=RULE, sw=1.4):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, stroke, sw)


def line(x0, y0, x1, y1, stroke=RULE, sw=1.4, dash=""):
    da = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
            'stroke-width="%.1f" vector-effect="non-scaling-stroke"%s/>'
            % (x0, y0, x1, y1, stroke, sw, da))


# Kazdy rzut renderuje sie w innej skali (rozne viewBox + max-height w CSS),
# wiec opisy w jednostkach viewBox wyszlyby raz duze, raz mikroskopijne.
# _K wyrownuje je do mniej wiecej 14 px na ekranie.
_K = [1.0]


def text(x, y, s, size=34, fill=DIM, anchor="middle", weight="500"):
    return ('<text x="%.2f" y="%.2f" font-size="%.1f" fill="%s" text-anchor="%s" '
            'font-weight="%s" font-family="ui-monospace,SFMono-Regular,Menlo,'
            'Consolas,monospace">%s</text>'
            % (x, y, size * _K[0], fill, anchor, weight, esc(s)))


def dim_h(x0, x1, y, label, off=0):
    """Wymiar poziomy z zaslepkami."""
    k = _K[0]
    g = [line(x0, y, x1, y, DIM, 1.2)]
    for x in (x0, x1):
        g.append(line(x, y - 12 * k, x, y + 12 * k, DIM, 1.2))
    g.append(text((x0 + x1) / 2.0, y - 14 * k + off, label))
    return "".join(g)


def dim_v(y0, y1, x, label):
    k = _K[0]
    g = [line(x, y0, x, y1, DIM, 1.2)]
    for y in (y0, y1):
        g.append(line(x - 12 * k, y, x + 12 * k, y, DIM, 1.2))
    g.append('<g transform="translate(%.2f,%.2f) rotate(-90)">%s</g>'
             % (x - 14 * k, (y0 + y1) / 2.0, text(0, 0, label)))
    return "".join(g)


def svg_open(vb, title):
    return ('<svg viewBox="%s" role="img" aria-label="%s" '
            'preserveAspectRatio="xMidYMid meet">' % (vb, esc(title)))


# ---------------------------------------------------------------- rzut z gory

def view_plan():
    """Rzut z gory na poziomie polki - pokazuje luk R150 i podzial przesel."""
    H = P["D"]

    def fx(x):
        return x

    def fy(y):
        return H - y          # front na dole rysunku

    _K[0] = 1.0
    # level_z jest lokalny wzgledem spodu korpusu - korpus stoi na cokole,
    # wiec sonda musi to uwzglednic (patrz shelf_model.build_parts)
    z_probe = D["level_z"][2] + P["T"] / 2.0 + P["PLINTH_H"]
    g = []

    for part in m.build_parts():
        z0, z1 = part.z_range()
        if not (z0 - 1e-6 <= z_probe <= z1 + 1e-6):
            continue
        fill = {"back": PLY_D, "vertical": PLY, "shelf": PLY}.get(part.kind)
        if fill is None:
            continue
        pts = [(fx(x), fy(y)) for x, y in part.footprint()]
        g.append(poly(pts, fill))

    # srodek luku + promien
    cx, cy = D["arc_center"]
    g.append(line(fx(cx) - 26, fy(cy), fx(cx) + 26, fy(cy), ACC, 1.2))
    g.append(line(fx(cx), fy(cy) - 26, fx(cx), fy(cy) + 26, ACC, 1.2))
    ang = math.radians(215)
    g.append(line(fx(cx), fy(cy),
                  fx(cx + P["R"] * math.cos(ang)), fy(cy + P["R"] * math.sin(ang)),
                  ACC, 1.2, dash="14 10"))
    # opis poza obrysem, zeby nie lezal na geometrii nosa
    lr = P["R"] + 34
    g.append(text(fx(cx + lr * math.cos(ang)), fy(cy + lr * math.sin(ang)) + 12,
                  "R150", 36, ACC, anchor="end"))

    # wymiary
    g.append(dim_h(0, P["W"], fy(0) + 96, "1800"))
    xs = D["vertical_x"]
    g.append(dim_h(0, P["R"], fy(0) + 46, "150"))
    for b in range(P["N_BAYS"]):
        g.append(dim_h(xs[b] + P["T"], xs[b + 1], fy(0) + 46, "526"))
    g.append(dim_v(fy(P["D"]), fy(0), -52, "400"))

    return (svg_open("-190 -120 2140 700", "Rzut z gory") + "".join(g) + "</svg>")


# ---------------------------------------------------------------- widok z przodu

def view_front():
    """Elewacja frontowa - cala bryla (cokol + korpus), przeslo i poziomy."""
    ph = P["PLINTH_H"]
    total_h = P["H"] + ph

    def fy(z):
        return total_h - z

    # rysowane z prawdziwych czesci (nie z recznie odtwarzanych wspolrzednych)
    _K[0] = 2.0
    g = [rect(0, fy(total_h), P["W"], fy(0), CAV)]
    for part in m.build_parts():
        if part.kind not in ("vertical", "shelf", "plinth", "drawer", "door"):
            continue
        if part.kind == "drawer" and not part.name.endswith("-front"):
            continue          # w elewacji widac tylko front szuflady
        x0, _, z0, x1, _, z1 = part.bbox()
        fill = {"plinth": PLY_D, "drawer": CAV, "door": CAV}.get(part.kind, PLY)
        g.append(rect(x0, fy(z1), x1, fy(z0), fill))

    g.append(line(0, fy(ph), P["W"], fy(ph), RULE, 1.2, dash="16 12"))
    g.append(text(P["W"] / 2.0, fy(ph / 2.0) + 12, "cokol %.0f mm" % ph, 30, DIM))

    g.append(dim_v(fy(total_h), fy(0), -60, "2000"))
    z0 = D["level_z"][0] + P["T"] + ph
    # etykieta liczona z modelu, nie wpisana recznie - do rundy 4 zostala tu
    # zamrozona wartosc 378.4 z rundy 3, mimo ze korpus skurczyl sie do 1900 mm
    # i swiatlo wynosi 358.4 mm (rysunek geometrycznie dobry, opis klamal)
    g.append(dim_v(fy(z0 + D["shelf_clear"]), fy(z0), P["W"] + 60,
                   "%.1f" % D["shelf_clear"]))
    g.append(dim_h(0, P["W"], fy(0) + 190, "1800"))
    g.append(dim_h(0, P["R"], fy(0) + 80, "150"))
    return (svg_open("-260 -140 2340 2560", "Widok z przodu") + "".join(g) + "</svg>")


# ---------------------------------------------------------------- widok z prawej

def view_right():
    """Przekroj pionowy przez prawy bok - plyty, kolki polkowe, sruby i cokol.

    Runda 7: nie ma juz wrebow. Widac dolna i gorna plyte (ciagle, pelnej
    glebokosci), pion stojacy miedzy nimi, otwory Ø5 pod kolki na czterech
    srodkowych wysokosciach i pionowe sruby M6 przez czola plyt.
    """
    ph = P["PLINTH_H"]
    total_h = P["H"] + ph
    Dp = P["D"]
    T = P["T"]
    fd = D["frame_depth"]

    def fx(y):
        return Dp - y

    def fy(z):
        return total_h - z

    _K[0] = 2.0
    g = [rect(fx(Dp), fy(total_h), fx(0), fy(ph), PLY)]
    g.append(line(fx(fd), fy(total_h), fx(fd), fy(ph), RULE, 1.0, dash="16 12"))

    # dolna i gorna plyta - ciagle, na pelna glebokosc
    for z in (ph, ph + P["H"] - T):
        g.append(rect(fx(fd), fy(z + T), fx(0), fy(z), PLY_D, ACC, 1.6))

    # sruby M6 pionowo przez czola plyt w mimosrod w pionie
    for y in P["BOLT_Y"]:
        for z in (ph + T / 2.0, ph + P["H"] - T / 2.0):
            g.append('<circle cx="%.2f" cy="%.2f" r="9" fill="none" stroke="%s" '
                     'stroke-width="1.6" vector-effect="non-scaling-stroke"/>'
                     % (fx(y), fy(z), ACC))

    # kolki polkowe Ø5 na czterech srodkowych wysokosciach
    for li in range(1, P["N_LEVELS"] - 1):
        z = D["level_z"][li] + ph
        g.append(line(fx(fd), fy(z), fx(0), fy(z), RULE, 1.0, dash="10 8"))
        for y in P["PIN_Y"]:
            g.append('<circle cx="%.2f" cy="%.2f" r="5" fill="%s" stroke="none"/>'
                     % (fx(y), fy(z), DIM))

    sd, sh = P["SKIRTING_DEPTH"], P["SKIRTING_H"]
    g.append(rect(fx(Dp - sd), fy(sh), fx(Dp), fy(0), "none", ACC, 1.4))
    g.append('<g transform="translate(%.2f,%.2f) rotate(-90)">%s</g>'
             % (fx(Dp) - 14, fy(sh / 2.0), text(0, 0, "listwa", 22, ACC)))

    g.append(dim_h(fx(Dp), fx(0), fy(0) + 110, "400"))
    g.append(dim_v(fy(total_h), fy(0), fx(Dp) - 60, "2000"))
    return (svg_open("-260 -160 900 2560", "Widok z prawej") + "".join(g) + "</svg>")

def view_bolts():
    """Elewacja frontowa - dokladne (X, Z) kazdego zlacza srubowego.

    Y (glebokosc) nie da sie pokazac w elewacji froncie - stad liczba przy
    kazdym znaczniku (ile srub przechodzi przez ten pion na tej wysokosci)
    i odeslanie do widoku z prawej / rzutu z gory po dokladne pozycje Y.
    """
    total_h, W = P["H"] + P["PLINTH_H"], P["W"]

    def fy(z):
        return total_h - z

    _K[0] = 2.0
    clusters = {}
    for x, y, z, direction in m.bolt_positions() + m.nose_corner_bolt_positions():
        key = (round(x, 1), round(z, 1))
        clusters[key] = clusters.get(key, 0) + 1

    g = [rect(0, fy(total_h), W, fy(0), CAV)]
    for part in m.build_parts():
        if part.kind not in ("vertical", "shelf", "plinth", "drawer", "door"):
            continue
        if part.kind == "drawer" and not part.name.endswith("-front"):
            continue          # w elewacji widac tylko front szuflady
        x0, _, z0, x1, _, z1 = part.bbox()
        fill = {"plinth": PLY_D, "drawer": CAV, "door": CAV}.get(part.kind, PLY)
        g.append(rect(x0, fy(z1), x1, fy(z0), fill))

    for (x, z), n in clusters.items():
        cy = fy(z)
        g.append('<circle cx="%.2f" cy="%.2f" r="30" fill="var(--surface)" '
                  'stroke="%s" stroke-width="3" vector-effect="non-scaling-stroke"/>'
                  % (x, cy, ACC))
        g.append(text(x, cy + 19, str(n), 36, ACC, weight="700"))

    g.append(dim_v(fy(total_h), fy(0), -60, "2000"))
    g.append(dim_h(0, W, fy(0) + 190, "1800"))
    return (svg_open("-260 -140 2340 2560", "Rozmieszczenie srub") + "".join(g) + "</svg>")


# ---------------------------------------------------------------- cokol

def view_plinth():
    """Rzut z gory na cokol - cofniecie 22 mm od krawedzi korpusu na
    wszystkich czterech bokach (runda 5, na zyczenie klienta - zastapilo
    dawna asymetrie z rundy 4: 0 mm z przodu/lewej, 20 mm z tylu/prawej).

    Przerywany obrys = footprint korpusu tuz nad cokolem (dno - teraz jedna
    plyta pelnej szerokosci, runda 5 - stad wciecia przy pionach
    posrednich), dla porownania jak daleko cokol jest cofniety. Ciagly
    czerwony obrys = sylwetka listwy przypodlogowej wzdluz obu scian
    (tyl + prawy bok), dla kontekstu - PLINTH_INSET (22 mm) > SKIRTING_DEPTH
    (20 mm), wiec cokol nadal ja omija.
    """
    Dp, W, R = P["D"], P["W"], P["R"]

    def fx(x):
        return x

    def fy(y):
        return Dp - y

    _K[0] = 1.0
    g = []

    z_probe = P["PLINTH_H"] + P["T"] / 2.0     # dno korpusu, tuz nad cokolem
    for part in m.build_parts():
        if part.kind not in ("vertical", "shelf"):
            continue
        z0, z1 = part.z_range()
        if not (z0 - 1e-6 <= z_probe <= z1 + 1e-6):
            continue
        pts = [(fx(x), fy(y)) for x, y in part.footprint()]
        g.append(poly(pts, "none", RULE, 1.2, 'stroke-dasharray="10 8"'))

    for part in m.build_parts():
        if part.kind != "plinth":
            continue
        pts = [(fx(x), fy(y)) for x, y in part.footprint()]
        g.append(poly(pts, PLY_D))

    sd = P["SKIRTING_DEPTH"]
    g.append(poly([(fx(0), fy(Dp)), (fx(W), fy(Dp)),
                   (fx(W), fy(Dp - sd)), (fx(0), fy(Dp - sd))],
                  "none", ACC, 1.4, 'stroke-dasharray="12 9"'))
    g.append(poly([(fx(W - sd), fy(Dp)), (fx(W), fy(Dp)),
                   (fx(W), fy(0)), (fx(W - sd), fy(0))],
                  "none", ACC, 1.4, 'stroke-dasharray="12 9"'))
    # etykieta nad obrysem, nie na nim - pasmo listwy ma tylko 20 mm
    # wysokosci, za malo dla czcionki 30 (i zejsc typu "y")
    g.append(text(fx(W / 2.0), -24, "listwa - tylna sciana", 30, ACC))
    g.append('<g transform="translate(%.2f,%.2f) rotate(-90)">%s</g>'
             % (fx(W - sd) - 14, fy(Dp / 2.0), text(0, 0, "listwa - prawa sciana", 30, ACC)))

    inset = P["PLINTH_INSET"]
    g.append(dim_h(0, W, fy(0) + 96, "1800"))
    g.append(dim_v(fy(Dp), fy(0), -52, "400"))
    g.append(dim_h(W - sd, W, fy(0) + 46, "20"))
    g.append(dim_v(fy(Dp), fy(Dp - sd), -110, "20"))
    g.append(dim_h(0, inset, fy(0) + 146, "22"))
    g.append(dim_h(inset, inset + P["T"], fy(0) + 196, "18"))

    return (svg_open("-190 -120 2140 700", "Rzut cokolu") + "".join(g) + "</svg>")


# ================================================================ strona

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --paper:#e9ecef; --surface:#f4f6f7; --ink:#12171b; --ink-2:#4a555e;
  --rule:#9aa5ad; --dim:#5d6a73; --edge:#c9d1d6;
  --accent:#c62f24; --drill:#2c8154; --grain:#a8781a;
  --viewer:#101519; --viewer-2:#1a2126; --viewer-rule:#2c363d;
  --ply:#d9bd8e; --ply-dark:#b8965f; --cavity:#7d6844;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#0e1216; --surface:#161c21; --ink:#e6ebee; --ink-2:#9aa7b0;
    --rule:#5a666e; --dim:#8b98a1; --edge:#2a333a;
    --accent:#f26355; --drill:#4fb87f; --grain:#d6a63c;
    --viewer:#080b0d; --viewer-2:#12181c;
  }
}
:root[data-theme="dark"]{
  --paper:#0e1216; --surface:#161c21; --ink:#e6ebee; --ink-2:#9aa7b0;
  --rule:#5a666e; --dim:#8b98a1; --edge:#2a333a;
  --accent:#f26355; --drill:#4fb87f; --grain:#d6a63c;
  --viewer:#080b0d; --viewer-2:#12181c;
}
:root[data-theme="light"]{
  --paper:#e9ecef; --surface:#f4f6f7; --ink:#12171b; --ink-2:#4a555e;
  --rule:#9aa5ad; --dim:#5d6a73; --edge:#c9d1d6;
  --accent:#c62f24; --drill:#2c8154; --grain:#a8781a;
  --viewer:#101519; --viewer-2:#1a2126;
}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
     line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1140px;margin:0 auto;padding:40px 24px 96px;
      display:flex;flex-direction:column;gap:48px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;
         text-transform:uppercase;color:var(--accent);margin:0 0 10px}
h1{font-size:clamp(30px,5vw,46px);line-height:1.05;letter-spacing:-.025em;
   font-weight:660;margin:0 0 14px;text-wrap:balance}
h2{font-size:20px;letter-spacing:-.01em;font-weight:640;margin:0 0 4px}
h2 .num{font-family:var(--mono);font-size:12px;color:var(--accent);
        margin-right:10px;letter-spacing:.08em}
.lede{font-size:17px;color:var(--ink-2);margin:0;max-width:64ch}
.sub{font-size:14px;color:var(--ink-2);margin:0 0 18px;max-width:70ch}
section{display:flex;flex-direction:column}
.hdr{border-top:1px solid var(--edge);padding-top:14px;margin-bottom:20px}

/* --- pasek kluczowych liczb --- */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));
       gap:1px;background:var(--edge);border:1px solid var(--edge)}
.stat{background:var(--surface);padding:14px 16px}
.stat .k{font-family:var(--mono);font-size:10px;letter-spacing:.14em;
         text-transform:uppercase;color:var(--ink-2)}
.stat .v{font-family:var(--mono);font-size:21px;font-weight:600;
         font-variant-numeric:tabular-nums;margin-top:3px}
.stat .u{font-size:12px;color:var(--ink-2);font-weight:400}

/* --- podglad 3D --- */
.viewer{background:var(--viewer);border:1px solid var(--edge);position:relative}
canvas{display:block;width:100%;height:clamp(420px,62vh,660px);
       touch-action:none;cursor:grab}
canvas.drag{cursor:grabbing}
.hud{position:absolute;left:14px;top:14px;font-family:var(--mono);font-size:10px;
     letter-spacing:.1em;text-transform:uppercase;color:#7d8f9b;pointer-events:none}
.readout{position:absolute;right:14px;top:14px;font-family:var(--mono);font-size:11px;
         color:#7d8f9b;font-variant-numeric:tabular-nums;pointer-events:none}
.nogl{position:absolute;inset:0;display:grid;place-content:center;margin:0;padding:0 32px;
      text-align:center;color:#93a3ad;font-size:14px;max-width:44ch;
      margin-inline:auto}
.bar{display:flex;flex-wrap:wrap;gap:6px;padding:12px;background:var(--viewer-2);
     border-top:1px solid var(--viewer-rule)}
.bar .sep{width:1px;background:var(--viewer-rule);margin:2px 6px}
button{font-family:var(--mono);font-size:11px;letter-spacing:.08em;
       text-transform:uppercase;padding:7px 11px;background:transparent;
       color:#93a3ad;border:1px solid var(--viewer-rule);cursor:pointer;
       transition:color .15s,border-color .15s,background .15s}
button:hover{color:#e2e9ed;border-color:#4a5860}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button[aria-pressed="true"]{color:#0e1216;background:#c9d4db;border-color:#c9d4db}
.swatch{display:inline-block;width:8px;height:8px;margin-right:7px;
        vertical-align:baseline;border:1px solid rgba(0,0,0,.3)}

/* --- rysunki --- */
.draw{display:grid;grid-template-columns:1fr;gap:1px;background:var(--edge);
      border:1px solid var(--edge)}
@media(min-width:820px){.draw{grid-template-columns:1.35fr 1fr}
  .plan,.wide{grid-column:1/-1}}
.sheet{background:var(--surface);padding:20px}
.sheet h3{font-family:var(--mono);font-size:10px;letter-spacing:.16em;
          text-transform:uppercase;color:var(--ink-2);margin:0 0 14px;font-weight:500}
.sheet svg{width:100%;height:auto;max-height:520px;display:block}
.figcap{font-size:12px;color:var(--ink-2);margin:-6px 0 14px;max-width:70ch}
.plan .sheet svg{max-height:300px}
.wide .sheet svg{max-height:640px;width:auto;max-width:100%;margin:0 auto;display:block}

/* --- tabele --- */
.tw{overflow-x:auto;border:1px solid var(--edge)}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--surface)}
th,td{text-align:left;padding:9px 14px;border-bottom:1px solid var(--edge)}
th{font-family:var(--mono);font-size:10px;letter-spacing:.13em;
   text-transform:uppercase;color:var(--ink-2);font-weight:500}
tbody tr:last-child td{border-bottom:none}
td.n{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
td.d{color:var(--ink-2);font-size:13px}

/* --- listy uwag --- */
.notes{display:grid;gap:1px;background:var(--edge);border:1px solid var(--edge)}
.note{background:var(--surface);padding:16px 18px;display:grid;
      grid-template-columns:auto 1fr;gap:14px;align-items:start}
.tag{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
     padding:3px 8px;border:1px solid currentColor;white-space:nowrap;margin-top:2px}
.tag.q{color:var(--accent)}
.tag.i{color:var(--drill)}
.tag.w{color:var(--grain)}
.note p{margin:0;font-size:14px}
.note p b{font-weight:620}
.note p .why{display:block;color:var(--ink-2);margin-top:4px;font-size:13px}
.foot{font-size:12px;color:var(--ink-2);font-family:var(--mono);
      border-top:1px solid var(--edge);padding-top:16px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
  var MESH = __PARTS__, KINDS = __KINDS__, BB = __BBOX__;
  var cv = document.getElementById('cv'), out = document.getElementById('ro');
  var gl = cv.getContext('webgl2', {antialias:true, alpha:false});
  if(!gl){
    document.querySelector('.viewer').insertAdjacentHTML('beforeend',
      '<p class="nogl">Podglad 3D wymaga WebGL 2. Rzuty ponizej pokazuja te sama '
      + 'geometrie.</p>');
    return;
  }

  var az = -32, el = 14, zoom = 1, on = {};
  var cen = [(BB[0]+BB[3])/2, (BB[1]+BB[4])/2, (BB[2]+BB[5])/2];
  var RAD = Math.hypot(BB[3]-BB[0], BB[4]-BB[1], BB[5]-BB[2]);

  var VS = `#version 300 es
  in vec3 aPos;
  uniform mat4 uMVP; uniform vec3 uCen;
  out vec3 vP;
  void main(){ vP = aPos - uCen; gl_Position = uMVP * vec4(vP, 1.0); }`;

  var FS = `#version 300 es
  precision highp float;
  in vec3 vP;
  uniform vec3 uCol, uView;
  out vec4 frag;
  void main(){
    // normalna z pochodnych - plaskie cieniowanie bez atrybutu normalnej
    vec3 N = normalize(cross(dFdx(vP), dFdy(vP)));
    if(dot(N, uView) > 0.0) N = -N;                 // cieniowanie dwustronne
    vec3 key  = normalize(vec3(-0.45, -0.72, 0.62));
    vec3 fill = normalize(vec3( 0.65,  0.40, 0.18));
    float l = 0.30 + 0.62*max(dot(N,key),0.0) + 0.20*max(dot(N,fill),0.0);
    frag = vec4(pow(uCol*l, vec3(0.85)), 1.0);
  }`;

  function sh(t, src){
    var s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
    if(!gl.getShaderParameter(s, gl.COMPILE_STATUS))
      throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  var prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS));
  gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
  gl.bindAttribLocation(prog, 0, 'aPos');
  gl.linkProgram(prog);
  gl.useProgram(prog);
  var uMVP = gl.getUniformLocation(prog,'uMVP'), uCol = gl.getUniformLocation(prog,'uCol'),
      uView = gl.getUniformLocation(prog,'uView'), uCen = gl.getUniformLocation(prog,'uCen');

  function vao(verts, idx){
    var a = gl.createVertexArray(); gl.bindVertexArray(a);
    var vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(verts), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
    if(idx){
      var ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(idx), gl.STATIC_DRAW);
    }
    gl.bindVertexArray(null);
    return a;
  }

  var layers = {};
  Object.keys(MESH).forEach(function(k){
    on[k] = true;
    layers[k] = {a: vao(MESH[k].v, MESH[k].t), n: MESH[k].t.length,
                 c: KINDS[k].c.map(function(x){ return x/255; })};
  });

  // siatka posadzki co 200 mm
  var gv = [], g0 = -300, g1x = BB[3]+300, g1y = BB[4]+300, gz = -12;
  for(var gx=g0; gx<=g1x; gx+=200) gv.push(gx,g0,gz, gx,g1y,gz);
  for(var gy=g0; gy<=g1y; gy+=200) gv.push(g0,gy,gz, g1x,gy,gz);
  var grid = {a: vao(gv, null), n: gv.length/3};

  function mvp(w,h){
    var a = az*Math.PI/180, e = el*Math.PI/180;
    var ca=Math.cos(a), sa=Math.sin(a), ce=Math.cos(e), se=Math.sin(e);
    // dopasowanie skali do rzutu bryly
    var mnx=1e9,mxx=-1e9,mnz=1e9,mxz=-1e9;
    for(var i=0;i<8;i++){
      var x=BB[i&1?3:0]-cen[0], y=BB[i&2?4:1]-cen[1], z=BB[i&4?5:2]-cen[2];
      var X = x*ca + y*sa, Y = -x*sa + y*ca;
      var Z = -Y*se + z*ce;
      if(X<mnx)mnx=X; if(X>mxx)mxx=X; if(Z<mnz)mnz=Z; if(Z>mxz)mxz=Z;
    }
    var s = Math.min(w/(mxx-mnx), h/(mxz-mnz))*0.88*zoom;
    var sx = 2*s/w, sy = 2*s/h, sz = 1/RAD;
    // wiersz z: NDC rosnie w glab sceny (gl.LESS -> blizszy fragment wygrywa)
    return {m:new Float32Array([
      ca*sx,      sa*se*sy,  -sa*ce*sz,   0,
      sa*sx,     -ca*se*sy,   ca*ce*sz,   0,
      0,          ce*sy,      se*sz,      0,
      0,          0,          0,          1]),
      view:[-sa*ce, ca*ce, se]};
  }

  function draw(){
    var dpr = Math.min(window.devicePixelRatio||1, 2);
    var w = cv.clientWidth, h = cv.clientHeight;
    cv.width = Math.round(w*dpr); cv.height = Math.round(h*dpr);
    gl.viewport(0,0,cv.width,cv.height);

    var dark = (document.documentElement.dataset.theme || (
      matchMedia('(prefers-color-scheme:dark)').matches ? 'dark':'light')) === 'dark';
    var bg = dark ? [0.031,0.043,0.051] : [0.063,0.082,0.098];
    gl.clearColor(bg[0],bg[1],bg[2],1);
    gl.enable(gl.DEPTH_TEST);
    gl.disable(gl.CULL_FACE);                    // cieniowanie dwustronne
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    var M = mvp(w,h);
    gl.uniformMatrix4fv(uMVP,false,M.m);
    gl.uniform3fv(uView,M.view);
    gl.uniform3fv(uCen,cen);

    gl.bindVertexArray(grid.a);
    gl.uniform3f(uCol, 0.16,0.20,0.23);
    gl.drawArrays(gl.LINES,0,grid.n);

    Object.keys(layers).forEach(function(k){
      if(!on[k]) return;
      var L = layers[k];
      gl.bindVertexArray(L.a);
      gl.uniform3fv(uCol, L.c);
      gl.drawElements(gl.TRIANGLES, L.n, gl.UNSIGNED_INT, 0);
    });
    gl.bindVertexArray(null);

    out.textContent = 'az ' + az.toFixed(0) + '°   el ' + el.toFixed(0)
                    + '°   ' + Math.round(zoom*100) + '%';
  }

  // --- orbita ---
  var drag = false, lx = 0, ly = 0;
  cv.addEventListener('pointerdown', function(e){
    drag = true; lx = e.clientX; ly = e.clientY;
    cv.classList.add('drag'); cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', function(e){
    if(!drag) return;
    az += (e.clientX-lx)*0.42;
    el = Math.max(-89, Math.min(89, el + (e.clientY-ly)*0.34));
    lx = e.clientX; ly = e.clientY; draw();
  });
  function stop(e){ drag = false; cv.classList.remove('drag');
    if(e && e.pointerId!=null && cv.hasPointerCapture(e.pointerId))
      cv.releasePointerCapture(e.pointerId); }
  cv.addEventListener('pointerup', stop);
  cv.addEventListener('pointercancel', stop);
  cv.addEventListener('wheel', function(e){
    e.preventDefault();
    zoom = Math.max(0.4, Math.min(4, zoom * (e.deltaY < 0 ? 1.1 : 0.909)));
    draw();
  }, {passive:false});

  document.querySelectorAll('[data-view]').forEach(function(b){
    b.addEventListener('click', function(){
      var v = b.dataset.view.split(',');
      az = +v[0]; el = +v[1]; zoom = 1; draw();
    });
  });
  document.querySelectorAll('[data-kind]').forEach(function(b){
    b.addEventListener('click', function(){
      var k = b.dataset.kind;
      on[k] = !on[k];
      b.setAttribute('aria-pressed', on[k] ? 'true' : 'false');
      draw();
    });
  });

  addEventListener('resize', draw);
  var mq = matchMedia('(prefers-color-scheme:dark)');
  (mq.addEventListener ? mq.addEventListener.bind(mq,'change') : mq.addListener.bind(mq))(draw);
  new MutationObserver(draw).observe(document.documentElement,
    {attributes:true, attributeFilter:['data-theme']});
  draw();
})();
"""

KIND_META = {
    "vertical": ("Piony", (216, 186, 138)),
    "shelf": ("Polki", (226, 199, 152)),
    "back": ("Plecy", (150, 121, 80)),
    "plinth": ("Cokol", (102, 84, 61)),
    "drawer": ("Szuflady", (198, 156, 104)),
    "door": ("Drzwiczki", (176, 140, 96)),
}


def build_html(n_tests):
    s = m.summary()
    parts = s["parts"]
    payload = parts_payload()

    bxs = [q.bbox() for q in parts]
    bbox = [min(b[0] for b in bxs), min(b[1] for b in bxs), min(b[2] for b in bxs),
            max(b[3] for b in bxs), max(b[4] for b in bxs), max(b[5] for b in bxs)]

    kinds = {k: {"c": list(v[1])} for k, v in KIND_META.items()}

    js = (JS.replace("__PARTS__", json.dumps(payload, separators=(",", ":")))
            .replace("__KINDS__", json.dumps(kinds, separators=(",", ":")))
            .replace("__BBOX__", json.dumps(bbox)))

    total_h = P["H"] + P["PLINTH_H"]
    stats = [
        ("Gabaryt", "1800&times;%.0f" % total_h, "&times;400 mm"),
        ("Zaoblenie", "R150", "przedni lewy"),
        ("Cokol", "%.0f" % P["PLINTH_H"], "mm (korpus %.0f)" % P["H"]),
        ("Swiatlo polki", "%.1f" % D["shelf_clear"], "mm"),
        ("Rozpietosc", "526", "mm / przeslo"),
        ("Elementow", str(len(parts)), "szt."),
        ("Srub M6", str(s["n_bolts"]), "+ %d kotew" % len(m.plinth_bolt_positions())),
        ("Prowadnice", str(len(P["DRAWER_CELLS"])), "par Blum TANDEM 562H"),
        ("Masa netto", "%.0f" % s["mass_kg"], "kg"),
    ]
    stat_html = "".join(
        '<div class="stat"><div class="k">%s</div>'
        '<div class="v">%s <span class="u">%s</span></div></div>' % t for t in stats)

    layer_btns = "".join(
        '<button type="button" data-kind="%s" aria-pressed="true">'
        '<span class="swatch" style="background:rgb(%d,%d,%d)"></span>%s</button>'
        % (k, v[1][0], v[1][1], v[1][2], v[0]) for k, v in KIND_META.items())

    # --- tabela elementow ---
    def blank(q):
        b = q.bbox()
        dd = sorted([b[3] - b[0], b[4] - b[1], b[5] - b[2]], reverse=True)
        return "%.0f &times; %.0f" % (dd[0], dd[1])

    groups = {}
    for q in parts:
        e = groups.setdefault(q.qty_group, {"n": 0, "p": q, "a": 0.0, "dims": []})
        e["n"] += 1
        e["a"] += q.area_m2()
        if blank(q) not in e["dims"]:            # plecy przesel nie sa rownej szerokosci
            e["dims"].append(blank(q))
    # etykiety per grupa - kazdy pion to w modelu kilka brol (pasma miedzy
    # wrebami + pasma progu), ale fizycznie to jedna deska - "szt." w tabeli
    # liczy bryly weryfikacyjne, nie gotowe wyciete czesci (te ustali dopiero
    # runda DXF, laczac bryly z powrotem w jeden flat pattern na desce)
    GROUP_PL = {
        "vertical-mid": "Piony posrednie (mid-1, mid-2)",
        "vertical-R-side": "Prawy bok",
        "vertical-L-gable": "Lewy bok &middot; grzbiet + zeby (wrab)",
        "plate": "Dolna i gorna plyta &middot; jeden kawalek 1800 mm",
        "shelf-bay": "Polki srodkowe &middot; na kolkach, przestawialne",
        "nose-corner": "Poleczki naroznika &middot; wspornikowe, skrecane do lewego boku",
        "plinth-rib": "Cokol &middot; zebra poprzeczne pod pionami",
        "drawer-front": "Szuflada &middot; front",
        "drawer-side": "Szuflada &middot; boki",
        "drawer-back": "Szuflada &middot; tyl",
        "drawer-bottom": "Szuflada &middot; dno",
        "door": "Drzwiczki &middot; plyta",
        "back-nose": "Plecy &middot; nos",
        "back-bay": "Plecy &middot; przeslo",
        "plinth": "Cokol &middot; rama (lewy/tyl/prawy/przod/naroznik)",
    }
    order = list(GROUP_PL)

    def gkey(item):
        try:
            return order.index(item[0])
        except ValueError:
            return len(order)

    GRAIN_PL = {"longitudinal": "wzdluzne", "crosswise": "poprzeczne", "free": "dowolne"}
    rows = []
    for name, e in sorted(groups.items(), key=gkey):
        q = e["p"]
        dims = " / ".join(e["dims"])
        rows.append(
            "<tr><td>%s</td><td class='n'>%d</td><td class='n'>%s</td>"
            "<td class='n'>%.0f mm</td><td class='d'>%s</td><td class='d'>%s</td></tr>"
            % (GROUP_PL.get(name, KIND_META[q.kind][0]), e["n"], dims, q.thickness,
               GRAIN_PL[q.grain], q.material))
    table = ("<div class='tw'><table><thead><tr><th>Grupa</th><th>Szt.</th>"
             "<th>Wymiar blanku</th><th>Grubosc</th><th>Sloje</th><th>Material</th>"
             "</tr></thead><tbody>%s</tbody></table></div>" % "".join(rows))

    n_dr = len(P["DRAWER_CELLS"])
    n_do = len(P["DOOR_CELLS"])
    n_runners = len(P["DRAWER_CELLS"])
    notes = [
        ("i", "Dwa dolne rzedy - szesc szuflad na prowadnicach Blum TANDEM 562H.",
         "Wariant ekonomiczny (bez BLUMOTION), pelny wysuw, nosnosc statyczna "
         "~45 kg/pare, dlugosc nominalna 350 mm dobrana do glebokosci szuflady. "
         "Drzwiczki przesunely sie na poziom wyzej (byl na poziomie 1, teraz na "
         "poziomie 2), zeby zwolnic miejsce."),
        ("i", "Boki i tyl korpusu szuflady zostaja w T = 18 mm, jak reszta mebla.",
         "Poprawka po uwadze klienta: wczesniejsza wersja scieniala je do 16 mm, "
         "myslac ze to twardy limit systemu Blum. Dokladniejsze zrodlo (blum.com) "
         "pokazuje, ze TANDEM przyjmuje boki 1/2\"-3/4\" (12.7-19 mm) - 16 mm to "
         "tylko punkt odniesienia we wzorze na luz montazowy, nie gorna granica. "
         "18 mm miesci sie w zakresie i jest standardowym arkuszem - jeden "
         "material w calym meblu, bez dodatkowego zamowienia sklejki 16 mm, "
         "ktorej dostawca nie ma w katalogu."),
        ("q", "Dzielnik miedzy dwoma rzedami szuflad przywrocony.",
         "Byl bledny usuniety: petla polek na kolkach pomijala plyte na poziomie "
         "1, bo traktowala ja tylko jako „dno komory z szuflada”, a ta sama plyta "
         "jest tez „sufitem” komory ponizej - z dwoma rzedami szuflad ten sufit "
         "byl potrzebny. Wraca zawsze, niezaleznie od zawartosci obu sasiadujacych "
         "komor - 12 polek na kolkach zamiast 9. Sprawdzane automatycznie."),
        ("i", "72 wkrety mocujace prowadnice, osobno od 24 srub M6 konstrukcji.",
         "Prowadnica to kupowane okucie, nie plyta - model generuje tylko punkty "
         "pod wiercenie (jak dla zawiasow), nie geometrie samej szyny. Po 6 "
         "wkretow na pare (3 w lico pionu, 3 w bok szuflady)."),
        ("i", "Male zaokraglone poleczki w rogu nosa (runda 8), bez zmian.",
         "Wspornikowo skrecone do lica lewego boku, 2 sruby M6 kazda. Niezalezne "
         "od zmian w szufladach."),
        ("i", "Zero wrebow w calym meblu (runda 7), bez zmian.",
         "Piony stoja miedzy dolna a gorna plyta. Sruby ida pionowo przez czolo "
         "plyty w mimosrod w czole pionu - leb zawsze ma na czym usiasc."),
        ("w", "Masa netto %.0f kg - wyraznie wiecej niz z 3 szufladami." % s["mass_kg"],
         "Dwa pelne rzedy szuflad to 6 kompletow okucia i materialu zamiast 3, "
         "plus przywrocony dzielnik. Do potwierdzenia z klientem, czy to "
         "akceptowalne przy transporcie i montazu w dwie osoby."),
        ("w", "Szablon DXF do ciecia CNC - poza zakresem tej rundy.",
         "Model ma teraz realne, poprawione wymiary Blum (grubosc bokow, rozstaw "
         "wkretow), wiec jest gotowy pod przyszly eksport DXF z warstwami wg "
         "CLAUDE.md - ale sam generator DXF jeszcze nie istnieje (patrz brief.md, "
         "sekcja „poza zakresem”). To osobna runda pracy."),
    ]
    notes_html = "".join(
        '<div class="note"><span class="tag %s">%s</span>'
        '<p><b>%s</b><span class="why">%s</span></p></div>'
        % (t, {"q": "decyzja", "w": "ryzyko", "i": "info"}[t], h, w)
        for t, h, w in notes)

    return """<title>Regal R150 &mdash; bryla do oceny</title>
<style>%s</style>
<div class="wrap">

<header>
  <p class="eyebrow">CNC Furniture Studio &middot; runda 9 &middot; bryla do oceny</p>
  <h1>Regal R150</h1>
  <p class="lede">Sklejka brzozowa 18 mm (jeden material w calym meblu), ciecie CNC
  na gotowo, montaz rozbieralny. Dolna i gorna plyta to jeden kawalek na pelne
  1800 mm; cztery piony stoja <b>miedzy</b> nimi, skrecane pionowo przez czolo
  plyty. W calym meblu nie ma ani jednego wrebu. Dwa dolne rzedy maja szuflady
  na prowadnicach kulkowych <b>Blum TANDEM 562H</b> (bez BLUMOTION - wariant
  ekonomiczny), korpus szuflady w tej samej sklejce 18 mm co reszta mebla
  (mieści się w oficjalnym zakresie Blum 1/2"-3/4"), dzielnik miedzy dwoma
  rzedami szuflad na kolkach jak reszta polek srodkowych. Wyzej dwoje
  drzwiczek (zawiasy z lewej albo z prawej - opcja parametryczna, plyta
  identyczna w obu wariantach). Stoi na cokole 100 mm, cofnietym 22 mm ze
  wszystkich stron. Przedni lewy narozik zaobolony promieniem 150 mm, z
  wlasnymi malymi poleczkami skreconymi do lica lewego boku.</p>
</header>

<section>
  <div class="stats">%s</div>
</section>

<section>
  <div class="hdr"><h2><span class="num">01</span>Bryla</h2>
  <p class="sub">Przeciagnij, zeby obrocic. Kolko myszy przybliza.
  Wylacz „Piony", zeby zobaczyc same plyty poziomow z wycieciami pod grzbiety,
  albo „Polki", zeby zobaczyc cztery grzebienie pionowe osobno.</p></div>
  <div class="viewer">
    <canvas id="cv"></canvas>
    <div class="hud">Regal R150 &middot; 1:20</div>
    <div class="readout" id="ro"></div>
  </div>
  <div class="bar">
    <button type="button" data-view="-32,14">Aksonometria</button>
    <button type="button" data-view="-62,6">Zaoblenie</button>
    <button type="button" data-view="0,0">Przod</button>
    <button type="button" data-view="0,88">Gora</button>
    <span class="sep"></span>
    %s
  </div>
</section>

<section>
  <div class="hdr"><h2><span class="num">02</span>Rzuty</h2>
  <p class="sub">Wymiary w milimetrach. Luk R150 ma srodek w punkcie (150, 150) &mdash;
  jest styczny do frontu w x=150 i do lewego boku w y=150, wiec przechodzi w plaszczyzny
  bez zalamania.</p></div>
  <div class="draw">
    <div class="plan"><div class="sheet"><h3>Rzut z gory &middot; poziom polki</h3>%s</div></div>
    <div class="sheet"><h3>Widok z przodu</h3>%s</div>
    <div class="sheet"><h3>Widok z prawej &middot; wrab oporowy i sruby</h3>
    <p class="figcap">Cienki czerwony prostokat przy podlodze = sylwetka listwy
    przypodlogowej. Cokol jest tu cofniety, wiec korpus odrobine nawisa nad pusta
    przestrzenia w tym rogu — patrz „Rzut cokolu" nizej.</p>%s</div>
    <div class="wide"><div class="sheet"><h3>Rozmieszczenie srub M6 (%d szt.)</h3>
    <p class="figcap">Kazdy znacznik = jeden pion na tej wysokosci; liczba = ile srub
    przez niego przechodzi (2 z jednej strony, 4 gdy dwie polki spotykaja sie na tym
    samym pionie z obu stron). Dno i wieniec bez znacznikow na pionach posrednich -
    to teraz jedna plyta pelnej szerokosci, zlacze wrebowe jak lewy bok (runda 5).
    Dokladne pozycje w glab (Y) sa w widoku z prawej i w rzucie z gory.</p>%s</div></div>
    <div class="plan"><div class="sheet"><h3>Rzut cokolu &middot; cofniecie od scian</h3>
    <p class="figcap">Przerywany szary obrys = footprint korpusu tuz nad cokolem.
    Przerywany czerwony obrys = sylwetka listwy przypodlogowej wzdluz obu scian
    (tyl + prawy bok, gdzie regal przylega). Naroznik pod noskiem podaza za tym
    samym lukiem R150 co korpus powyzej.</p>%s</div></div>
  </div>
</section>

<section>
  <div class="hdr"><h2><span class="num">03</span>Elementy</h2>
  <p class="sub">Wymiar blanku gotowy do ciecia (bez wrebow od rundy 7). Jeden material
  w calym meblu - sklejka 18 mm (plyty, piony, polki, szuflady, drzwiczki) plus 4 mm
  na plecy i dna szuflad. Pelny szablon DXF z warstwami, nesting i BOM z cenami
  wchodza w kolejnej rundzie.</p></div>
  %s
</section>

<section>
  <div class="hdr"><h2><span class="num">04</span>Do rozstrzygniecia</h2>
  <p class="sub">Runda 9 dodala szuflady na realnym okuciu Blum. Otwarte: czy masa
  z dwoma pelnymi rzedami szuflad jest akceptowalna, i kiedy zrobic szablon DXF.</p></div>
  <div class="notes">%s</div>
</section>

<p class="foot">Model parametryczny: shelf_model.py &middot; %d/%d testow geometrii
przechodzi (gabaryt, stycznosc luku, domkniecie lancucha wymiarowego, brak przenikania
na %d elementach) &middot; skrypt do Blendera: build_shelf_blender.py</p>

</div>
<script>%s</script>
""" % (CSS, stat_html, layer_btns, view_plan(), view_front(), view_right(), s["n_bolts"],
       view_bolts(), view_plinth(), table, notes_html, n_tests, n_tests, len(parts), js)


def main():
    res = checks.run()
    failed = sum(1 for _, ok, _ in res.rows if not ok)
    if failed:
        res.report()
        raise SystemExit("przerwano: %d testow geometrii nie przeszlo" % failed)

    html = build_html(len(res.rows))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("testy geometrii: %d/%d PASS" % (len(res.rows), len(res.rows)))
    print("zapisano %s (%.0f kB)" % (os.path.basename(OUT), len(html) / 1024.0))


if __name__ == "__main__":
    main()
