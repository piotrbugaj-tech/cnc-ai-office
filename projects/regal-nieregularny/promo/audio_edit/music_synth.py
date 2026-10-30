#!/usr/bin/env python3
"""music_synth.py - syntezowana muzyka wg research-brief.md (sekcja 6.1): fallback dla muzyki z fal.ai
i REFERENCJA TIMINGU (wszystkie akcenty w klatkach 25 fps).

100 BPM, F-dur, 4/4, minimal/ambient z pulsem half-time; takt = 60 kl. = 2,4 s, 16-tka = 3,75 kl.
Wersja 30 s (750 kl.):
  takt 1     f0-60     HOOK       nuty polek (marimba, prawie sucha) F3 A3 C4 D4 F4 G4 A4 C5 na 16-tkach 0.3.6.7.9.12.14.15,
                                  pad od f30 (-30 dB), od f45 odwrocony poglos akordu
  takty 2-3  f60-180   ODSLONA    Fmaj9 -> Dm9, f60 sub + otwarcie pada, motyw RYTM w takcie 3 (cicho, oktawe nizej)
  takty 4-7  f180-420  GROOVE A   Bbmaj7 -> C(sus4->3) -> Fmaj9 -> Dm9; kick na 1, wood clap na 3, shaker, RYTM co takt
  takt 8     f420-480  BREAKDOWN  Bbmaj7(#11), pad + riser (f420-474), bez perkusji, cisza f474-480
  takty 9-10 f480-600  DROP       Fmaj9 -> Dm9, sub+kick f480, bas, ladowania polek = melodia (tab. 5.8),
                                  fronty = arpeggio D4 F4 A4 C5 E5 F5 A5, f585 akord F5+A5+C6 z F2
  takt 11    f600-660  ROZWIAZANIE Bbmaj7, bez bebnow, rzadka marimba
  takt 12+   f660-750  LOGO       sygnal RYTM F4 f660, A4 f671.25, C5 f682.5, D5 f686.25, F5 f693.75 + sub F1 + pad Fmaj9;
                                  gasnie do f744, ostatnie 6 kl. ciszy
Wersja 15 s (375 kl., cutdown 9:16): hook | 2,4-6,0 groove (1,5 taktu) | 6,0-7,2 breakdown (cisza od 6,96) |
  7,2-12,0 drop | 12,0-15,0 sygnal i wybrzmienie.

Stemy (do miksu z muzyka AI): pads, motif (nuty zwiazane ze zdarzeniami: hook, ladowania, fronty, f585),
logo (sygnal RYTM), groove_marimba, drums, bass, fx, reverb. Z muzyka z fal.ai mozna podlozyc tylko `motif` (+ ewentualnie `fx`).

Uzycie:
  python3 music_synth.py                               # music/synth_v1.wav (30 s) + stems + markers JSON
  python3 music_synth.py --version 15 -o music/synth_v1_15s.wav
  python3 music_synth.py --seed 7 -o music/synth_v2.wav
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
FPS = 25.0

NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nm(name):
    """'F3' / 'Bb1' / 'C#4' -> MIDI."""
    n = NOTE[name[0]]
    i = 1
    while i < len(name) and name[i] in 'b#':
        n += -1 if name[i] == 'b' else 1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)


CHORDS = {   # pad (MIDI) + bas
    'Fmaj9': dict(pad=['A3', 'C4', 'E4', 'G4'], bass='F2'),
    'Dm9': dict(pad=['F3', 'A3', 'C4', 'E4'], bass='D2'),
    'Bbmaj7': dict(pad=['F3', 'A3', 'Bb3', 'D4'], bass='Bb1'),
    'Bbmaj7#11': dict(pad=['F3', 'A3', 'Bb3', 'D4', 'E4'], bass='Bb1'),
    'Csus4': dict(pad=['F3', 'G3', 'C4', 'D4'], bass='C2'),
    'C': dict(pad=['E3', 'G3', 'C4', 'D4'], bass='C2'),
    'Fmaj9full': dict(pad=['F3', 'A3', 'C4', 'E4', 'G4'], bass='F1'),
}
RYTM_16THS = [0, 3, 6, 7, 9, 12, 14, 15]
SHELF_NOTES = ['F3', 'A3', 'C4', 'D4', 'F4', 'G4', 'A4', 'C5']
# tab. 5.8: (klatka ladowania, nuta)
LANDINGS = [(502.5, 'F3'), (506.25, 'A3'), (510, 'C4'), (513.75, 'D4'), (517.5, 'D4'), (521.25, 'F4'),
            (525, 'G4'), (528.75, 'G4'), (532.5, 'A4'), (536.25, 'A4'), (540, 'C5'), (543.75, 'C5'),
            (547.5, 'D5'), (555, 'F5')]
FRONTS = [(558.75, 'D4'), (562.5, 'F4'), (566.25, 'A4'), (570, 'C5'), (573.75, 'E5'), (577.5, 'F5'), (581.25, 'A5')]
LOGO = [(0.0, 'F4'), (11.25, 'A4'), (22.5, 'C5'), (26.25, 'D5'), (33.75, 'F5')]   # klatki wzgledem startu logo


# --------------------------------------------------------------------------
# instrumenty (receptury 6.1)
# --------------------------------------------------------------------------
def saw_blep(freq, n, phase0=0.0):
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


def pad_note(m, dur, r, attack=1.2, release=2.5, vel=1.0):
    """3 piły PolyBLEP rozstrojone +-7 centow, panorama glosow +-40 %."""
    f0 = mtof(m)
    n = dsp.n_of(dur + release)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    drift = 1 + 0.0008 * dsp.smooth_noise(n, r, 0.3)
    for cents, pan in [(-7, -0.4), (0, 0.0), (7, 0.4)]:
        out += dsp.pan_mono(saw_blep(f0 * 2 ** (cents / 1200) * drift, n, r.uniform()), pan)
    env = dsp.smoothstep(t / attack) * np.where(t < dur, 1.0, np.exp(-(t - dur) / (release / 4.6)))
    return out * env[:, None] * vel / 3


def marimba(m, vel, r, pan=0.0):
    s = sfx_synth.marimba(midi=int(m), vel=vel, seed=int(r.integers(1, 99999)), pan=pan, dry=True)
    return s.audio, s.anchors['impact']


def sub_kick(vel, r):
    """Sinus 110 -> 46 Hz (tau 40 ms), amplituda tau 0,28 s, klik 2 ms (szum HP 2 kHz, -24 dB)."""
    n = dsp.n_of(1.4)
    t = np.arange(n) / SR
    f = 46 + 64 * np.exp(-t / 0.04)
    y = np.sin(dsp.phase_from_freq(f)) * np.exp(-t / 0.28) * dsp.smoothstep(t / 0.0015)
    k = dsp.n_of(0.002)
    y[:k] += dsp.hp(r.standard_normal(k), 2000, 2) * dsp.db2lin(-24) * 4
    return dsp.soft_clip(y * vel, 1.1)


def wood_clap(vel, r):
    """Blok drewniany modalnie (900 Hz + 2,4 kHz, tau 25 ms) + szum BP 1,5 kHz 8 ms."""
    n = dsp.n_of(0.3)
    e = np.zeros(n)
    e[:24] = np.hanning(24)
    y = dsp.resonator_bank(e, [900 * r.uniform(0.99, 1.01), 2400], [0.025, 0.025], [1.0, 0.55])
    y /= (np.max(np.abs(y)) + 1e-12)
    nz = dsp.bp(r.standard_normal(n), 1000, 2200, 2) * dsp.env_ad(n, 0.0005, 0.004)
    nz[dsp.n_of(0.008):] = 0
    nz /= (np.max(np.abs(nz)) + 1e-12)
    return (y + 0.5 * nz) * vel


def shaker(vel, r):
    """Szum HP 6 kHz, 25 ms."""
    n = dsp.n_of(0.05)
    y = dsp.hp(r.standard_normal(n), 6000, 2) * dsp.env_ad(n, 0.004, 0.009, curve=1.5)
    y[dsp.n_of(0.025):] *= np.linspace(1, 0, n - dsp.n_of(0.025))
    return y / (np.max(np.abs(y)) + 1e-12) * vel


def bass_note(m, dur, vel=1.0):
    """Sinus + 2. harmoniczna -12 dB + tanh; A 5 ms, D 300 ms, S 0,6."""
    f = mtof(m)
    n = dsp.n_of(dur + 0.12)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + dsp.db2lin(-12) * np.sin(4 * np.pi * f * t)
    env = np.minimum(t / 0.005, 1) * (0.6 + 0.4 * np.exp(-t / 0.3))
    env = np.where(t < dur, env, env * np.exp(-(t - dur) / 0.03))
    return dsp.soft_clip(y * env * vel, 1.4)


def hall_ir(seed=77, predelay=0.02):
    """IR: RT60 2,8 s (<500 Hz) / 2,2 s (0,5-2 kHz) / 1,5 s (2-6 kHz) / 0,8 s (>6 kHz), predelay 20 ms."""
    r = dsp.rng(seed)
    L = 3.2
    n = dsp.n_of(L)
    t = np.arange(n) / SR
    chans = []
    for c in range(2):
        nz = r.standard_normal(n)
        ir = np.zeros(n)
        for lo, hi, rt in [(None, 500, 2.8), (500, 2000, 2.2), (2000, 6000, 1.5), (6000, None, 0.8)]:
            b = dsp.lp(nz, hi, 4) if lo is None else (dsp.hp(nz, lo, 4) if hi is None else dsp.bp(nz, lo, hi, 2))
            ir += b * np.exp(-6.9078 * t / rt)
        ir *= dsp.smoothstep((t - predelay) / 0.03)
        chans.append(ir)
    ir = np.stack(chans, axis=1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def hall(x, ir):
    from scipy import signal
    m = dsp.hp(dsp.to_stereo(x).mean(axis=1), 150, 2)
    return np.stack([signal.fftconvolve(m, ir[:, 0])[:len(x)], signal.fftconvolve(m, ir[:, 1])[:len(x)]], axis=1)


# --------------------------------------------------------------------------
# partytura
# --------------------------------------------------------------------------
def score(version=30):
    """Zwraca dict: chords [(f0, f1, nazwa)], sekcje, zdarzenia (wszystko w klatkach)."""
    S = {}
    if version == 30:
        S['total_f'] = 750
        S['chords'] = [(30, 60, 'Fmaj9'), (60, 120, 'Fmaj9'), (120, 180, 'Dm9'), (180, 240, 'Bbmaj7'),
                       (240, 270, 'Csus4'), (270, 300, 'C'), (300, 360, 'Fmaj9'), (360, 420, 'Dm9'),
                       (420, 474, 'Bbmaj7#11'), (480, 540, 'Fmaj9'), (540, 600, 'Dm9'), (600, 660, 'Bbmaj7'),
                       (660, 744, 'Fmaj9full')]
        S['hook'] = 0
        S['reveal'] = 60
        S['rytm_quiet_bars'] = [120]                       # takt 3, oktawe nizej
        S['rytm_bars'] = [180, 240, 300, 360]              # groove A, co takt
        S['groove'] = [(180, 420)]
        S['breakdown'] = (420, 474, 480)                   # riser od, twarde ciecie, koniec ciszy
        S['drop'] = (480, 600)
        S['landing_shift'] = 0
        S['resolution'] = (600, 660)
        S['logo'] = 660
        S['fade_end'] = 744
    else:  # 15 s
        S['total_f'] = 375
        S['chords'] = [(30, 60, 'Fmaj9'), (60, 120, 'Bbmaj7'), (120, 150, 'C'), (150, 174, 'Bbmaj7#11'),
                       (180, 240, 'Fmaj9'), (240, 300, 'Dm9'), (300, 369, 'Fmaj9full')]
        S['hook'] = 0
        S['reveal'] = 60
        S['rytm_quiet_bars'] = []
        S['rytm_bars'] = [60, 120]
        S['groove'] = [(60, 150)]
        S['breakdown'] = (150, 174, 180)
        S['drop'] = (180, 300)
        S['landing_shift'] = -300                          # f480 (30 s) = f180 (15 s)
        S['resolution'] = None
        S['logo'] = 300
        S['fade_end'] = 369
    return S


def compose(version=30, seed=1, bpm=100.0):
    r = dsp.rng(seed)
    S = score(version)
    k = 100.0 / bpm                                       # skala czasu dla eksperymentow z BPM
    F = lambda f: f / FPS * k                              # noqa: E731
    beat_f = 15.0
    total = F(S['total_f'])
    N = dsp.n_of(total + 3.5)
    st = {n: np.zeros((N, 2)) for n in ['pads', 'motif', 'logo', 'groove_marimba', 'drums', 'bass', 'fx']}
    hum_t = lambda: r.uniform(-0.005, 0.005)               # noqa: E731
    hum_g = lambda: dsp.db2lin(r.uniform(-1.5, 1.5))      # noqa: E731
    notes_log = []

    def mar(stem, m, f, vel, pan=0.0, exact=False):
        y, a = marimba(m, vel * hum_g(), r, pan)
        t = F(f) + (0 if exact else hum_t())
        dsp.place(st[stem], y, t - a)
        notes_log.append({'frame': round(f, 3), 't': round(F(f), 4), 'midi': int(m), 'stem': stem})

    # ---------------- PAD ----------------
    pads = np.zeros((N, 2))
    for f0, f1, name in S['chords']:
        ch = CHORDS[name]
        vel = 0.18 if f0 < S['reveal'] else 1.0           # od f30 -30 dB (wzgledem pelnego pada ~-10 dB w miksie)
        att = 1.2 if f0 != S['reveal'] else 0.35
        for m in ch['pad']:
            dsp.place(pads, pad_note(nm(m), F(f1 - f0), r, attack=att, release=2.5, vel=vel), F(f0))
    tt = np.arange(N) / SR
    rev, logo = F(S['reveal']), F(S['logo'])
    b0, bcut, bend = (F(x) for x in S['breakdown'])
    d0, d1 = (F(x) for x in S['drop'])
    base = dsp.env_lin(tt, [(0, 600), (rev - 0.05, 700), (rev + 0.25, 1400), (b0, 1400), (bcut, 2300),
                            (d0, 1700), (d1, 1500), (logo, 1400), (logo + 1.2, 1700), (total, 900)])
    fc = base + 300 * np.sin(2 * np.pi * 0.07 * tt)     # LP 1400 +- 300 Hz, LFO 0,07 Hz
    pads = np.stack([dsp.tv_biquad(pads[:, c], fc, q=0.707, kind='lowpass', stages=1) for c in range(2)], axis=1)
    pads = dsp.chorus(pads, mix=0.5)
    pads = dsp.hp(pads, 90, 2)
    # odwrocony poglos akordu Fmaj9 od f45 -> wpada w f60
    burst = np.zeros((dsp.n_of(0.25), 2))
    for m in CHORDS['Fmaj9']['pad']:
        burst += dsp.pad_to(pad_note(nm(m), 0.12, r, attack=0.01, release=0.1), len(burst))
    ir = hall_ir(seed + 3)
    wet = hall(np.concatenate([burst, np.zeros((dsp.n_of(3.0), 2))]), ir)
    swell = wet[::-1]
    sw_len = dsp.n_of(F(S['reveal'] - 45))
    swell = swell[-sw_len - dsp.n_of(0.25):-dsp.n_of(0.25)] if len(swell) > sw_len + dsp.n_of(0.25) else swell
    swell = dsp.fade(swell / (np.max(np.abs(swell)) + 1e-12), 0.05, 0.004)
    dsp.place(st['fx'], swell * 0.5, rev - len(swell) / SR)
    st['pads'] += pads

    # ---------------- MOTYW (nuty zwiazane z obrazem) ----------------
    for i, s16 in enumerate(RYTM_16THS):                   # hook: nuty polek
        mar('motif', nm(SHELF_NOTES[i]), S['hook'] + s16 * 3.75, 0.85, pan=-0.1, exact=True)
    for f0 in S['rytm_quiet_bars']:                       # takt 3: cicho, oktawe nizej
        for i, s16 in enumerate(RYTM_16THS):
            mar('groove_marimba', nm(SHELF_NOTES[i]) - 12, f0 + s16 * 3.75, 0.3, pan=0.15)
    for j, f0 in enumerate(S['rytm_bars']):               # groove A: RYTM co takt (rozne odwrocenia)
        for i, s16 in enumerate(RYTM_16THS):
            m = nm(SHELF_NOTES[(i + 2 * j) % 8])
            mar('groove_marimba', m, f0 + s16 * 3.75, (0.55 if i in (0, 4) else 0.42), pan=[-0.3, 0.25][i % 2])
    sh = S['landing_shift']
    for f, n_ in LANDINGS:                                # drop: ladowania polek = melodia
        mar('motif', nm(n_), f + sh, 0.8 if f != 555 else 1.0, pan=0.0, exact=True)
    for f, n_ in FRONTS:                                  # fronty: arpeggio
        mar('motif', nm(n_), f + sh, 0.6, pan=0.2, exact=True)
    for n_ in ['F5', 'A5', 'C6']:                         # f585 akord
        mar('motif', nm(n_), 585 + sh, 0.7, exact=True)
    dsp.place(st['bass'], dsp.to_stereo(bass_note(nm('F2'), F(15) * 1.5, 0.9)), F(585 + sh))
    if S['resolution']:                                    # rzadka marimba w rozwiazaniu
        r0 = S['resolution'][0]
        for f, n_ in [(r0 + 7.5, 'D5'), (r0 + 22.5, 'A4'), (r0 + 41.25, 'F4')]:
            mar('groove_marimba', nm(n_), f, 0.38, pan=0.3)
    for f, n_ in LOGO:                                     # sygnal RYTM
        mar('logo', nm(n_), S['logo'] + f, 0.95, pan=0.0, exact=True)
    dsp.place(st['bass'], dsp.to_stereo(bass_note(nm('F1'), F(S['fade_end'] - S['logo']) * 0.8, 0.9)), logo)

    # ---------------- PERKUSJA ----------------
    kicks = []
    drums = np.zeros((N, 2))
    for g0, g1 in S['groove'] + [S['drop']]:
        for bar0 in np.arange(g0, g1, 60):
            dsp.place(drums, dsp.to_stereo(sub_kick(0.95, r)), F(bar0))
            kicks.append(F(bar0))
            dsp.place(drums, dsp.pan_mono(wood_clap(0.55 * hum_g(), r), -0.12), F(bar0 + 30) + hum_t())
            for s in range(16):
                acc = 1.0 if s % 4 == 2 else (0.7 if s % 2 else 0.5)
                sw = 0.02 if s % 2 else 0.0
                dsp.place(drums, dsp.pan_mono(shaker(acc * hum_g(), r), 0.3), F(bar0 + s * 3.75) + sw + hum_t())
    # akcenty: f60 (odslona), f480 (drop), logo
    for f, v in [(S['reveal'], 1.0), (S['logo'], 0.9)]:
        dsp.place(drums, dsp.to_stereo(sub_kick(v, r)), F(f))
        kicks.append(F(f))
    st['drums'] += drums

    # ---------------- BAS (drop) ----------------
    for bar0, ch in [(S['drop'][0], 'Fmaj9'), (S['drop'][0] + 60, 'Dm9')]:
        root = nm(CHORDS[ch]['bass'])
        for b, dur_b, v in [(0, 1.5, 1.0), (1.5, 0.5, 0.7), (2.5, 1.0, 0.85)]:
            dsp.place(st['bass'], dsp.to_stereo(bass_note(root, F(dur_b * beat_f), v)), F(bar0 + b * beat_f))

    # ---------------- FX ----------------
    ris = sfx_synth.riser(duration=bcut - b0, tonal=0.55, seed=seed + 40, root_hz=220.0)
    rs = ris.audio * np.linspace(dsp.db2lin(-26), 1.0, len(ris.audio))[:, None]   # crescendo -40 -> -14 dB
    m_, a_ = marimba(nm('C5'), 0.9, r)                     # odwrocona, pogloszona marimba
    mw = hall(np.concatenate([m_, np.zeros((dsp.n_of(3.0), 2))]), ir)[::-1]
    mw = dsp.pad_to(mw[-len(rs):] if len(mw) >= len(rs) else np.pad(mw, ((len(rs) - len(mw), 0), (0, 0))), len(rs))
    rs = rs + 0.5 * mw / (np.max(np.abs(mw)) + 1e-12) * np.linspace(0, 1, len(rs))[:, None] ** 2
    rs = dsp.fade(rs, 0.05, 0.003)                        # twarde ciecie
    dsp.place(st['fx'], rs * 0.6, b0)
    for f, d, v in [(S['reveal'], 2.6, 0.45), (S['drop'][0], 3.0, 0.8), (S['logo'], 3.0, 0.5)]:
        b = sfx_synth.sub_boom(duration=d, seed=seed + int(f))
        dsp.place(st['fx'], b.audio * v, F(f) - b.anchors['hit'])

    # ---------------- SIDECHAIN (kick -> pad/bas) ----------------
    sc = np.ones(N)
    for kt in kicks:
        i0 = int(kt * SR)
        seg = np.arange(min(int(0.4 * SR), max(0, N - i0))) / SR
        g = 1 - (1 - np.exp(-seg / 0.005)) * np.exp(-seg / 0.15)
        sc[i0:i0 + len(seg)] = np.minimum(sc[i0:i0 + len(seg)], g)
    for name, d in [('pads', 0.3), ('bass', 0.45), ('groove_marimba', 0.1)]:
        st[name] *= (1 - d * (1 - sc))[:, None]

    # ---------------- POGLOS ----------------
    hook_end = F(60)
    motif_send = st['motif'].copy()
    motif_send[:dsp.n_of(hook_end)] *= 0.25                # hook prawie suchy
    send = st['pads'] * 0.3 + motif_send * 0.35 + st['logo'] * 0.4 + st['groove_marimba'] * 0.35 + st['drums'] * 0.06
    st['reverb'] = hall(send, ir)
    short = dsp.reverb(st['motif'][:dsp.n_of(hook_end + 1.0)], wet=1.0, dry=0.0, rt60=0.9, seed=seed + 9, tail=False)
    st['reverb'][:len(short)] += short * 0.12

    # ---------------- balans + glue + master ----------------
    levels = {'pads': -22.0, 'motif': -21.0, 'logo': None, 'groove_marimba': -25.0, 'drums': -23.5, 'bass': -24.0,
              'reverb': -27.0, 'fx': -26.0}
    act = slice(dsp.n_of(F(S['groove'][0][0])), dsp.n_of(F(S['drop'][1])))
    for name, tgt in levels.items():
        if tgt is None:
            continue
        cur = dsp.rms_db(st[name][act]) if np.any(st[name][act]) else dsp.rms_db(st[name])
        st[name] *= dsp.db2lin(tgt - cur)
    st['logo'] *= dsp.db2lin(-21.0 - dsp.rms_db(st['logo'][dsp.n_of(logo):dsp.n_of(logo + 2.0)]))
    n_tot = dsp.n_of(total)
    fade_end = F(S['fade_end'])
    g = np.ones(N)
    i_fe = dsp.n_of(fade_end)
    i_fs = dsp.n_of(fade_end - 1.8)
    g[i_fs:i_fe] = np.cos(np.linspace(0, np.pi / 2, i_fe - i_fs)) ** 2
    g[i_fe:] = 0
    # cisza przed dropem (f474-480): calosc do zera w ~10 ms, wejscie na f480
    i_c, i_d = dsp.n_of(bcut), dsp.n_of(bend)
    g[i_c:i_d] = 0.0
    for name in st:
        st[name] = (st[name] * g[:, None])[:n_tot]
    mix = sum(st.values())
    mix = dsp.soft_clip(mix * 1.0, 1.2)                     # nasycenie "tasmowe"
    mix = dsp.eq(mix, 'highshelf', 12000, -2.0)
    lo = dsp.lp(mix, 120, 4)                               # bas < 120 Hz w mono
    mix = mix - lo + lo.mean(axis=1, keepdims=True)
    env = np.sqrt(np.maximum(dsp.uniform_filter1d(np.mean(mix ** 2, axis=1), int(0.05 * SR)), 0))
    lvl = dsp.lin2db(env)
    thr = np.percentile(lvl[lvl > -60], 70) if np.any(lvl > -60) else -20
    gr = np.where(lvl > thr, (lvl - thr) * (1 - 1 / 1.5), 0.0)
    mix = mix * dsp.db2lin(-dsp.uniform_filter1d(gr, int(0.1 * SR)))[:, None]
    mix, L, tp = dsp.normalize_lufs(mix, -14.0, -1.5)
    mix[i_c:i_d] = 0.0
    mix[i_fe:] = 0.0
    markers = {
        'version_s': version, 'bpm': bpm, 'fps': FPS, 'duration': round(total, 3),
        'bar_s': round(F(60), 4), 'sections_frames': {k_: v for k_, v in S.items() if k_ not in ('chords',)},
        'chords_frames': S['chords'], 'reveal_s': round(rev, 4), 'drop_s': round(d0, 4), 'logo_s': round(logo, 4),
        'silence_s': [round(bcut, 4), round(bend, 4)], 'kicks_s': [round(x, 4) for x in sorted(kicks)],
        'notes': sorted(notes_log, key=lambda x: x['t']), 'lufs': round(L, 2), 'true_peak_dbtp': round(tp, 2),
        'seed': seed,
    }
    return mix, st, markers


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('-o', '--out', default=None)
    ap.add_argument('--version', type=int, choices=[30, 15], default=30)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--bpm', type=float, default=100.0, help='tylko eksperymentalnie: skaluje caly timing (brief: 100)')
    ap.add_argument('--no-stems', action='store_true')
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, 'music', 'synth_v1.wav' if a.version == 30 else 'synth_v1_15s.wav')
    mix, stems, mk = compose(a.version, a.seed, a.bpm)
    dsp.write_wav(out, mix)
    base = os.path.splitext(out)[0]
    if not a.no_stems:
        for k, v in stems.items():
            dsp.write_wav(os.path.join(base + '_stems', f'{k}.wav'), v)
    with open(base + '.json', 'w') as f:
        json.dump(mk, f, indent=1)
    print(f'{out}: {len(mix) / SR:.2f} s, {mk["lufs"]} LUFS, TP {mk["true_peak_dbtp"]} dBTP, '
          f'odslona {mk["reveal_s"]} s, drop {mk["drop_s"]} s, logo {mk["logo_s"]} s, nut motywu: {len(mk["notes"])}')


if __name__ == '__main__':
    main()
