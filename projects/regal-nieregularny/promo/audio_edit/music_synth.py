#!/usr/bin/env python3
"""music_synth.py - fallback: syntezowany podklad 30 s w stylu docelowego jingla.

Styl: minimal / premium / cieply. F-dur, domyslnie 104 BPM, 13 taktow = 30.0 s.
  takty 1-4   INTRO   - cieple pady (detune + filtr + chorus), rzadka marimba, "zegar" (tick),
                        riser i oddech (pauza 1/8) przed reveal,
  takt 5      REVEAL  - sub-boom + stopa + pelny akord + iskra kalimby (akcent ~9.2 s),
  takty 5-11  GROOVE  - delikatny bit (stopa, woodblock, shaker, hi-hat), arpeggio marimby,
                        sub-bas z sidechainem,
  takt 12     END CARD- kadencja V-I, "sonic logo" (4 nuty marimba+kalimba), wybrzmienie do 30 s.

Instrumenty "drewniane" (marimba, woodblock) nawiazuja do sklejki.

Uzycie:
  python3 music_synth.py                              # music/synth_v1.wav + stems + markers JSON
  python3 music_synth.py --bpm 100 -o music/synth_v2.wav --seed 7
  python3 music_synth.py --reveal 9.0                 # dobiera BPM tak, by reveal (takt 5) wypadl w 9.0 s
  python3 music_synth.py --reveal 8.5 --reveal-bar 4 --end-bar 11 --bars 12
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402
import sfx_synth  # noqa: E402
from dsp import SR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)


# --------------------------------------------------------------------------
# harmonia (F-dur). bass = MIDI basu, pad = glosy padu
# --------------------------------------------------------------------------
CH = {
    'Dm9':     dict(bass=38, pad=[53, 57, 60, 64]),
    'Bbmaj9':  dict(bass=34, pad=[50, 53, 57, 60]),
    'Fmaj9/A': dict(bass=33, pad=[52, 55, 57, 60]),
    'Csus4':   dict(bass=36, pad=[53, 55, 60, 62]),
    'Cadd9':   dict(bass=36, pad=[52, 55, 60, 62]),
    'Fmaj9':   dict(bass=29, pad=[52, 55, 57, 60]),
    'Fmaj9+':  dict(bass=29, pad=[52, 55, 57, 60, 64, 69]),
    'F69':     dict(bass=29, pad=[53, 57, 62, 67, 72]),
}


def build_form(reveal_bar=5, end_bar=12, bars=13):
    """Lista (takt_od_1, beat_offset, czas_beatow, akord). Intro dopasowuje sie do reveal_bar."""
    intro = ['Dm9', 'Bbmaj9', 'Fmaj9/A', ('Csus4', 'Cadd9')]
    groove = ['Fmaj9+', 'Dm9', 'Bbmaj9', ('Csus4', 'Cadd9'), 'Fmaj9', 'Dm9', ('Bbmaj9', 'Csus4')]
    form = []
    n_intro = reveal_bar - 1
    seq = intro[-n_intro:] if n_intro <= len(intro) else (intro * 2)[-n_intro:]
    n_groove = end_bar - reveal_bar
    gseq = (groove * 2)[:n_groove]
    if n_groove >= 2:
        gseq[-1] = ('Bbmaj9', 'Csus4')    # zawsze kadencja do end card
    allb = list(seq) + gseq + ['F69'] * (bars - end_bar + 1)
    for b, c in enumerate(allb, start=1):
        if isinstance(c, tuple):
            form.append((b, 0, 2, c[0]))
            form.append((b, 2, 2, c[1]))
        else:
            form.append((b, 0, 4, c))
    return form


# --------------------------------------------------------------------------
# instrumenty
# --------------------------------------------------------------------------
def saw_blep(freq, n, phase0=0.0):
    """Pila band-limited (polyBLEP), wektorowo. freq: skalar lub tablica [Hz]."""
    dt = np.broadcast_to(np.asarray(freq, dtype=float) / SR, (n,))
    ph = (phase0 + np.cumsum(dt)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    t = ph[m] / dt[m]
    y[m] -= t + t - t * t - 1
    m = ph > 1 - dt
    t = (ph[m] - 1) / dt[m]
    y[m] -= t * t + t + t + 1
    return y


def pad_note(m, dur, r, voices=5, detune_cents=11, attack=0.9, release=1.6, vel=1.0):
    f0 = mtof(m)
    n = dsp.n_of(dur + release)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    drift = 1 + 0.0012 * dsp.smooth_noise(n, r, 0.4)
    for v in range(voices):
        c = (v - (voices - 1) / 2) / ((voices - 1) / 2 + 1e-9) * detune_cents
        f = f0 * 2 ** (c / 1200) * drift
        s = saw_blep(f, n, r.uniform())
        pan = (v - (voices - 1) / 2) / ((voices - 1) / 2 + 1e-9) * 0.7
        out += dsp.pan_mono(s, pan)
    # cieply sub-oscylator (sinus oktawe nizej) tylko dla nizszych glosow
    if m < 52:
        out += dsp.to_stereo(np.sin(2 * np.pi * f0 / 2 * t) * 0.25)
    env = dsp.smoothstep(t / attack) * np.where(t < dur, 1.0, np.exp(-(t - dur) / (release / 4)))
    return out * env[:, None] * vel / voices


def marimba(m, vel, r, decay_scale=1.0):
    """Marimba (sztabka strojona 1:4:10) + rezonator + mlotek z filcu."""
    f = mtof(m)
    dur = 1.6 * decay_scale
    n = dsp.n_of(dur)
    t = np.arange(n) / SR
    d1 = 0.55 * (440 / f) ** 0.45 * decay_scale
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / d1)
    y += 0.32 * vel * np.sin(2 * np.pi * f * 3.99 * t + 0.4) * np.exp(-t / (d1 * 0.22))
    y += 0.1 * vel ** 2 * np.sin(2 * np.pi * f * 9.9 * t + 1.1) * np.exp(-t / (d1 * 0.07))
    y += 0.25 * np.sin(2 * np.pi * f * t + 0.2) * np.exp(-t / (d1 * 1.8)) * (1 - np.exp(-t / 0.02))  # rezonator
    mallet = dsp.lp(r.standard_normal(n), 1800 + 2500 * vel, 2) * dsp.env_ad(n, 0.0005, 0.004)
    y = y * dsp.smoothstep(t / 0.0015) + 0.18 * vel * mallet
    return y * vel


def kalimba(m, vel, r):
    f = mtof(m)
    n = dsp.n_of(1.8)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7)
    y += 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.08)
    y += 0.08 * np.sin(2 * np.pi * f * 7.1 * t) * np.exp(-t / 0.04)
    y += 0.05 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.3)
    click = dsp.hp(r.standard_normal(n), 3000, 2) * dsp.env_ad(n, 0.0002, 0.002) * 0.15
    return (y * dsp.smoothstep(t / 0.001) + click) * vel


def sub_bass(m, dur, vel=1.0):
    f = mtof(m)
    n = dsp.n_of(dur + 0.15)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
    env = dsp.smoothstep(t / 0.008) * np.where(t < dur, 1 - 0.25 * np.clip(t / max(dur, 1e-3), 0, 1),
                                               0.75 * np.exp(-(t - dur) / 0.04))
    return dsp.soft_clip(y * env * vel * 0.9, 1.3)


def kick(vel, r, tight=1.0):
    n = dsp.n_of(0.5)
    t = np.arange(n) / SR
    f = 50 + 95 * np.exp(-t / (0.028 * tight))
    y = np.sin(dsp.phase_from_freq(f)) * np.exp(-t / (0.22 * tight))
    y += dsp.bp(r.standard_normal(n), 1500, 6000, 2) * dsp.env_ad(n, 0.0002, 0.0025) * 0.25
    return dsp.soft_clip(y * vel, 1.5)


def woodblock(vel, r, pitch=1.0):
    n = dsp.n_of(0.25)
    exc = np.zeros(n)
    exc[:24] = np.hanning(24)
    y = dsp.resonator_bank(exc, np.array([820, 1745, 2890, 4100]) * pitch * r.uniform(0.99, 1.01),
                           [0.028, 0.013, 0.007, 0.004], [1.0, 0.55, 0.3, 0.12])
    y /= (np.max(np.abs(y)) + 1e-12)
    snap = dsp.bp(r.standard_normal(n), 2000, 8000, 2) * dsp.env_ad(n, 0.0003, 0.006)
    snap /= (np.max(np.abs(snap)) + 1e-12)
    return (y + 0.35 * snap) * vel


def shaker(vel, r):
    n = dsp.n_of(0.12)
    y = dsp.bp(r.standard_normal(n), 5200, 13000, 2)
    e = dsp.env_ad(n, 0.008, 0.028, curve=1.5)
    return y / (np.std(y) + 1e-12) * e * vel * 0.4


def hat(vel, r):
    n = dsp.n_of(0.15)
    t = np.arange(n) / SR
    sq = sum(np.sign(np.sin(2 * np.pi * f * t + r.uniform(0, 6))) for f in [205.3, 304.4, 369.6, 522.7, 540.0, 800.0])
    y = dsp.bp(sq, 7000, 14000, 2) + 0.4 * dsp.hp(r.standard_normal(n), 8000, 2)
    return y / (np.std(y) + 1e-12) * dsp.env_ad(n, 0.0005, 0.03) * vel * 0.35


def tick(vel, r):
    """Cichy 'zegar' (olowek o drewno) - napiecie w intro."""
    n = dsp.n_of(0.06)
    exc = np.zeros(n)
    exc[:4] = [1, -0.5, 0.2, -0.1]
    y = dsp.resonator_bank(exc, [2400 * r.uniform(0.98, 1.02), 3900, 5600], [0.006, 0.004, 0.0025], [1, 0.5, 0.3])
    return y / (np.max(np.abs(y)) + 1e-12) * vel


# --------------------------------------------------------------------------
# kompozycja
# --------------------------------------------------------------------------
def compose(bpm=104.0, bars=13, reveal_bar=5, end_bar=12, duration=None, seed=1):
    r = dsp.rng(seed)
    beat = 60.0 / bpm
    bar = 4 * beat
    T = lambda b, bt=0.0: (b - 1) * bar + bt * beat  # noqa: E731
    total = duration or bars * bar
    N = dsp.n_of(total + 4.0)
    stems = {k: np.zeros((N, 2)) for k in ['pads', 'marimba', 'bass', 'drums', 'fx']}
    t_rev, t_end = T(reveal_bar), T(end_bar)
    hum = lambda s=0.005: r.normal(0, s)  # noqa: E731
    form = build_form(reveal_bar, end_bar, bars)

    # ---------------- PADY ----------------
    pads_dry = np.zeros((N, 2))
    for b, bo, nb, name in form:
        st, d = T(b, bo), nb * beat
        ch = CH[name]
        is_end = b >= end_bar
        vel = 0.75 if b < reveal_bar else 1.0
        for m in ch['pad']:
            note = pad_note(m, d + (2.0 if is_end else 0.05), r, attack=0.9 if b < reveal_bar else 0.35,
                            release=2.2 if is_end else 1.4, vel=vel)
            dsp.place(pads_dry, note, st + hum(0.01))
    # obwiednia filtra: ciemne intro -> otwarcie na reveal -> groove -> wolne zamykanie na koncu
    tt = np.arange(N) / SR
    fc = dsp.env_lin(tt, [(0, 800), (t_rev - bar, 1500), (t_rev - 0.05, 4200), (t_rev + 0.4, 3600),
                          (t_end - bar, 3300), (t_end, 4500), (t_end + 1.5, 2800), (total, 1100), (total + 4, 800)])
    fc = fc * (1 + 0.08 * np.sin(2 * np.pi * tt / (2 * bar)))
    pads = np.stack([dsp.tv_biquad(pads_dry[:, c], fc, q=0.85, kind='lowpass', stages=2) for c in range(2)], axis=1)
    pads = dsp.chorus(pads, mix=0.55)
    pads = dsp.eq(pads, 'peak', 280, -2.5, 0.9)   # odchudzenie "blota"
    pads = dsp.hp(pads, 110, 2)                    # pady nie wchodza basowi w droge
    stems['pads'] += pads

    # ---------------- MARIMBA / KALIMBA ----------------
    mar = np.zeros((N, 2))

    def mnote(m, at, vel, pan=0.0, dec=1.0, kal=0.0):
        y = marimba(m, vel, r, dec)
        dsp.place(mar, dsp.pan_mono(y, pan), at + hum(0.004))
        if kal > 0:
            dsp.place(mar, dsp.pan_mono(kalimba(m + 12, vel * kal, r), -pan * 0.6), at + hum(0.003))

    chord_at = {}
    for b, bo, nb, name in form:
        for k in range(int(bo), int(bo + nb)):
            chord_at[(b, k)] = name
    # intro: rzadki motyw (narasta)
    for b in range(1, reveal_bar):
        name = chord_at[(b, 0)]
        tones = sorted(CH[name]['pad'])
        lvl = 0.35 + 0.12 * (b - 1)
        mnote(tones[-1] + 12, T(b, 0), lvl, 0.25)
        mnote(tones[-2] + 12, T(b, 1.5), lvl * 0.7, -0.3)
        if b >= reveal_bar - 2:
            mnote(tones[-3] + 12, T(b, 2.5), lvl * 0.65, 0.35)
            mnote(tones[-1] + 12, T(b, 3.0), lvl * 0.55, -0.1)
    # reveal: stab akordowy + iskra kalimby
    for i, m in enumerate(sorted(CH['Fmaj9+']['pad'])[-4:]):
        mnote(m + 12, t_rev + i * 0.012, 0.75, (i - 1.5) * 0.3, dec=1.4, kal=0.5)
    # groove: arpeggio 8-mek z synkopa
    patt = [(0, 0), (0.75, 2), (1.5, 1), (2.0, 3), (2.5, 2), (3.25, 1), (3.5, 0)]
    for b in range(reveal_bar, end_bar):
        for bt, idx in patt:
            if b == reveal_bar and bt < 1.5:
                continue
            name = chord_at[(b, int(bt))]
            tones = sorted(CH[name]['pad'])
            m = tones[idx % len(tones)] + 12
            vel = (0.62 if bt in (0, 2.0) else 0.45) * r.uniform(0.85, 1.05)
            mnote(m, T(b, bt), vel, [-0.35, 0.3, -0.15, 0.4][idx % 4] * 0.8)
    # sonic logo na end card (marimba + kalimba oktawe wyzej)
    logo = [(0.0, 69, 0.8), (0.5, 72, 0.7), (1.0, 77, 0.85), (1.75, 76, 0.65), (2.5, 77, 0.9)]
    for bt, m, v in logo:
        mnote(m, T(end_bar, bt), v, 0.15 * np.sign(bt - 1.2), dec=1.6, kal=0.55)
    mar = dsp.pingpong(mar, 0.75 * beat, feedback=0.32, mix=0.22, lp_hz=3200)[:N]
    stems['marimba'] += mar

    # ---------------- BAS ----------------
    bass_patt = [(0, 1.5, 1.0), (1.5, 0.45, 0.7), (2.5, 0.9, 0.85), (3.5, 0.45, 0.6)]
    for b, bo, nb, name in form:
        root = CH[name]['bass']
        while root > 40:
            root -= 12
        if b < reveal_bar - 1:
            continue
        if b == reveal_bar - 1:   # przedtakt: dlugi, cichy dzwiek narastajacy
            if bo == 0:
                dsp.place(stems['bass'], dsp.to_stereo(sub_bass(root, 3.4 * beat, 0.35)), T(b, 0))
            continue
        if b >= end_bar:
            if bo == 0 and b == end_bar:
                dsp.place(stems['bass'], dsp.to_stereo(sub_bass(root, 2.5 * bar, 0.9)), T(b, 0))
            continue
        for bt, dur, v in bass_patt:
            if bo <= bt < bo + nb:
                dsp.place(stems['bass'], dsp.to_stereo(sub_bass(root, dur * beat, v)), T(b, bt))

    # ---------------- PERKUSJA ----------------
    drums = np.zeros((N, 2))
    kicks = []

    def hit(fn_y, at, pan=0.0, g=1.0):
        dsp.place(drums, dsp.pan_mono(fn_y, pan), at, gain=g)

    for b in range(1, bars + 1):
        # intro: tick 8-mek od taktu 2, narasta
        if 2 <= b < reveal_bar:
            for k in range(8):
                v = (0.12 + 0.1 * (b - 2) / max(1, reveal_bar - 3)) * (1.0 if k % 2 == 0 else 0.6)
                if b == reveal_bar - 1 and k == 7:
                    continue   # oddech przed reveal
                hit(tick(v, r), T(b, k * 0.5) + hum(0.003), 0.45 if k % 2 else -0.2)
        if b == reveal_bar - 1:   # shaker narasta w ostatnim takcie intro
            for k in range(14):
                hit(shaker(0.15 + 0.5 * k / 14, r), T(b, k * 0.25) + hum(0.003), 0.3)
        if reveal_bar <= b < end_bar:
            kp = [0, 2] if (b - reveal_bar) % 2 == 0 else [0, 2, 2.75]
            if b == end_bar - 1:
                kp = [0, 2, 2.75]
            for bt in kp:
                hit(kick(0.95 if bt == 0 else 0.75, r), T(b, bt) + hum(0.002))
                kicks.append(T(b, bt))
            for bt in (1, 3):
                if b == end_bar - 1 and bt == 3:
                    # przejscie: trzy woodblocki (triola) i pauza 1/8 przed end card
                    for j, x in enumerate([3.0, 3.167, 3.333]):
                        hit(woodblock(0.45 + 0.1 * j, r, 1.0 + 0.06 * j), T(b, x), 0.2 - 0.2 * j)
                    continue
                hit(woodblock(0.55, r), T(b, bt) + hum(0.003), -0.15)
            for k in range(16):
                if b == end_bar - 1 and k >= 14:
                    continue
                sw = 0.035 * beat if k % 2 else 0.0
                v = (0.55 if k % 4 == 2 else 0.32) * r.uniform(0.8, 1.1)
                hit(shaker(v, r), T(b, k * 0.25) + sw + hum(0.003), 0.35)
            if b >= reveal_bar + 2:
                for k in range(4):
                    if b == end_bar - 1 and k == 3:
                        continue
                    hit(hat(0.45 * r.uniform(0.8, 1.1), r), T(b, k + 0.5) + hum(0.002), -0.4)
    # reveal + end card: stopa akcentowa
    hit(kick(1.0, r, tight=1.3), t_rev)
    hit(kick(0.9, r, tight=1.4), t_end)
    kicks += [t_rev, t_end]
    stems['drums'] += dsp.reverb(drums, wet=0.1, rt60=0.5, predelay=0.004, brightness=0.55, seed=31, tail=False)

    # ---------------- FX (z biblioteki sfx_synth) ----------------
    ris = sfx_synth.riser(duration=bar, tonal=0.35, seed=seed + 40, root_hz=float(mtof(53)))
    dsp.place(stems['fx'], ris.audio * 0.32, t_rev - 0.5 * beat - ris.anchors['end'])   # konczy sie przed oddechem
    boom = sfx_synth.sub_boom(duration=3.2, seed=seed + 41)
    dsp.place(stems['fx'], boom.audio * 0.85, t_rev - boom.anchors['hit'])
    boom2 = sfx_synth.sub_boom(duration=2.4, f_start=80, f_end=43, seed=seed + 42)
    dsp.place(stems['fx'], boom2.audio * 0.55, t_end - boom2.anchors['hit'])
    a = sfx_synth.air(duration=1.4, brightness=0.6, seed=seed + 43, peak_at=0.8)
    dsp.place(stems['fx'], a.audio * 0.18, t_end - a.anchors['peak'])

    # ---------------- SIDECHAIN ----------------
    sc = np.ones(N)
    for k in kicks:
        i0 = int(k * SR)
        ln = int(0.32 * SR)
        if i0 >= N:
            continue
        seg = np.arange(min(ln, N - i0)) / SR
        g = 1 - (1 - np.exp(-seg / 0.004)) * np.exp(-seg / 0.11)
        sc[i0:i0 + len(seg)] = np.minimum(sc[i0:i0 + len(seg)], g)
    duck = {'pads': 0.38, 'bass': 0.55, 'marimba': 0.12}
    for k, d in duck.items():
        stems[k] *= (1 - d * (1 - sc))[:, None]

    # ---------------- POGLOS (send) ----------------
    send = stems['pads'] * 0.35 + stems['marimba'] * 0.3 + stems['drums'] * 0.05
    hall = dsp.reverb(send, wet=1.0, dry=0.0, rt60=2.3, predelay=0.024, brightness=0.4, seed=77, tail=False)
    stems['reverb'] = hall[:N]

    # ---------------- balans (RMS w groove) + master ----------------
    g0, g1 = int(t_rev * SR), int(t_end * SR)
    targets = {'pads': -21.0, 'marimba': -24.0, 'bass': -23.5, 'drums': -22.5, 'reverb': -27.0, 'fx': None}
    for k, tgt in targets.items():
        if tgt is None:
            continue
        cur = dsp.rms_db(stems[k][g0:g1])
        stems[k] *= dsp.db2lin(tgt - cur)
    stems['fx'] *= dsp.db2lin(-6.0)
    mix = sum(stems.values())
    mix = dsp.eq(mix, 'lowshelf', 90, 1.0)
    mix = dsp.eq(mix, 'highshelf', 9000, 1.5)
    mix = dsp.eq(mix, 'peak', 3000, 1.5, 0.8)
    mix = dsp.hp(mix, 30, 2)
    # koniec: wybrzmienie do `total`, fade 1.6 s
    n_tot = dsp.n_of(total)
    mix = dsp.fade(mix[:n_tot], 0.01, 1.6)
    for k in stems:
        stems[k] = dsp.fade(stems[k][:n_tot], 0.01, 1.6)
    # lekka kompresja "glue" (RMS 40 ms, 1.6:1 powyzej -18 dBFS)
    env = np.sqrt(dsp.uniform_filter1d(np.mean(mix ** 2, axis=1), int(0.04 * SR)))
    lvl = dsp.lin2db(env)
    gr = np.where(lvl > -18, (lvl + 18) * (1 - 1 / 1.6), 0.0)
    gr = dsp.uniform_filter1d(gr, int(0.08 * SR))
    mix = mix * dsp.db2lin(-gr)[:, None]
    mix, L, tp = dsp.normalize_lufs(mix, -14.0, -1.0)
    markers = {
        'bpm': bpm, 'beat_s': beat, 'bar_s': bar, 'bars': bars, 'duration': total,
        'reveal_bar': reveal_bar, 'reveal_s': round(t_rev, 4),
        'end_bar': end_bar, 'endcard_s': round(t_end, 4),
        'bar_times': [round(T(b), 4) for b in range(1, bars + 1)],
        'kicks': [round(k, 4) for k in sorted(kicks)],
        'form': [dict(bar=b, beat=bo, beats=nb, chord=c) for b, bo, nb, c in form],
        'lufs': round(L, 2), 'true_peak_dbtp': round(tp, 2), 'seed': seed,
    }
    return mix, stems, markers


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--out', default=os.path.join(HERE, 'music', 'synth_v1.wav'))
    ap.add_argument('--bpm', type=float, default=104.0)
    ap.add_argument('--reveal', type=float, help='czas reveal [s] - BPM zostanie dobrane')
    ap.add_argument('--reveal-bar', type=int, default=5)
    ap.add_argument('--end-bar', type=int, default=12)
    ap.add_argument('--bars', type=int, default=13)
    ap.add_argument('--duration', type=float, default=30.0)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--no-stems', action='store_true')
    a = ap.parse_args()
    bpm = a.bpm
    if a.reveal:
        bpm = (a.reveal_bar - 1) * 4 * 60.0 / a.reveal
        print(f'BPM dobrane do reveal {a.reveal:.2f} s: {bpm:.2f}')
    mix, stems, mk = compose(bpm, a.bars, a.reveal_bar, a.end_bar, a.duration, a.seed)
    dsp.write_wav(a.out, mix)
    base = os.path.splitext(a.out)[0]
    if not a.no_stems:
        sd = base + '_stems'
        for k, v in stems.items():
            dsp.write_wav(os.path.join(sd, f'{k}.wav'), v)
    with open(base + '.json', 'w') as f:
        json.dump(mk, f, indent=1)
    print(f'{a.out}: {len(mix) / SR:.2f} s, {mk["lufs"]} LUFS, TP {mk["true_peak_dbtp"]} dBTP, '
          f'BPM {bpm:.2f}, reveal {mk["reveal_s"]} s, end card {mk["endcard_s"]} s')


if __name__ == '__main__':
    main()
