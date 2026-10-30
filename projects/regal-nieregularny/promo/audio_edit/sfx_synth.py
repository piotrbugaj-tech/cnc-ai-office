#!/usr/bin/env python3
"""sfx_synth.py - syntezowany Foley premium dla promo regalu ze sklejki.

Modele fizyczne (uproszczone), nie "syntezator":
  * prowadnica kulkowa = proces Poissona mikro-uderzen kulek (gestosc ~ predkosc)
    -> bank modow stalowej szyny + szum tarcia + toczenie z okresowoscia klatki kulek,
    calosc przez rezonanse skrzynki ze sklejki,
  * cichy domyk = zaczep (klik tworzywa) + tlumik (szum powietrza z opadajacym filtrem)
    + spowalnianie wg wykladniczej krzywej + miekki "tok" frontu (modalna plyta 18 mm),
  * ladowanie formatki = mody plyty (wzor dla plyty swobodnie podpartej, E~9 GPa,
    rho~680 kg/m3, h=18 mm) + poduszka powietrzna + "thud" masy,
  * wkretarka = silnik (harmoniczne + komutator + przekladnia) + trzaski wlokien drewna.
Kazdy dzwiek ma lekka symulacje pomieszczenia (wczesne odbicia + krotki ogon).

Uzycie:
  python3 sfx_synth.py --all                 # probki do samples/ + samples/index.json + sfx_demo.wav
  python3 sfx_synth.py --one drawer_close --params '{"push":0.4,"damp":0.6}' --seed 3 -o x.wav
  python3 sfx_synth.py --list

Z kodu (np. edit.py / timeline.py):
  from sfx_synth import render
  sfx = render('drawer_close', seed=2, push=0.4, damp=0.55)   # -> Sfx(audio[n,2], anchors{}, meta{})
Kazdy Sfx ma `anchors` (sekundy od poczatku pliku) - punkt synchronizacji,
np. 'engage' / 'closed' dla domyku, 'impact' dla ladowania, 'peak' dla whoosha.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402
from dsp import SR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PRE = 0.04  # pre-roll [s] przed pierwszym zdarzeniem w kazdym dzwieku


@dataclass
class Sfx:
    audio: np.ndarray                      # (n, 2) float64
    anchors: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    @property
    def duration(self):
        return len(self.audio) / SR


# ==========================================================================
# wspolne klocki
# ==========================================================================
def _finish(dry, r, room='small', wet=None, pan=0.0, width=0.35, hp_hz=28.0, tail=True):
    """Mono dry -> pan + pomieszczenie (stereo) -> filtr podcinajacy."""
    rooms = {
        # rt60, predelay, brightness, wet
        'small': (0.32, 0.0035, 0.55, 0.13),     # studio/salon z meblami
        'studio': (0.55, 0.006, 0.5, 0.16),      # wieksze studio fotograficzne
        'hall': (1.9, 0.022, 0.35, 0.22),        # na akcenty (boom)
        'dry': (0.18, 0.002, 0.6, 0.06),
    }
    rt, pdl, br, w = rooms[room]
    w = w if wet is None else wet
    st = dsp.pan_mono(dry, pan)
    if width > 0:
        side = dsp.decorrelate(dry, r, 5.0) * 0.5
        st[:, 0] += side * width * 0.35
        st[:, 1] -= side * width * 0.35
    out = dsp.reverb(st, wet=w, dry=1.0, rt60=rt, predelay=pdl, brightness=br, seed=int(r.integers(1, 9999)))
    out = dsp.hp(out, hp_hz, 2)
    # wyciszenie ogona do zera (bez obcietego szumu)
    out = dsp.fade(out, 0.0, min(0.06, len(out) / SR * 0.2))
    return out


def _plate_modes(L, W, h=0.018, E=9.0e9, rho=680.0, nu=0.3, mmax=4, nmax=4, fmax=6000):
    """Czestotliwosci modow plyty swobodnie podpartej [Hz] (posortowane) + indeksy (m,n)."""
    D = E * h ** 3 / (12 * (1 - nu ** 2))
    c = np.pi / 2 * np.sqrt(D / (rho * h))
    out = []
    for m in range(1, mmax + 1):
        for n in range(1, nmax + 1):
            f = c * ((m / L) ** 2 + (n / W) ** 2)
            if f < fmax:
                out.append((f, m, n))
    out.sort()
    return out


def _wood_knock(r, L=0.5, W=0.2, contact=0.002, loss=0.03, level=1.0, low_body=0.0,
                body_f=110.0, dur=0.35, x0=None, y0=None):
    """Uderzenie w element ze sklejki 18 mm (synteza modalna + kontakt polsinusoidalny)."""
    modes = _plate_modes(L, W)[:16]
    x0 = r.uniform(0.2, 0.8) if x0 is None else x0
    y0 = r.uniform(0.2, 0.8) if y0 is None else y0
    freqs, decs, amps = [], [], []
    f1 = modes[0][0] if modes else 200
    for f, m, n in modes:
        f *= r.uniform(0.97, 1.03)            # niejednorodnosc sklejki
        a = abs(np.sin(m * np.pi * x0) * np.sin(n * np.pi * y0)) * (f1 / f) ** 0.35
        tau = 1.0 / (np.pi * f * loss * r.uniform(0.8, 1.25))
        freqs.append(f); decs.append(min(tau, 0.25)); amps.append(a)
    # dodatkowe mody "materialowe" (wlokna, krawedzie warstw) - krotkie, jasniejsze
    for f in r.uniform(900, 3200, 5):
        freqs.append(f); decs.append(r.uniform(0.004, 0.012)); amps.append(r.uniform(0.05, 0.15))
    n = dsp.n_of(dur)
    exc = np.zeros(n)
    p = dsp.half_sine_pulse(contact)
    exc[:len(p)] = p
    y = dsp.resonator_bank(exc, freqs, decs, amps)
    y /= (np.max(np.abs(y)) + 1e-12)
    # krotki "klik" kontaktu (jasny), ograniczony przez miekkosc kontaktu
    click = dsp.bp(r.standard_normal(n) * dsp.env_ad(n, 0.0002, 0.0025), 1500, 7000)
    click = dsp.lp(click, min(9000, 1.2 / max(contact, 1e-4)), 2)
    y += click * 0.25 / (np.max(np.abs(click)) + 1e-12)
    if low_body > 0:
        t = dsp.t_axis(dur)
        fb = body_f * (1 + 0.18 * np.exp(-t / 0.012))
        body = np.sin(dsp.phase_from_freq(fb)) * dsp.env_ad(n, 0.0015, 0.055)
        y += body * low_body
    return y * level


def _plastic_click(r, level=1.0, bright=1.0, dur=0.06):
    """Klik mechanizmu z tworzywa/stali (zaczep, zatrzask)."""
    n = dsp.n_of(dur)
    exc = np.zeros(n)
    exc[:3] = [1.0, -0.6, 0.2]
    freqs = np.array([2150, 3420, 4870, 6630, 8900]) * r.uniform(0.92, 1.08) * (0.85 + 0.15 * bright)
    decs = np.array([0.009, 0.006, 0.004, 0.003, 0.002]) * r.uniform(0.8, 1.2)
    amps = np.array([1.0, 0.7, 0.45, 0.3, 0.15]) * r.uniform(0.7, 1.0, 5)
    y = dsp.resonator_bank(exc, freqs, decs, amps)
    # druga, cichsza "polowka" klika (zatrzask ma 2 fazy)
    d2 = int(r.uniform(0.004, 0.009) * SR)
    y2 = np.zeros(n)
    y2[d2:] = y[:n - d2] * r.uniform(0.25, 0.45)
    y = y + y2
    return y / (np.max(np.abs(y)) + 1e-12) * level


def _ballbearing_layer(r, v, vmax, intensity=1.0, pos=None):
    """Toczenie prowadnicy kulkowej dla profilu predkosci v [m/s].
    pos 0..1 = wysuw; mody szyny przesuwaja sie wraz z dlugoscia wysiegu (2 banki, crossfade)."""
    n = len(v)
    vn = np.clip(v / max(vmax, 1e-6), 0, 1.5)
    if pos is None:
        pos = np.cumsum(np.maximum(v, 0)) / SR
        pos = pos / (pos[-1] + 1e-12)
    # 1) mikro-uderzenia kulek (Poisson), amplituda lognormalna
    rate = 3200 * vn + 30 * (vn > 0.02)
    idx = dsp.poisson_events(rate, r)
    imp = np.zeros(n)
    amp = r.lognormal(0, 0.6, len(idx)) * (vn[idx] ** 0.7 if len(idx) else 1)
    np.add.at(imp, idx, amp * r.choice([-1, 1], len(idx)))
    base = np.array([1340, 2210, 3170, 4480, 6120, 8350, 10400]) * r.uniform(0.95, 1.05)
    rail_d = np.array([0.0045, 0.0035, 0.003, 0.0024, 0.0018, 0.0013, 0.001])  # Q ~ 15-30 (blacha w stali ocynk.)
    rail_a = np.array([0.55, 1.0, 0.85, 0.65, 0.45, 0.25, 0.12])
    t_in = dsp.resonator_bank(imp, base, rail_d, rail_a)
    t_out = dsp.resonator_bank(imp, base * r.uniform(0.86, 0.92, len(base)), rail_d * 1.2, rail_a)
    ticks = t_in * (1 - pos) + t_out * pos
    ticks /= (np.std(ticks) + 1e-12)
    # 2) syk tarcia (szum szerokopasmowy) ~ v^1.3
    hiss = dsp.bp(r.standard_normal(n), 1600, 9000, 2)
    hiss = hiss / (np.std(hiss) + 1e-12) * vn ** 1.3
    # 3) toczenie "rrrr" w srednicy + okresowosc klatki kulek (rozstaw ~6.5 mm)
    ph = dsp.phase_from_freq(np.maximum(v, 0) / 0.0065)
    roll_am = 1 + 0.35 * np.sin(ph) + 0.15 * np.sin(2 * ph + 1.1)
    rumble = dsp.bp(dsp.pink(n, r), 220, 1400, 2)
    rumble = rumble / (np.std(rumble) + 1e-12) * vn ** 1.2 * roll_am
    layer = 0.6 * ticks * vn ** 0.6 + 0.2 * hiss + 0.5 * rumble
    return layer * intensity


def _box_resonance(r, x, mix=0.45, size=1.0):
    """Skrzynka szuflady ze sklejki jako rezonator (mody scianek ~200-1300 Hz)."""
    # gesty zbior modow (scianki, dno 6.5 mm, polaczenia na wkrety) -> formanty, nie "tony"
    f = np.sort(np.exp(r.uniform(np.log(180), np.log(1700), 14))) / size
    d = 1.0 / (np.pi * f * r.uniform(0.045, 0.075, len(f)))
    a = np.interp(np.log(f), np.log([180, 400, 800, 1700]), [0.5, 1.0, 0.8, 0.35]) * r.uniform(0.6, 1.0, len(f))
    y = dsp.resonator_bank(x, f, d, a)
    y = y / (np.std(y) + 1e-12) * (np.std(x) + 1e-12)
    return (1 - mix) * x + mix * y


def _air_puff(r, n, at_i, level=0.3, dur=0.07, lo=60, hi=320):
    """Niskie "whump" sprezonego powietrza (zamykanie szuflady/drzwiczek)."""
    k = dsp.n_of(dur)
    nz = dsp.lp(dsp.bp(r.standard_normal(k), lo, hi, 2), hi, 2)
    e = dsp.env_ad(k, dur * 0.35, dur * 0.25)
    y = np.zeros(n)
    i0 = max(0, at_i - int(k * 0.35))
    seg = (nz * e)[: n - i0]
    y[i0:i0 + len(seg)] = seg / (np.max(np.abs(seg)) + 1e-12) * level
    return y


# ==========================================================================
# SZUFLADA (Hettich KA 4532 Silent System)
# ==========================================================================
def drawer_open(duration=0.9, intensity=1.0, travel=0.35, end_hit=0.35, seed=0, pan=0.0, room='small'):
    """Wysuw szuflady na prowadnicy kulkowej (pelny wysuw).
    duration = czas ruchu [s] (dopasuj do animacji), travel = wysuw [m]."""
    r = dsp.rng(seed)
    tail = 0.45
    n = dsp.n_of(PRE + duration + tail)
    t = np.arange(n) / SR
    s = np.clip((t - PRE) / duration, 0, 1)
    # profil: szybkie szarpniecie i hamowanie na ogranicznik (asymetryczna beta)
    shape = (s ** 0.55) * ((1 - s) ** 1.25)
    shape[(t < PRE) | (t > PRE + duration)] = 0
    v = shape / (np.sum(shape) / SR + 1e-12) * travel
    vmax = v.max()
    y = _ballbearing_layer(r, v, vmax, 1.0)
    y = _box_resonance(r, y, 0.45)
    y /= (np.max(np.abs(y)) + 1e-12)
    y *= 0.55
    # zwolnienie zatrzasku Silent System + lekkie "puk" frontu przy pociagnieciu
    i0 = int(PRE * SR)
    c = _plastic_click(r, 0.32, 0.9)
    y[i0:i0 + len(c)] += c[: n - i0]
    k = _wood_knock(r, 0.55, 0.2, contact=0.004, loss=0.05, level=0.12)
    y[i0:i0 + len(k)] += k[: n - i0]
    # ogranicznik wysuwu: gumowy odbojnik + dogonienie koszyka kulek
    ie = int((PRE + duration) * SR)
    if end_hit > 0 and ie < n:
        stop = _stop_core(r) * 0.6 * end_hit
        y[ie:ie + len(stop)] += stop[: n - ie]
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'start': PRE, 'sync': PRE, 'end': PRE + duration},
               {'type': 'drawer_open', 'duration': duration, 'seed': seed})


def drawer_close(push=0.42, damp=0.55, intensity=1.0, seed=0, pan=0.0, room='small', catch_level=0.35):
    """Domykanie z Silent System: pchniecie -> zaczep -> tlumienie ("fssst") -> miekki stuk.
    push = czas od startu do zaczepu [s], damp = czas tlumienia do zamkniecia [s]."""
    r = dsp.rng(seed)
    tail = 0.5
    t_eng = PRE + push
    t_cls = t_eng + damp
    n = dsp.n_of(t_cls + tail)
    t = np.arange(n) / SR
    # predkosc: pchniecie (narasta 60 ms) i hamowanie tarciem, potem tlumik (wykladniczo)
    v0 = 0.32 / max(push, 0.15) * 1.25
    vp = v0 * dsp.smoothstep((t - PRE) / 0.06) * (1 - 0.6 * np.clip((t - PRE) / push, 0, 1))
    v = np.where(t < t_eng, vp, 0.0)
    ve = v0 * 0.4
    sd = np.clip((t - t_eng) / damp, 0, 1)
    v_damp = ve * (1 - sd) ** 2.2
    v = np.where((t >= t_eng) & (t < t_cls), v_damp, v)
    v[t < PRE] = 0
    vmax = v.max()
    y = _ballbearing_layer(r, v, vmax, 0.9)
    y = _box_resonance(r, y, 0.5)
    y /= (np.max(np.abs(y)) + 1e-12)
    y *= 0.5
    # zaczep mechanizmu domyku
    ie = int(t_eng * SR)
    c = _catch_core(r) * catch_level
    y[ie:ie + len(c)] += c[: n - ie]
    # tlumik: "fssst" - szum z opadajacym srodkiem pasma (powietrze uciekajace z tlumika)
    k = int(damp * SR) + int(0.05 * SR)
    td = np.arange(k) / SR
    fc = 2300 * (1 - 0.65 * np.clip(td / damp, 0, 1) ** 0.8) + 450
    nz = dsp.tv_biquad(dsp.pink(k, r), fc, q=1.3, kind='bandpass', stages=2)
    env = dsp.smoothstep(td / 0.045) * (1 - np.clip(td / damp, 0, 1)) ** 1.4
    hiss = nz / (np.std(nz) + 1e-12) * env * 0.1
    y[ie:ie + k] += hiss[: n - ie]
    # finalny miekki stuk frontu (zderzak) + puff powietrza zamykanej komory
    ic = int(t_cls * SR)
    tk_ = _thup_core(r) * 0.55
    y[ic:ic + len(tk_)] += tk_[: n - ic]
    y += _air_puff(r, n, ic, level=0.12)
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'start': PRE, 'engage': t_eng, 'closed': t_cls, 'sync': t_cls},
               {'type': 'drawer_close', 'push': push, 'damp': damp, 'seed': seed})


# ==========================================================================
# DRZWICZKI (Blum CLIP top BLUMOTION)
# ==========================================================================
def _creak(r, n, i0, k, level, f_lo=140, f_hi=330):
    """Stick-slip zawiasu: impulsy o zmiennej czestotliwosci przez rezonanse metalu/drewna."""
    if level <= 0:
        return np.zeros(n)
    td = np.arange(k) / SR
    f = f_lo + (f_hi - f_lo) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * td + r.uniform(0, 6)))
    f *= 1 + 0.08 * dsp.smooth_noise(k, r, 12)
    ph = dsp.phase_from_freq(f) / (2 * np.pi)
    pulses = np.diff(np.floor(ph), prepend=0) > 0
    exc = pulses.astype(float) * r.lognormal(0, 0.3, k)
    y = dsp.resonator_bank(exc, [880, 1740, 2630, 3900], [0.006, 0.004, 0.003, 0.002], [1, 0.7, 0.4, 0.2])
    y *= np.sin(np.pi * np.clip(td / (k / SR), 0, 1)) ** 2
    out = np.zeros(n)
    out[i0:i0 + k] = (y / (np.max(np.abs(y)) + 1e-12) * level)[: n - i0]
    return out


def door_open(duration=0.8, intensity=1.0, creak=0.0, seed=0, pan=0.0, room='small'):
    """Otwieranie drzwiczek: wyskok z zawiasu (sprezyna), ruch powietrza, opcjonalne skrzypniecie."""
    r = dsp.rng(seed)
    tail = 0.35
    n = dsp.n_of(PRE + duration + tail)
    t = np.arange(n) / SR
    i0 = int(PRE * SR)
    y = np.zeros(n)
    c = _plastic_click(r, 0.22, 1.2)                     # zawias "puszcza" sprezyne
    y[i0:i0 + len(c)] += c[: n - i0]
    k = _wood_knock(r, 0.4, 0.3, contact=0.005, loss=0.06, level=0.08)
    y[i0:i0 + len(k)] += k[: n - i0]
    s = np.clip((t - PRE) / duration, 0, 1)
    w = np.sin(np.pi * s) ** 1.5 * ((t > PRE) & (t < PRE + duration))
    air = dsp.bp(dsp.pink(n, r), 160, 1100, 2)
    y += air / (np.std(air) + 1e-12) * w * 0.03
    y += _creak(r, n, i0 + int(0.08 * SR), int(duration * 0.6 * SR), 0.12 * creak)
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'start': PRE, 'sync': PRE, 'end': PRE + duration},
               {'type': 'door_open', 'duration': duration, 'seed': seed})


def door_close(push=0.45, damp=0.6, intensity=1.0, creak=0.0, seed=0, pan=0.0, room='small'):
    """Zamykanie z BLUMOTION: ruch -> tlumik hydrauliczny (cichy, nizszy niz w szufladzie)
    -> finalne ciche "tk" (ramie zawiasu + zlicowany front)."""
    r = dsp.rng(seed)
    tail = 0.45
    t_eng = PRE + push
    t_cls = t_eng + damp
    n = dsp.n_of(t_cls + tail)
    t = np.arange(n) / SR
    y = np.zeros(n)
    # ruch powietrza przez plyte drzwiczek
    w = np.clip((t - PRE) / push, 0, 1)
    swing = np.where(t < t_eng, np.sin(np.pi * 0.5 * w) ** 2, np.exp(-(t - t_eng) / (damp * 0.35)))
    swing[t < PRE] = 0
    air = dsp.bp(dsp.pink(n, r), 140, 900, 2)
    y += air / (np.std(air) + 1e-12) * swing * 0.035
    # zaczep tlumika (bardzo delikatny)
    ie = int(t_eng * SR)
    c = _door_catch_core(r) * 0.16
    y[ie:ie + len(c)] += c[: n - ie]
    # tlumienie hydrauliczne - lepkie "hsss"
    k = int(damp * SR)
    td = np.arange(k) / SR
    fc = 1800 * (1 - 0.5 * td / damp) + 450
    nz = dsp.tv_biquad(r.standard_normal(k), fc, q=1.6, kind='bandpass', stages=2)
    env = dsp.smoothstep(td / 0.05) * (1 - td / damp) ** 1.8
    y[ie:ie + k] += (nz / (np.std(nz) + 1e-12) * env * 0.07)[: n - ie]
    y += _creak(r, n, ie, k, 0.08 * creak, 90, 180)
    # finalne "tk": metal zawiasu (jasny klik) + delikatne drewno
    ic = int(t_cls * SR)
    tk_ = _tok_core(r) * 0.5
    y[ic:ic + len(tk_)] += tk_[: n - ic]
    y += _air_puff(r, n, ic, level=0.07, lo=80, hi=400)
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'start': PRE, 'engage': t_eng, 'closed': t_cls, 'click': t_cls, 'sync': t_cls},
               {'type': 'door_close', 'push': push, 'damp': damp, 'seed': seed})


# ==========================================================================
# MONTAZ FLAT-PACK
# ==========================================================================
def whoosh(duration=0.7, size=1.0, height=0.5, direction=1.0, intensity=1.0, seed=0, room='studio',
           peak_at=0.62):
    """Przelot formatki. size ~ dlugosc [m] (wieksza = nizej, wiecej 'flutter'),
    height 0..1 (wyzej = jasniej), direction +1 L->P, -1 P->L, 0 = srodek."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration + 0.25)
    t = np.arange(n) / SR
    tp = duration * peak_at
    wl, wr = tp * 0.55, (duration - tp) * 0.45 + 0.03
    e = np.where(t < tp, np.exp(-((t - tp) / wl) ** 2), np.exp(-((t - tp) / wr) ** 2))
    dop = -np.tanh((t - tp) / (0.25 * duration))  # +1 -> -1 (spadek "wysokosci")
    f0 = 900 / np.sqrt(max(size, 0.1)) * (0.7 + 0.6 * height)
    fc = f0 * (1 + 0.45 * dop) * (1 + 0.6 * e)
    src = dsp.pink(n, r)
    body = dsp.tv_biquad(src, fc, q=0.9, kind='bandpass', stages=2)
    body /= (np.std(body) + 1e-12)
    # turbulencja plaskiej plyty (flutter) - im wieksza formatka tym wolniej i mocniej
    f_fl = 22 / max(size, 0.3) ** 0.5
    am = 1 + (0.18 + 0.15 * min(size, 1.5)) * np.sin(2 * np.pi * f_fl * t + r.uniform(0, 6)) \
        + 0.25 * dsp.smooth_noise(n, r, 35)
    low = dsp.lp(dsp.brown(n, r), 220, 2)
    low /= (np.std(low) + 1e-12)
    air = dsp.hp(dsp.pink(n, r), 5000, 2)
    air /= (np.std(air) + 1e-12)
    y = (body * np.clip(am, 0.2, 2) + 0.55 * min(size, 1.6) * low + 0.18 * (0.5 + height) * air) * e
    y /= (np.max(np.abs(y)) + 1e-12)
    pan = 0.8 * direction * np.tanh((t - tp) / (0.3 * duration))
    st = dsp.pan_mono(y * 0.8 * intensity, pan)
    out = dsp.reverb(st, wet=0.12, rt60=0.55, predelay=0.006, brightness=0.5, seed=seed + 11)
    out = dsp.fade(dsp.hp(out, 30, 2), 0.01, 0.08)
    return Sfx(out, {'start': 0.0, 'peak': tp, 'sync': tp, 'end': duration},
               {'type': 'whoosh', 'duration': duration, 'size': size, 'seed': seed})


def land(mass=6.0, size=(1.0, 0.4), surface='floor', hardness=0.5, intensity=1.0, seed=0, pan=0.0,
         room='studio', bounce=None):
    """Ladowanie formatki 18 mm: poduszka powietrzna + mody plyty + 'thud' masy.
    mass [kg] (formatka 1000x400x18 ~ 4.9 kg), size (L, W) [m], surface floor|stack|table."""
    r = dsp.rng(seed)
    L, W = size
    dur = 0.9
    n = dsp.n_of(PRE + dur)
    i0 = int(PRE * SR)
    loss = {'floor': 0.04, 'stack': 0.03, 'table': 0.034}[surface]
    contact = 0.0007 + (1 - hardness) * 0.0028 + 0.0006 * np.sqrt(mass / 6)
    panel = _wood_knock(r, L, W, contact=contact, loss=loss, level=1.0, dur=dur)
    y = np.zeros(n)
    y[i0:] += panel[: n - i0] * 1.0
    # "thud" masy (podloga/stos) - nizej i dluzej dla ciezszych
    fb = 78 * (6.0 / max(mass, 0.3)) ** 0.22 * {'floor': 1.0, 'stack': 1.15, 'table': 1.35}[surface]
    tt = np.arange(n - i0) / SR
    thud = np.sin(dsp.phase_from_freq(fb * (1 + 0.25 * np.exp(-tt / 0.01)))) * \
        dsp.env_ad(n - i0, 0.002, 0.045 + 0.012 * np.sqrt(mass))
    y[i0:] += thud * 0.42 * min(1.6, (mass / 6) ** 0.45)
    # poduszka powietrzna miedzy plaskimi powierzchniami ("pff" tuz przed i w chwili uderzenia)
    k = int(0.04 * SR)
    cush = dsp.bp(r.standard_normal(k), 250, 2200, 2)
    ce = np.concatenate([np.linspace(0, 1, int(k * 0.6)) ** 2, np.exp(-np.arange(k - int(k * 0.6)) / (0.004 * SR))])
    cush = cush / (np.max(np.abs(cush)) + 1e-12) * ce * 0.22 * min(1.5, L * W / 0.3) ** 0.5
    j0 = i0 - int(k * 0.6)
    y[j0:j0 + k] += cush
    # odbicie wtorne dla lekkich elementow
    if bounce is None:
        bounce = mass < 4
    if bounce:
        dt = r.uniform(0.035, 0.07)
        b = _wood_knock(r, L, W, contact=contact * 1.3, loss=loss * 1.3, level=r.uniform(0.12, 0.22), dur=0.4)
        j = i0 + int(dt * SR)
        y[j:j + len(b)] += b[: n - j]
    # krawedziowe "grzechotanie" warstw sklejki - delikatny, szybki szum
    grit = dsp.hp(r.standard_normal(n - i0), 2500, 2) * dsp.env_ad(n - i0, 0.0005, 0.012) * 0.06
    y[i0:] += grit
    y = dsp.soft_clip(y / (np.max(np.abs(y)) + 1e-12), 1.2) * 0.9 * intensity
    out = _finish(y, r, room=room, pan=pan, wet=0.15)
    return Sfx(out, {'impact': PRE, 'sync': PRE},
               {'type': 'land', 'mass': mass, 'size': list(size), 'surface': surface, 'seed': seed})


def screw(duration=0.9, rpm_hz=310.0, load=0.7, intensity=1.0, seed=0, pan=0.0, room='small', seat=True):
    """Krotkie wkrecanie wkretu 4x50 wkretarka akumulatorowa: rozpedzenie, obciazenie
    (spadek obrotow + trzaski wlokien), osadzenie lba w fazie, puszczenie spustu."""
    r = dsp.rng(seed)
    tail = 0.35
    n = dsp.n_of(PRE + duration + tail)
    t = np.arange(n) / SR
    s = np.clip((t - PRE) / duration, 0, 1)
    on = (t >= PRE) & (t <= PRE + duration)
    spin = 1 - np.exp(-np.maximum(t - PRE, 0) / 0.035)
    loadc = 1 - 0.16 * load * s ** 1.3 - 0.03 * dsp.smooth_noise(n, r, 9)
    f = rpm_hz * spin * loadc
    # wybieg po puszczeniu spustu
    rel = np.exp(-np.maximum(t - (PRE + duration), 0) / 0.07)
    f = np.where(t > PRE + duration, rpm_hz * (1 - 0.16 * load) * rel, f)
    f[t < PRE] = 0
    ph = dsp.phase_from_freq(f)
    motor = np.zeros(n)
    for k_, a in [(1, 1.0), (2, 0.75), (3, 0.55), (4, 0.25), (5, 0.18), (6, 0.22), (8, 0.1), (10, 0.06), (12, 0.05)]:
        motor += a * np.sin(k_ * ph + r.uniform(0, 6))
    gear = np.sin(7.31 * ph) * 0.22 + np.sin(14.62 * ph) * 0.08     # zazebienie przekladni
    brush = dsp.bp(r.standard_normal(n), 2000, 8000, 2) * (1 + 0.6 * np.sin(2 * ph))
    brush /= (np.std(brush) + 1e-12)
    amp = np.where(t <= PRE + duration, dsp.smoothstep((t - PRE) / 0.02), rel ** 1.5)
    amp[t < PRE] = 0
    y = (motor * 0.28 + gear + brush * 0.12) * amp
    y = dsp.eq(y, 'peak', 1150, 6, 1.4)      # rezonans obudowy
    y = dsp.eq(y, 'peak', 2700, 3, 2.0)
    y = dsp.hp(y, 120, 2)
    # trzaski wlokien drewna (gestosc rosnie z glebokoscia)
    rate = (120 + 520 * s ** 1.2) * on * load
    idx = dsp.poisson_events(rate, r)
    imp = np.zeros(n)
    np.add.at(imp, idx, r.lognormal(0, 0.6, len(idx)) * r.choice([-1, 1], len(idx)))
    crack = dsp.resonator_bank(imp, [430, 880, 1520, 2610, 3900], [0.012, 0.009, 0.006, 0.004, 0.003],
                               [0.7, 1, 0.8, 0.5, 0.3])
    crack /= (np.std(crack) + 1e-12)
    y = y / (np.std(y[on]) + 1e-12) * 0.18 + crack * 0.07 * (0.4 + s)
    anchors = {'start': PRE, 'sync': PRE, 'end': PRE + duration}
    if seat:
        # osadzenie lba w fazie: krotkie skrzypniecie + stuk
        i_s = int((PRE + duration - 0.06) * SR)
        cr = _creak(r, n, i_s, int(0.08 * SR), 0.18, 45, 70)
        y += cr
        kn = _wood_knock(r, 0.6, 0.4, contact=0.003, loss=0.05, level=0.28, low_body=0.25, body_f=130)
        j = int((PRE + duration) * SR)
        y[j:j + len(kn)] += kn[: n - j]
        anchors['seat'] = PRE + duration
    y = y / (np.max(np.abs(y)) + 1e-12) * 0.8 * intensity
    out = _finish(y, r, room=room, pan=pan, wet=0.1)
    return Sfx(out, anchors, {'type': 'screw', 'duration': duration, 'seed': seed})


def wood_tap(intensity=1.0, seed=0, pan=0.0, room='small', soft=0.5):
    """Dotkniecie / stukniecie palcem w front (gałka, dotyk dloni)."""
    r = dsp.rng(seed)
    y = _wood_knock(r, 0.4, 0.2, contact=0.0015 + soft * 0.003, loss=0.04, level=0.8, dur=0.4)
    y = np.concatenate([np.zeros(int(PRE * SR)), y])
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'wood_tap', 'seed': seed})


# ==========================================================================
# AKCENTY
# ==========================================================================
def sub_boom(duration=2.8, f_start=92.0, f_end=41.0, intensity=1.0, click=0.5, seed=0, tail_room=True):
    """Sub-hit na reveal: opadajacy sinus + harmoniczne (slyszalne na malych glosnikach)
    + miekki transjent + ciemny ogon hali."""
    r = dsp.rng(seed)
    n = dsp.n_of(PRE + duration)
    t = np.arange(n) / SR
    tt = np.maximum(t - PRE, 0)
    f = f_end + (f_start - f_end) * np.exp(-tt / 0.09)
    amp = dsp.smoothstep(tt / 0.006) * np.exp(-tt / (duration * 0.32))
    amp[t < PRE] = 0
    sub = np.sin(dsp.phase_from_freq(f)) * amp
    sub = dsp.soft_clip(sub * 1.6, 1.4) * 0.8  # 2. i 3. harmoniczna
    thump = dsp.lp(r.standard_normal(n), 180, 4) * dsp.env_ad(n, 0.002, 0.05)
    thump = np.roll(thump, int(PRE * SR))
    thump = thump / (np.max(np.abs(thump)) + 1e-12) * 0.35
    cl = dsp.bp(r.standard_normal(n), 1200, 5000, 2) * dsp.env_ad(n, 0.0003, 0.003)
    cl = np.roll(cl, int(PRE * SR))
    cl = cl / (np.max(np.abs(cl)) + 1e-12) * 0.12 * click
    y = sub + thump + cl
    st = dsp.to_stereo(y)
    if tail_room:
        st = dsp.reverb(st, wet=0.22, rt60=2.2, predelay=0.02, brightness=0.25, seed=seed + 5, hp_wet=60, tail=False)
    st = dsp.fade(st, 0.0, 0.25)
    st = dsp.peak_normalize(st, -1.0) * intensity
    return Sfx(st, {'hit': PRE, 'sync': PRE}, {'type': 'sub_boom', 'seed': seed})


def riser(duration=3.0, tonal=0.5, intensity=1.0, seed=0, root_hz=174.6):
    """Riser konczacy sie dokladnie w `end` (= anchor 'sync'): szum z otwierajacym sie filtrem,
    glissando kwinty i oktawy, odwrocony poglos."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    t = np.arange(n) / SR
    s = t / duration
    fc = 250 * (7500 / 250) ** (s ** 1.4)
    nz = dsp.tv_biquad(dsp.pink(n, r), fc, q=0.8, kind='bandpass', stages=1)
    nz /= (np.std(nz) + 1e-12)
    y_noise = nz * s ** 2.2
    tone = np.zeros(n)
    gl = 2 ** (s ** 1.6)   # +1 oktawa
    for mult, a in [(1, 0.5), (1.5, 0.35), (2, 0.3), (3, 0.12)]:
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
        tone += a * np.sin(dsp.phase_from_freq(root_hz * mult * gl * vib) + r.uniform(0, 6))
    tone *= s ** 3
    # odwrocony poglos szumowego "uderzenia"
    burst = dsp.hp(r.standard_normal(dsp.n_of(0.05)), 300, 2) * np.hanning(dsp.n_of(0.05))
    wet = dsp.reverb(burst, wet=1.0, dry=0.0, rt60=min(2.4, duration * 0.8), predelay=0.0, brightness=0.6, seed=seed + 3)
    rev = wet[::-1][:, 0]
    rev = dsp.pad_to(rev[-n:] if len(rev) >= n else np.pad(rev, (n - len(rev), 0)), n)
    rev /= (np.max(np.abs(rev)) + 1e-12)
    y = 0.6 * y_noise / (np.max(np.abs(y_noise)) + 1e-12) + tonal * 0.35 * tone / (np.max(np.abs(tone)) + 1e-12) \
        + 0.4 * rev
    st = dsp.to_stereo(y)
    st[:, 1] = st[:, 1] * 0.6 + 0.4 * dsp.decorrelate(y, r, 8)
    st = dsp.ms_width(st, 1.0 + 0.6 * s.mean())
    st = dsp.fade(st, 0.05, 0.006)
    st = dsp.peak_normalize(st, -1.0) * intensity
    return Sfx(st, {'start': 0.0, 'end': duration, 'sync': duration}, {'type': 'riser', 'seed': seed})


def air(duration=1.2, brightness=0.5, intensity=1.0, seed=0, peak_at=0.45):
    """'Air' na przejscie: oddechowy, jasny szum z wolnym ruchem filtra, szeroki stereo."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    t = np.arange(n) / SR
    s = t / duration
    e = np.where(s < peak_at, np.sin(np.pi / 2 * s / peak_at) ** 2,
                 np.cos(np.pi / 2 * (s - peak_at) / (1 - peak_at)) ** 2)
    chans = []
    for c in range(2):
        fc = (4500 + 4000 * brightness) * (1 + 0.25 * dsp.smooth_noise(n, r, 1.5)) * (0.85 + 0.3 * e)
        z = dsp.tv_biquad(dsp.pink(n, r), fc, q=0.6, kind='bandpass', stages=1)
        z /= (np.std(z) + 1e-12)
        low = dsp.lp(dsp.brown(n, r), 180, 2)
        low /= (np.std(low) + 1e-12)
        chans.append((z + 0.25 * low) * e)
    st = np.stack(chans, axis=1)
    st = dsp.peak_normalize(st, -1.0) * intensity
    return Sfx(st, {'start': 0.0, 'peak': duration * peak_at, 'sync': duration * peak_at, 'end': duration},
               {'type': 'air', 'seed': seed})


def room_tone(duration=32.0, level_db=-52.0, hum=0.25, seed=0):
    """Cichy szum pokoju (studio dzienne): szum rozowy LP + niskie dudnienie budynku + slabe 50 Hz.
    level_db = RMS pliku. Zapetla sie (koniec przechodzi w poczatek)."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    t = np.arange(n) / SR
    chans = []
    common = dsp.lp(dsp.pink(n, r), 1200, 2)
    for c in range(2):
        own = dsp.lp(dsp.pink(n, r), 1200, 2)
        x = 0.55 * common + 0.45 * own
        x = dsp.eq(x, 'highshelf', 4000, -6)
        rumble = dsp.lp(dsp.brown(n, r), 120, 2)
        drift = 1 + 0.12 * dsp.smooth_noise(n, r, 0.15)
        x = (x / np.std(x) + 0.8 * rumble / np.std(rumble)) * drift
        h = sum(a * np.sin(2 * np.pi * f * t + r.uniform(0, 6)) for f, a in [(50, 1), (100, 0.5), (150, 0.25)])
        x += hum * 0.25 * h
        chans.append(x)
    st = np.stack(chans, axis=1)
    # bezszwowa petla: crossfade konca z poczatkiem
    xf = dsp.n_of(1.0)
    w = np.linspace(0, 1, xf)[:, None]
    st[:xf] = st[:xf] * w + st[-xf:] * (1 - w)
    st = st[:-xf]
    st = st * dsp.db2lin(level_db - dsp.rms_db(st))
    return Sfx(st, {'start': 0.0, 'sync': 0.0}, {'type': 'room_tone', 'level_db': level_db, 'seed': seed})


# ==========================================================================
# RECEPTURY Z research-brief.md (sekcja 6.2) - "hyper-real" Foley regalu RYTM
# ==========================================================================
def _modal_hit(r, freqs, taus, amps, exc_ms=1.0, dur=0.5, jitter=0.02, exc='hann'):
    """Uderzenie modalne wzbudzone krotkim impulsem (podniesiony kosinus = miekki, np. filc)."""
    n = dsp.n_of(dur)
    k = max(2, int(exc_ms * 1e-3 * SR))
    e = np.zeros(n)
    e[:k] = np.hanning(k + 2)[1:-1] if exc == 'hann' else dsp.half_sine_pulse(exc_ms * 1e-3)[:k]
    f = np.asarray(freqs, float) * r.uniform(1 - jitter, 1 + jitter, len(freqs))
    y = dsp.resonator_bank(e, f, taus, amps)
    return y / (np.max(np.abs(y)) + 1e-12)


def _thup_core(r, scale=1.0, soft_ms=5.0, low=1.0):
    """'thup' cichego domyku: sinus 82->70 Hz (tau 90 ms) + mody panelu 190/360/590/1050/1900 Hz
    wzbudzone podniesionym kosinusem 5 ms (filcowy odbojnik) + podmuch LP 500 Hz 35 ms."""
    dur = 0.6
    n = dsp.n_of(dur)
    t = np.arange(n) / SR
    f = (70 + 12 * np.exp(-t / 0.03)) * (scale ** 0.5)
    a = np.sin(dsp.phase_from_freq(f)) * np.exp(-t / 0.09) * dsp.smoothstep(t / 0.003)
    b = _modal_hit(r, np.array([190, 360, 590, 1050, 1900]) * scale, [0.07, 0.05, 0.032, 0.018, 0.009],
                   [1, 0.55, 0.35, 0.2, 0.08], exc_ms=soft_ms, dur=dur)
    c = dsp.lp(r.standard_normal(n), 500, 2) * dsp.env_ad(n, 0.004, 0.012)
    c[dsp.n_of(0.035):] = 0
    c /= (np.max(np.abs(c)) + 1e-12)
    y = 0.85 * low * a + 1.0 * b + 0.25 * c
    return y / (np.max(np.abs(y)) + 1e-12)


def _tok_core(r):
    """'tok' drzwiczek: mody 150/300/510/860/1550 Hz (tau 80/55/35/20/10 ms) + uderzenie 65 Hz (tau 60 ms)
    + klik zawiasu 5 kHz 2 ms (-26 dB, +15 ms)."""
    dur = 0.6
    n = dsp.n_of(dur)
    t = np.arange(n) / SR
    m = _modal_hit(r, [150, 300, 510, 860, 1550], [0.08, 0.055, 0.035, 0.02, 0.01], [1, 0.6, 0.4, 0.22, 0.1],
                   exc_ms=3.0, dur=dur)
    low = np.sin(2 * np.pi * 65 * t) * np.exp(-t / 0.06) * dsp.smoothstep(t / 0.002)
    y = m + 0.7 * low
    y /= (np.max(np.abs(y)) + 1e-12)
    k = dsp.bp(r.standard_normal(dsp.n_of(0.002)), 4000, 6500, 2)
    i = dsp.n_of(0.015)
    y[i:i + len(k)] += k / (np.max(np.abs(k)) + 1e-12) * dsp.db2lin(-26) * 4
    return y


def _stop_core(r):
    """Ogranicznik pelnego wysuwu: drewno 150/340/620 Hz (tau 50/35/20 ms) + klik metalu 2.8/5.6 kHz
    (tau 6 ms) + odbicie po 70 ms (-14 dB)."""
    dur = 0.5
    w = _modal_hit(r, [150, 340, 620], [0.05, 0.035, 0.02], [1, 0.6, 0.35], exc_ms=2.0, dur=dur)
    m = _modal_hit(r, [2800, 5600], [0.006, 0.006], [1, 0.5], exc_ms=0.3, dur=dur)
    y = w + 0.35 * m
    i = dsp.n_of(0.07)
    y[i:] += y[:len(y) - i] * dsp.db2lin(-14)
    return y / (np.max(np.abs(y)) + 1e-12)


def _catch_core(r):
    """Zatrzask Silent System: impuls 1.5 ms przez BP 2.2 kHz (Q4) + 3.6 kHz (plastik)."""
    n = dsp.n_of(0.08)
    e = np.zeros(n)
    k = dsp.n_of(0.0015)
    e[:k] = r.standard_normal(k) * np.hanning(k)
    b1, a1 = dsp.biquad('bandpass', 2200 * r.uniform(0.97, 1.03), 4)
    b2, a2 = dsp.biquad('bandpass', 3600 * r.uniform(0.97, 1.03), 6)
    from scipy import signal as _sg
    y = _sg.lfilter(b1, a1, e) + 0.6 * _sg.lfilter(b2, a2, e)
    y += 0.5 * dsp.resonator_bank(e, [2200, 3600], [0.004, 0.003], [1, 0.6])
    return y / (np.max(np.abs(y)) + 1e-12)


def _door_catch_core(r):
    """Zatrzask BLUMOTION: mody metalu 2.35/4.8/7.9 kHz (tau 7 ms) + szum 3 ms."""
    y = _modal_hit(r, [2350, 4800, 7900], [0.007, 0.007, 0.007], [1, 0.6, 0.35], exc_ms=0.25, dur=0.08)
    nz = r.standard_normal(dsp.n_of(0.003)) * np.hanning(dsp.n_of(0.003))
    y[:len(nz)] += dsp.hp(nz, 2000, 2) * 0.4
    return y / (np.max(np.abs(y)) + 1e-12)


def _roll_core(r, v, intensity=1.0):
    """Toczenie kulek KA 4532 wg briefu: A) Poisson 400 + 2500*v/vmax [1/s] przez BP 3.1/4.7/6.3 kHz (Q12, 4 ms),
    +-40 %; B) korpus: rozowy BP 120-450 Hz ~ v^0.8 + mody 180/260/410 Hz (tau 60 ms); C) szyna: HP 7 kHz ~ v.
    Filtry jasnieja z predkoscia (crossfade wersji ciemnej/jasnej)."""
    n = len(v)
    vn = np.clip(v / (np.max(v) + 1e-9), 0, 1)
    rate = (400 + 2500 * vn) * (vn > 0.01)
    idx = dsp.poisson_events(rate, r)
    imp = np.zeros(n)
    np.add.at(imp, idx, r.uniform(0.6, 1.4, len(idx)) * r.choice([-1, 1], len(idx)))
    A = dsp.resonator_bank(imp, [3100, 4700, 6300], [0.004] * 3, [1.0, 0.8, 0.55])
    A_dark = dsp.resonator_bank(imp, [2500, 3800, 5100], [0.004] * 3, [1.0, 0.8, 0.55])
    A = A * vn + A_dark * (1 - vn)
    A /= (np.std(A) + 1e-12)
    B = dsp.bp(dsp.pink(n, r), 120, 450, 2)
    B = B / (np.std(B) + 1e-12) * vn ** 0.8
    B = 0.6 * B + 0.4 * dsp.resonator_bank(B, [180, 260, 410], [0.06] * 3, [1, 0.8, 0.6]) / 30
    C = dsp.hp(r.standard_normal(n), 7000, 2)
    C = C / (np.std(C) + 1e-12) * vn
    y = 0.9 * A * vn ** 0.5 + 0.5 * B + 0.14 * C
    return y * intensity


def _v_from_curve(v_curve, fps, pre=PRE, tail=0.3):
    vc = np.abs(np.asarray(v_curve, float))
    tf = np.arange(len(vc)) / fps
    n = dsp.n_of(pre + len(vc) / fps + tail)
    t = np.arange(n) / SR - pre
    return np.interp(t, tf, vc, left=0, right=0)


def roll(duration=0.88, v_curve=None, fps=25, profile='open', intensity=1.0, seed=0, pan=0.0, room='small'):
    """Samo toczenie prowadnicy (bez zatrzaskow) wg krzywej predkosci z Blendera (v_curve: wartosc na klatke,
    dowolne jednostki) albo profilu 'open' (Hermite 0->max) / 'push' (szybkie dopchniecie)."""
    r = dsp.rng(seed)
    if v_curve is not None:
        v = _v_from_curve(v_curve, fps)
        duration = len(v_curve) / fps
    else:
        n = dsp.n_of(PRE + duration + 0.3)
        t = np.arange(n) / SR - PRE
        u = np.clip(t / duration, 0, 1)
        v = (6 * u * (1 - u)) if profile == 'open' else (u ** 0.4 * (1 - u) ** 0.9)
        v[(t < 0) | (t > duration)] = 0
    y = _roll_core(r, v, intensity)
    y = dsp.peak_normalize(y, -3)
    out = _finish(y, r, room=room, pan=pan)
    return Sfx(out, {'start': PRE, 'sync': PRE, 'end': PRE + duration}, {'type': 'roll', 'duration': duration})


def drawer_stop(intensity=1.0, seed=0, pan=0.0, room='small'):
    """'tunk' ogranicznika pelnego wysuwu (S03 f210)."""
    r = dsp.rng(seed)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), _stop_core(r)])
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'drawer_stop'})


def thup(intensity=1.0, scale=1.0, seed=0, pan=0.0, room='small', wet=None):
    """'thup' kontaktu cichego domyku (S04 f285, S09 f630 = logo dzwiekowe cz. 1)."""
    r = dsp.rng(seed)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), _thup_core(r, scale)])
    out = _finish(y * intensity, r, room=room, pan=pan, wet=wet)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'thup'})


def tok(intensity=1.0, seed=0, pan=0.0, room='small'):
    """'tok' + klik zawiasu przy domknieciu drzwiczek (S05 f330)."""
    r = dsp.rng(seed)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), _tok_core(r)])
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'tok'})


def catch(mech='drawer', intensity=1.0, seed=0, pan=0.0, room='small'):
    """Zatrzask mechanizmu: mech='drawer' (Silent System, plastik) albo 'door' (BLUMOTION, metal)."""
    r = dsp.rng(seed)
    core = _catch_core(r) if mech == 'drawer' else _door_catch_core(r)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), core, np.zeros(dsp.n_of(0.1))])
    out = _finish(y * intensity, r, room=room, pan=pan)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'catch', 'mech': mech})


def damper(duration=0.92, mech='drawer', intensity=1.0, seed=0, pan=0.0, room='small'):
    """Tlumik: szum LP 900 Hz ~ v (zanika) + olejowy syk BP 1.2-3 kHz (drawer) / ciszej i nizej (door)."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration + 0.1)
    t = np.arange(n) / SR
    u = np.clip(t / duration, 0, 1)
    v = 3 * (1 - u) ** 2 * dsp.smoothstep(t / 0.03)          # pochodna p = (1-u)^3
    a = dsp.lp(dsp.pink(n, r), 900, 2)
    lo, hi = (1200, 3000) if mech == 'drawer' else (700, 2000)
    b = dsp.bp(r.standard_normal(n), lo, hi, 2)
    y = dsp.hp((a / np.std(a) * 0.7 + b / np.std(b) * 0.35) * v, 90, 2)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y])
    y = dsp.peak_normalize(y, -3) * intensity
    out = _finish(y, r, room=room, pan=pan)
    return Sfx(out, {'start': PRE, 'sync': PRE, 'end': PRE + duration}, {'type': 'damper', 'mech': mech})


def door_air(duration=0.72, intensity=1.0, seed=0, pan_from=0.3, pan_to=-0.1, room='small'):
    """Powietrze zamykanych drzwi: szum BP 200-700 Hz ~ predkosc katowa, ruch w stereo."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    t = np.arange(n) / SR
    u = t / duration
    w = np.sin(np.pi * np.clip(u * 0.9 + 0.1, 0, 1)) ** 1.2
    y = dsp.bp(dsp.pink(n, r), 200, 700, 2)
    y = y / np.std(y) * w
    y = dsp.peak_normalize(y, -3) * intensity
    st = dsp.pan_mono(y, pan_from + (pan_to - pan_from) * u)
    st = dsp.reverb(st, wet=0.1, rt60=0.32, seed=seed + 2)
    return Sfx(st, {'start': 0.0, 'sync': 0.0, 'end': duration}, {'type': 'door_air'})


def caliper(midi=89, intensity=1.0, seed=0, pan=0.0):
    """Tykniecie 'suwmiarki' przy napisach CAD: klik 1 ms HP 3 kHz + ping sinus (F6/A6/C7) tau 70 ms."""
    r = dsp.rng(seed)
    n = dsp.n_of(0.5)
    t = np.arange(n) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    ping = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.07) * dsp.smoothstep(t / 0.0008)
    k = dsp.n_of(0.001)
    click = np.zeros(n)
    click[:k] = dsp.hp(r.standard_normal(k), 3000, 2)
    y = 0.8 * ping + 0.6 * click / (np.max(np.abs(click)) + 1e-12)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y])
    st = dsp.reverb(dsp.pan_mono(y, pan), wet=0.12, rt60=0.6, seed=seed + 3, tail=False)
    return Sfx(dsp.peak_normalize(st, -1) * intensity, {'impact': PRE, 'sync': PRE}, {'type': 'caliper', 'midi': midi})


def pops(count=140, spread=0.24, intensity=1.0, seed=0, width=0.6, times=None, pans=None):
    """'pop' formatek: count mikro-tykniec modalnych (f0 1.6-3.4 kHz, tau 10 ms), czas radialny
    (gestosc rosnie od srodka kadru na zewnatrz), panorama losowa. times/pans: dokladne czasy [s, wzgledem
    pierwszego] i panoramy z events.json (po jednym zdarzeniu 'pop' na formatke)."""
    r = dsp.rng(seed)
    if times is not None:
        times = PRE + np.asarray(times, float)
        count = len(times)
        spread = float(np.max(times) - PRE) if count else 0.0
    n = dsp.n_of(PRE + spread + 0.3)
    out = np.zeros((n, 2))
    if times is None:
        radial = np.sqrt(r.uniform(0, 1, count))      # rownomierne na tarczy -> wiecej na obwodzie
        times = PRE + radial * spread + r.normal(0, 0.004, count)
    for i in range(count):
        f0 = r.uniform(1600, 3400)
        y = _modal_hit(r, [f0, f0 * 2.31, f0 * 3.9], [0.01, 0.006, 0.003], [1, 0.4, 0.15], exc_ms=0.4, dur=0.06)
        y *= r.uniform(0.5, 1.0) * dsp.db2lin(r.uniform(-3, 0))
        pn = float(pans[i]) if pans is not None else r.uniform(-width, width)
        dsp.place(out, dsp.pan_mono(y, pn), times[i])
    out = dsp.reverb(out, wet=0.1, rt60=0.45, seed=seed + 4, tail=False)
    return Sfx(dsp.peak_normalize(out, -1) * intensity, {'start': PRE, 'sync': PRE, 'end': PRE + spread},
               {'type': 'pops', 'count': count})


def levitate(duration=0.32, intensity=1.0, seed=0):
    """Szum 'uniesienia' (S08 f480): BP przemiatany w gore w 0.32 s (sub-kick i bas sa w muzyce)."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration + 0.25)
    t = np.arange(n) / SR
    u = np.clip(t / duration, 0, 1)
    fc = 300 * (4000 / 300) ** u
    y = dsp.tv_biquad(dsp.pink(n, r), fc, q=1.2, kind='bandpass', stages=2)
    y = y / np.std(y) * np.sin(np.pi * np.clip(t / (duration + 0.2), 0, 1)) ** 1.5
    st = dsp.ms_width(np.stack([y, dsp.decorrelate(y, r, 7)], axis=1), 1.2)
    st = dsp.reverb(st, wet=0.15, rt60=0.9, seed=seed + 5, tail=False)
    return Sfx(dsp.peak_normalize(st, -1) * intensity, {'start': 0.0, 'sync': 0.0}, {'type': 'levitate'})


def fly(duration=0.56, peak_at=0.6, intensity=1.0, seed=0, pan_from=-0.3, pan_to=0.3):
    """Whoosh lotu formatki wg briefu: szum BP 350 Hz -> 2.2 kHz -> 700 Hz w 0.56 s, szczyt przy 60 %."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration + 0.1)
    t = np.arange(n) / SR
    u = np.clip(t / duration, 0, 1)
    lu = np.where(u < peak_at, np.log(350) + (np.log(2200) - np.log(350)) * (u / peak_at),
                  np.log(2200) + (np.log(700) - np.log(2200)) * ((u - peak_at) / (1 - peak_at)))
    y = dsp.tv_biquad(dsp.pink(n, r), np.exp(lu), q=1.0, kind='bandpass', stages=2)
    e = np.where(u < peak_at, (u / peak_at) ** 2, ((1 - u) / (1 - peak_at)) ** 1.5)
    y = y / np.std(y) * e
    st = dsp.pan_mono(dsp.peak_normalize(y, -1), pan_from + (pan_to - pan_from) * u)
    return Sfx(st * intensity, {'start': 0.0, 'peak': duration * peak_at, 'end': duration, 'sync': duration},
               {'type': 'fly'})


def divider_tick(intensity=1.0, seed=0, pan=0.0):
    """Tik przegrody: drewno 1.1 + 2.7 kHz, tau 15 ms."""
    r = dsp.rng(seed)
    y = _modal_hit(r, [1100, 2700], [0.015, 0.012], [1, 0.6], exc_ms=0.8, dur=0.15)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y])
    out = _finish(y * intensity, r, room='small', pan=pan, wet=0.1)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'divider_tick'})


def szuff(duration=0.15, intensity=1.0, seed=0, pan=0.0):
    """Plecy 6.5 mm wsuwane za mebel: szum BP 1-3 kHz, 150 ms."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    y = dsp.bp(dsp.pink(n, r), 1000, 3000, 2) * np.sin(np.pi * np.arange(n) / n) ** 1.5
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y])
    out = _finish(dsp.peak_normalize(y, -1) * intensity, r, pan=pan)
    return Sfx(out, {'start': PRE, 'sync': PRE + duration}, {'type': 'szuff'})


def fabric(duration=0.12, intensity=1.0, seed=0, pan=0.0):
    """Tkaniny w szufladzie: szum BP 2-6 kHz, 120 ms, miekka obwiednia."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration * 3)
    y = dsp.bp(dsp.pink(n, r), 2000, 6000, 2) * (1 + 0.6 * dsp.smooth_noise(n, r, 25))
    y *= np.sin(np.pi * np.arange(n) / n) ** 2
    out = _finish(dsp.peak_normalize(y, -1) * intensity, r, pan=pan)
    return Sfx(out, {'start': 0.0, 'sync': 0.0}, {'type': 'fabric'})


def front_clip(intensity=1.0, seed=0, pan=0.0, knob=True):
    """Front 'wpina sie' w lico: lzejszy thup (+wyzej) + tik galki 4 kHz 2 klatki pozniej."""
    r = dsp.rng(seed)
    y = _thup_core(r, scale=1.35, soft_ms=3.0, low=0.4) * 0.8
    if knob:
        kt = _modal_hit(r, [4000, 6100], [0.008, 0.005], [1, 0.4], exc_ms=0.3, dur=0.06) * 0.35
        i = dsp.n_of(0.08)
        y[i:i + len(kt)] += kt
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y])
    out = _finish(y * intensity, r, pan=pan)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'front_clip'})


def knob_tick(intensity=1.0, seed=0, pan=0.0):
    """Galka PLA 'wskakuje' na front: tik 4 kHz (modalnie, tau 8 ms)."""
    r = dsp.rng(seed)
    y = _modal_hit(r, [4000, 6100, 8800], [0.008, 0.005, 0.003], [1, 0.4, 0.15], exc_ms=0.3, dur=0.08)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y])
    out = _finish(y * intensity, r, pan=pan, wet=0.08)
    return Sfx(out, {'impact': PRE, 'sync': PRE}, {'type': 'knob_tick'})


def crane_air(duration=2.4, intensity=1.0, seed=0):
    """'Powietrze' jazdy kamery S01: szum LP narastajacy 150 -> 600 Hz."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    t = np.arange(n) / SR
    fc = 150 * 4 ** (t / duration)
    y = np.stack([dsp.tv_biquad(dsp.pink(n, r), fc, q=0.7, kind='lowpass', stages=2) for _ in range(2)], axis=1)
    y = dsp.hp(y / np.std(y), 40, 2) * dsp.smoothstep(t / 0.4)[:, None] * (0.6 + 0.4 * t / duration)[:, None]
    return Sfx(dsp.peak_normalize(y, -1) * intensity, {'start': 0.0, 'sync': 0.0}, {'type': 'crane_air'})


def birds(duration=4.8, rate=2.5, intensity=1.0, seed=0):
    """Ptaki za oknem (daleko): cwierkanie FM, nosna 3.2-5.5 kHz, modulacja 15-40 Hz, 80-250 ms."""
    r = dsp.rng(seed)
    n = dsp.n_of(duration)
    out = np.zeros((n, 2))
    k = max(1, int(duration * rate))
    for _ in range(k):
        d = r.uniform(0.08, 0.25)
        m = dsp.n_of(d)
        t = np.arange(m) / SR
        fc = r.uniform(3200, 5500) * (1 + r.uniform(-0.15, 0.15) * t / d)
        fm = r.uniform(15, 40)
        y = np.sin(dsp.phase_from_freq(fc * (1 + 0.08 * np.sin(2 * np.pi * fm * t)))) * np.sin(np.pi * t / d) ** 2
        dsp.place(out, dsp.pan_mono(y * r.uniform(0.3, 1.0), r.uniform(0.2, 0.8)), r.uniform(0, duration - d))
    out = dsp.lp(out, 6000, 2)
    out = dsp.reverb(out, wet=0.5, dry=0.6, rt60=0.9, brightness=0.3, seed=seed + 6, tail=False)
    return Sfx(dsp.peak_normalize(out, -1) * intensity, {'start': 0.0, 'sync': 0.0}, {'type': 'birds'})


def marimba(midi=65, vel=1.0, seed=0, pan=0.0, dry=False, rt60=0.9):
    """Marimba wg briefu: partiale 1 : 3.99 : 10.0, amplitudy 1 / 0.25 / 0.06,
    tau = 0.9*sqrt(220/f) s / 0.09 s / 0.03 s, palka = polsinus 1.5 ms + szum BP 2-4 kHz (-18 dB)."""
    r = dsp.rng(seed)
    f = 440.0 * 2 ** ((midi - 69) / 12)
    dur = min(4.0, 0.9 * np.sqrt(220 / f) * 5 + 0.2)
    n = dsp.n_of(dur)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / (0.9 * np.sqrt(220 / f)))
    y += 0.25 * vel * np.sin(2 * np.pi * f * 3.99 * t + 0.3) * np.exp(-t / 0.09)
    y += 0.06 * vel ** 1.5 * np.sin(2 * np.pi * f * 10.0 * t + 0.9) * np.exp(-t / 0.03)
    k = dsp.n_of(0.0015)
    mallet = np.zeros(n)
    mallet[:k] = dsp.half_sine_pulse(0.0015)[:k]
    nz = dsp.bp(r.standard_normal(n), 2000, 4000, 2) * dsp.env_ad(n, 0.0003, 0.006)
    nz = nz / (np.max(np.abs(nz)) + 1e-12) * dsp.db2lin(-18)
    y = y * dsp.smoothstep(t / 0.0012) + nz + 0.1 * dsp.lp(mallet, 3000, 1)
    y = np.concatenate([np.zeros(dsp.n_of(PRE)), y]) * vel
    st = dsp.pan_mono(y, pan)
    if not dry:
        st = dsp.reverb(st, wet=0.18, rt60=rt60, predelay=0.012, brightness=0.45, seed=seed + 7)
    return Sfx(st, {'impact': PRE, 'sync': PRE}, {'type': 'marimba', 'midi': midi})


# ==========================================================================
# rejestr + render
# ==========================================================================
GENERATORS = {
    'drawer_open': drawer_open,
    'drawer_close': drawer_close,
    'door_open': door_open,
    'door_close': door_close,
    'whoosh': whoosh,
    'land': land,
    'screw': screw,
    'wood_tap': wood_tap,
    'sub_boom': sub_boom,
    'riser': riser,
    'air': air,
    'room_tone': room_tone,
    # receptury z briefu
    'roll': roll, 'drawer_stop': drawer_stop, 'thup': thup, 'tok': tok, 'catch': catch, 'damper': damper,
    'door_air': door_air, 'caliper': caliper, 'pops': pops, 'levitate': levitate, 'fly': fly,
    'divider_tick': divider_tick, 'szuff': szuff, 'fabric': fabric, 'front_clip': front_clip,
    'crane_air': crane_air, 'birds': birds, 'marimba': marimba, 'knob_tick': knob_tick,
}

# poziom szczytowy w miksie [dBFS] PRZED normalizacja mastera (tabela 6.2 briefu); mikser ustawia
# probke (znormalizowana do -1 dBFS) na ten szczyt, chyba ze konfiguracja poda gain_db
SUGGESTED_PEAK_DBFS = {
    'drawer_open': -16, 'drawer_close': -12, 'door_open': -24, 'door_close': -12,
    'whoosh': -24, 'land': -14, 'screw': -18, 'wood_tap': -20,
    'sub_boom': -10, 'riser': -14, 'air': -26, 'room_tone': None,
    'roll': -16, 'drawer_stop': -12, 'thup': -9, 'tok': -11, 'catch': -24, 'damper': -34,
    'door_air': -38, 'caliper': -26, 'pops': -24, 'levitate': -16, 'fly': -30, 'divider_tick': -22,
    'szuff': -30, 'fabric': -34, 'front_clip': -16, 'crane_air': -40, 'birds': -42, 'marimba': -14, 'knob_tick': -28,
}
SUGGESTED_GAIN_DB = {k: (v + 1 if v is not None else 0) for k, v in SUGGESTED_PEAK_DBFS.items()}


def render(kind, seed=0, normalize=True, **params):
    if kind not in GENERATORS:
        raise KeyError(f'nieznany typ SFX: {kind} (dostepne: {", ".join(GENERATORS)})')
    sfx = GENERATORS[kind](seed=seed, **params)
    if normalize and kind != 'room_tone':
        sfx.audio = dsp.peak_normalize(sfx.audio, -1.0)
    sfx.meta.setdefault('type', kind)
    sfx.meta['params'] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in params.items()
                          if not isinstance(v, (list, np.ndarray)) or len(v) < 16}
    sfx.meta['suggested_gain_db'] = SUGGESTED_GAIN_DB.get(kind, -15)
    return sfx


# warianty do biblioteki samples/
CATALOG = [
    ('drawer_open_a', 'drawer_open', 1, dict(duration=0.75)),
    ('drawer_open_b', 'drawer_open', 2, dict(duration=1.0)),
    ('drawer_open_full_S09', 'drawer_open', 3, dict(duration=0.88, end_hit=1.0)),
    ('drawer_close_a', 'drawer_close', 4, dict(push=0.38, damp=0.5)),
    ('drawer_close_S10', 'drawer_close', 5, dict(push=0.48, damp=0.92)),
    ('drawer_close_gentle', 'drawer_close', 6, dict(push=0.6, damp=0.75, intensity=0.8, catch_level=0.25)),
    ('door_open_a', 'door_open', 7, dict(duration=0.7)),
    ('door_open_creak', 'door_open', 8, dict(duration=0.9, creak=0.6)),
    ('door_close_DZ02', 'door_close', 9, dict(push=0.72, damp=0.48)),
    ('door_close_b', 'door_close', 10, dict(push=0.55, damp=0.7)),
    ('whoosh_short_lr', 'whoosh', 11, dict(duration=0.45, size=0.4, height=0.7, direction=1)),
    ('whoosh_short_rl', 'whoosh', 12, dict(duration=0.5, size=0.5, height=0.5, direction=-1)),
    ('whoosh_long_panel', 'whoosh', 13, dict(duration=0.9, size=1.5, height=0.4, direction=1)),
    ('whoosh_big_drop', 'whoosh', 14, dict(duration=1.1, size=1.9, height=0.2, direction=0.3)),
    ('land_light_small', 'land', 15, dict(mass=1.2, size=(0.4, 0.3), surface='stack', hardness=0.6)),
    ('land_medium_shelf', 'land', 16, dict(mass=4.9, size=(1.0, 0.38), surface='stack')),
    ('land_heavy_long', 'land', 17, dict(mass=9.5, size=(1.9, 0.38), surface='floor', hardness=0.4)),
    ('land_floor_medium', 'land', 18, dict(mass=6.0, size=(1.2, 0.4), surface='floor')),
    ('screw_short', 'screw', 19, dict(duration=0.6)),
    ('screw_long', 'screw', 20, dict(duration=1.2, load=0.85)),
    ('wood_tap_soft', 'wood_tap', 21, dict(soft=0.7)),
    ('sub_boom_reveal', 'sub_boom', 22, dict(duration=3.2)),
    ('sub_hit_short', 'sub_boom', 23, dict(duration=1.4, f_start=110, f_end=45, click=0.8)),
    ('riser_2s', 'riser', 24, dict(duration=2.0)),
    ('riser_brief_2p16s', 'riser', 25, dict(duration=2.16, tonal=0.6, root_hz=220.0)),
    ('air_transition_a', 'air', 26, dict(duration=1.1)),
    ('air_transition_b', 'air', 27, dict(duration=1.6, brightness=0.8)),
    ('room_tone_30s', 'room_tone', 28, dict(duration=32.0, level_db=-50.0)),
    # receptury z briefu (6.2)
    ('brief_roll_S09_f188-210', 'roll', 30, dict(duration=0.88)),
    ('brief_drawer_stop_f210', 'drawer_stop', 31, dict()),
    ('brief_catch_silent_f262', 'catch', 32, dict(mech='drawer')),
    ('brief_damper_f262-285', 'damper', 33, dict(duration=0.92)),
    ('brief_thup_f285', 'thup', 34, dict()),
    ('brief_door_air_f300-318', 'door_air', 35, dict(duration=0.72)),
    ('brief_catch_blumotion_f318', 'catch', 36, dict(mech='door')),
    ('brief_tok_f330', 'tok', 37, dict()),
    ('brief_caliper_F6', 'caliper', 38, dict(midi=89)),
    ('brief_caliper_A6', 'caliper', 39, dict(midi=93)),
    ('brief_caliper_C7', 'caliper', 40, dict(midi=96)),
    ('brief_pops_140_f465', 'pops', 41, dict()),
    ('brief_levitate_f480', 'levitate', 42, dict()),
    ('brief_fly_0p56', 'fly', 43, dict()),
    ('brief_divider_tick', 'divider_tick', 44, dict()),
    ('brief_szuff_backs_f551', 'szuff', 45, dict()),
    ('brief_fabric_f211', 'fabric', 46, dict()),
    ('brief_front_clip', 'front_clip', 47, dict()),
    ('brief_crane_air_S01', 'crane_air', 48, dict()),
    ('brief_birds_far', 'birds', 49, dict()),
    ('brief_marimba_F4', 'marimba', 50, dict(midi=65)),
    ('brief_knob_tick', 'knob_tick', 51, dict()),
]


def build_library(out_dir, demo_path=None):
    os.makedirs(out_dir, exist_ok=True)
    index = {}
    demo = []
    for name, kind, seed, params in CATALOG:
        sfx = render(kind, seed=seed, **params)
        path = os.path.join(out_dir, f'{name}.wav')
        dsp.write_wav(path, sfx.audio)
        index[name] = {
            'file': os.path.relpath(path, HERE), 'type': kind, 'seed': seed, 'params': params,
            'duration': round(sfx.duration, 4), 'anchors': {k: round(v, 4) for k, v in sfx.anchors.items()},
            'suggested_gain_db': sfx.meta['suggested_gain_db'],
            'peak_dbfs': round(float(dsp.lin2db(np.max(np.abs(sfx.audio)))), 2),
        }
        print(f'  {name:22s} {sfx.duration:5.2f} s  anchors={index[name]["anchors"]}')
        if kind == 'room_tone':
            demo.append((name, sfx.audio[: dsp.n_of(3.0)] * dsp.db2lin(-30 - dsp.rms_db(sfx.audio))))
        else:   # demo: kazda probka na szczycie -6 dBFS (do odsluchu; poziomy w miksie wg SUGGESTED_PEAK_DBFS)
            demo.append((name, dsp.peak_normalize(sfx.audio, -6.0)))
    with open(os.path.join(out_dir, 'index.json'), 'w') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    if demo_path:
        gap = np.zeros((dsp.n_of(0.55), 2))
        parts, cues, tpos = [], [], 0.0
        for name, a in demo:
            cues.append((round(tpos, 2), name))
            parts += [a, gap]
            tpos += (len(a) + len(gap)) / SR
        d = np.concatenate(parts)
        d = dsp.peak_normalize(d, -1.0)
        dsp.write_wav(demo_path, d)
        with open(os.path.splitext(demo_path)[0] + '_cues.txt', 'w') as f:
            for tc, name in cues:
                f.write(f'{tc:7.2f}s  {name}\n')
        print(f'demo: {demo_path} ({len(d) / SR:.1f} s), cue sheet: {os.path.splitext(demo_path)[0]}_cues.txt')
    return index


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--all', action='store_true', help='wygeneruj biblioteke samples/ + sfx_demo.wav')
    ap.add_argument('--one', help='typ dzwieku (patrz --list)')
    ap.add_argument('--params', default='{}', help='JSON z parametrami')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('-o', '--out', help='plik WAV wyjsciowy dla --one')
    ap.add_argument('--samples', default=os.path.join(HERE, 'samples'))
    ap.add_argument('--demo', default=os.path.join(HERE, 'sfx_demo.wav'))
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()
    if a.list:
        for k, fn in GENERATORS.items():
            print(f'{k:14s} {fn.__doc__.strip().splitlines()[0]}')
        return
    if a.one:
        sfx = render(a.one, seed=a.seed, **json.loads(a.params))
        out = a.out or os.path.join(HERE, f'{a.one}_s{a.seed}.wav')
        dsp.write_wav(out, sfx.audio)
        print(json.dumps({'file': out, 'duration': sfx.duration, 'anchors': sfx.anchors}, indent=1))
        return
    if a.all:
        build_library(a.samples, a.demo)
        return
    ap.print_help()


if __name__ == '__main__':
    main()
