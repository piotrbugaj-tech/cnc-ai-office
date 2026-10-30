#!/usr/bin/env python3
"""lut.py - look "Nordycki poranek" (research-brief 7.2) jako LUT .cube 33^3 + maska winiety.

Krzywa S przez punkty (0;0,02) (0,25;0,235) (0,5;0,5) (0,75;0,77) (1;0,98) - PCHIP, monotoniczna,
saturacja 0,92, poltony R +2 % / B -1,5 %, cienie R -1 % / B +1 %. Wszystko w przestrzeni wyswietlania (sRGB).
Winieta: rogi -8...10 %, maska radialna z potega 2,5 (PNG 16-bit, mnozona w ffmpeg blend=multiply).

  python3 lut.py                       # luts/nordic_morning.cube + luts/vignette_1920x1080.png
  python3 lut.py --size 1080x1920 --strength 0.09
"""
from __future__ import annotations

import argparse
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CURVE = [(0.0, 0.02), (0.25, 0.235), (0.5, 0.5), (0.75, 0.77), (1.0, 0.98)]


def grade(rgb, curve=CURVE, sat=0.92, mid=(0.02, 0.0, -0.015), shadow=(-0.01, 0.0, 0.01), strength=1.0):
    from scipy.interpolate import PchipInterpolator
    x, y = zip(*curve)
    f = PchipInterpolator(x, y)
    out = f(np.clip(rgb, 0, 1))
    L = out @ np.array([0.2126, 0.7152, 0.0722])
    out = L[..., None] + (out - L[..., None]) * sat
    m_mid = np.clip(1 - np.abs(2 * L - 1) ** 1.5, 0, 1)[..., None]
    m_sh = np.clip(1 - L / 0.4, 0, 1)[..., None] ** 1.5
    out = out + m_mid * np.array(mid) + m_sh * np.array(shadow)
    out = rgb + (out - rgb) * strength
    return np.clip(out, 0, 1)


def write_cube(path, size=33, **kw):
    g = np.linspace(0, 1, size)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')      # R zmienia sie najszybciej
    rgb = np.stack([r, gg, b], axis=-1).reshape(-1, 3)
    out = grade(rgb, **kw)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w') as fh:
        fh.write('TITLE "RYTM nordic morning (research-brief 7.2)"\n')
        fh.write(f'LUT_3D_SIZE {size}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        for row in out:
            fh.write(f'{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n')
    return path


def write_vignette(path, w, h, strength=0.09, power=2.5):
    from PIL import Image
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - (w - 1) / 2) / ((w - 1) / 2)
    ny = (yy - (h - 1) / 2) / ((h - 1) / 2)
    r = np.sqrt(nx ** 2 + ny ** 2) / np.sqrt(2)          # 1 w rogach
    v = 1 - strength * r ** power
    im = Image.fromarray(np.round(v * 65535).astype(np.uint16))   # -> tryb I;16 (PNG 16-bit)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    im.save(path)
    return path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=os.path.join(HERE, 'luts', 'nordic_morning.cube'))
    ap.add_argument('--size', default='1920x1080')
    ap.add_argument('--strength', type=float, default=0.09)
    a = ap.parse_args()
    print(write_cube(a.out))
    w, h = map(int, a.size.split('x'))
    print(write_vignette(os.path.join(os.path.dirname(a.out), f'vignette_{w}x{h}.png'), w, h, a.strength))
