#!/usr/bin/env python3
"""make_mock_events.py - atrapa renders/events.json zgodna z build_scene.export_events()
i z harmonogramem z research-brief.md (5, 5.8, 6.2). Sluzy do testu timeline/miksu przed renderami.

  python3 make_mock_events.py [-o test/brief_events_mock.json]
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def ev(t, f, target='', **meta):
    e = dict(type=t, frame=int(round(f)), frame_exact=round(float(f), 3), time_s=round(f / 25, 3), target=target)
    if meta:
        e['meta'] = meta
    return e


def build():
    E = []
    shelves = [('P000', 0), ('P030', 11.25), ('P060', 22.5), ('P070a', 26.25), ('P090', 33.75), ('P120a', 45),
               ('P140a', 52.5), ('P150a', 56.25)]
    for name, f in shelves:                                   # S01: czola polek mijaja srodek kadru
        E.append(ev('shelf_pass', f, name, screen_x=0.5))
    E.append(ev('crane', 0, 'S01_cam'))
    E.append(ev('drawer_open_start', 188, 'S09', travel_mm=352, screen_x=0.45))   # S03
    E.append(ev('drawer_open_end', 210, 'S09', full_extension=True, screen_x=0.45))
    E.append(ev('fabric', 211, 'S09', screen_x=0.45))
    E.append(ev('drawer_close_start', 250, 'S10', screen_x=0.5))                  # S04
    E.append(ev('drawer_softclose_engage', 262, 'S10', remaining_mm=40, screen_x=0.5))
    E.append(ev('drawer_closed', 285, 'S10', screen_x=0.5))
    E.append(ev('door_close_start', 300, 'DZ02', screen_x=0.8))                    # S05
    E.append(ev('door_softclose_engage', 318, 'DZ02', remaining_deg=14, screen_x=0.7))
    E.append(ev('door_close_click', 330, 'DZ02', screen_x=0.62))
    for f, lab, x in [(360, '18 mm', 0.64), (375, '2 mm', 0.25), (390, '13 warstw', 0.68)]:   # S06
        E.append(ev('callout', f, lab, screen_x=x))
    E.append(ev('pop', 465, 'sheets', count=140, spread_s=0.24))                  # S07
    E.append(ev('levitate', 480, 'all'))                                          # S08
    steps = [('P000', 502.5, ['D010-000', 'D040-000', 'D080-000', 'D140-000', 'D170-000']),
             ('P030', 506.25, ['D030-030', 'D070-030', 'D100-030', 'D160-030']),
             ('P060', 510, ['D010-060', 'D050-060', 'D080-060', 'D120-060', 'D150-060', 'D170-060']),
             ('P070a', 513.75, ['D020-070', 'D060-070']), ('P070b', 517.5, ['D180-070']),
             ('P090', 521.25, ['D030-090', 'D070-090', 'D110-090', 'D130-090', 'D170-090']),
             ('P120a', 525, ['D010-120']), ('P120b', 528.75, ['D100-120', 'D140-120', 'D160-120']),
             ('P140a', 532.5, ['D020-140', 'D050-140', 'D080-140', 'D110-140']), ('P140b', 536.25, ['D180-140']),
             ('P150a', 540, ['D010-150', 'D040-150']), ('P150b', 543.75, ['D150-150', 'D170-150']),
             ('P170', 547.5, ['D020-170', 'D060-170', 'D100-170', 'D140-170', 'D180-170']), ('P200', 555, [])]
    for k, (sh, fl, divs) in enumerate(steps):
        x = 0.36 + 0.29 * (k % 5) / 4
        E.append(ev('part_launch', fl - 14, sh, screen_x=x))
        E.append(ev('part_landing', fl, sh, kind='shelf', screen_x=x))
        for d in divs:
            E.append(ev('part_launch', fl + 2 - 14, d))
            E.append(ev('part_landing', fl + 2, d, kind='divider', screen_x=x))
    for i in range(16):
        E.append(ev('part_landing', 551.25, f'PL{i + 1:02d}', kind='back'))
    slots = [(558.75, ['S01', 'S02']), (562.5, ['S05', 'S07']), (566.25, ['S03', 'DZ03']), (570, ['S08', 'S04', 'S09']),
             (573.75, ['S06', 'DZ06']), (577.5, ['DZ01', 'DZ05', 'S10']), (581.25, ['DZ04', 'DZ02']),
             (585, ['DZ08', 'DZ07', 'DZ09'])]
    for k, (f, fronts) in enumerate(slots):
        for fr in fronts:
            E.append(ev('part_landing', f, fr, kind='drawer' if fr.startswith('S') else 'door',
                        screen_x=0.38 + 0.26 * k / 7))
    E.append(ev('drawer_close_start', 600, 'S03', screen_x=0.5))                   # S09
    E.append(ev('drawer_softclose_engage', 612, 'S03', screen_x=0.5))
    E.append(ev('drawer_closed', 630, 'S03', screen_x=0.5))
    E.sort(key=lambda e: (e['frame_exact'], e['type']))
    return dict(fps=25, frame_start=0, frame_end=749, events=E, mock=True,
                note='ATRAPA wg research-brief.md - zastapic plikiem z Blendera (renders/events.json)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-o', '--out', default=os.path.join(HERE, 'test', 'brief_events_mock.json'))
    a = ap.parse_args()
    d = build()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(f'{a.out}: {len(d["events"])} zdarzen')
