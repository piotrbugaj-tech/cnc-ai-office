#!/usr/bin/env python3
"""timeline.py - zdarzenia animacji z Blendera -> lista efektow (SFX cues) w czasie montazu.

Czas montazu = start_ujecia + ((klatka - event_frame_offset) / fps_zrodla - in_ujecia) / speed

Akceptowane formaty JSON z Blendera (elastycznie):
  {"fps": 25, "events": [{"frame": 40, "type": "drawer_open_start", "object": "S03", "screen_x": 0.42}, ...]}
  [{"frame": 40, "event": "drawer_open_start", "obj": "S03"}, ...]
  {"drawer_open_start": [40, 120], "door_close_click": [{"frame": 88, "object": "DZ02"}]}
  {"shots": {"s03": {"fps": 25, "events": [...]}}}       (wybor --shot / klucz 'shot' w konfiguracji)
Pola dodatkowe zdarzenia (opcjonalne): object/obj/name, screen_x (0..1 w kadrze), world_x [m],
mass_kg, length_mm, width_mm, duration (s), intensity, direction (+1/-1).

Reguly (EVENT_MAP, nadpisywalne w konfiguracji `event_map`):
  drawer_open_start (+drawer_open_end)                          -> drawer_open
  drawer_close_start (+drawer_softclose_engage, +drawer_closed) -> drawer_close (dokladne 3 punkty sync)
  drawer_softclose_engage / drawer_closed (same)                -> drawer_close (sync = engage / closed)
  door_open_start (+door_open_end)                              -> door_open
  door_close_start (+door_softclose_engage, +door_close_click)  -> door_close
  door_close_click / door_closed (same)                         -> door_close (sync = click)
  part_launch|part_fly_start (+part_landing)                    -> whoosh (konczy sie na ladowaniu)
  part_landing                                                  -> land (masa z mass_kg albo wymiarow)
  screw_start (+screw_end)                                      -> screw
  reveal|hero_reveal|product_reveal                             -> sub_boom
  transition                                                    -> air
  knob_touch|hand_touch|tap                                     -> wood_tap
"""
from __future__ import annotations

import json
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ALIASES = {
    'drawer_open': 'drawer_open_start', 'drawer_opening_start': 'drawer_open_start',
    'drawer_opened': 'drawer_open_end', 'drawer_open_stop': 'drawer_open_end',
    'drawer_close': 'drawer_close_start', 'drawer_closing_start': 'drawer_close_start',
    'drawer_softclose': 'drawer_softclose_engage', 'drawer_soft_close_engage': 'drawer_softclose_engage',
    'drawer_close_end': 'drawer_closed', 'drawer_close_click': 'drawer_closed',
    'door_open': 'door_open_start', 'door_opened': 'door_open_end',
    'door_close': 'door_close_start', 'door_blumotion_engage': 'door_softclose_engage',
    'door_softclose': 'door_softclose_engage', 'door_closed': 'door_close_click',
    'door_close_end': 'door_close_click',
    'part_fly_start': 'part_launch', 'part_takeoff': 'part_launch', 'part_start': 'part_launch',
    'part_land': 'part_landing', 'part_landed': 'part_landing',
    'hero_reveal': 'reveal', 'product_reveal': 'reveal',
    'hand_touch': 'tap', 'knob_touch': 'tap',
    # typy proponowane w research-brief.md (6)
}

# nuty polek (brief 5.1/5.8): poziom polki -> marimba
SHELF_NOTE = {'000': 53, '030': 57, '060': 60, '070': 62, '090': 65, '120': 67, '140': 69, '150': 72,
              '170': 74, '200': 77}
FRONT_ARP = [62, 65, 69, 72, 76, 77, 81]          # D4 F4 A4 C5 E5 F5 A5
FRONT_CHORD = [77, 81, 84]                        # F5 A5 C6 (ostatni slot, f585)
CALIPER_NOTES = [89, 93, 96]                      # F6 A6 C7


def part_class(name, kind=None):
    import re
    n = str(name)
    k = (kind or '').lower()
    if re.match(r'^P\d{3}', n) or k in ('shelf', 'polka'):
        return 'shelf'
    if re.match(r'^D\d{3}-\d{3}', n) or k in ('divider', 'przegroda'):
        return 'divider'
    if re.match(r'^(PL|PS)\d', n) or k in ('back', 'plecy'):
        return 'back'
    if re.match(r'^(S\d{2}|DZ\d{2})$', n) or k in ('drawer', 'door', 'front'):
        return 'front'
    if re.match(r'^S\d{2}-', n) or k in ('box', 'drawer_part'):
        return 'box'
    return 'part'

# reguly proste (zdarzenie -> synth); pary/trojki obsluguje build_cues
EVENT_MAP = {
    'reveal': dict(synth='sub_boom', anchor='hit', params=dict(duration=3.0), gain_offset_db=0),
    'transition': dict(synth='air', anchor='peak', params=dict(duration=1.2), gain_offset_db=0),
    'tap': dict(synth='wood_tap', anchor='impact', params=dict(), gain_offset_db=0),
    'fabric': dict(synth='fabric', anchor='start', params=dict(), gain_offset_db=0),
    'crane': dict(synth='crane_air', anchor='start', params=dict(duration=2.4), gain_offset_db=0),
    'birds': dict(synth='birds', anchor='start', params=dict(duration=4.8), gain_offset_db=0),
}


def _norm_event(e, default_name=None):
    if isinstance(e, (int, float)):
        return {'name': default_name, 'frame': float(e)}
    name = e.get('type') or e.get('event') or e.get('name') or e.get('kind') or default_name
    frame = e.get('frame', e.get('f', e.get('frame_number')))
    if frame is None and 'time' in e:
        frame = None
    out = dict(e)
    if isinstance(e.get('meta'), dict):          # format build_scene.log_event: {type, frame, frame_exact, target, meta}
        for k, v in e['meta'].items():
            out.setdefault(k, v)
    if e.get('frame_exact') is not None:
        frame = e['frame_exact']
    out['name'] = ALIASES.get(str(name).lower(), str(name).lower()) if name else None
    out['frame'] = float(frame) if frame is not None else None
    out['obj'] = e.get('object') or e.get('obj') or e.get('target') or e.get('id') or ''
    return out


def load_events(path, shot=None):
    """Zwraca (fps, lista_zdarzen) - kazde zdarzenie: name, frame, obj + pola dodatkowe."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    fps = 25.0
    if isinstance(data, dict) and 'shots' in data and 'events' not in data:
        shots = data['shots']
        if isinstance(shots, dict):
            data = shots.get(shot) or next(iter(shots.values()))
        else:
            data = next((s for s in shots if s.get('id') == shot or s.get('name') == shot), shots[0])
    if isinstance(data, dict):
        fps = float(data.get('fps', data.get('frame_rate', fps)))
        evs = data.get('events') or data.get('timeline') or data.get('markers')
        if evs is None:  # slownik nazwa -> klatki
            evs = []
            for k, v in data.items():
                if isinstance(v, list):
                    evs += [_norm_event(x, k) for x in v]
            raw = evs
        else:
            raw = [_norm_event(x) for x in evs]
    else:
        raw = [_norm_event(x) for x in data]
    curves = data.get('curves', {}) if isinstance(data, dict) else {}
    out = []
    for e in raw:
        if e.get('frame') is None and 'time' in e:
            e['frame'] = float(e['time']) * fps
        if 'x_frame' in e and 'screen_x' not in e:
            e['screen_x'] = e['x_frame']
        if e.get('name') and e.get('frame') is not None:
            e['_curve'] = curves.get(e.get('obj')) if curves else None
            out.append(e)
    out.sort(key=lambda e: e['frame'])
    return fps, out


def _seed(*parts):
    return zlib.crc32('|'.join(str(p) for p in parts).encode()) % 100000


def _pan_of(e, pan_width=0.8):
    if 'pan' in e:
        return float(e['pan'])
    if 'screen_x' in e:
        x = min(1.0, max(0.0, float(e['screen_x'])))          # poza kadrem -> krawedz
        return max(-1.0, min(1.0, (x - 0.5) * 2 * pan_width))
    if 'world_x' in e:   # regal 1.9 m szerokosci, srodek w x=0.95 (lub 0, jesli ujemne wartosci)
        wx = float(e['world_x'])
        rel = wx / 1.9 if wx >= 0 else (wx + 0.95) / 1.9
        return max(-1.0, min(1.0, (rel - 0.5) * 2 * pan_width * 0.6))
    return 0.0


def _find_next(evs, i, names, obj, max_dt_frames=None):
    for j in range(i + 1, len(evs)):
        e = evs[j]
        if e.get('_used'):
            continue
        if e['name'] in names and (not obj or not e['obj'] or e['obj'] == obj):
            if max_dt_frames is None or e['frame'] - evs[i]['frame'] <= max_dt_frames:
                return j
    return None


BRIEF_TYPES = {'shelf_pass', 'reveal', 'caption', 'drawer_roll', 'drawer_stop', 'cloth_rustle', 'softclose_catch',
               'softclose_contact', 'door_swing', 'door_catch', 'door_contact', 'callout', 'riser', 'pop', 'silence',
               'levitate', 'land', 'divider_tick', 'box_land', 'back_land', 'front_land', 'knob_pop', 'chord',
               'crossfade', 'sting'}


def note_midi(name):
    """'F3', 'Bb2', 'F5 + sub' -> MIDI (pierwsza nuta w tekscie); None, gdy brak nuty."""
    import re
    m = re.search(r'([A-Ga-g])([#b]?)(-?\d)', str(name))
    if not m:
        return None
    n = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[m.group(1).upper()]
    n += {'#': 1, 'b': -1, '': 0}[m.group(2)]
    return n + 12 * (int(m.group(3)) + 1)


def build_cues_brief(evs, fps, event_map=None, pan_width=0.8):
    """Format events.json z Blendera wg research-brief.md (typy: shelf_pass, land, drawer_roll + curves, ...).
    Flagi cue: music_note (nuty -> szyna notes, sterowane audio.event_notes), music_fx (akcenty muzyczne:
    reveal/riser -> sterowane audio.event_music_fx), kind='silence' (proznia)."""
    import re
    sec = lambda f: f / fps  # noqa: E731
    cues, groups = [], {}
    ev = [dict(e) for e in evs]
    emap = event_map or {}

    def add(e, synth, anchor='impact', t=None, params=None, gain=0.0, pan='auto', label=None, **flags):
        c = dict(t_src=sec(e['frame']) if t is None else t, synth=synth, params=params or {},
                 seed=_seed(e['name'], e['obj'], e['frame'], synth), anchor=anchor,
                 pan=_pan_of(e, pan_width) if pan == 'auto' else pan, gain_offset_db=gain,
                 label=label or f"{e['name']}:{e['obj']}")
        c.update(flags)
        cues.append(c)
        return c

    def nxt(i, names, obj):
        for j in range(i + 1, len(ev)):
            if ev[j]['name'] in names and (not obj or ev[j]['obj'] == obj):
                return ev[j]
        return None

    for i, e in enumerate(ev):
        n, obj = e['name'], e['obj']
        if n in emap:
            r = emap[n]
            if r is None:
                continue
            add(e, r['synth'], r.get('anchor', 'sync'), params=dict(r.get('params', {})), gain=r.get('gain_offset_db', 0))
            continue
        end = e.get('end')
        if n == 'shelf_pass':
            m = (note_midi(e['note']) if e.get('note') else None) or \
                SHELF_NOTE.get(''.join(ch for ch in obj[1:4] if ch.isdigit()), 65)
            add(e, 'marimba', params=dict(midi=m, dry=False, rt60=0.9), gain=-3, pan=0.0, music_note=True)
        elif n == 'reveal':
            add(e, 'sub_boom', 'hit', params=dict(duration=2.6), gain=-2, pan=None, music_fx=True)
        elif n == 'riser':
            d = sec((end or e['frame'] + 54) - e['frame'])
            add(e, 'riser', 'end', t=sec(end or e['frame'] + 54), params=dict(duration=d, tonal=0.55, root_hz=220.0),
                pan=None, music_fx=True)
        elif n == 'silence':
            cues.append(dict(kind='silence', t_src=sec(e['frame']), t_end=sec(end or e['frame'] + 6), label='silence'))
        elif n == 'drawer_roll':
            f1 = end or e['frame'] + 12
            cv = e.get('_curve')
            prm = dict(duration=sec(f1 - e['frame']))
            if cv and cv.get('speed'):
                fr = np.asarray(cv['frames'], float)
                sp = np.abs(np.asarray(cv['speed'], float))
                sel = (fr >= e['frame']) & (fr <= f1)
                if sel.sum() > 2:
                    prm = dict(v_curve=sp[sel].tolist(), fps=fps)
            c = add(e, 'roll', 'start', params=prm, label=f'roll:{obj}')
            c['t_end'] = sec(f1)
        elif n == 'drawer_stop':
            add(e, 'drawer_stop')
        elif n == 'cloth_rustle':
            add(e, 'fabric', 'start', params=dict(duration=max(0.08, sec((end or e['frame'] + 3) - e['frame']) / 3)))
        elif n in ('softclose_catch', 'door_catch'):
            mech = 'drawer' if n == 'softclose_catch' else 'door'
            add(e, 'catch', params=dict(mech=mech))
            ct = nxt(i, {'softclose_contact' if mech == 'drawer' else 'door_contact'}, obj)
            d = sec(ct['frame'] - e['frame']) if ct else 0.6
            c = add(e, 'damper', 'start', params=dict(duration=max(0.2, d), mech=mech), label=f'damper:{obj}')
            c['t_end'] = sec(e['frame']) + d
        elif n == 'softclose_contact':
            add(e, 'thup', label=f'thup:{obj}')
        elif n == 'door_contact':
            add(e, 'tok', label=f'tok:{obj}')
        elif n == 'door_swing':
            d = sec((end or e['frame'] + 18) - e['frame'])
            p = _pan_of(e, pan_width)
            c = add(e, 'door_air', 'start', params=dict(duration=max(0.2, d), pan_from=p + 0.15, pan_to=p - 0.1),
                    pan=None)
            c['t_end'] = sec(e['frame']) + d
        elif n == 'callout':
            m = (note_midi(e['note']) if e.get('note') else None) or \
                CALIPER_NOTES[sum(1 for c in cues if c.get('synth') == 'caliper') % 3]
            add(e, 'caliper', params=dict(midi=m))
        elif n == 'pop':
            groups.setdefault(('pop', round(e['frame'] / 25)), []).append(e)
        elif n == 'levitate':
            add(e, 'levitate', 'start', pan=None)
        elif n == 'land':
            kind = (e.get('kind') or part_class(obj)).lower()
            if kind == 'shelf' or part_class(obj) == 'shelf':
                add(e, 'thup', params=dict(scale=1.2), gain=-4, label=f'shelf_land:{obj}')
                add(e, 'fly', 'end', params=dict(duration=0.56, peak_at=0.6, pan_from=0.0,
                                                  pan_to=_pan_of(e, pan_width)), pan=None, label=f'fly:{obj}')
                m = note_midi(e['note']) if e.get('note') else None
                if m:
                    add(e, 'marimba', params=dict(midi=m, dry=False), music_note=True, label=f'note:{obj}')
                if obj.startswith('P200'):
                    add(e, 'sub_boom', 'hit', params=dict(duration=1.6, f_start=80, f_end=44), gain=-4, pan=None,
                        label='P200_sub')
            else:
                add(e, 'land', params=dict(mass=4.0), gain=-2)
        elif n in ('divider_tick', 'back_land', 'front_land', 'knob_pop'):
            groups.setdefault((n, round(e['frame'], 2)), []).append(e)
        elif n == 'chord':
            notes = re.findall(r'([A-G][#b]?\d)', e.get('note', '')) or ['F5', 'A5', 'C6']
            for nn in notes:
                if note_midi(nn) >= 48:      # F2 -> bas (muzyka), tu tylko marimba
                    add(e, 'marimba', params=dict(midi=note_midi(nn), dry=False), gain=-3, pan=0.0,
                        music_note=True, label=f'chord:{nn}')
        elif n == 'sting':
            pairs = re.findall(r'([A-G][#b]?\d)\s*f\s*([\d.]+)', e.get('notes', '') or e.get('note', ''))
            for nn, fr in pairs:
                add(e, 'marimba', t=sec(float(fr)), params=dict(midi=note_midi(nn), dry=False, rt60=1.4), pan=0.0,
                    music_note=True, label=f'sting:{nn}')
        elif n in ('caption', 'crossfade', 'box_land'):
            continue
    # grupy jednoczesnych zdarzen -> jeden dzwiek (+ nuty frontow)
    for (n, key), es in sorted(groups.items(), key=lambda kv: kv[1][0]['frame']):
        e0 = es[0]
        pan = float(np.mean([_pan_of(x, pan_width) for x in es]))
        if n == 'pop':
            t0 = min(x['frame'] for x in es)
            add(e0, 'pops', 'start', t=sec(t0), params=dict(times=[sec(x['frame'] - t0) for x in es],
                pans=[_pan_of(x, pan_width) for x in es]), pan=None, label=f'pops x{len(es)}')
        elif n == 'divider_tick':
            add(e0, 'divider_tick', pan=pan, gain=min(4.0, 1.5 * np.log2(len(es))), label=f'dividers x{len(es)}')
        elif n == 'back_land':
            add(e0, 'szuff', 'sync', pan=pan, label=f'backs x{len(es)}')
        elif n == 'knob_pop':
            add(e0, 'knob_tick', pan=pan, label=f'knobs x{len(es)}')
        elif n == 'front_land':
            add(e0, 'front_clip', pan=pan, params=dict(knob=False), label=f'fronts x{len(es)}')
            for nn in sorted({x['note'] for x in es if x.get('note') and note_midi(x['note'])}):
                add(e0, 'marimba', params=dict(midi=note_midi(nn), dry=False), gain=-3, pan=pan, music_note=True,
                    label=f'front_note:{nn}')
    cues.sort(key=lambda c: c['t_src'])
    return cues


def build_cues(evs, fps, event_map=None, pan_width=0.8):
    if any(e['name'] in BRIEF_TYPES for e in evs):
        return build_cues_brief(evs, fps, event_map, pan_width)
    return build_cues_legacy(evs, fps, event_map, pan_width)


def build_cues_legacy(evs, fps, event_map=None, pan_width=0.8):
    """Zdarzenia (klatki zrodla) -> cue: dict(t_src, synth, params, seed, anchor, pan, gain_offset_db, label).
    t_src = czas w zrodle [s] liczony od klatki 0."""
    emap = dict(EVENT_MAP)
    if event_map:
        emap.update(event_map)
    cues, skipped = [], []
    evs = [dict(e) for e in evs]
    sec = lambda f: f / fps  # noqa: E731
    for i, e in enumerate(evs):
        if e.get('_used'):
            continue
        n, obj = e['name'], e['obj']
        sd = _seed(n, obj, e['frame'])
        pan = _pan_of(e, pan_width)
        inten = float(e.get('intensity', 1.0))
        if n in emap and emap[n] is None:
            skipped.append(n)
            continue
        if event_map and n in event_map and event_map[n] is not None:     # nadpisanie z konfiguracji
            r = event_map[n]
            cues.append(dict(t_src=sec(e['frame']), synth=r['synth'], params=dict(r.get('params', {})), seed=sd,
                             anchor=r.get('anchor', 'sync'), pan=pan, gain_offset_db=r.get('gain_offset_db', 0),
                             label=f'{n}:{obj}'))
            continue
        if n == 'drawer_open_start':
            j = _find_next(evs, i, {'drawer_open_end'}, obj, fps * 4)
            dur = sec(evs[j]['frame'] - e['frame']) if j is not None else float(e.get('duration', 0.9))
            full = bool(evs[j].get('full_extension', True)) if j is not None else True
            if j is not None:
                evs[j]['_used'] = True
            prm = dict(duration=max(0.3, dur), intensity=inten, end_hit=1.0 if full else 0.25)
            cues.append(dict(t_src=sec(e['frame']), synth='drawer_open', params=prm, seed=sd, anchor='start', pan=pan,
                             gain_offset_db=0, label=f'drawer_open:{obj}', t_end=sec(e['frame']) + dur))
        elif n in ('drawer_close_start', 'drawer_softclose_engage', 'drawer_closed'):
            t_start = t_eng = t_cls = None
            if n == 'drawer_close_start':
                t_start = e['frame']
                j = _find_next(evs, i, {'drawer_softclose_engage'}, obj, fps * 4)
                if j is not None:
                    t_eng = evs[j]['frame']
                    evs[j]['_used'] = True
                k = _find_next(evs, i, {'drawer_closed'}, obj, fps * 5)
                if k is not None:
                    t_cls = evs[k]['frame']
                    evs[k]['_used'] = True
            elif n == 'drawer_softclose_engage':
                t_eng = e['frame']
                k = _find_next(evs, i, {'drawer_closed'}, obj, fps * 3)
                if k is not None:
                    t_cls = evs[k]['frame']
                    evs[k]['_used'] = True
            else:
                t_cls = e['frame']
            push = sec(t_eng - t_start) if (t_eng is not None and t_start is not None) else 0.42
            damp = sec(t_cls - t_eng) if (t_cls is not None and t_eng is not None) else 0.55
            if t_start is not None and t_eng is None and t_cls is not None:
                tot = sec(t_cls - t_start)
                push, damp = tot * 0.45, tot * 0.55
            anchor, t_ref = ('start', t_start) if t_start is not None else (('engage', t_eng) if t_eng is not None
                                                                            else ('closed', t_cls))
            t_last = max(x for x in (t_start, t_eng, t_cls) if x is not None)
            cues.append(dict(t_src=sec(t_ref), synth='drawer_close',
                             params=dict(push=max(0.15, push), damp=max(0.2, damp), intensity=inten), seed=sd,
                             anchor=anchor, pan=pan, gain_offset_db=0, label=f'drawer_close:{obj}',
                             t_end=sec(t_last)))
        elif n == 'door_open_start':
            j = _find_next(evs, i, {'door_open_end'}, obj, fps * 4)
            dur = sec(evs[j]['frame'] - e['frame']) if j is not None else float(e.get('duration', 0.8))
            if j is not None:
                evs[j]['_used'] = True
            cues.append(dict(t_src=sec(e['frame']), synth='door_open',
                             params=dict(duration=max(0.3, dur), intensity=inten, creak=float(e.get('creak', 0.0))),
                             seed=sd, anchor='start', pan=pan, gain_offset_db=0, label=f'door_open:{obj}'))
        elif n in ('door_close_start', 'door_softclose_engage', 'door_close_click'):
            t_start = t_eng = t_cls = None
            if n == 'door_close_start':
                t_start = e['frame']
                j = _find_next(evs, i, {'door_softclose_engage'}, obj, fps * 4)
                if j is not None:
                    t_eng = evs[j]['frame']
                    evs[j]['_used'] = True
                k = _find_next(evs, i, {'door_close_click'}, obj, fps * 5)
                if k is not None:
                    t_cls = evs[k]['frame']
                    evs[k]['_used'] = True
            elif n == 'door_softclose_engage':
                t_eng = e['frame']
                k = _find_next(evs, i, {'door_close_click'}, obj, fps * 3)
                if k is not None:
                    t_cls = evs[k]['frame']
                    evs[k]['_used'] = True
            else:
                t_cls = e['frame']
            push = sec(t_eng - t_start) if (t_eng is not None and t_start is not None) else 0.45
            damp = sec(t_cls - t_eng) if (t_cls is not None and t_eng is not None) else 0.6
            if t_start is not None and t_eng is None and t_cls is not None:
                tot = sec(t_cls - t_start)
                push, damp = tot * 0.45, tot * 0.55
            anchor, t_ref = ('start', t_start) if t_start is not None else (('engage', t_eng) if t_eng is not None
                                                                            else ('click', t_cls))
            t_last = max(x for x in (t_start, t_eng, t_cls) if x is not None)
            cues.append(dict(t_src=sec(t_ref), synth='door_close',
                             params=dict(push=max(0.15, push), damp=max(0.2, damp), intensity=inten), seed=sd,
                             anchor=anchor, pan=pan, gain_offset_db=0, label=f'door_close:{obj}',
                             t_end=sec(t_last)))
        elif n == 'part_launch':
            pc = part_class(obj, e.get('kind'))
            if pc != 'shelf':          # brief: whoosh tylko na kroki korpusu (polki), nie 140 razy
                continue
            j = _find_next(evs, i, {'part_landing'}, obj, fps * 5)
            dur = sec(evs[j]['frame'] - e['frame']) if j is not None else 0.56
            cues.append(dict(t_src=sec(e['frame']), synth='fly', params=dict(duration=max(0.2, dur), peak_at=0.6,
                             pan_from=pan * 0.5, pan_to=pan), seed=sd, anchor='start', pan=None, gain_offset_db=0,
                             label=f'fly:{obj}'))
        elif n == 'part_landing':
            pc = part_class(obj, e.get('kind'))
            t = sec(e['frame'])
            if pc == 'shelf':
                cues.append(dict(t_src=t, synth='thup', params=dict(scale=1.2, intensity=inten), seed=sd,
                                 anchor='impact', pan=pan, gain_offset_db=-4, label=f'shelf_land:{obj}'))
                lvl = ''.join(ch for ch in str(obj)[1:4] if ch.isdigit())
                if lvl in SHELF_NOTE:
                    cues.append(dict(t_src=t, synth='marimba', params=dict(midi=SHELF_NOTE[lvl], dry=False), seed=sd,
                                     anchor='impact', pan=pan, gain_offset_db=0, label=f'note:{obj}', music_note=True))
                if lvl == '200':       # wieniec P200: F5 + glebokie 'tok' + sub (brief 6.2, f555)
                    cues.append(dict(t_src=t, synth='sub_boom', params=dict(duration=1.6, f_start=80, f_end=44),
                                     seed=sd, anchor='hit', pan=None, gain_offset_db=-4, label='P200_sub'))
            elif pc == 'divider':
                cues.append(dict(t_src=t, synth='divider_tick', params=dict(), seed=sd, anchor='impact', pan=pan,
                                 gain_offset_db=0, label=f'divider:{obj}', group_key=('divider', round(t, 2))))
            elif pc == 'back':
                cues.append(dict(t_src=t, synth='szuff', params=dict(), seed=sd, anchor='sync', pan=pan,
                                 gain_offset_db=0, label=f'back:{obj}', group_key=('back', round(t, 2))))
            elif pc == 'front':
                cues.append(dict(t_src=t, synth='front_clip', params=dict(), seed=sd, anchor='impact', pan=pan,
                                 gain_offset_db=0, label=f'front:{obj}', front_slot=round(t, 3),
                                 group_key=('front', round(t, 2))))
            elif pc == 'box':
                continue               # czesci skrzynek laduja w ciemnym wnetrzu - bez dzwieku
            else:
                mass = e.get('mass_kg')
                L = float(e.get('length_mm', 900)) / 1000.0
                W = float(e.get('width_mm', 380)) / 1000.0
                if mass is None:
                    mass = L * W * 0.018 * 680.0
                cues.append(dict(t_src=t, synth='land', params=dict(mass=float(mass), size=(max(L, 0.15), max(W, 0.1)),
                                 surface=e.get('surface', 'stack'), intensity=inten), seed=sd, anchor='impact', pan=pan,
                                 gain_offset_db=0, label=f'land:{obj}'))
        elif n == 'shelf_pass':
            lvl = ''.join(ch for ch in str(obj)[1:4] if ch.isdigit())
            midi = int(e.get('midi', SHELF_NOTE.get(lvl, 65)))
            cues.append(dict(t_src=sec(e['frame']), synth='marimba', params=dict(midi=midi, dry=False, rt60=0.9),
                             seed=sd, anchor='impact', pan=pan, gain_offset_db=0, label=f'shelf_pass:{obj}',
                             music_note=True))
        elif n == 'callout':
            k_ = sum(1 for c in cues if c['synth'] == 'caliper')
            midi = int(e.get('midi', CALIPER_NOTES[k_ % 3]))
            cues.append(dict(t_src=sec(e['frame']), synth='caliper', params=dict(midi=midi), seed=sd, anchor='impact',
                             pan=pan, gain_offset_db=0, label=f'callout:{obj}'))
        elif n == 'pop':
            cues.append(dict(t_src=sec(e['frame']), synth='pops', params=dict(count=int(e.get('count', 140)),
                             spread=float(e.get('spread_s', 0.24))), seed=sd, anchor='start', pan=None,
                             gain_offset_db=0, label='pop'))
        elif n == 'levitate':
            cues.append(dict(t_src=sec(e['frame']), synth='levitate', params=dict(), seed=sd, anchor='start', pan=None,
                             gain_offset_db=0, label='levitate'))
        elif n == 'drawer_roll':
            vc = e.get('velocity') or e.get('v') or e.get('speed')
            prm = dict(v_curve=vc, fps=fps) if isinstance(vc, list) and len(vc) > 1 else \
                dict(duration=float(e.get('duration', 0.5)))
            cues.append(dict(t_src=sec(e['frame']), synth='roll', params=prm, seed=sd, anchor='start', pan=pan,
                             gain_offset_db=0, label=f'roll:{obj}'))
        elif n == 'screw_start':
            j = _find_next(evs, i, {'screw_end'}, obj, fps * 4)
            dur = sec(evs[j]['frame'] - e['frame']) if j is not None else float(e.get('duration', 0.8))
            if j is not None:
                evs[j]['_used'] = True
            cues.append(dict(t_src=sec(e['frame']), synth='screw', params=dict(duration=max(0.25, dur)), seed=sd,
                             anchor='start', pan=pan, gain_offset_db=0, label=f'screw:{obj}'))
        elif n in emap:
            r = emap[n]
            cues.append(dict(t_src=sec(e['frame']), synth=r['synth'], params=dict(r.get('params', {})), seed=sd,
                             anchor=r.get('anchor', 'sync'), pan=pan, gain_offset_db=r.get('gain_offset_db', 0),
                             label=f'{n}:{obj}'))
        elif n in ('drawer_open_end', 'door_open_end', 'screw_end'):
            pass
        else:
            skipped.append(n)
    # jednoczesne przegrody / plecy -> jeden dzwiek na grupe
    seen, merged = set(), []
    for c in cues:
        gk = c.get('group_key')
        if gk:
            if gk in seen:
                continue
            seen.add(gk)
        merged.append(c)
    cues = merged
    # fronty: sloty czasowe -> nuty arpeggio D4 F4 A4 C5 E5 F5 A5, ostatni slot = akord F5 A5 C6
    slots = sorted({c['front_slot'] for c in cues if 'front_slot' in c})
    if slots:
        done = set()
        for c in list(cues):
            if 'front_slot' not in c or c['front_slot'] in done:
                continue
            done.add(c['front_slot'])
            k_ = slots.index(c['front_slot'])
            notes = FRONT_CHORD if (k_ == len(slots) - 1 and len(slots) > 1) else [FRONT_ARP[min(k_, len(FRONT_ARP) - 1)]]
            for m in notes:
                cues.append(dict(t_src=c['t_src'], synth='marimba', params=dict(midi=m, dry=False), seed=c['seed'] + m,
                                 anchor='impact', pan=c['pan'], gain_offset_db=-3, label=f'front_note:{m}',
                                 music_note=True))
    if skipped:
        print(f'  [timeline] pominiete zdarzenia (brak reguly): {sorted(set(skipped))}')
    cues.sort(key=lambda c: c['t_src'])
    return cues


def cues_for_shot(shot, shot_start, shot_dur, event_map=None, pan_width=0.8, base_dir='.'):
    """Wczytuje zdarzenia ujecia i przelicza na czas montazu. shot: dict z konfiguracji."""
    path = shot.get('events')
    if not path:
        return []
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.join(base_dir, path))
    if not os.path.isfile(path):
        print(f'  [timeline] brak pliku zdarzen: {path}')
        return []
    fps, evs = load_events(path, shot.get('events_shot', shot.get('id')))
    fps = float(shot.get('events_fps', fps))
    off = float(shot.get('event_frame_offset', 0))
    for e in evs:
        e['frame'] -= off
    cues = build_cues(evs, fps, event_map, pan_width * float(shot.get('pan_scale', 1.0)))
    t_in = float(shot.get('_in_s', 0.0))
    speed = float(shot.get('speed', 1.0))
    out = []
    for c in cues:
        t = shot_start + (c['t_src'] - t_in) / speed
        if shot_start - 0.25 <= t <= shot_start + shot_dur + 0.1:
            c = dict(c)
            c['at'] = t
            c['shot'] = shot.get('id')
            if speed != 1.0:   # czasy trwania skalowane predkoscia ujecia
                for k in ('duration', 'push', 'damp'):
                    if k in c['params']:
                        c['params'][k] = c['params'][k] / speed
            out.append(c)
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Podglad: zdarzenia Blendera -> cues')
    ap.add_argument('events')
    ap.add_argument('--shot')
    ap.add_argument('--start', type=float, default=0.0, help='start ujecia w montazu [s]')
    a = ap.parse_args()
    fps, evs = load_events(a.events, a.shot)
    for c in build_cues(evs, fps):
        if c.get('kind') == 'silence':
            print(f"{a.start + c['t_src']:7.3f}s  SILENCE do {a.start + c['t_end']:.3f}s")
            continue
        pn = 'stereo' if c['pan'] is None else f"{c['pan']:+.2f}"
        prm = {k: (f'[{len(v)}]' if isinstance(v, list) else v) for k, v in c['params'].items()}
        fl = ' [nuta]' if c.get('music_note') else (' [muz-fx]' if c.get('music_fx') else '')
        print(f"{a.start + c['t_src']:7.3f}s  {c['synth']:13s} anchor={c['anchor']:7s} pan={pn:6s}  "
              f"{c['label']}{fl}  {prm}")
