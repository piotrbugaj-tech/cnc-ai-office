#!/usr/bin/env python3
"""typo.py - typografia premium (research-brief 7.3/7.4): napisy, wymiary CAD i plansza koncowa
renderowane w Pillow (raqm: kerning) jako sekwencje PNG RGBA, nakladane w ffmpeg.

Fonty (SIL OFL): Inter Display (tytuly), Inter (drobny tekst), JetBrains Mono (CAD, opis).
Tracking = ulamek em (brief: -1 % -> -0.01, +24 % -> 0.24); kerning zachowany (pozycje z dlugosci prefiksu).
Ruch subpikselowy (transformacja afiniczna bicubic), easing ease-out cubic.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIRS = ['/usr/share/fonts/opentype/inter', '/usr/share/fonts/truetype/jetbrains-mono',
             os.path.join(HERE, 'fonts'), os.path.expanduser('~/Library/Fonts'), '/Library/Fonts',
             '/usr/share/fonts/truetype/dejavu']
FALLBACK = ['Inter-Regular', 'DejaVuSans']

STYLES = {
    '16x9': {
        'title': dict(font='InterDisplay-Light', size=60, tracking=-0.01, color='#24211E'),
        'title_light': dict(font='InterDisplay-Light', size=60, tracking=-0.01, color='#F6F2EA'),
        'cad': dict(font='JetBrainsMono-Regular', size=26, tracking=0.0, color='#24211E'),
        'end_name': dict(font='InterDisplay-Medium', size=120, tracking=0.24, color='#24211E'),
        'end_tag': dict(font='InterDisplay-Light', size=44, tracking=0.0, color='#24211E'),
        'end_desc': dict(font='JetBrainsMono-Regular', size=22, tracking=0.0, color='#6E655B'),
        'end_brand': dict(font='Inter-Medium', size=24, tracking=0.10, color='#24211E'),
    },
    '9x16': {
        'title': dict(font='InterDisplay-Light', size=72, tracking=-0.01, color='#24211E'),
        'title_light': dict(font='InterDisplay-Light', size=72, tracking=-0.01, color='#F6F2EA'),
        'cad': dict(font='JetBrainsMono-Regular', size=30, tracking=0.0, color='#24211E'),
        'end_name': dict(font='InterDisplay-Medium', size=140, tracking=0.24, color='#24211E'),
        'end_tag': dict(font='InterDisplay-Light', size=52, tracking=0.0, color='#24211E'),
        'end_desc': dict(font='JetBrainsMono-Regular', size=26, tracking=0.0, color='#6E655B'),
        'end_brand': dict(font='Inter-Medium', size=28, tracking=0.10, color='#24211E'),
    },
}
_FONT_CACHE = {}


def find_font(name):
    if os.path.isfile(os.path.expanduser(name)):
        return os.path.expanduser(name)
    for cand in [name] + FALLBACK:
        for d in FONT_DIRS:
            for ext in ('.otf', '.ttf'):
                p = os.path.join(d, cand + ext)
                if os.path.isfile(p):
                    if cand != name:
                        print(f'  [typo] brak fontu {name}, uzywam {cand}')
                    return p
    raise FileNotFoundError(name)


def font(name, size):
    key = (name, int(round(size)))
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(find_font(name), int(round(size)),
                                              layout_engine=ImageFont.Layout.RAQM)
    return _FONT_CACHE[key]


def hex_rgba(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def ease_out_cubic(u):
    u = np.clip(u, 0, 1)
    return 1 - (1 - u) ** 3


def text_image(text, style, scale=1.0, uppercase=False, leading=1.2):
    """Tekst (wiele linii) -> (RGBA, baseline pierwszej linii, cap height) z trackingiem i kerningiem."""
    st = dict(style)
    size = st['size'] * scale
    f = font(st['font'], size)
    track = st.get('tracking', 0.0) * size
    if uppercase or st.get('uppercase'):
        text = text.upper()
    lines = text.split('\n')
    asc, desc = f.getmetrics()
    lh = size * st.get('leading', leading)
    widths = []
    for ln in lines:
        widths.append(f.getlength(ln) + track * max(0, len(ln) - 1))
    W = int(np.ceil(max(widths) + size * 0.4)) + 4
    H = int(np.ceil(asc + desc + lh * (len(lines) - 1))) + 4
    col = hex_rgba(st.get('color', '#24211E'))
    im = Image.new('RGBA', (W, H), col[:3] + (0,))     # RGB = kolor tekstu takze w przezroczystych pikselach
    d = ImageDraw.Draw(im)
    pad = 2
    for li, ln in enumerate(lines):
        y = pad + li * lh
        x0 = pad
        if st.get('align') == 'center':
            x0 = pad + (max(widths) - widths[li]) / 2
        elif st.get('align') == 'right':
            x0 = pad + (max(widths) - widths[li])
        if abs(track) < 1e-6:
            d.text((x0, y), ln, font=f, fill=col)
        else:
            for i, ch in enumerate(ln):
                x = x0 + f.getlength(ln[:i]) + track * i
                d.text((x, y), ch, font=f, fill=col)
    try:
        cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    except Exception:  # noqa: BLE001
        cap = size * 0.72
    return im, pad + asc, cap, max(widths)


def _shift(im, dx, dy):
    return im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BICUBIC)


def _alpha(im, a):
    if a >= 0.999:
        return im
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge('RGBA', (r, g, b, al))


def render_title(spec, version, W, H, fps, out_dir, scale=1.0):
    """spec: text, style, x, y (srodek linii), align, f:[in,out] (klatki montazu), anim{in,out,rise},
    glow (bool). Zwraca dict(pattern, x, y, start_s, n)."""
    st = dict(STYLES[version].get(spec.get('style', 'title'), STYLES[version]['title']))
    st.update({k: spec[k] for k in ('font', 'size', 'tracking', 'color', 'align') if k in spec})
    img, base, cap, tw = text_image(spec['text'], st, scale, spec.get('uppercase', False))
    an = spec.get('anim', {})
    fin, fout, rise = int(an.get('in', 10)), int(an.get('out', 8)), float(an.get('rise', 12)) * scale
    f0, f1 = spec['f']
    n = int(round(f1 - f0))
    x = spec.get('x', 144)
    x = x * W if isinstance(x, float) and x <= 1 else x * scale
    yc = spec.get('y', H / 2)
    yc = yc * H if isinstance(yc, float) and yc <= 1 else yc * scale
    align = st.get('align', spec.get('align', 'left'))
    if align == 'center':
        x0 = x - tw / 2 - 2
    elif align == 'right':
        x0 = x - tw - 2
    else:
        x0 = x - 2
    y0 = yc - (base - cap / 2)                          # srodek wersalikow na yc
    glow = spec.get('glow', False)
    m = int(rise + 40 * scale) if glow else int(rise + 4)
    RW, RH = img.width + 2 * m, img.height + 2 * m
    canvas_base = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
    if glow:   # poswiata: rozmywamy tylko maske alfa (bez ciemnych obwodek od RGB=0 w przezroczystosci)
        mask = Image.new('L', (RW, RH), 0)
        ImageDraw.Draw(mask).ellipse([m * 0.4, m * 0.4, RW - m * 0.4, RH - m * 0.4],
                                     fill=int(255 * float(spec.get('glow_opacity', 0.35))))
        mask = mask.filter(ImageFilter.GaussianBlur(m * 0.45))
        canvas_base = Image.new('RGBA', (RW, RH), hex_rgba(spec.get('glow_color', '#EFEAE2'), 0))
        canvas_base.putalpha(mask)
    os.makedirs(out_dir, exist_ok=True)
    for i in range(n):
        a_in = ease_out_cubic((i + 1) / max(fin, 1)) if fin > 0 else 1.0
        a_out = 1.0 - ease_out_cubic((i - (n - fout) + 1) / max(fout, 1)) if (fout > 0 and i >= n - fout) else 1.0
        a = max(0.0, min(a_in, a_out))
        dy = rise * (1 - a_in)
        fr = canvas_base.copy()
        layer = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
        layer.paste(img, (m, m))
        layer = _shift(layer, 0, dy)
        fr = Image.alpha_composite(fr, layer)
        _alpha(fr, a).save(os.path.join(out_dir, f'{i:04d}.png'), compress_level=1)
    return dict(pattern=os.path.join(out_dir, '%04d.png'), x=int(round(x0 - m)), y=int(round(y0 - m)),
                start_s=f0 / fps, n=n)


# --------------------------------------------------------------------------
# wymiar CAD (S06): linia rysuje sie w 8 kl., kreski architektoniczne 45 st. 10 px, tekst po 4 kl.
# --------------------------------------------------------------------------
def render_dim(spec, version, W, H, fps, out_dir, scale=1.0):
    st = dict(STYLES[version]['cad'])
    p1 = np.array(spec['p1'], float) * scale
    p2 = np.array(spec['p2'], float) * scale
    f0, f1 = spec['f']
    n = int(round(f1 - f0))
    lw = max(1, int(round(2 * scale)))
    col = hex_rgba(st['color'])
    img, base, cap, tw = text_image(spec['text'], st, scale)
    lo = np.minimum(p1, p2) - 60 * scale
    hi = np.maximum(p1, p2) + 60 * scale
    tpos = np.array(spec.get('text_pos', ((p1 + p2) / 2 + np.array([12, -40]) * scale)), float)
    lo = np.minimum(lo, tpos - 10)
    hi = np.maximum(hi, tpos + np.array([tw + 20, img.height + 10]))
    ox, oy = int(lo[0]), int(lo[1])
    RW, RH = int(hi[0] - lo[0]), int(hi[1] - lo[1])
    os.makedirs(out_dir, exist_ok=True)
    fout = int(spec.get('out', 8))
    for i in range(n):
        fr = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
        d = ImageDraw.Draw(fr)
        u = ease_out_cubic((i + 1) / 8)
        a = p1 + (p2 - p1) * u
        d.line([tuple(p1 - [ox, oy]), tuple(a - [ox, oy])], fill=col, width=lw)
        if u >= 0.999:
            for p in (p1, p2):
                k = 5 * scale
                d.line([(p[0] - ox - k, p[1] - oy + k), (p[0] - ox + k, p[1] - oy - k)], fill=col, width=lw)
        ta = ease_out_cubic((i - 8 - 4 + 1) / 4) if i >= 12 else 0.0
        if ta > 0:
            fr.alpha_composite(_alpha(img, ta), (int(tpos[0] - ox), int(tpos[1] - oy)))
        if i >= n - fout:
            fr = _alpha(fr, 1 - ease_out_cubic((i - (n - fout) + 1) / fout))
        fr.save(os.path.join(out_dir, f'{i:04d}.png'), compress_level=1)
    return dict(pattern=os.path.join(out_dir, '%04d.png'), x=ox, y=oy, start_s=f0 / fps, n=n)


# --------------------------------------------------------------------------
# plansza koncowa (S10)
# --------------------------------------------------------------------------
def glyph_lines(model_path):
    """Sylwetka z model.json: polki -> linie poziome (x0,x1,z), przegrody -> pionowe (x,z0,z1), mm."""
    m = json.load(open(model_path, encoding='utf-8'))
    shelves, divs = [], []
    for p in m['parts']:
        if p.get('group') != 'korpus':
            continue
        o, eu, ev, ew = (np.array(p[k], float) for k in ('origin', 'eu', 'ev', 'ew'))
        pts = []
        for u, v in p['outline']:
            base = o + u * eu + v * ev
            pts += [base, base + ew * p['t']]
        pts = np.array(pts)
        x0, x1 = pts[:, 0].min(), pts[:, 0].max()
        z0, z1 = pts[:, 2].min(), pts[:, 2].max()
        if p['pid'].startswith('P'):
            shelves.append((x0, x1, (z0 + z1) / 2))
        elif p['pid'].startswith('D'):
            divs.append(((x0 + x1) / 2, z0, z1))
    return sorted(shelves, key=lambda s: s[2]), divs


def render_endcard(spec, version, W, H, fps, out_dir, scale=1.0, base_dir='.'):
    """Pelne klatki planszy: tlo + elementy {type: glyph|text, f:[in,out] (wzgl. startu planszy), ...}."""
    n = int(spec.get('dur_f', 90))
    bg = hex_rgba(spec.get('bg', '#EFEAE2'))
    os.makedirs(out_dir, exist_ok=True)
    els = []
    for e in spec.get('elements', []):
        e = dict(e)
        if e['type'] == 'glyph':
            mp = e['model'] if os.path.isabs(e['model']) else os.path.join(base_dir, e['model'])
            sh, dv = glyph_lines(mp)
            zmax = max(s[2] for s in sh)
            zmin = min(s[2] for s in sh)
            xmax = max(s[1] for s in sh)
            hpx = e.get('height', 240) * scale
            k = hpx / (zmax - zmin)
            cx, cy = e.get('cx', W / 2 / scale) * scale, e.get('cy', 380) * scale
            X = lambda x: cx + (x - xmax / 2) * k            # noqa: E731
            Z = lambda z: cy + hpx / 2 - (z - zmin) * k      # noqa: E731
            e['_sh'] = [(X(a), X(b), Z(z)) for a, b, z in sh]
            e['_dv'] = [(X(x), Z(z0), Z(z1)) for x, z0, z1 in dv]
            e['_lvl'] = sorted({round(z, 1) for _, _, z in e['_sh']}, reverse=True)   # ekranowe y: od dolu
        elif e['type'] == 'text':
            st = dict(STYLES[version].get(e.get('style', 'title')))
            st.update({kk: e[kk] for kk in ('font', 'size', 'tracking', 'color') if kk in e})
            st['align'] = e.get('align', 'center')
            e['_img'], e['_base'], e['_cap'], e['_tw'] = text_image(e['text'], st, scale)
        els.append(e)
    for i in range(n):
        fr = Image.new('RGBA', (W, H), bg)
        d = ImageDraw.Draw(fr)
        for e in els:
            f0, f1 = e.get('f', [0, n])
            if i < f0:
                continue
            if e['type'] == 'glyph':
                col = hex_rgba(e.get('color', '#24211E'))
                lw = max(1, int(round(e.get('stroke', 2) * scale)))
                per, stag = e.get('shelf_frames', 6), e.get('stagger', 3)
                for j, lvl in enumerate(e['_lvl']):          # od dolu do gory
                    t0 = f0 + j * stag
                    u = ease_out_cubic((i - t0 + 1) / per)
                    if u <= 0:
                        continue
                    for a, b, z in e['_sh']:
                        if abs(round(z, 1) - lvl) < 0.05:
                            d.line([(a, z), (a + (b - a) * u, z)], fill=col, width=lw)
                    ug = ease_out_cubic((i - t0 - per + 1) / 4)
                    if ug > 0:
                        for x, za, zb in e['_dv']:
                            if abs(za - lvl) < 3 * scale + lw:      # przegroda stoi na tej polce, rosnie w gore
                                d.line([(x, za), (x, za + (zb - za) * ug)], fill=col, width=lw)
            elif e['type'] == 'text':
                u = ease_out_cubic((i - f0 + 1) / max(1, f1 - f0))
                rise = e.get('rise', 12) * scale * (1 - u)
                x = e.get('x', W / 2 / scale) * scale
                yc = e.get('y', H / 2 / scale) * scale
                align = e.get('align', 'center')
                x0 = x - e['_tw'] / 2 - 2 if align == 'center' else x - 2
                y0 = yc - (e['_base'] - e['_cap'] / 2) + rise
                im_ = e['_img']
                lay = Image.new('RGBA', (im_.width + 2, im_.height + 2), (0, 0, 0, 0))
                lay.paste(im_, (0, 0))
                lay = _alpha(_shift(lay, x0 - np.floor(x0), y0 - np.floor(y0)), u)
                fr.alpha_composite(lay, (int(np.floor(x0)), int(np.floor(y0))))
                d = ImageDraw.Draw(fr)
        fr.convert('RGB').save(os.path.join(out_dir, f'{i:04d}.png'), compress_level=1)
    return dict(pattern=os.path.join(out_dir, '%04d.png'), n=n)
