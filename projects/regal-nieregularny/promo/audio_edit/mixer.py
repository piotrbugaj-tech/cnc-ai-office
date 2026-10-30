#!/usr/bin/env python3
"""mixer.py - miks: muzyka (plik AI albo stemy syntezy) + Foley/SFX z timeline'u + room tone,
ducking muzyki pod Foley, panorama wg pozycji w kadrze, master -14 LUFS / true peak (brief 6.3).

Szyny:
  music  - lozko muzyczne (AI lub synteza; opcjonalnie montaz odcinkow music.edit), DUCKOWANE pod Foley,
  notes  - nuty zwiazane z obrazem (shelf_pass, ladowania, fronty) z events.json (nie duckowane),
  foley  - efekty (z events.json i z listy `sfx` w konfiguracji), zrodlo sidechainu,
  room   - room tone.
Master: kompresja 1,5:1 -> normalizacja LUFS -> limiter true-peak -> 'proznia' (silence) -> WAV 48 kHz/24 bit.

Uzywane przez edit.py; samodzielnie:
  python3 mixer.py configs/brief_audio_only.yaml          # tylko audio (np. animatik dzwiekowy)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402
import sfx_synth  # noqa: E402
import timeline  # noqa: E402
from dsp import SR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_INDEX = None


def _abs(p, base):
    if p is None:
        return None
    p = os.path.expanduser(str(p))
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))


def sample_index():
    global _SAMPLE_INDEX
    if _SAMPLE_INDEX is None:
        path = os.path.join(HERE, 'samples', 'index.json')
        _SAMPLE_INDEX = json.load(open(path)) if os.path.isfile(path) else {}
    return _SAMPLE_INDEX


def render_cue(c, base):
    """cue -> (stereo audio, czas anchora [s], typ, sugerowany gain dB)."""
    if c.get('synth'):
        params = dict(c.get('params', {}))
        if 'size' in params and isinstance(params['size'], list):
            params['size'] = tuple(params['size'])
        s = sfx_synth.render(c['synth'], seed=int(c.get('seed', 0)), **params)
        anchor = c.get('anchor', 'sync')
        a = s.anchors.get(anchor, s.anchors.get('sync', 0.0)) if isinstance(anchor, str) else float(anchor)
        return s.audio, a, c['synth'], s.meta['suggested_gain_db']
    if c.get('sample'):
        idx = sample_index()
        ent = idx.get(c['sample'])
        if ent is None:
            raise KeyError(f"brak probki {c['sample']} w samples/index.json")
        x = dsp.read_audio(os.path.join(HERE, ent['file']))
        anchor = c.get('anchor', 'sync')
        a = ent['anchors'].get(anchor, ent['anchors'].get('sync', 0.0)) if isinstance(anchor, str) else float(anchor)
        return x, a, ent['type'], ent.get('suggested_gain_db', -15)
    if c.get('file'):
        x = dsp.read_audio(_abs(c['file'], base))
        return x, float(c.get('anchor', 0.0) or 0.0), 'file', -12.0
    raise ValueError(f'cue bez zrodla: {c}')


def load_music(mcfg, base, total):
    """Muzyka: {file|stems_dir+use, gain_db|lufs, in, at, fade_in, fade_out, edit:[{src_in,src_out,at,xfade}]}."""
    if not mcfg:
        return np.zeros((dsp.n_of(total), 2))
    if mcfg.get('stems_dir'):
        sd = _abs(mcfg['stems_dir'], base)
        use = mcfg.get('use') or [os.path.splitext(f)[0] for f in os.listdir(sd) if f.endswith('.wav')]
        parts = [dsp.read_audio(os.path.join(sd, f'{u}.wav')) for u in use]
        n = max(len(p) for p in parts)
        src = sum(dsp.pad_to(p, n) for p in parts)
    else:
        src = dsp.read_audio(_abs(mcfg['file'], base))
    out = np.zeros((dsp.n_of(total), 2))
    edits = mcfg.get('edit')
    if edits:                                   # montaz odcinkow (np. 15 s z wersji 30 s) z krotkim crossfade
        for e in edits:
            i0, i1 = dsp.n_of(e['src_in']), dsp.n_of(e['src_out'])
            seg = src[i0:i1].copy()
            xf = float(e.get('xfade', 0.02))
            seg = dsp.fade(seg, xf, xf)
            dsp.place(out, seg, float(e['at']))
    else:
        i0 = dsp.n_of(float(mcfg.get('in', 0.0)))
        dsp.place(out, src[i0:], float(mcfg.get('at', 0.0)))
    out = dsp.fade(out, float(mcfg.get('fade_in', 0.0)), 0.0)
    fo = float(mcfg.get('fade_out', 0.0))
    if fo > 0:
        end = float(mcfg.get('fade_out_end', total))
        k1, k0 = dsp.n_of(end), dsp.n_of(end - fo)
        g = np.ones(len(out))
        g[k0:k1] = np.cos(np.linspace(0, np.pi / 2, k1 - k0)) ** 2
        g[k1:] = 0
        out *= g[:, None]
    if 'lufs' in mcfg:
        act = out[np.max(np.abs(out), axis=1) > 1e-5]
        if len(act) > SR:
            out *= dsp.db2lin(float(mcfg['lufs']) - dsp.lufs(act))
    out *= dsp.db2lin(float(mcfg.get('gain_db', 0.0)))
    return out


def mix(acfg, total, cues, base, report=None, verbose=True):
    """acfg: sekcja 'audio' konfiguracji. cues: lista z timeline (z polem 'at') + reczne z acfg['sfx'].
    Zwraca (stereo, raport)."""
    n = dsp.n_of(total)
    rep = report if report is not None else {}
    pan_max = float(acfg.get('pan_max', 0.3))
    music = load_music(acfg.get('music'), base, total)
    notes = np.zeros((n, 2))
    foley = np.zeros((n, 2))
    use_notes = bool(acfg.get('event_notes', True))
    placed = []
    manual = []
    for c in acfg.get('sfx', []) or []:
        c = dict(c)
        c.setdefault('at', 0.0)
        manual.append(c)
    sil_ev = []
    use_mfx = bool(acfg.get('event_music_fx', True))
    for c in list(cues) + manual:
        if c.get('kind') == 'silence':                # 'proznia' ze zdarzenia -> obszar ciszy
            sil_ev.append([float(c['at']), float(c['at']) + float(c['t_end']) - float(c['t_src'])])
            placed.append(dict(t=round(float(c['at']), 3), type='silence', label='silence', ev=c.get('ev'),
                               shot=c.get('shot'), bus='master'))
            continue
        if (c.get('music_note') and not use_notes) or (c.get('music_fx') and not use_mfx):
            placed.append(dict(t=round(float(c['at']), 3), type=c.get('synth'), label=c.get('label'), ev=c.get('ev'),
                               evs=c.get('evs'), shot=c.get('shot'), bus='muzyka (stem)', skipped=True))
            continue
        if c.get('mute'):
            continue
        try:
            x, a, typ, sug = render_cue(c, base)
        except Exception as e:  # noqa: BLE001
            print(f"  [mix] pominieto cue {c.get('label', c)}: {e}")
            continue
        if c.get('gain_db') is not None:
            g = float(c['gain_db'])
        else:
            g = sug + float(c.get('gain_offset_db', 0.0)) + float(acfg.get('sfx_gain_db', 0.0))
            if c.get('music_note'):
                g += float(acfg.get('notes_gain_db', 0.0))
        x = x * dsp.db2lin(g)
        pan = c.get('pan')
        if pan is None and c.get('screen_x') is not None:
            pan = (float(c['screen_x']) - 0.5) * 2
        if pan is not None and abs(pan) > 1e-3:
            x = dsp.pan_stereo(x, float(np.clip(pan, -pan_max, pan_max)))
        if c.get('clip_from') is not None:       # przyciecie do ciecia montazowego (10 ms fade-in)
            k0 = dsp.n_of(max(0.0, float(c['clip_from']) - (float(c['at']) - a)))
            if k0 > 0:
                x = x.copy()
                x[:k0] = 0
                kf = min(len(x) - k0, dsp.n_of(0.01))
                x[k0:k0 + kf] *= np.linspace(0, 1, kf)[:, None]
        bus = notes if c.get('music_note') else foley
        dsp.place(bus, x, float(c['at']) - a)
        placed.append(dict(t=round(float(c['at']), 3), t0=round(float(c['at']) - a, 3), dur=round(len(x) / SR, 3),
                           shot=c.get('shot'), ev=c.get('ev'), evs=c.get('evs'), clip_from=c.get('clip_from'),
                           type=typ, label=c.get('label', c.get('sample', c.get('file', ''))),
                           gain_db=round(g, 1), pan=None if pan is None else round(float(np.clip(pan, -pan_max, pan_max)), 2),
                           bus='notes' if c.get('music_note') else 'foley'))
    # room tone
    room = np.zeros((n, 2))
    rt = acfg.get('room_tone', {'sample': 'room_tone_30s', 'level_db': -48})
    if rt:
        if rt.get('file'):
            src = dsp.read_audio(_abs(rt['file'], base))
        else:
            src = dsp.read_audio(os.path.join(HERE, sample_index()[rt.get('sample', 'room_tone_30s')]['file']))
        reps = int(np.ceil(n / len(src))) + 1
        room = np.tile(src, (reps, 1))[:n]
        room *= dsp.db2lin(float(rt.get('level_db', -48)) - dsp.rms_db(room))
    # ducking muzyki pod Foley (brief: -4 dB, atak 10 ms, puszczenie 300 ms)
    dk = acfg.get('duck', {})
    depth = float(dk.get('depth_db', 4.0))
    if depth > 0 and np.any(foley):
        env = dsp.envelope_follower(foley, attack=float(dk.get('attack', 0.01)), release=float(dk.get('release', 0.3)))
        thr = float(dk.get('threshold_db', -42.0))
        rng_db = float(dk.get('range_db', 12.0))
        amt = np.clip((dsp.lin2db(env) - thr) / rng_db, 0, 1)
        gr = dsp.db2lin(-depth * amt)
        music *= gr[:, None]
        rep['duck_max_db'] = round(float(-dsp.lin2db(np.min(gr))), 2)
    bus = music + notes + foley + room
    # master: kompresja 1,5:1 (RMS 50 ms)
    m = acfg.get('master', {})
    ratio = float(m.get('comp_ratio', 1.5))
    if ratio > 1:
        env = np.sqrt(np.maximum(dsp.uniform_filter1d(np.mean(bus ** 2, axis=1), int(0.05 * SR)), 0))
        lvl = dsp.lin2db(env)
        act = lvl[lvl > -60]
        thr = float(np.percentile(act, 80)) if len(act) else -20.0
        gr = np.where(lvl > thr, (lvl - thr) * (1 - 1 / ratio), 0.0)
        bus = bus * dsp.db2lin(-dsp.uniform_filter1d(gr, int(0.08 * SR)))[:, None]
    # LP przed limiterem = to samo pasmo co AAC (inaczej obciecie wysokich w koderze daje przestrzaly true-peak)
    lp_hz = float(m.get('lowpass_hz', 17500))
    if lp_hz and lp_hz < SR / 2:
        bus = dsp.lp(bus, lp_hz, 4)
    target, tp = float(m.get('lufs', -14.0)), float(m.get('true_peak', -1.5))
    out, L, TP = dsp.normalize_lufs(bus, target, tp)
    # 'proznia': przyciszenie calosci (np. f474-480 -> -60 dB w 80 ms)
    for s0, s1 in list(acfg.get('silence', []) or []) + sil_ev:
        g = np.ones(n)
        i0, i1 = dsp.n_of(s0), dsp.n_of(s1)
        ramp = dsp.n_of(float(acfg.get('silence_ramp', 0.08)))
        g[max(0, i0 - ramp):i0] = np.linspace(1, dsp.db2lin(-60), min(ramp, i0))
        g[i0:i1] = dsp.db2lin(-60)
        out *= g[:, None]
    rep.update(lufs=round(dsp.lufs(out), 2), true_peak_dbtp=round(dsp.true_peak_db(out), 2),
               n_cues=len([p for p in placed if not p.get('skipped') and p.get('type') != 'silence']))
    rep['cues'] = placed
    if verbose:
        print(f"  [mix] {rep['n_cues']} efektow, {rep['lufs']} LUFS, TP {rep['true_peak_dbtp']} dBTP"
              + (f", ducking do -{rep.get('duck_max_db')} dB" if 'duck_max_db' in rep else ''))
    return out, rep


def cues_from_events(acfg, base, shots=None, total=None, event_map=None):
    """Zdarzenia: acfg['events'] = sciezka (czas globalny = klatka/fps + offset) albo per ujecie (shots)."""
    cues = []
    evc = acfg.get('events')
    if evc:
        evs = evc if isinstance(evc, list) else [evc]
        for e in evs:
            e = {'file': e} if isinstance(e, str) else dict(e)
            path = _abs(e['file'], base)
            if not os.path.isfile(path):
                print(f'  [mix] brak pliku zdarzen: {path}')
                continue
            fps, ev = timeline.load_events(path, e.get('shot'))
            off_f = float(e.get('frame_offset', 0))
            for x in ev:
                x['frame'] -= off_f
            for c in timeline.build_cues(ev, fps, event_map, float(acfg.get('pan_width', 0.8))):
                t = c['t_src'] + float(e.get('offset_s', 0.0))
                lo, hi = e.get('window', [-1e9, 1e9])
                if lo <= c['t_src'] <= hi and (total is None or -0.5 <= t <= total):
                    c['at'] = t
                    cues.append(c)
    return cues


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config')
    ap.add_argument('-o', '--out')
    a = ap.parse_args()
    import yaml
    cfg = yaml.safe_load(open(a.config, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(a.config))
    acfg = cfg['audio']
    total = float(cfg.get('duration', 30.0))
    cues = cues_from_events(acfg, base, total=total, event_map=cfg.get('event_map'))
    out, rep = mix(acfg, total, cues, base)
    path = _abs(a.out or cfg.get('output', 'mix.wav'), base)
    dsp.write_wav(path, out)
    with open(os.path.splitext(path)[0] + '_cues.json', 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=1, ensure_ascii=False)
    print(f'{path}: {len(out) / SR:.2f} s')
