"""
Generator szczegolu szuflady -> drawer-detail.html (runda 9.2)

Osobny plik na zyczenie klienta: jedna szuflada osobno (5 elementow) plus
rozmieszczenie 12 punktow wiercenia pod wkrety mocujace prowadnice Blum
TANDEM 562H (6 w lico pionu/"corpus", 6 w bok szuflady/"drawer") dla pary
(poziom 0, przeslo 0) - reprezentatywnej dla wszystkich szesciu szuflad
(geometria kazdej pary jest identyczna, rozni sie tylko polozeniem w bryle).

Reuzywa CSS/JS/pomocnicze SVG z preview_gen.py - ten sam wyglad, ten sam
generyczny renderer WebGL (payload MESH/KINDS/BBOX, nic specyficznego dla
calego regalu).

Uruchomienie:  python3 drawer_detail_gen.py
"""

import json
import os

import preview_gen as pv
import shelf_model as m

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "drawer-detail.html")

P, D = m.PARAMS, m.DERIVED
LI, BAY = 0, 0     # reprezentatywna para - poziom 0, przeslo 0 (lewe skrajne)


def _box_mesh(bx0, by0, bz0, bx1, by1, bz1):
    """(verts, tris) dla prostopadloscianu - ta sama triangulacja co Part.mesh()."""
    v = [(bx0, by0, bz0), (bx1, by0, bz0), (bx1, by1, bz0), (bx0, by1, bz0),
         (bx0, by0, bz1), (bx1, by0, bz1), (bx1, by1, bz1), (bx0, by1, bz1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    tris = []
    for face in f:
        for i in range(1, len(face) - 1):
            tris.append((face[0], face[i], face[i + 1]))
    return v, tris


def _cube_mesh(cx, cy, cz, s):
    """Mala kostka (marker punktu wiercenia)."""
    h = s / 2.0
    return _box_mesh(cx - h, cy - h, cz - h, cx + h, cy + h, cz + h)


def drawer_parts():
    prefix = "drawer-%d%d-" % (LI, BAY)
    return [q for q in m.build_parts() if q.name.startswith(prefix)]


def runner_points_for_cell():
    """Filtruje runner_positions() do samej pary (LI, BAY).

    Z sam w sobie NIE wystarcza - wszystkie przesla na tym samym poziomie
    (li) dziela ta sama wysokosc zc, wiec bez filtra na X zlapaloby to
    punkty z 3 przesel naraz (36 zamiast 12). X musi miescic sie w swietle
    tej konkretnej komory.
    """
    x0, x1, z0, z1 = m._cell_opening(LI, BAY, P, D)
    zc = z0 + P["DRAWER_BOX_Z"] + P["DRAWER_BOX_H"] / 2.0 + P["PLINTH_H"]
    return [pt for pt in m.runner_positions()
            if abs(pt[2] - zc) < 1e-6 and x0 - 1e-6 <= pt[0] <= x1 + 1e-6]


def dowel_points_for_cell():
    """Kolki naroznikowe korpusu (bok<->tyl, front<->bok) - runda 9.2.

    drawer_corner_dowel_positions()/drawer_front_dowel_positions() zwracaja
    punkty dla WSZYSTKICH szesciu par naraz (jak runner_positions()) - tu
    filtrujemy do samej pary (LI, BAY) po zakresie X (swiatlo komory) i Z
    (wysokosc korpusu tej konkretnej pary), tym samym schematem co
    runner_points_for_cell()."""
    x0, x1, z0, z1 = m._cell_opening(LI, BAY, P, D)
    z_off = P["PLINTH_H"]
    bz0 = z0 + P["DRAWER_BOX_Z"] + z_off
    bz1 = bz0 + P["DRAWER_BOX_H"]
    pts = m.drawer_corner_dowel_positions() + m.drawer_front_dowel_positions()
    return [pt for pt in pts if x0 - 1e-6 <= pt[0] <= x1 + 1e-6 and bz0 - 1e-6 <= pt[2] <= bz1 + 1e-6]


# ================================================================ payload 3D

KIND_META = {
    "front": ("Front", (198, 156, 104)),
    "side": ("Boki", (216, 186, 138)),
    "back": ("Tyl", (176, 140, 96)),
    "bottom": ("Dno", (150, 121, 80)),
    "gable-ref": ("Lico pionow (odniesienie)", (90, 100, 108)),
    "drill-corpus": ("Wiercenie - lico pionu", (44, 129, 84)),
    "drill-drawer": ("Wiercenie - bok szuflady", (198, 76, 56)),
    "drill-dowel": ("Kolki naroznikowe", (60, 140, 200)),
}

# qty_group -> kind, nie nazwa Part - runda 9.2 rozbila boki/tyl na pasma
# (rowek pod dno, patrz _build_drawers) wiec nazwy Part nie sa juz stale
# ("drawer-00-side-L-gv" itd.), ale qty_group zostaje ten sam
QTY_GROUP_KIND = {
    "drawer-front": "front",
    "drawer-side": "side",
    "drawer-back": "back",
    "drawer-bottom": "bottom",
}


def parts_payload():
    buckets = {}

    def add(kind, verts, tris):
        b = buckets.setdefault(kind, {"v": [], "t": []})
        base = len(b["v"]) // 3
        for x, y, z in verts:
            b["v"] += [round(x, 1), round(y, 1), round(z, 1)]
        for a, c, d in tris:
            b["t"] += [base + a, base + c, base + d]

    for part in drawer_parts():
        add(QTY_GROUP_KIND[part.qty_group], *part.triangles())

    # lico pionow jako cienkie plyty odniesienia - pokazuja gdzie w bryle
    # regalu wypadaja wkrety "corpus", bez rysowania calego korpusu
    x0, x1, z0, z1 = m._cell_opening(LI, BAY, P, D)
    z_off = P["PLINTH_H"]
    ref_t = 6.0
    add("gable-ref", *_box_mesh(x0 - ref_t, 0.0, z0 + z_off, x0, P["D"] - P["BACK"], z1 + z_off))
    add("gable-ref", *_box_mesh(x1, 0.0, z0 + z_off, x1 + ref_t, P["D"] - P["BACK"], z1 + z_off))

    marker_s = 12.0
    for x, y, z, side in runner_points_for_cell():
        kind = "drill-corpus" if side == "corpus" else "drill-drawer"
        add(kind, *_cube_mesh(x, y, z, marker_s))

    dowel_s = 10.0
    for x, y, z, side in dowel_points_for_cell():
        add("drill-dowel", *_cube_mesh(x, y, z, dowel_s))

    return buckets


# ================================================================ SVG - rozstaw wiercenia

def view_drill_pattern():
    """Elewacja boczna (Y poziomo = glab, Z pionowo lokalnie w obrebie boku
    szuflady/lica pionu na tej wysokosci) - rozstaw 3 wkretow.

    Lokalny uklad: 0 = dol komory szuflady, box_h = gora - bez offsetu
    cokolu/poziomu, bo to i tak ten sam wzor na kazdej z szesciu par.
    Corpus i drawer maja te sama (Y, Z) - roznia sie tylko X (ktore lico) -
    wiec jeden rysunek pokazuje wzor obowiazujacy jednoczesnie dla lica
    pionu i dla boku szuflady.
    """
    Dp = P["D"]
    box_h = P["DRAWER_BOX_H"]
    top, bot = 0.0, box_h    # SVG y rosnie w dol - "top" (gora komory) = mala wartosc
    zc = box_h / 2.0

    g = [pv.rect(0, top, Dp, bot, "var(--ply)")]
    ys = P["RUNNER_SCREW_Y"]
    for y in ys:
        g.append(pv.line(y, top, y, bot, pv.ACC, 1.0, dash="8 6"))
        g.append('<circle cx="%.2f" cy="%.2f" r="7" fill="var(--drill)" stroke="none"/>'
                  % (y, zc))
    g.append(pv.dim_h(0, ys[0], top + 30, "%.0f" % ys[0]))
    g.append(pv.dim_h(ys[0], ys[1], top + 30, "%.0f" % (ys[1] - ys[0])))
    g.append(pv.dim_h(ys[1], ys[2], top + 30, "%.0f" % (ys[2] - ys[1])))
    g.append(pv.dim_h(0, Dp, top + 80, "%.0f gl." % Dp))
    g.append(pv.dim_v(bot, top, -40, "%.0f" % box_h))
    return (pv.svg_open("-90 -40 560 380", "Rozstaw wiercenia") + "".join(g) + "</svg>")


# ================================================================ HTML

def build_html():
    payload = parts_payload()

    x0, x1, z0, z1 = m._cell_opening(LI, BAY, P, D)
    z_off = P["PLINTH_H"]
    ref_t = 6.0
    bbox = [x0 - ref_t, 0.0, z0 + z_off - 10, x1 + ref_t, P["D"], z1 + z_off + 10]

    kinds = {k: {"c": list(v[1])} for k, v in KIND_META.items()}
    js = (pv.JS.replace("__PARTS__", json.dumps(payload, separators=(",", ":")))
                .replace("__KINDS__", json.dumps(kinds, separators=(",", ":")))
                .replace("__BBOX__", json.dumps(bbox)))

    layer_btns = "".join(
        '<button type="button" data-kind="%s" aria-pressed="true">'
        '<span class="swatch" style="background:rgb(%d,%d,%d)"></span>%s</button>'
        % (k, v[1][0], v[1][1], v[1][2], v[0]) for k, v in KIND_META.items())

    rows_html = []
    for q in drawer_parts():
        b = q.bbox()
        dd = sorted([b[3] - b[0], b[4] - b[1], b[5] - b[2]], reverse=True)
        rows_html.append(
            "<tr><td>%s</td><td class='n'>%.0f &times; %.0f</td>"
            "<td class='n'>%.0f mm</td><td class='d'>%s</td></tr>"
            % (q.name, dd[0], dd[1], q.thickness, q.material))
    table = ("<div class='tw'><table><thead><tr><th>Element</th><th>Wymiar</th>"
             "<th>Grubosc</th><th>Material</th></tr></thead><tbody>%s</tbody></table></div>"
             % "".join(rows_html))

    runs = runner_points_for_cell()
    drill_rows = "".join(
        "<tr><td>%s</td><td class='n'>%.1f</td><td class='n'>%.1f</td><td class='n'>%.1f</td></tr>"
        % ({"corpus": "lico pionu", "drawer": "bok szuflady"}[side], x, y, z)
        for x, y, z, side in sorted(runs, key=lambda r: (r[3], r[1])))
    drill_table = ("<div class='tw'><table><thead><tr><th>Strona</th>"
                   "<th>X (mm)</th><th>Y - w glab (mm)</th><th>Z (mm, od podlogi)</th>"
                   "</tr></thead><tbody>%s</tbody></table></div>" % drill_rows)

    return """<title>Regal R150 &mdash; szuflada, szczegol</title>
<style>%s</style>
<div class="wrap">

<header>
  <p class="eyebrow">CNC Furniture Studio &middot; runda 9.2 &middot; szczegol szuflady</p>
  <h1>Szuflada &mdash; konstrukcja i wiercenie pod Blum TANDEM 562H</h1>
  <p class="lede">Jedna reprezentatywna szuflada (poziom %d, przeslo %d) - wszystkie
  szesc szuflad w regale ma identyczna geometrie, rozni je tylko polozenie w bryle.
  Dno wsuniete w prawdziwy rowek (3 strony: oba boki + tyl, 6 mm gleboko) - nie
  tylko oparte o krawedzie. Naroznik bok&harr;tyl i front&harr;bok: kolki + klej
  (kazdy bok/tyl to w modelu 3 sklejone pasma - pelne/rowek/pelne - fizycznie
  jedna deska). Plus 12 punktow wiercenia pod wkrety mocujace prowadnice: 6 w
  lico sasiadujacych pionow ("corpus"), 6 w bok korpusu szuflady ("drawer").
  Szare plyty w podgladzie 3D to fragment lica pionow - odniesienie, nie czesc
  szuflady.</p>
</header>

<section>
  <div class="hdr"><h2><span class="num">01</span>Bryla</h2>
  <p class="sub">Przeciagnij, zeby obrocic. Kolko myszy przybliza. Wylacz „Lico pionow",
  zeby zobaczyc sama szuflade bez odniesienia.</p></div>
  <div class="viewer">
    <canvas id="cv"></canvas>
    <div class="hud">Szuflada &middot; 1:2</div>
    <div class="readout" id="ro"></div>
  </div>
  <div class="bar">
    <button type="button" data-view="-32,14">Aksonometria</button>
    <button type="button" data-view="0,0">Przod</button>
    <button type="button" data-view="90,0">Bok</button>
    <button type="button" data-view="0,88">Gora</button>
    <span class="sep"></span>
    %s
  </div>
</section>

<section>
  <div class="hdr"><h2><span class="num">02</span>Rozstaw wiercenia</h2>
  <p class="sub">Widok z boku (glab &times; wysokosc komory). Ten sam rozstaw trzech
  wkretow powtarza sie identycznie na licu pionu i na boku szuflady - rozni je tylko
  wspolrzedna X (ktore lico), niewidoczna w tym rzucie.</p></div>
  <div class="draw"><div class="wide"><div class="sheet"><h3>3 wkrety na strone, na pare szuflady</h3>
  %s</div></div></div>
</section>

<section>
  <div class="hdr"><h2><span class="num">03</span>Zlacze korpusu (runda 9.2)</h2>
  <p class="sub">Klient: „nie widze zadnego rowka ani polaczen dla spodu szuflady" -
  pierwsza wersja rzeczywiscie nie miala zamodelowanego zlacza. Poprawione:</p></div>
  <div class="notes">
    <div class="note"><span class="tag i">rowek</span><p><b>Dno wsuniete w rowek,
    3 strony (oba boki + tyl).</b><span class="why">Rowek 6 mm gleboko, %.0f mm od
    dolu boku/tylu, zostawia scianke %.0f mm materialu. Kazdy bok/tyl to w modelu
    3 sklejone pasma w pionie (pelne / rowek / pelne) - fizycznie jedna deska,
    frezowana jednym przejsciem wraz z reszta konturu. Przod bez rowka - dno konczy
    sie dokladnie w licu frontu, tam trzymaja je kolki nizej.</span></p></div>
    <div class="note"><span class="tag i">kolki</span><p><b>Naroznik bok&harr;tyl:
    kolki Ø%.0f + klej, 2 na naroznik.</b><span class="why">Wiercone poziomo od
    zewnetrznego lica boku w material tylu, slepy otwor %.0f mm. Korpus szuflady,
    w odroznieniu od korpusu glownego regalu, nie jest rozkladany wielokrotnie -
    klej + kolek to prostsze, wystarczajace zlacze (nie mimosrod/sruba jak gdzie
    indziej w meblu).</span></p></div>
    <div class="note"><span class="tag i">kolki</span><p><b>Naroznik front&harr;bok:
    kolki Ø%.0f + klej, 2 na bok.</b><span class="why">Wiercone od tylnego
    (niewidocznego) lica frontu w material boku - nie przechodza na wylot, bez
    sladu na licu widocznym.</span></p></div>
  </div>
</section>

<section>
  <div class="hdr"><h2><span class="num">04</span>Elementy szuflady</h2></div>
  %s
</section>

<section>
  <div class="hdr"><h2><span class="num">05</span>Wspolrzedne wiercenia (ta para)</h2>
  <p class="sub">Uklad wspolrzednych calego regalu (patrz preview.html): X wzdluz
  szerokosci, Y w glab, Z od podlogi. 12 punktow - 6 „lico pionu" (nawiercane w
  sasiadujace piony), 6 „bok szuflady" (nawiercane w korpus szuflady).</p></div>
  %s
</section>

<footer class="foot">Regal R150 &middot; runda 9.2 &middot; wygenerowano z
design/drawer_detail_gen.py (ta sama geometria co design/shelf_model.py,
zero recznego przepisywania wymiarow)</footer>
</div>
<script>%s</script>
""" % (pv.CSS, LI, BAY, layer_btns, view_drill_pattern(),
       P["DRAWER_GROOVE_MARGIN"], P["T"] - P["DRAWER_GROOVE_DEPTH"],
       P["DRAWER_DOWEL_D"], P["DRAWER_DOWEL_DEPTH"], P["DRAWER_DOWEL_D"],
       table, drill_table, js)


def main():
    html = build_html()
    with open(OUT, "w") as f:
        f.write(html)
    print("zapisano drawer-detail.html (%d kB)" % (len(html) // 1000))


if __name__ == "__main__":
    main()
