"""Materiały proceduralne (Cycles + EEVEE) do wideo promo regału ze sklejki brzozowej.

Wszystko proceduralne – brak zewnętrznych tekstur. Kompatybilne z Blenderem 4.2+ / 5.x.

Najważniejszy materiał: `plywood()` – sklejka brzozowa olejowana:
  * lico: kremowo‑miodowa brzoza (albedo ~#E3CDA6–#D8BE92), falista figura rotary‑cut, drobne pory,
    zmiana tonu między arkuszami (losowo per obiekt), satynowy połysk oleju (roughness ~0,4 + lekki coat,
    anizotropia wzdłuż usłojenia);
  * krawędź: warstwy forniru (18 mm = 13 warstw ~1,38 mm), naprzemiennie jasne (wzdłużne) i ciemniejsze
    (poprzeczne, czoło włókien), ciemne spoiny klejowe, lekko nierówne grubości i faliste granice warstw.

Konwencja geometrii (patrz build_scene.part_mesh): siatka elementu w układzie lokalnym, oś Z = grubość
(0..t), UV = (wzdłuż usłojenia, w poprzek) w metrach, z przesunięciem losowym per element.
"""
from __future__ import annotations

import math

import bpy


# --------------------------------------------------------------------------- narzędzia
def srgb_to_lin(c):
    c = c / 255.0 if c > 1.0 else c
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h, a=1.0):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (a,)


def kelvin_rgb(k):
    """Przybliżenie barwy ciała doskonale czarnego (Tanner Helland) -> RGB liniowe, znormalizowane."""
    t = k / 100.0
    if t <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(t) - 161.1195681661
        b = 0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        b = 255.0
    rgb = [srgb_to_lin(max(0.0, min(255.0, v)) / 255.0) for v in (r, g, b)]
    m = max(rgb)
    return tuple(v / m for v in rgb)


class NB:
    """Mały pomocnik do budowania drzew węzłów."""

    def __init__(self, nt):
        self.nt = nt
        self.x = 0

    def n(self, typ, loc=(0, 0), **kw):
        node = self.nt.nodes.new(typ)
        node.location = loc
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    def link(self, a, b):
        self.nt.links.new(a, b)

    def math(self, op, a, b=None, loc=(0, 0), clamp=False):
        m = self.n("ShaderNodeMath", loc, operation=op)
        m.use_clamp = clamp
        self._feed(m.inputs[0], a)
        if b is not None:
            self._feed(m.inputs[1], b)
        return m.outputs[0]

    def vmath(self, op, a, b=None, loc=(0, 0)):
        m = self.n("ShaderNodeVectorMath", loc, operation=op)
        self._feed(m.inputs[0], a)
        if b is not None:
            self._feed(m.inputs[1], b)
        return m.outputs[0] if op not in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else m.outputs["Value"]

    def _feed(self, sock, v):
        if hasattr(v, "is_linked") or hasattr(v, "links"):
            self.nt.links.new(v, sock)
        else:
            sock.default_value = v

    def noise(self, vec, scale=1.0, detail=2.0, rough=0.5, distortion=0.0, dims="3D", loc=(0, 0)):
        t = self.n("ShaderNodeTexNoise", loc)
        try:
            t.noise_dimensions = dims
        except Exception:
            pass
        if vec is not None:
            self.link(vec, t.inputs["Vector"])
        if dims == "4D" and "W" in t.inputs:
            pass
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough
        t.inputs["Distortion"].default_value = distortion
        return t

    def ramp(self, fac, stops, loc=(0, 0), interp="LINEAR"):
        r = self.n("ShaderNodeValToRGB", loc)
        r.color_ramp.interpolation = interp
        els = r.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, (pos, col) in zip(els, stops):
            e.position = pos
            e.color = col if len(col) == 4 else (*col, 1.0)
        self._feed(r.inputs[0], fac)
        return r.outputs[0]

    def mix(self, fac, a, b, loc=(0, 0), blend="MIX"):
        m = self.n("ShaderNodeMix", loc, data_type="RGBA")
        m.blend_type = blend
        self._feed(m.inputs[0], fac)
        self._feed(m.inputs[6], a)
        self._feed(m.inputs[7], b)
        return m.outputs[2]

    def mixf(self, fac, a, b, loc=(0, 0)):
        m = self.n("ShaderNodeMix", loc, data_type="FLOAT")
        self._feed(m.inputs[0], fac)
        self._feed(m.inputs[2], a)
        self._feed(m.inputs[3], b)
        return m.outputs[0]

    def maprange(self, v, a0, a1, b0=0.0, b1=1.0, loc=(0, 0), interp="LINEAR", clamp=True):
        m = self.n("ShaderNodeMapRange", loc, interpolation_type=interp)
        m.clamp = clamp
        self._feed(m.inputs[0], v)
        m.inputs[1].default_value = a0
        m.inputs[2].default_value = a1
        m.inputs[3].default_value = b0
        m.inputs[4].default_value = b1
        return m.outputs[0]

    def combine(self, x, y, z, loc=(0, 0)):
        c = self.n("ShaderNodeCombineXYZ", loc)
        for i, v in enumerate((x, y, z)):
            self._feed(c.inputs[i], v)
        return c.outputs[0]

    def separate(self, v, loc=(0, 0)):
        s = self.n("ShaderNodeSeparateXYZ", loc)
        self.link(v, s.inputs[0])
        return s.outputs


def new_material(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True          # w 5.x zawsze True (deprecated) – bezpiecznie ignorujemy
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, NB(nt)


def principled(nb, loc=(600, 0)):
    b = nb.n("ShaderNodeBsdfPrincipled", loc)
    return b


def set_in(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def out_node(nb, shader, loc=(1000, 0)):
    o = nb.n("ShaderNodeOutputMaterial", loc)
    nb.link(shader, o.inputs["Surface"])
    return o


# --------------------------------------------------------------------------- sklejka brzozowa
BIRCH = dict(
    face_light=hex_lin("E6D1AA"),   # jasne partie lica (po oleju)
    face_mid=hex_lin("DCC59C"),
    face_dark=hex_lin("CDB084"),    # ciemniejsze pasma figury
    pore=hex_lin("B8955F"),         # pory / smugi
    ply_light=hex_lin("E2C99C"),    # warstwa wzdłużna na krawędzi
    ply_dark=hex_lin("B48A57"),     # warstwa poprzeczna (czoło włókien) – wyraźnie ciemniejsza
    glue=hex_lin("6B4A2A"),         # spoina klejowa
)


def plywood(name="Sklejka_brzoza_18", t_mm=18.0, plies=13, tint=(1.0, 1.0, 1.0), face_rough=0.40,
            coat=0.12, anis=0.25, edge_contrast=1.0, variation=1.0, uv_name="UVMap", grade="BB",
            per_object_pattern=True):
    """Sklejka brzozowa olejowana. `tint` mnoży kolor (np. fronty minimalnie jaśniejsze),
    `variation` – siła różnic tonu między arkuszami, `grade` "BB" (lica) / "CP" (plecy – więcej plam),
    `per_object_pattern=False` – figura zależy tylko od UV (fronty z UV w układzie świata = ciągłe usłojenie
    przez wszystkie fronty, jak fornir z jednego arkusza)."""
    m, nt, nb = new_material(name)
    ply = t_mm / plies * 0.001
    tc = nb.n("ShaderNodeTexCoord", (-2200, 0))
    uv = nb.n("ShaderNodeUVMap", (-2200, -300))
    uv.uv_map = uv_name
    oi = nb.n("ShaderNodeObjectInfo", (-2200, 300))
    rnd = oi.outputs["Random"]
    pr = rnd if per_object_pattern else 0.0

    # ---------------- lico (UV: x = wzdłuż usłojenia, y = w poprzek; metry)
    uvs = nb.separate(uv.outputs["UV"], (-2000, -300))
    g, c = uvs[0], uvs[1]
    # losowe przesunięcie w obrębie "arkusza" – każdy element inny fragment fornira
    g2 = nb.math("ADD", g, nb.math("MULTIPLY", pr, 37.0), (-1800, -200))
    c2 = nb.math("ADD", c, nb.math("MULTIPLY", pr, 11.0), (-1800, -350))
    # wektor anizotropowy: figura rozciągnięta wzdłuż usłojenia
    v_fig = nb.combine(nb.math("MULTIPLY", g2, 0.9), nb.math("MULTIPLY", c2, 9.0), pr, (-1600, -250))
    warp = nb.noise(v_fig, scale=1.6, detail=4.0, rough=0.55, loc=(-1400, -150))
    # figura rotary-cut: faliste pasma (fala wzdłuż c, zniekształcona szumem)
    band_c = nb.math("ADD", nb.math("MULTIPLY", c2, 38.0), nb.math("MULTIPLY", warp.outputs["Fac"], 3.2),
                     (-1200, -250))
    band_g = nb.math("MULTIPLY", g2, 1.3, (-1200, -400))
    band = nb.math("SINE", nb.math("ADD", band_c, nb.math("SINE", band_g)), loc=(-1000, -250))
    band01 = nb.maprange(band, -1.0, 1.0, 0.0, 1.0, (-850, -250))
    # "płomienie": dodatkowa miękka modulacja z szumu o niskiej częstotliwości
    flame = nb.noise(nb.combine(nb.math("MULTIPLY", g2, 2.5), nb.math("MULTIPLY", c2, 14.0), pr),
                     scale=1.2, detail=2.0, rough=0.5, loc=(-1000, -500))
    fig = nb.math("MULTIPLY", band01, nb.maprange(flame.outputs["Fac"], 0.35, 0.7, 0.25, 1.0), (-700, -300))
    # drobne pory / smugi wzdłuż włókien
    v_pore = nb.combine(nb.math("MULTIPLY", g2, 6.0), nb.math("MULTIPLY", c2, 700.0), 0.0, (-1200, -700))
    pores = nb.noise(v_pore, scale=1.0, detail=3.0, rough=0.6, loc=(-1000, -750))
    pore_m = nb.maprange(pores.outputs["Fac"], 0.58, 0.78, 0.0, 1.0, (-800, -750))
    v_fine = nb.combine(nb.math("MULTIPLY", g2, 40.0), nb.math("MULTIPLY", c2, 2500.0), 0.0, (-1200, -950))
    fine = nb.noise(v_fine, scale=1.0, detail=1.0, loc=(-1000, -950))
    fine_m = nb.maprange(fine.outputs["Fac"], 0.3, 0.75, 0.0, 1.0, (-800, -950))

    face = nb.mix(fig, BIRCH["face_light"], BIRCH["face_dark"], (-500, -200))
    face = nb.mix(nb.math("MULTIPLY", fine_m, 0.25), face, BIRCH["face_mid"], (-350, -300))
    face = nb.mix(nb.math("MULTIPLY", pore_m, 0.45), face, BIRCH["pore"], (-200, -350))
    if grade == "CP":
        spots = nb.noise(nb.combine(nb.math("MULTIPLY", g2, 3.0), nb.math("MULTIPLY", c2, 8.0), rnd),
                         scale=3.0, detail=3.0, loc=(-500, -600))
        sp = nb.maprange(spots.outputs["Fac"], 0.62, 0.72, 0.0, 0.35, (-350, -600))
        face = nb.mix(sp, face, hex_lin("A88456"), (-200, -500))

    # ---------------- krawędź (Object: z = grubość 0..t)
    obj = nb.separate(tc.outputs["Object"], (-2000, 400))
    ox, oy, oz = obj[0], obj[1], obj[2]
    # współrzędna wzdłuż krawędzi (x+y wystarczy do falowania)
    along = nb.math("ADD", ox, oy, (-1800, 550))
    # nierówne grubości warstw: wolne zniekształcenie z (stałe na całej długości krawędzi) + falowanie granic
    zn = nb.noise(nb.combine(nb.math("MULTIPLY", oz, 900.0), rnd, 0.0), scale=1.0, detail=1.0,
                  loc=(-1700, 300))
    wav = nb.noise(nb.combine(nb.math("MULTIPLY", along, 9.0), nb.math("MULTIPLY", oz, 120.0),
                              nb.math("MULTIPLY", rnd, 5.0)), scale=1.0, detail=3.0, loc=(-1700, 600))
    zw = nb.math("ADD", oz, nb.math("MULTIPLY", nb.math("SUBTRACT", zn.outputs["Fac"], 0.5), ply * 0.45),
                 (-1450, 350))
    zw = nb.math("ADD", zw, nb.math("MULTIPLY", nb.math("SUBTRACT", wav.outputs["Fac"], 0.5), ply * 0.18),
                 (-1300, 400))
    pz = nb.math("DIVIDE", zw, ply, (-1150, 400))
    k = nb.math("FLOOR", pz, loc=(-1000, 500))
    f = nb.math("FRACT", pz, loc=(-1000, 350))
    parity = nb.math("MODULO", k, 2.0, (-850, 500))   # 0 = warstwa wzdłużna (jasna), 1 = poprzeczna
    parity = nb.math("ABSOLUTE", parity, loc=(-720, 500))
    # losowy ton każdej warstwy
    wn = nb.n("ShaderNodeTexWhiteNoise", (-850, 650))
    try:
        wn.noise_dimensions = "2D"
    except Exception:
        pass
    nb.link(nb.combine(k, nb.math("MULTIPLY", rnd, 13.0), 0.0), wn.inputs["Vector"])
    # spoina: odległość do granicy warstwy
    dist = nb.math("MINIMUM", f, nb.math("SUBTRACT", 1.0, f), (-850, 300))
    glue_w = 0.075 / (t_mm / plies)      # ~0,075 mm w jednostkach warstwy
    glue = nb.maprange(dist, glue_w * 0.4, glue_w * 1.6, 1.0, 0.0, (-700, 300), interp="SMOOTHSTEP")
    # tekstura wewnątrz warstwy: wzdłużne smugi (jasne) / punktowe pory czoła (ciemne)
    streak = nb.noise(nb.combine(nb.math("MULTIPLY", along, 25.0), nb.math("MULTIPLY", oz, 3000.0), rnd),
                      scale=1.0, detail=2.0, loc=(-850, 850))
    endg = nb.noise(tc.outputs["Object"], scale=2200.0, detail=1.0, loc=(-850, 1050))
    tex = nb.mixf(parity, streak.outputs["Fac"], endg.outputs["Fac"], (-600, 900))
    tex_m = nb.maprange(tex, 0.35, 0.75, -1.0, 1.0, (-450, 900))

    ply_col = nb.mix(parity, BIRCH["ply_light"], BIRCH["ply_dark"], (-450, 600))
    # jasność warstwy: ±6 % + tekstura
    var = nb.math("ADD", nb.math("MULTIPLY", nb.math("SUBTRACT", wn.outputs["Value"], 0.5), 0.14),
                  nb.math("MULTIPLY", tex_m, 0.06), (-300, 800))
    var = nb.math("ADD", var, 1.0, (-150, 800))
    ply_col = nb.mix(1.0, ply_col, nb.combine(var, var, var), (-150, 600), blend="MULTIPLY")
    edge = nb.mix(nb.math("MULTIPLY", glue, 0.85 * edge_contrast), ply_col, BIRCH["glue"], (0, 500))

    # ---------------- maska lico / krawędź (|N.z| w układzie obiektu, miękko na fazie)
    nz = nb.separate(tc.outputs["Normal"], (-700, 100))[2]
    is_face = nb.maprange(nb.math("ABSOLUTE", nz), 0.55, 0.85, 0.0, 1.0, (-500, 100), interp="SMOOTHSTEP")

    # ton arkusza: różnice między elementami (subtelne)
    sheet = nb.math("ADD", 1.0, nb.math("MULTIPLY", nb.math("SUBTRACT", rnd, 0.5), 0.07 * variation), (-300, 200))
    sheet_h = nb.combine(sheet, nb.math("ADD", 1.0, nb.math("MULTIPLY", nb.math("SUBTRACT", rnd, 0.5),
                                                              0.09 * variation)),
                         nb.math("ADD", 1.0, nb.math("MULTIPLY", nb.math("SUBTRACT", rnd, 0.5), 0.14 * variation)),
                         (-150, 200))
    face = nb.mix(1.0, face, sheet_h, (0, -100), blend="MULTIPLY")
    tint_v = (*tint, 1.0)
    col = nb.mix(is_face, edge, face, (200, 200))
    col = nb.mix(1.0, col, tint_v, (350, 200), blend="MULTIPLY")

    # ---------------- roughness / bump
    r_face = nb.math("ADD", face_rough, nb.math("MULTIPLY", pore_m, 0.10), (0, -600))
    r_edge = nb.math("ADD", 0.56, nb.math("MULTIPLY", tex_m, 0.05), (0, -750))
    rough = nb.mixf(is_face, r_edge, r_face, (200, -650))

    h_face = nb.math("ADD", nb.math("MULTIPLY", pore_m, -1.0), nb.math("MULTIPLY", fine_m, -0.25), (0, -950))
    h_edge = nb.math("ADD", nb.math("MULTIPLY", glue, -1.0), nb.math("MULTIPLY", tex_m, 0.35), (0, -1100))
    h = nb.mixf(is_face, h_edge, h_face, (200, -1000))
    bump = nb.n("ShaderNodeBump", (400, -950))
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.00004
    nb.link(h, bump.inputs["Height"])

    tan = nb.n("ShaderNodeTangent", (200, -1300), direction_type="UV_MAP")
    tan.uv_map = uv_name

    b = principled(nb, (650, 0))
    nb.link(col, b.inputs["Base Color"])
    nb.link(rough, b.inputs["Roughness"])
    nb.link(bump.outputs[0], b.inputs["Normal"])
    set_in(b, "Specular IOR Level", 0.5)
    set_in(b, "Coat Weight", 0.0)
    coat_w = nb.math("MULTIPLY", is_face, coat, (400, -300))
    nb.link(coat_w, b.inputs["Coat Weight"])
    set_in(b, "Coat Roughness", 0.32)
    set_in(b, "Coat IOR", 1.48)
    if "Anisotropic" in b.inputs:
        nb.link(nb.math("MULTIPLY", is_face, anis, (400, -450)), b.inputs["Anisotropic"])
        nb.link(tan.outputs[0], b.inputs["Tangent"])
    out_node(nb, b.outputs[0], (1000, 0))
    m.diffuse_color = (*BIRCH["face_mid"][:3], 1.0)
    m["kind"] = "plywood"
    return m


# --------------------------------------------------------------------------- okucia, gałki
def metal(name, color=(0.80, 0.81, 0.83), rough=0.26, aniso=0.0, rough_var=0.06):
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-900, 0))
    nz = nb.noise(tc.outputs["Object"], scale=900.0, detail=2.0, loc=(-700, 0))
    r = nb.maprange(nz.outputs["Fac"], 0.3, 0.7, rough - rough_var, rough + rough_var, (-450, 0))
    b = principled(nb)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = 1.0
    nb.link(r, b.inputs["Roughness"])
    if aniso and "Anisotropic" in b.inputs:
        b.inputs["Anisotropic"].default_value = aniso
    out_node(nb, b.outputs[0])
    m.diffuse_color = (*color, 1)
    return m


def plastic(name, color, rough=0.45, sss=0.0):
    m, nt, nb = new_material(name)
    b = principled(nb)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if sss:
        set_in(b, "Subsurface Weight", sss)
        set_in(b, "Subsurface Scale", 0.002)
    out_node(nb, b.outputs[0])
    m.diffuse_color = (*color, 1)
    return m


def knob_pla(name="Galka_PLA_bialy", layer_mm=0.2, axis="Z"):
    """Biały matowy PLA/PETG z drukarki 3D: lekki subsurface, linie warstw co 0,2 mm wzdłuż osi gałki
    (lokalna oś Z obiektu = oś druku), delikatna nierówność ekstruzji."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-1200, 0))
    o = nb.separate(tc.outputs["Object"], (-1000, 0))
    zc = o[2] if axis == "Z" else o[1]
    # fala o okresie layer_mm
    ph = nb.math("MULTIPLY", zc, 2 * math.pi / (layer_mm * 0.001), (-800, 0))
    jitter = nb.noise(tc.outputs["Object"], scale=180.0, detail=2.0, loc=(-1000, -300))
    ph = nb.math("ADD", ph, nb.math("MULTIPLY", jitter.outputs["Fac"], 1.5), (-650, -100))
    wave = nb.math("SINE", ph, loc=(-500, 0))
    lines = nb.math("POWER", nb.math("ABSOLUTE", wave), 0.6, (-350, 0))
    bump = nb.n("ShaderNodeBump", (-100, -200))
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.00003
    nb.link(lines, bump.inputs["Height"])
    b = principled(nb)
    col = hex_lin("F2F0EA")
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = 0.42
    set_in(b, "Subsurface Weight", 0.35)
    set_in(b, "Subsurface Radius", (1.0, 0.9, 0.75))
    set_in(b, "Subsurface Scale", 0.0012)
    set_in(b, "Specular IOR Level", 0.45)
    nb.link(bump.outputs[0], b.inputs["Normal"])
    out_node(nb, b.outputs[0])
    m.diffuse_color = col
    return m


# --------------------------------------------------------------------------- otoczenie
def plaster(name="Sciana_tynk", color="E9E4DB", bump=0.12):
    """Ciepła biel / jasny greige, delikatna faktura tynku (mikro + makro nierówności)."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-1200, 0))
    big = nb.noise(tc.outputs["Object"], scale=0.9, detail=3.0, rough=0.55, loc=(-900, 200))
    mid = nb.noise(tc.outputs["Object"], scale=14.0, detail=4.0, rough=0.6, loc=(-900, 0))
    fine = nb.noise(tc.outputs["Object"], scale=260.0, detail=2.0, rough=0.7, loc=(-900, -200))
    base = hex_lin(color)
    v = nb.maprange(big.outputs["Fac"], 0.3, 0.7, 0.975, 1.02, (-650, 200))
    v2 = nb.maprange(mid.outputs["Fac"], 0.3, 0.7, 0.99, 1.01, (-650, 50))
    vv = nb.math("MULTIPLY", v, v2, (-500, 150))
    col = nb.mix(1.0, base, nb.combine(vv, vv, vv), (-300, 150), blend="MULTIPLY")
    h = nb.math("ADD", nb.math("MULTIPLY", mid.outputs["Fac"], 0.5), fine.outputs["Fac"], (-500, -150))
    bp = nb.n("ShaderNodeBump", (-250, -200))
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.0004
    nb.link(h, bp.inputs["Height"])
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    set_in(b, "Specular IOR Level", 0.3)
    nb.link(bp.outputs[0], b.inputs["Normal"])
    out_node(nb, b.outputs[0])
    m.diffuse_color = base
    return m


def microcement(name="Podloga_mikrocement", color="CFC6B8", rough=0.55):
    """Mikrocement: chmurkowe przetarcia, ślady pacy, satynowy połysk."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-1400, 0))
    co = tc.outputs["Object"]
    cloud = nb.noise(co, scale=0.7, detail=5.0, rough=0.6, loc=(-1100, 300))
    cloud2 = nb.noise(co, scale=3.5, detail=4.0, rough=0.6, distortion=0.6, loc=(-1100, 100))
    # ślady pacy – rozciągnięty szum w kilku kierunkach
    mp = nb.n("ShaderNodeMapping", (-1250, -200))
    mp.inputs["Scale"].default_value = (1.0, 7.0, 1.0)
    mp.inputs["Rotation"].default_value = (0, 0, 0.6)
    nb.link(co, mp.inputs["Vector"])
    trowel = nb.noise(mp.outputs[0], scale=2.5, detail=3.0, rough=0.5, loc=(-1100, -200))
    speck = nb.noise(co, scale=900.0, detail=1.0, loc=(-1100, -450))
    base = hex_lin(color)
    v = nb.maprange(cloud.outputs["Fac"], 0.3, 0.72, 0.90, 1.07, (-850, 300))
    v2 = nb.maprange(cloud2.outputs["Fac"], 0.35, 0.65, 0.96, 1.03, (-850, 100))
    v3 = nb.maprange(trowel.outputs["Fac"], 0.4, 0.62, 0.985, 1.02, (-850, -200))
    vv = nb.math("MULTIPLY", nb.math("MULTIPLY", v, v2), v3, (-650, 150))
    sp = nb.maprange(speck.outputs["Fac"], 0.68, 0.74, 1.0, 0.85, (-850, -450))
    vv = nb.math("MULTIPLY", vv, sp, (-500, 100))
    col = nb.mix(1.0, base, nb.combine(vv, vv, vv), (-350, 100), blend="MULTIPLY")
    r = nb.maprange(trowel.outputs["Fac"], 0.3, 0.7, rough - 0.12, rough + 0.1, (-650, -250))
    r = nb.math("ADD", r, nb.maprange(cloud2.outputs["Fac"], 0.3, 0.7, -0.06, 0.06), (-450, -250))
    bp = nb.n("ShaderNodeBump", (-300, -450))
    bp.inputs["Strength"].default_value = 0.08
    bp.inputs["Distance"].default_value = 0.0005
    nb.link(nb.math("ADD", trowel.outputs["Fac"], nb.math("MULTIPLY", speck.outputs["Fac"], 0.3)),
            bp.inputs["Height"])
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    nb.link(r, b.inputs["Roughness"])
    nb.link(bp.outputs[0], b.inputs["Normal"])
    set_in(b, "Coat Weight", 0.15)
    set_in(b, "Coat Roughness", 0.35)
    out_node(nb, b.outputs[0])
    m.diffuse_color = base
    return m


def oak_floor(name="Podloga_dab", plank_w=0.19, plank_l=1.9, color="C9A77C"):
    """Jasny dąb olejowany – deski z cegiełek (Brick), losowy ton desek, usłojenie."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-1600, 0))
    co = tc.outputs["Object"]
    s = nb.separate(co, (-1450, 0))
    # układ desek: x wzdłuż deski
    bx = nb.n("ShaderNodeTexBrick", (-1150, 200))
    bx.offset = 0.37
    bx.offset_frequency = 1
    bx.squash = 1.0
    bx.inputs["Scale"].default_value = 1.0
    bx.inputs["Mortar Size"].default_value = 0.0012
    bx.inputs["Mortar Smooth"].default_value = 0.3
    bx.inputs["Brick Width"].default_value = plank_l
    bx.inputs["Row Height"].default_value = plank_w
    bx.inputs["Color1"].default_value = (0, 0, 0, 1)
    bx.inputs["Color2"].default_value = (1, 1, 1, 1)
    nb.link(co, bx.inputs["Vector"])
    plank_rand = nb.separate(bx.outputs["Color"], (-950, 250))[0]
    v = nb.combine(nb.math("MULTIPLY", s[0], 2.0), nb.math("MULTIPLY", s[1], 45.0),
                   nb.math("MULTIPLY", plank_rand, 20.0), (-950, 0))
    grain = nb.noise(v, scale=3.0, detail=6.0, rough=0.6, distortion=0.4, loc=(-750, 0))
    rings = nb.n("ShaderNodeTexWave", (-750, -250), wave_type="BANDS", bands_direction="Y")
    rings.inputs["Scale"].default_value = 6.0
    rings.inputs["Distortion"].default_value = 6.0
    rings.inputs["Detail"].default_value = 3.0
    nb.link(v, rings.inputs["Vector"])
    base = hex_lin(color)
    g = nb.maprange(grain.outputs["Fac"], 0.3, 0.75, 0.84, 1.08, (-550, 0))
    rr = nb.maprange(rings.outputs["Fac"], 0.0, 1.0, 0.92, 1.03, (-550, -250))
    pr = nb.maprange(plank_rand, 0.0, 1.0, 0.86, 1.1, (-550, 250))
    vv = nb.math("MULTIPLY", nb.math("MULTIPLY", g, rr), pr, (-400, 0))
    col = nb.mix(1.0, base, nb.combine(vv, vv, nb.math("MULTIPLY", vv, 0.97)), (-250, 0), blend="MULTIPLY")
    mortar = nb.math("SUBTRACT", 1.0, bx.outputs["Fac"], (-700, 450))
    col = nb.mix(nb.math("MULTIPLY", mortar, 0.7), col, hex_lin("5A4632"), (-100, 100))
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    nb.link(nb.maprange(grain.outputs["Fac"], 0.3, 0.7, 0.42, 0.55), b.inputs["Roughness"])
    bp = nb.n("ShaderNodeBump", (-100, -300))
    bp.inputs["Strength"].default_value = 0.2
    bp.inputs["Distance"].default_value = 0.0004
    nb.link(nb.math("ADD", bx.outputs["Fac"], nb.math("MULTIPLY", grain.outputs["Fac"], 0.1)), bp.inputs["Height"])
    nb.link(bp.outputs[0], b.inputs["Normal"])
    out_node(nb, b.outputs[0])
    m.diffuse_color = base
    return m


def studio_backdrop(name="Studio_tlo", color="2A2724", rough=0.8):
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-800, 0))
    n = nb.noise(tc.outputs["Object"], scale=2.0, detail=3.0, loc=(-600, 0))
    v = nb.maprange(n.outputs["Fac"], 0.3, 0.7, 0.93, 1.06, (-400, 0))
    col = nb.mix(1.0, hex_lin(color), nb.combine(v, v, v), (-200, 0), blend="MULTIPLY")
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    out_node(nb, b.outputs[0])
    m.diffuse_color = hex_lin(color)
    return m


# --------------------------------------------------------------------------- rekwizyty
def ceramic(name, color="E8E1D4", rough=0.55, speckle=0.35, glaze=0.15, speck_col="6B5E50"):
    """Kamionka: matowe/satynowe szkliwo z kropkami (speckle)."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-1000, 0))
    vor = nb.n("ShaderNodeTexVoronoi", (-800, 100))
    vor.inputs["Scale"].default_value = 260.0
    nb.link(tc.outputs["Object"], vor.inputs["Vector"])
    big = nb.noise(tc.outputs["Object"], scale=25.0, detail=3.0, loc=(-800, -150))
    sp = nb.maprange(vor.outputs["Distance"], 0.0, 0.09, speckle, 0.0, (-600, 100))
    base = hex_lin(color)
    v = nb.maprange(big.outputs["Fac"], 0.3, 0.7, 0.95, 1.04, (-600, -150))
    col = nb.mix(1.0, base, nb.combine(v, v, v), (-400, -100), blend="MULTIPLY")
    col = nb.mix(sp, col, hex_lin(speck_col), (-250, 0))
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    nb.link(nb.maprange(big.outputs["Fac"], 0.3, 0.7, rough - 0.08, rough + 0.08), b.inputs["Roughness"])
    set_in(b, "Coat Weight", glaze)
    set_in(b, "Coat Roughness", 0.2)
    bp = nb.n("ShaderNodeBump", (-200, -350))
    bp.inputs["Strength"].default_value = 0.15
    bp.inputs["Distance"].default_value = 0.0003
    nb.link(big.outputs["Fac"], bp.inputs["Height"])
    nb.link(bp.outputs[0], b.inputs["Normal"])
    out_node(nb, b.outputs[0])
    m.diffuse_color = base
    return m


def cloth_cover(name, color, rough=0.75):
    """Okładka książki – płótno introligatorskie (drobny splot) / papier."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-900, 0))
    wv = nb.n("ShaderNodeTexWave", (-700, 100), wave_type="BANDS", bands_direction="X")
    wv.inputs["Scale"].default_value = 900.0
    nb.link(tc.outputs["Object"], wv.inputs["Vector"])
    wv2 = nb.n("ShaderNodeTexWave", (-700, -100), wave_type="BANDS", bands_direction="Z")
    wv2.inputs["Scale"].default_value = 900.0
    nb.link(tc.outputs["Object"], wv2.inputs["Vector"])
    n = nb.noise(tc.outputs["Object"], scale=40.0, detail=3.0, loc=(-700, -300))
    h = nb.math("ADD", nb.math("MULTIPLY", wv.outputs["Fac"], wv2.outputs["Fac"]), 0.0, (-500, 0))
    base = hex_lin(color)
    v = nb.maprange(n.outputs["Fac"], 0.3, 0.7, 0.93, 1.05, (-500, -300))
    col = nb.mix(1.0, base, nb.combine(v, v, v), (-300, -200), blend="MULTIPLY")
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    set_in(b, "Sheen Weight", 0.25)
    bp = nb.n("ShaderNodeBump", (-250, -450))
    bp.inputs["Strength"].default_value = 0.12
    bp.inputs["Distance"].default_value = 0.0001
    nb.link(h, bp.inputs["Height"])
    nb.link(bp.outputs[0], b.inputs["Normal"])
    out_node(nb, b.outputs[0])
    m.diffuse_color = base
    return m


def paper_block(name="Kartki"):
    """Blok kartek: kremowy papier z liniami kartek wzdłuż lokalnej osi X (grubość książki)."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-900, 0))
    wv = nb.n("ShaderNodeTexWave", (-700, 0), wave_type="BANDS", bands_direction="X")
    wv.inputs["Scale"].default_value = 3500.0
    wv.inputs["Distortion"].default_value = 2.0
    wv.inputs["Detail"].default_value = 2.0
    nb.link(tc.outputs["Object"], wv.inputs["Vector"])
    base = hex_lin("EDE6D6")
    col = nb.mix(nb.maprange(wv.outputs["Fac"], 0.0, 1.0, 0.0, 0.18), base, hex_lin("C9BEA8"), (-400, 0))
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    set_in(b, "Subsurface Weight", 0.1)
    set_in(b, "Subsurface Scale", 0.001)
    out_node(nb, b.outputs[0])
    m.diffuse_color = base
    return m


def leaf(name="Lisc_oliwka", color="5E6B4E", back="8C9A78"):
    """Liść: matowy wierzch + przeświecanie (translucent) – oliwka/eukaliptus, stonowana zieleń."""
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-900, 0))
    n = nb.noise(tc.outputs["Object"], scale=300.0, detail=3.0, loc=(-700, 0))
    base = hex_lin(color)
    v = nb.maprange(n.outputs["Fac"], 0.3, 0.7, 0.88, 1.1, (-500, 0))
    col = nb.mix(1.0, base, nb.combine(v, v, v), (-300, 0), blend="MULTIPLY")
    b = principled(nb, (0, 100))
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    set_in(b, "Sheen Weight", 0.3)
    tr = nb.n("ShaderNodeBsdfTranslucent", (0, -250))
    tr.inputs["Color"].default_value = hex_lin(back)
    mx = nb.n("ShaderNodeMixShader", (300, 0))
    mx.inputs[0].default_value = 0.25
    nb.link(b.outputs[0], mx.inputs[1])
    nb.link(tr.outputs[0], mx.inputs[2])
    out_node(nb, mx.outputs[0], (500, 0))
    m.diffuse_color = base
    return m


def bark(name="Galazka", color="6E5A45"):
    m, nt, nb = new_material(name)
    tc = nb.n("ShaderNodeTexCoord", (-700, 0))
    n = nb.noise(tc.outputs["Object"], scale=400.0, detail=4.0, loc=(-500, 0))
    col = nb.mix(n.outputs["Fac"], hex_lin(color), hex_lin("9A8670"), (-250, 0))
    b = principled(nb)
    nb.link(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    out_node(nb, b.outputs[0])
    m.diffuse_color = hex_lin(color)
    return m


def dark_inner(name="Ciemne_wnetrze", color="1A1714"):
    return plastic(name, hex_lin(color)[:3], rough=0.9)


def shadow_catcher_black(name="Czern"):
    return plastic(name, (0.01, 0.01, 0.01), rough=0.9)
