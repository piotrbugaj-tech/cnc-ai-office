#!/usr/bin/env python3
"""sync_check.py - kontrola synchronizacji montazu z events.json i z research-brief.md.

Sprawdza:
  1. ciecia na siatce 100 BPM (cwiercnuta = 15 kl., takt = 60 kl.),
  2. czy kazde zdarzenie mechaniczne w oknach ujec ma dzwiek (albo jest w stemie muzyki),
  3. czy dzwiek nie wypada poza ujecie (start akcji przed cieciem / punkt synchronizacji po cieciu),
  4. zgodnosc klatek zdarzen z harmonogramem briefu (5, 5.8, 6.2, 10) i siatka 16-tek (3,75 kl.).

  python3 sync_check.py configs/robocza_30s_16x9.yaml [--md test/sync_30s.md]
Wymaga wczesniejszego `edit.py ... --audio-only` albo pelnego przebiegu (raport *_cues.json w work_dir).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit  # noqa: E402

FPS = 25.0
# research-brief.md: klatki referencyjne
BRIEF = {
    ('shelf_pass', 'P000'): 0, ('shelf_pass', 'P030'): 11.25, ('shelf_pass', 'P060'): 22.5,
    ('shelf_pass', 'P070a'): 26.25, ('shelf_pass', 'P090'): 33.75, ('shelf_pass', 'P120a'): 45,
    ('shelf_pass', 'P140a'): 52.5, ('shelf_pass', 'P150a'): 56.25,
    ('reveal', 'regal'): 60, ('drawer_roll', 'S09'): 188, ('drawer_stop', 'S09'): 210, ('cloth_rustle', 'S09'): 211,
    ('drawer_roll', 'S10'): 250, ('softclose_catch', 'S10'): 262, ('softclose_contact', 'S10'): 285,
    ('door_swing', 'DZ02'): 300, ('door_catch', 'DZ02'): 318, ('door_contact', 'DZ02'): 330,
    ('callout', 'A_18mm'): 360, ('callout', 'B_2mm'): 375, ('callout', 'C_13warstw'): 390,
    ('riser', ''): 420, ('silence', ''): 474, ('levitate', 'all'): 480,
    ('land', 'P000'): 502.5, ('land', 'P030'): 506.25, ('land', 'P060'): 510, ('land', 'P070a'): 513.75,
    ('land', 'P070b'): 517.5, ('land', 'P090'): 521.25, ('land', 'P120a'): 525, ('land', 'P120b'): 528.75,
    ('land', 'P140a'): 532.5, ('land', 'P140b'): 536.25, ('land', 'P150a'): 540, ('land', 'P150b'): 543.75,
    ('land', 'P170'): 547.5, ('land', 'P200'): 555, ('chord', ''): 585,
    ('drawer_roll', 'S03'): 600, ('softclose_catch', 'S03'): 612, ('softclose_contact', 'S03'): 630,
    ('sting', 'RYTM'): 660,
}
FRONT_SLOTS = {558.75: {'S01', 'S02'}, 562.5: {'S05', 'S07'}, 566.25: {'S03', 'DZ03'}, 570: {'S08', 'S04', 'S09'},
               573.75: {'S06', 'DZ06'}, 577.5: {'DZ01', 'DZ05', 'S10'}, 581.25: {'DZ04', 'DZ02'},
               585: {'DZ08', 'DZ07', 'DZ09'}}
SILENT_BY_DESIGN = {'caption', 'crossfade', 'box_land'}
ACCENT = {'drawer_stop', 'softclose_contact', 'door_contact', 'callout', 'land', 'front_land', 'chord', 'sting',
          'reveal', 'levitate', 'shelf_pass'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('--md')
    a = ap.parse_args()
    cfg = edit.load_cfg(a.config)
    base = os.path.dirname(os.path.abspath(a.config))
    out = []
    for vname, V in cfg['versions'].items():
        work = edit.absp(V.get('work_dir', os.path.join(cfg.get('work_dir', 'work'), vname)), base)
        out_mp4 = edit.absp(V.get('export', {}).get('output', f'out/{vname}.mp4'), base)
        cj = os.path.join(work, os.path.splitext(os.path.basename(out_mp4))[0] + '_cues.json')
        rep = json.load(open(cj, encoding='utf-8'))
        evp = edit.absp(V['audio']['events'], base)
        ej = json.load(open(evp, encoding='utf-8'))
        evs = ej['events']
        starts = rep['shot_starts_f']
        shots = V['shots']
        total_f = int(round(rep['duration_s'] * FPS))
        out.append(f'### {vname} ({rep["duration_s"]:.2f} s)\n')
        # 1. ciecia
        rows = []
        for sh, st in zip(shots, starts):
            beat = st % 15 == 0
            bar = st % 60 == 0
            pos = f'takt {st // 60 + 1}, cwiercnuta {int((st % 60) // 15) + 1}' if beat else f'{st % 15} kl. poza siatka'
            rows.append(f"| {sh.get('id')} | {st} | {st / FPS:.2f} | {'tak' if beat else 'NIE'} | "
                        f"{'raz taktu' if bar else pos} |")
        out.append('**Ciecia na siatce 100 BPM**\n\n| ujecie | kl. montazu | s | na cwiercnucie | pozycja |\n|---|---|---|---|---|')
        out += rows
        # okna ujec (klatki zrodla) -> montaz
        wins = []
        for i, (sh, st) in enumerate(zip(shots, starts)):
            if 'f' in sh and sh.get('events') is not False:
                f1 = sh['f'][1]
                if i + 1 < len(starts):          # okno efektywne do startu nastepnego ujecia
                    f1 = min(f1, sh['f'][0] + starts[i + 1] - st)
                wins.append((sh.get('id'), sh['f'][0], f1, st))
        placed = rep['mix']['cues']
        covered = {}
        for c in placed:
            keys = c.get('evs') or ([c['ev']] if c.get('ev') else [])
            for k in keys:
                covered.setdefault((k[0], k[1], round(float(k[2]), 3)), []).append(c)
        # 2./3. pokrycie i granice ujec
        miss, outside, notin = [], [], []
        n_mech = n_cov = 0
        for e in evs:
            t = e['type']
            if t in SILENT_BY_DESIGN:
                continue
            fe = float(e.get('frame_exact', e['frame']))
            w = next((x for x in wins if x[1] - 0.02 <= fe < x[2] - 0.001), None)
            if w is None:
                notin.append(e)
                continue
            n_mech += 1
            cs = covered.get((t, e.get('target', ''), round(fe, 3)))
            if not cs:
                miss.append((e, w))
                continue
            n_cov += 1
            for c in cs:
                if c.get('skipped') or c.get('type') == 'silence' or c.get('t0') is None:
                    continue
                sh_start = w[3] / FPS
                sh_end = (w[3] + (w[2] - w[1])) / FPS
                if c['t0'] < sh_start - 0.05 and not c.get('clip_from'):
                    outside.append((e, w, c, f"start {c['t0']:.2f} s < ciecie {sh_start:.2f} s"))
                if c['t'] > sh_end + 0.02:
                    outside.append((e, w, c, f"sync {c['t']:.2f} s > koniec ujecia {sh_end:.2f} s"))
        out.append(f'\n**Pokrycie zdarzen w oknach ujec:** {n_cov}/{n_mech} ma dzwiek '
                   f'(pominiete celowo: {sorted(SILENT_BY_DESIGN)}; poza wersja: {len(notin)} zdarzen).')
        if miss:
            out.append('\nBez dzwieku:')
            for e, w in miss:
                out.append(f"- {e['type']} {e.get('target')} f{e.get('frame_exact')} (ujecie {w[0]})")
        clipped = [c for c in placed if c.get('clip_from')]
        if clipped:
            out.append('\nDzwiek zaczety przed cieciem (przyciety do ciecia, fade 10 ms):')
            for c in clipped:
                out.append(f"- {c['label']}: start {c['t0']:.2f} s, ciecie {c['clip_from']:.2f} s ({c.get('shot')})")
        if outside:
            out.append('\nPoza ujeciem:')
            for e, w, c, why in outside:
                out.append(f"- {c['label']} ({w[0]}): {why}")
        else:
            out.append('\nZaden punkt synchronizacji nie wypada poza swoje ujecie.')
        sk = [c for c in placed if c.get('skipped')]
        if sk:
            out.append('\nZdarzenia obsluzone przez stem muzyki (nie dublowane): ' +
                       ', '.join(sorted({f"{c['label']} @{c['t']:.2f}s" for c in sk})))
        out.append('')
    # 4. events.json vs brief (raz)
    ej = json.load(open(edit.absp(list(cfg['versions'].values())[0]['audio']['events'], base), encoding='utf-8'))
    evs = ej['events']
    diffs, offgrid = [], []
    got = {(e['type'], e.get('target', '')): float(e.get('frame_exact', e['frame'])) for e in evs}
    for k, fb in BRIEF.items():
        fe = got.get(k)
        if fe is None:
            diffs.append(f'| {k[0]} {k[1]} | {fb} | brak | — |')
        elif abs(fe - fb) > 0.01:
            diffs.append(f'| {k[0]} {k[1]} | {fb} | {fe} | {fe - fb:+.2f} kl. |')
    fr = {}
    for e in evs:
        if e['type'] == 'front_land':
            fr.setdefault(float(e['frame_exact']), set()).add(e['target'].split('-')[0])
    for f, s in FRONT_SLOTS.items():
        if fr.get(f) != s:
            diffs.append(f"| front_land slot | {f} {sorted(s)} | {sorted(fr.get(f, set()))} | — |")
    for e in evs:
        if e['type'] in ACCENT:
            fe = float(e.get('frame_exact', e['frame']))
            if abs(fe / 3.75 - round(fe / 3.75)) > 0.01:
                offgrid.append(f"{e['type']} {e.get('target')} f{fe}")
    out.append('### events.json vs research-brief.md\n')
    if diffs:
        out.append('| zdarzenie | brief [kl.] | events.json [kl.] | roznica |\n|---|---|---|---|')
        out += diffs
    else:
        out.append(f'Wszystkie {len(BRIEF)} klatki referencyjne briefu i 8 slotow frontow zgodne co do klatki.')
    out.append('\nAkcenty poza siatka 16-tek (3,75 kl.): ' + (', '.join(offgrid) if offgrid else 'brak') + '.')
    txt = '\n'.join(out)
    print(txt)
    if a.md:
        with open(a.md, 'w', encoding='utf-8') as f:
            f.write(txt + '\n')


if __name__ == '__main__':
    main()
