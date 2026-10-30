"""dsp.py - wspolne narzedzia DSP dla sfx_synth / music_synth / mixer.

Wszystko w float64, 48 kHz. Brak petli probka-po-probce (numpy/scipy), zeby
renderowanie 30 s muzyki trwalo sekundy, nie minuty.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d

SR = 48000


# --------------------------------------------------------------------------
# podstawy
# --------------------------------------------------------------------------
def rng(seed):
    return np.random.default_rng(seed)


def n_of(dur, sr=SR):
    return max(1, int(round(dur * sr)))


def t_axis(dur, sr=SR):
    return np.arange(n_of(dur, sr)) / sr


def db2lin(x):
    return 10.0 ** (np.asarray(x) / 20.0)


def lin2db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))


def place(buf, x, start_s, sr=SR, gain=1.0):
    """Dodaje x (mono lub stereo) do bufora od czasu start_s (moze byc ujemny)."""
    i0 = int(round(start_s * sr))
    j0 = 0
    if i0 < 0:
        j0 = -i0
        i0 = 0
    if j0 >= len(x) or i0 >= len(buf):
        return buf
    n = min(len(x) - j0, len(buf) - i0)
    if buf.ndim == 2 and x.ndim == 1:
        buf[i0:i0 + n] += gain * x[j0:j0 + n, None]
    else:
        buf[i0:i0 + n] += gain * x[j0:j0 + n]
    return buf


def pad_to(x, n):
    if len(x) >= n:
        return x[:n]
    pad = [(0, n - len(x))] + [(0, 0)] * (x.ndim - 1)
    return np.pad(x, pad)


# --------------------------------------------------------------------------
# szumy
# --------------------------------------------------------------------------
def white(n, r):
    return r.standard_normal(n)


def colored(n, r, slope_db_oct=-3.0, fmin=10.0):
    """Szum o nachyleniu widma slope dB/okt (-3 rozowy, -6 brazowy, +3 niebieski)."""
    x = r.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    f = np.maximum(f, fmin)
    X *= (f / 1000.0) ** (slope_db_oct / 6.0206)
    y = np.fft.irfft(X, n)
    return y / (np.std(y) + 1e-12)


def pink(n, r):
    return colored(n, r, -3.0)


def brown(n, r):
    return colored(n, r, -6.0, fmin=20.0)


def smooth_noise(n, r, rate_hz):
    """Gladki losowy przebieg (LFO szumowe) o pasmie ~rate_hz, std=1."""
    x = r.standard_normal(n)
    sos = signal.butter(2, max(rate_hz, 0.05), 'lowpass', fs=SR, output='sos')
    y = signal.sosfiltfilt(sos, x)
    return y / (np.std(y) + 1e-12)


# --------------------------------------------------------------------------
# filtry statyczne
# --------------------------------------------------------------------------
def _clampf(f):
    return float(np.clip(f, 5.0, SR * 0.49))


def lp(x, fc, order=2):
    sos = signal.butter(order, _clampf(fc), 'lowpass', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def hp(x, fc, order=2):
    sos = signal.butter(order, _clampf(fc), 'highpass', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def bp(x, lo, hi, order=2):
    lo, hi = _clampf(lo), _clampf(hi)
    if hi <= lo * 1.01:
        hi = lo * 1.2
    sos = signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def biquad(kind, f0, q=0.707, gain_db=0.0):
    """Wspolczynniki RBJ (b, a). kind: lowpass, highpass, bandpass, peak, lowshelf, highshelf."""
    f0 = _clampf(f0)
    A = 10 ** (gain_db / 40.0)
    w = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w), np.sin(w)
    alpha = sw / (2 * q)
    if kind == 'lowpass':
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'highpass':
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'bandpass':
        b = [alpha, 0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == 'peak':
        b = [1 + alpha * A, -2 * cw, 1 - alpha * A]
        a = [1 + alpha / A, -2 * cw, 1 - alpha / A]
    elif kind == 'lowshelf':
        sa = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) - (A - 1) * cw + sa), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sa)]
        a = [(A + 1) + (A - 1) * cw + sa, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sa]
    elif kind == 'highshelf':
        sa = 2 * np.sqrt(A) * alpha
        b = [A * ((A + 1) + (A - 1) * cw + sa), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sa)]
        a = [(A + 1) - (A - 1) * cw + sa, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sa]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return b, a


def eq(x, kind, f0, gain_db=0.0, q=0.707):
    b, a = biquad(kind, f0, q, gain_db)
    return signal.lfilter(b, a, x, axis=0)


def tv_biquad(x, f_curve, q=0.707, kind='lowpass', block=64, stages=1):
    """Filtr zmienny w czasie (wspolczynniki aktualizowane co `block` probek, stan przenoszony)."""
    x = np.asarray(x, dtype=np.float64)
    f_curve = np.broadcast_to(np.asarray(f_curve, dtype=np.float64), (len(x),))
    y = x.copy()
    for _ in range(stages):
        out = np.empty_like(y)
        zi = np.zeros(2)
        for i in range(0, len(y), block):
            seg = y[i:i + block]
            b, a = biquad(kind, f_curve[i], q)
            # przeksztalcenie stanu DF2T jest ciagle przy wolnych zmianach -> brak trzaskow
            out[i:i + block], zi = signal.lfilter(b, a, seg, zi=zi)
        y = out
    return y


def resonator_bank(exc, freqs, decays, amps=None):
    """Synteza modalna: pobudzenie przez bank rezonatorow 2-biegunowych.
    decays = czas zaniku do 1/e w sekundach."""
    exc = np.asarray(exc, dtype=np.float64)
    y = np.zeros_like(exc)
    if amps is None:
        amps = np.ones(len(freqs))
    for f, tau, a in zip(freqs, decays, amps):
        if f >= SR * 0.45 or a == 0:
            continue
        r = np.exp(-1.0 / (max(tau, 1e-4) * SR))
        w = 2 * np.pi * f / SR
        y += a * signal.lfilter([np.sin(w)], [1.0, -2 * r * np.cos(w), r * r], exc)
    return y


def modal_ir(dur, freqs, decays, amps, r=None, phase_rand=True):
    """Bezposrednia odpowiedz modalna (suma zanikajacych sinusow)."""
    t = t_axis(dur)
    y = np.zeros_like(t)
    for i, (f, tau, a) in enumerate(zip(freqs, decays, amps)):
        if f >= SR * 0.45:
            continue
        ph = r.uniform(0, 2 * np.pi) if (r is not None and phase_rand) else 0.0
        y += a * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + ph)
    return y


# --------------------------------------------------------------------------
# obwiednie
# --------------------------------------------------------------------------
def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def env_lin(t, pts):
    """Obwiednia z punktow [(czas, wartosc), ...] - interpolacja liniowa."""
    p = np.array(pts, dtype=float)
    return np.interp(t, p[:, 0], p[:, 1])


def env_ad(n, attack, decay, sr=SR, curve=1.0):
    t = np.arange(n) / sr
    a = np.clip(t / max(attack, 1e-5), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-5))
    return (a ** curve) * d


def half_sine_pulse(contact_s):
    n = max(2, int(contact_s * SR))
    return np.sin(np.pi * np.arange(n) / n)


def poisson_events(rate_curve, r):
    """Indeksy probek zdarzen procesu Poissona o zmiennej intensywnosci rate_curve [1/s]."""
    lam = np.cumsum(np.maximum(rate_curve, 0)) / SR
    total = lam[-1] if len(lam) else 0
    if total <= 0:
        return np.array([], dtype=int)
    k = r.poisson(total) + 8
    draws = np.cumsum(r.exponential(1.0, size=k))
    draws = draws[draws < total]
    return np.searchsorted(lam, draws).clip(0, len(rate_curve) - 1)


def phase_from_freq(f_curve):
    return 2 * np.pi * np.cumsum(f_curve) / SR


# --------------------------------------------------------------------------
# stereo / przestrzen
# --------------------------------------------------------------------------
def pan_mono(x, pan):
    """Constant-power: pan -1 (L) .. +1 (P); pan moze byc tablica."""
    pan = np.clip(pan, -1, 1)
    th = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], axis=1) * np.sqrt(2) * 0.7071


def to_stereo(x):
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    return x


def pan_stereo(x, pan):
    """Balans dla sygnalu stereo (pan -1..1), zachowuje srodek przy 0."""
    x = to_stereo(x)
    p = np.broadcast_to(np.clip(np.asarray(pan, dtype=float), -1, 1), (len(x),))
    a = np.maximum(p, 0) * np.pi / 2   # w prawo: lewy kanal przechodzi do prawego
    b = np.maximum(-p, 0) * np.pi / 2  # w lewo
    L = x[:, 0] * np.cos(a) + x[:, 1] * np.sin(b)
    R = x[:, 1] * np.cos(b) + x[:, 0] * np.sin(a)
    return np.stack([L, R], axis=1)


def ms_width(x, width):
    x = to_stereo(x)
    m = (x[:, 0] + x[:, 1]) * 0.5
    s = (x[:, 0] - x[:, 1]) * 0.5 * width
    return np.stack([m + s, m - s], axis=1)


def decorrelate(x, r, ms=6.0):
    """Delikatna dekorelacja (krotki 'velvet noise' FIR) - szerokosc bez fazowania."""
    n = int(ms * 1e-3 * SR)
    h = np.zeros(n)
    idx = r.choice(n, size=max(4, n // 40), replace=False)
    h[idx] = r.choice([-1, 1], size=len(idx)) * np.exp(-idx / (n * 0.5))
    h[0] = 1.0
    h /= np.sqrt(np.sum(h ** 2))
    return signal.fftconvolve(x, h)[:len(x)]


def room_ir(rt60=0.35, predelay=0.004, er_count=14, er_span=0.028, brightness=0.6,
            size=1.0, seed=7, stereo=True, length=None):
    """Syntetyczna odpowiedz impulsowa pomieszczenia: wczesne odbicia + ogon
    z zanikiem zaleznym od czestotliwosci (wysokie gasna szybciej)."""
    r = rng(seed)
    length = length or (rt60 * 1.3 + predelay + er_span + 0.05)
    n = n_of(length)
    chans = []
    for c in range(2 if stereo else 1):
        ir = np.zeros(n)
        # wczesne odbicia
        t_er = predelay + np.sort(r.uniform(0.0015, er_span * size, er_count))
        for k, te in enumerate(t_er):
            i = int(te * SR)
            if i < n:
                ir[i] += r.choice([-1, 1]) * (0.75 / (1 + 30 * te)) * r.uniform(0.6, 1.0)
        ir = lp(ir, 4500 + 7000 * brightness, 1)
        # pozny ogon (3 pasma, rozne RT60)
        t = np.arange(n) / SR
        onset = smoothstep((t - predelay - 0.004) / (0.012 * size + 0.006))
        tail = np.zeros(n)
        bands = [(None, 400, 1.15), (400, 3500, 1.0), (3500, None, 0.45 + 0.35 * brightness)]
        for lo, hi, k in bands:
            nz = r.standard_normal(n)
            if lo is None:
                nz = lp(nz, hi, 2)
            elif hi is None:
                nz = hp(nz, lo, 2)
            else:
                nz = bp(nz, lo, hi, 2)
            tail += nz * np.exp(-6.9078 * t / (rt60 * k))
        tail *= onset
        tail *= 0.32 / (np.sqrt(np.sum(tail ** 2) / SR) + 1e-9) * np.sqrt(rt60)
        ir = ir + tail * 0.25
        ir[0] = 0.0
        chans.append(ir)
    ir = np.stack(chans, axis=1) if stereo else chans[0]
    return ir


_IR_CACHE = {}


def reverb(x, wet=0.15, dry=1.0, rt60=0.35, predelay=0.004, brightness=0.6, size=1.0, seed=7,
           hp_wet=120.0, tail=True):
    """Splot z syntetycznym IR. Zwraca stereo; dlugosc wydluzona o ogon jesli tail=True."""
    key = (round(rt60, 3), round(predelay, 4), round(brightness, 2), round(size, 2), seed)
    if key not in _IR_CACHE:
        _IR_CACHE[key] = room_ir(rt60, predelay, brightness=brightness, size=size, seed=seed)
    ir = _IR_CACHE[key]
    xs = to_stereo(x)
    src = xs.mean(axis=1)
    if hp_wet:
        src = hp(src, hp_wet, 1)
    wl = signal.fftconvolve(src, ir[:, 0])
    wr = signal.fftconvolve(src, ir[:, 1])
    w = np.stack([wl, wr], axis=1)
    n = len(w) if tail else len(xs)
    out = np.zeros((n, 2))
    out[:len(xs)] += dry * xs[:n]
    out += wet * w[:n]
    return out


def mod_delay(x, base_ms, depth_ms, rate_hz, phase=0.0):
    """Linia opozniajaca modulowana (chorus/flanger), interpolacja liniowa."""
    n = len(x)
    t = np.arange(n) / SR
    d = (base_ms + depth_ms * np.sin(2 * np.pi * rate_hz * t + phase)) * 1e-3 * SR
    idx = np.arange(n) - d
    return np.interp(idx, np.arange(n), x, left=0.0, right=0.0)


def chorus(x, mix=0.5, seed=3):
    """Stereo chorus z dwoch modulowanych linii (rozne LFO L/P)."""
    xs = to_stereo(x)
    m = xs.mean(axis=1)
    l = mod_delay(m, 11.0, 2.4, 0.31, 0.0) + mod_delay(m, 17.0, 1.7, 0.19, 1.3) * 0.6
    r_ = mod_delay(m, 13.0, 2.8, 0.27, 2.1) + mod_delay(m, 19.0, 1.5, 0.23, 0.4) * 0.6
    wet = np.stack([l, r_], axis=1) / 1.6
    return xs * (1 - mix * 0.5) + wet * mix


def pingpong(x, delay_s, feedback=0.35, mix=0.25, lp_hz=3500, taps=6):
    xs = to_stereo(x)
    m = lp(xs.mean(axis=1), lp_hz, 1)
    n = len(xs) + int(delay_s * SR * taps)
    out = np.zeros((n, 2))
    out[:len(xs)] += xs
    g = 1.0
    for k in range(1, taps + 1):
        g *= feedback
        ch = (k + 1) % 2
        i0 = int(round(k * delay_s * SR))
        out[i0:i0 + len(m), ch] += mix * g / feedback * m
        m = lp(m, lp_hz * 0.85, 1)
    return out


# --------------------------------------------------------------------------
# dynamika / glosnosc
# --------------------------------------------------------------------------
def soft_clip(x, drive=1.0):
    if drive <= 0:
        return x
    return np.tanh(drive * x) / np.tanh(drive)


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    n = len(x)
    if fin > 0:
        k = min(n, n_of(fin))
        g = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
        x[:k] = (x[:k].T * g).T
    if fout > 0:
        k = min(n, n_of(fout))
        g = np.cos(np.linspace(0, np.pi / 2, k)) ** 2
        x[n - k:] = (x[n - k:].T * g).T
    return x


def true_peak(x, os_factor=4):
    xs = x if x.ndim == 2 else x[:, None]
    up = signal.resample_poly(xs, os_factor, 1, axis=0)
    return float(np.max(np.abs(up)))


def true_peak_db(x):
    return float(lin2db(true_peak(x)))


def lufs(x):
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    xs = to_stereo(x)
    if len(xs) < SR * 0.5:
        xs = pad_to(xs, int(SR * 0.5))
    return float(meter.integrated_loudness(xs))


def peak_normalize(x, peak_db=-1.0):
    p = np.max(np.abs(x))
    if p <= 0:
        return x
    return x * (db2lin(peak_db) / p)


def rms_db(x):
    return float(lin2db(np.sqrt(np.mean(np.square(x))) + 1e-12))


def limiter(x, ceiling_db=-1.0, lookahead=0.004, release=0.09, os_factor=4):
    """Limiter true-peak bez petli: wykrywanie piku na nadprobkowanym sygnale,
    min-hold w oknie +-lookahead, wygladzenie ataku, wolny powrot (release)."""
    xs = to_stereo(x).astype(np.float64)
    c = db2lin(ceiling_db)
    up = signal.resample_poly(xs, os_factor, 1, axis=0)
    pk = np.max(np.abs(up), axis=1)
    n = len(xs)
    pk = pk[:n * os_factor].reshape(n, os_factor).max(axis=1) if len(pk) >= n * os_factor else np.pad(pk, (0, n * os_factor - len(pk))).reshape(n, os_factor).max(axis=1)
    g = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    L = max(3, int(lookahead * SR))
    g = minimum_filter1d(g, size=2 * L + 1, mode='nearest')
    g = uniform_filter1d(g, size=L, mode='nearest')
    a = 1.0 - np.exp(-1.0 / (release * SR))
    g_rel = signal.lfilter([a], [1, -(1 - a)], g, zi=[g[0] * (1 - a)])[0]
    g = np.minimum(g, g_rel)
    return (xs.T * g).T


def normalize_lufs(x, target=-14.0, tp_ceiling=-1.0, iterations=3):
    """Glosnosc zintegrowana do target LUFS + limiter true-peak. Zwraca (y, lufs, tp)."""
    y = to_stereo(x)
    for _ in range(iterations):
        cur = lufs(y)
        y = y * db2lin(target - cur)
        y = limiter(y, tp_ceiling - 0.15)
        if abs(lufs(y) - target) < 0.1 and true_peak_db(y) <= tp_ceiling:
            break
    return y, lufs(y), true_peak_db(y)


def envelope_follower(x, attack=0.01, release=0.25):
    m = np.max(np.abs(to_stereo(x)), axis=1)
    a = 1.0 - np.exp(-1.0 / (release * SR))
    e = signal.lfilter([a], [1, -(1 - a)], m)
    e = np.maximum(e, maximum_filter1d(m, size=max(3, int(attack * SR))) * 0.5)
    e = uniform_filter1d(e, size=max(3, int(attack * SR)), mode='nearest')
    return e


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------
def write_wav(path, x, sr=SR, subtype='PCM_24'):
    import soundfile as sf
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    y = np.clip(to_stereo(np.asarray(x, dtype=np.float64)), -1.0, 1.0)
    sf.write(path, y, sr, subtype=subtype)
    return path


def read_audio(path, sr=SR):
    """Czyta WAV/FLAC/MP3/M4A... -> stereo float64 @ sr. Dla formatow nieobslugiwanych
    przez libsndfile dekoduje przez ffmpeg."""
    import soundfile as sf
    try:
        x, fs = sf.read(path, always_2d=True, dtype='float64')
    except Exception:
        ff = shutil.which('ffmpeg')
        if not ff:
            raise
        with tempfile.TemporaryDirectory() as td:
            tmp = os.path.join(td, 'dec.wav')
            subprocess.run([ff, '-v', 'error', '-y', '-i', path, '-ac', '2', '-ar', str(sr),
                            '-c:a', 'pcm_f32le', tmp], check=True)
            x, fs = sf.read(tmp, always_2d=True, dtype='float64')
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    elif x.shape[1] > 2:
        x = x[:, :2]
    if fs != sr:
        from math import gcd
        g = gcd(int(fs), int(sr))
        x = signal.resample_poly(x, sr // g, int(fs) // g, axis=0)
    return x
