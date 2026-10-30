#!/usr/bin/env python3
"""edit.py - montaz promo regalu RYTM: ujecia -> przejscia -> grading -> typografia -> miks -> eksport.

Wejscie: konfiguracja YAML/JSON (przyklady: configs/rytm_30s_16x9.yaml, test/pipeline_test.yaml).
  versions:
    <nazwa>:
      size: [1920, 1080]            # rozdzielczosc wyjscia
      fps: 25
      shots:                        # kolejno w montazu
        - id: S01
          src: ../renders/S01/####.png | plik.mp4 | obraz.png | "color:#EFEAE2"
          f: [0, 60]                # klatki ZRODLA (globalne f z Blendera; dla sekwencji = numery plikow)
          # albo: in: 1.5, dur: 2.4 (sekundy zrodla)
          cx: 0.45 | [0.50, 0.46, 0.47]   # srodek kadrowania (0-1), lista = klucze rozlozone rowno w czasie
          cy: 0.5
          zoom: 1.0
          transition: {type: dissolve, frames: 10}   # przejscie DO tego ujecia (domyslnie twarde ciecie)
          sharpen: true             # unsharp 5:5:0.4 (9:16 po upscalu)
        - id: S10
          type: endcard             # plansza 2D (Pillow): bg, dur_f, elements[glyph|text]
      titles:   [{text, style, x, y, f: [in, out], anim: {in, out, rise}, glow}]   # f = klatki MONTAZU
      dims:     [{text, p1: [x,y], p2: [x,y], f: [in, out]}]                       # wymiary CAD
      audio:    {music, events, event_notes, sfx: [...], duck, silence, master}    # patrz mixer.py
      grade:    {lut: auto|sciezka|none, vignette: 0.09, grain: 5}
      export:   {output: out/x.mp4, crf: 16, preset: slow, prores: false}
Zdarzenia z Blendera (audio.events: sciezka do events.json) sa przeliczane per ujecie:
  czas_montazu = start_ujecia + (f_zdarzenia - f_in_ujecia) / fps   (tylko w oknie ujecia).

Uzycie:
  python3 edit.py configs/rytm_30s_16x9.yaml                 # wszystkie wersje z pliku
  python3 edit.py test/pipeline_test.yaml --version 16x9 --draft
  python3 edit.py cfg.yaml --audio-only                      # tylko miks (WAV + raport)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402
import lut  # noqa: E402
import mixer  # noqa: E402
import timeline  # noqa: E402
import typo  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FF = shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
FP = shutil.which('ffprobe') or '/usr/bin/ffprobe'


def run(cmd, quiet=True):
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(' '.join(cmd)[:2000])
        print(r.stderr[-3000:])
        raise RuntimeError('ffmpeg nie powiodl sie')
    if not quiet:
        print(r.stderr[-1500:])
    return r, time.time() - t0


def load_cfg(path):
    txt = open(path, encoding='utf-8').read()
    if path.endswith(('.yaml', '.yml')):
        import yaml
        return yaml.safe_load(txt)
    return json.loads(txt)


def absp(p, base):
    p = os.path.expanduser(str(p))
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))


# --------------------------------------------------------------------------
# zrodla
# --------------------------------------------------------------------------
def seq_pattern(src, base):
    """'dir/####.png' -> (wzorzec ffmpeg, lista numerow) albo None."""
    p = absp(src, base)
    m = re.search(r'(#+)', os.path.basename(p))
    if not m:
        return None
    k = len(m.group(1))
    d = os.path.dirname(p)
    pre, post = os.path.basename(p).split(m.group(1), 1)
    rx = re.compile('^' + re.escape(pre) + r'(\d{%d,})' % k + re.escape(post) + '$')
    nums = sorted(int(mm.group(1)) for f in (os.listdir(d) if os.path.isdir(d) else []) if (mm := rx.match(f)))
    return os.path.join(d, pre + f'%0{k}d' + post), nums


def probe(path):
    r = subprocess.run([FP, '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,r_frame_rate,nb_frames,duration', '-of', 'json', path],
                       capture_output=True, text=True)
    s = json.loads(r.stdout)['streams'][0]
    num, den = s['r_frame_rate'].split('/')
    return int(s['width']), int(s['height']), float(num) / float(den)


def lerp_expr(keys, dur):
    """Lista wartosci (rozlozone rowno w [0, dur]) albo [[t, v], ...] -> wyrazenie ffmpeg od t."""
    if not isinstance(keys, (list, tuple)):
        return f'{float(keys)}', float(keys)
    if keys and not isinstance(keys[0], (list, tuple)):
        if len(keys) == 1:
            return f'{float(keys[0])}', float(keys[0])
        keys = [[dur * i / (len(keys) - 1), v] for i, v in enumerate(keys)]
    expr = f'{keys[-1][1]}'
    for (t0, v0), (t1, v1) in reversed(list(zip(keys[:-1], keys[1:]))):
        seg = f'({v0}+({v1}-{v0})*(t-{t0})/{max(t1 - t0, 1e-6)})'
        expr = f'if(lt(t,{t1}),{seg},{expr})'
    expr = f'if(lt(t,{keys[0][0]}),{keys[0][1]},{expr})'
    return expr, float(keys[0][1])


# --------------------------------------------------------------------------
# etap 1: normalizacja ujec do posrednich plikow (FFV1, RGB 10-bit)
# --------------------------------------------------------------------------
def normalize_shot(sh, V, base, work, idx, draft=False):
    W, H, fps = V['W'], V['H'], V['fps']
    out = os.path.join(work, f'shot_{idx:02d}_{sh.get("id", idx)}.mkv')
    src = sh.get('src')
    stype = sh.get('type')
    inp = []
    n_frames = None
    src_w = src_h = None
    if stype == 'endcard':
        ed = os.path.join(work, f'endcard_{idx:02d}')
        shutil.rmtree(ed, ignore_errors=True)
        res = typo.render_endcard(sh, V['name_style'], W, H, fps, ed, scale=V['scale'], base_dir=base)
        inp = ['-framerate', str(fps), '-start_number', '0', '-i', res['pattern']]
        n_frames = res['n']
        src_w, src_h = W, H
    elif isinstance(src, str) and src.startswith('color:'):
        n_frames = int(round(float(sh.get('dur', sh.get('dur_f', 50) / fps)) * fps)) if 'dur' in sh else int(sh.get('dur_f', 50))
        col = src.split(':', 1)[1].lstrip('#')
        inp = ['-f', 'lavfi', '-i', f'color=c=0x{col}:s={W}x{H}:r={fps}:d={n_frames / fps + 0.1}']
        src_w, src_h = W, H
    else:
        sq = seq_pattern(src, base)
        if sq:
            pattern, nums = sq
            if not nums:
                raise FileNotFoundError(f'brak klatek: {src}')
            f0, f1 = sh.get('f', [nums[0], nums[-1] + 1])
            f0 = int(round(f0))
            n_frames = int(round(f1 - f0))
            missing = [f for f in range(f0, f0 + n_frames) if f not in set(nums)]
            if missing:
                print(f'  [uwaga] {sh.get("id")}: brak {len(missing)} klatek (np. {missing[:5]}) - ffmpeg zatrzyma sie wczesniej')
            inp = ['-framerate', str(sh.get('src_fps', fps)), '-start_number', str(f0), '-i', pattern]
            from PIL import Image
            with Image.open(pattern % f0) as im:
                src_w, src_h = im.size
        else:
            path = absp(src, base)
            ext = os.path.splitext(path)[1].lower()
            if ext in ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.exr', '.webp'):
                n_frames = int(round(float(sh.get('dur', 2.0)) * fps))
                inp = ['-loop', '1', '-framerate', str(fps), '-i', path]
                from PIL import Image
                with Image.open(path) as im:
                    src_w, src_h = im.size
            else:
                src_w, src_h, sfps = probe(path)
                if 'f' in sh:
                    t_in = sh['f'][0] / sfps
                    dur = (sh['f'][1] - sh['f'][0]) / sfps
                else:
                    t_in = float(sh.get('in', 0.0))
                    dur = float(sh['dur'])
                speed = float(sh.get('speed', 1.0))
                n_frames = int(round(dur / speed * fps))
                inp = ['-ss', f'{t_in:.4f}', '-t', f'{dur + 0.5:.4f}', '-i', path]
                sh['_src_fps'] = sfps
    # kadrowanie do proporcji wyjscia (cx/cy/zoom) + skalowanie Lanczos
    zoom = float(sh.get('zoom', 1.0))
    ar = W / H
    cw = min(src_w, src_h * ar) / zoom
    ch = cw / ar
    dur_s = n_frames / fps
    cx_e, _ = lerp_expr(sh.get('cx', 0.5), dur_s)
    cy_e, _ = lerp_expr(sh.get('cy', 0.5), dur_s)
    cwi, chi = int(round(cw / 2) * 2), int(round(ch / 2) * 2)
    fx = (f"crop=w={cwi}:h={chi}:x='max(0,min(iw-ow,({cx_e})*iw-ow/2))':"
          f"y='max(0,min(ih-oh,({cy_e})*ih-oh/2))'")
    pre, vf = [], []
    if sh.get('_src_fps') and abs(sh['_src_fps'] - fps) > 0.01:
        if sh.get('conform', False):
            pre.append(f'setpts=N/({fps}*TB)')
        else:
            pre.append(f'fps={fps}')
    if float(sh.get('speed', 1.0)) != 1.0:
        pre.append(f'setpts=PTS/{float(sh["speed"])}')
    if (cwi, chi) != (src_w, src_h):
        vf.append(fx)
    vf.append(f'scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int')
    if sh.get('sharpen', V.get('sharpen', False)) and cwi < W:
        vf.append('unsharp=5:5:0.4')
    post = f'setsar=1,fps={fps},format=gbrp10le'
    # pasek z nakladka animatiku (ID ujecia / klatka) przenoszony 1:1 nad kadrowaniem - nie zaslaniamy go
    strip = sh.get('strip', V.get('strip'))
    if strip and sh.get('strip') is not False:
        sx, sy, sw, shh = strip.get('crop', [0, 0, 640, 21])
        k = float(strip.get('scale', 3.0)) * V['scale']
        ow, oh = int(round(sw * k / 2) * 2), int(round(shh * k / 2) * 2)
        px, py = strip.get('pos', [0, 0])
        sfx_ = f'crop={sw}:{shh}:{sx}:{sy},scale={ow}:{oh}:flags=lanczos'
        ss = sh.get('strip_from')                    # np. plansza z Pillow: pasek z animatiku w zadanym oknie
        if ss:
            sp = absp(ss['src'], base)
            inp += ['-ss', f"{ss['f'][0] / fps:.4f}", '-t', f'{n_frames / fps + 0.5:.4f}', '-i', sp]
            fc = (f"[0:v]{','.join(pre + vf) or 'null'}[mm];[1:v]fps={fps},{sfx_}[ss];"
                  f"[mm][ss]overlay={px}:{py}:eof_action=repeat,{post}[out]")
        else:
            fc = (f"[0:v]{','.join(pre) or 'null'},split=2[m][s];[m]{','.join(vf)}[mm];[s]{sfx_}[ss];"
                  f"[mm][ss]overlay={px}:{py},{post}[out]")
        cmd = [FF, '-v', 'error', '-y'] + inp + ['-filter_complex', fc, '-map', '[out]']
    else:
        cmd = [FF, '-v', 'error', '-y'] + inp + ['-vf', ','.join(pre + vf + [post])]
    cmd += ['-frames:v', str(n_frames), '-an', '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'gbrp10le', out]
    run(cmd)
    return out, n_frames


# --------------------------------------------------------------------------
# etap 2: sklejenie z przejsciami
# --------------------------------------------------------------------------
XFADE = {'dissolve': 'fade', 'fade': 'fade', 'fadeblack': 'fadeblack', 'fadewhite': 'fadewhite',
         'wipeleft': 'wipeleft', 'slideleft': 'slideleft', 'smoothleft': 'smoothleft', 'smoothup': 'smoothup'}


def assemble(clips, shots, V, work):
    fps = V['fps']
    starts, L = [], 0
    fc = []
    inputs = []
    for i, ((path, n), sh) in enumerate(zip(clips, shots)):
        inputs += ['-i', path]
        tr = sh.get('transition') or {}
        d = int(tr.get('frames', round(float(tr.get('dur', 0)) * fps))) if tr.get('type', 'cut') != 'cut' else 0
        if i == 0:
            starts.append(0)
            fc.append(f'[0:v]settb=1/{fps},setpts=N/({fps}*TB)[c0]')
            L = n
            continue
        fc.append(f'[{i}:v]settb=1/{fps},setpts=N/({fps}*TB)[s{i}]')
        if d > 0:
            off = (L - d) / fps
            fc.append(f'[c{i - 1}][s{i}]xfade=transition={XFADE.get(tr["type"], "fade")}:duration={d / fps}:'
                      f'offset={off:.6f}[c{i}]')
            starts.append(L - d)
            L = L + n - d
        else:
            fc.append(f'[c{i - 1}][s{i}]concat=n=2:v=1:a=0[cc{i}]')
            fc.append(f'[cc{i}]settb=1/{fps},setpts=N/({fps}*TB)[c{i}]')
            starts.append(L)
            L = L + n
    out = os.path.join(work, 'assembled.mkv')
    last = f'c{len(clips) - 1}'
    cmd = [FF, '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(fc), '-map', f'[{last}]',
                                               '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'gbrp10le', out]
    run(cmd)
    return out, starts, L


# --------------------------------------------------------------------------
# etap 3: grading + typografia + ziarno + enkod + audio
# --------------------------------------------------------------------------
def finalize(assembled, total_f, V, gcfg, overlays, audio_wav, out_path, ecfg, work, draft=False):
    W, H, fps = V['W'], V['H'], V['fps']
    inputs = ['-i', assembled]
    fc = []
    cur = '0:v'
    k = 1
    lut_path = gcfg.get('lut', 'auto')
    if lut_path and lut_path != 'none':
        if lut_path == 'auto':
            lut_path = os.path.join(work, 'nordic_morning.cube')
            lut.write_cube(lut_path, strength=float(gcfg.get('strength', 1.0)))
        fc.append(f"[{cur}]lut3d=file='{lut_path}':interp=tetrahedral[g0]")
        cur = 'g0'
    vig = float(gcfg.get('vignette', 0.09))
    if vig > 0:
        vpath = os.path.join(work, f'vignette_{W}x{H}.png')
        lut.write_vignette(vpath, W, H, vig, float(gcfg.get('vignette_power', 2.5)))
        inputs += ['-loop', '1', '-framerate', str(fps), '-i', vpath]
        fc.append(f'[{k}:v]format=gbrp10le,setsar=1[vm]')
        fc.append(f'[{cur}][vm]blend=all_mode=multiply:shortest=1[g1]')
        cur = 'g1'
        k += 1
    fc.append(f'[{cur}]format=gbrp[g2]')
    cur = 'g2'
    for j, ov in enumerate(overlays):
        inputs += ['-framerate', str(fps), '-start_number', '0', '-i', ov['pattern']]
        fc.append(f'[{k}:v]format=rgba,setpts=PTS+{ov["start_s"]:.6f}/TB[o{j}]')
        fc.append(f'[{cur}][o{j}]overlay=x={ov["x"]}:y={ov["y"]}:eof_action=pass:format=gbrp[t{j}]')
        cur = f't{j}'
        k += 1
    grain = float(gcfg.get('grain', 5))
    tail = ['scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd', 'format=yuv420p']
    if grain > 0 and not draft:
        tail.append(f'noise=c0s={grain}:c0f=t+u')
    fc.append(f'[{cur}]' + ','.join(tail) + '[vout]')
    inputs += ['-i', audio_wav]
    a_idx = k
    crf = str(ecfg.get('crf', 16 if not draft else 23))
    preset = ecfg.get('preset', 'slow' if not draft else 'veryfast')
    common = [FF, '-v', 'error', '-y'] + inputs + [
        '-filter_complex', ';'.join(fc), '-map', '[vout]', '-map', f'{a_idx}:a',
        '-frames:v', str(total_f), '-r', str(fps), '-t', f'{total_f / fps:.4f}',
        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']
    cmd = common + ['-c:v', 'libx264', '-preset', preset, '-crf', crf, '-profile:v', 'high', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart', out_path]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    _, dt = run(cmd)
    if ecfg.get('prores') and not draft:
        mov = os.path.splitext(out_path)[0] + '_master.mov'
        run(common + ['-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', '-c:a', 'pcm_s24le', mov])
        print(f'  ProRes 422 HQ: {mov}')
    return dt


def measure_loudness(path):
    r = subprocess.run([FF, '-hide_banner', '-nostats', '-i', path, '-map', '0:a', '-af',
                        'loudnorm=I=-14:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True)
    txt = r.stderr
    j = json.loads(txt[txt.rindex('{'):txt.rindex('}') + 1])
    r2 = subprocess.run([FF, '-hide_banner', '-nostats', '-i', path, '-map', '0:a', '-af', 'ebur128=peak=true',
                         '-f', 'null', '-'], capture_output=True, text=True)
    s = r2.stderr[r2.stderr.rfind('Summary:'):]
    I = re.search(r'I:\s+(-?[\d.]+) LUFS', s)
    P = re.search(r'Peak:\s+(-?[\d.]+) dBFS', s)
    return {'loudnorm_input_i': float(j['input_i']), 'loudnorm_input_tp': float(j['input_tp']),
            'loudnorm_input_lra': float(j['input_lra']),
            'ebur128_I': float(I.group(1)) if I else None, 'ebur128_true_peak': float(P.group(1)) if P else None}


# --------------------------------------------------------------------------
def build_version(name, V0, cfg, base, args):
    t_start = time.time()
    V = dict(cfg.get('defaults', {}))
    V.update(V0)
    W, H = V.get('size', [1920, 1080])
    scale_draft = 0.5 if args.draft else 1.0
    W, H = int(W * scale_draft) // 2 * 2, int(H * scale_draft) // 2 * 2
    fps = float(V.get('fps', 25))
    style_set = '9x16' if H > W else '16x9'
    scale = (min(W, H) / (1080 if style_set == '16x9' else 1080))
    Vx = dict(W=W, H=H, fps=fps, name_style=style_set, scale=scale, sharpen=V.get('sharpen', False))
    work = absp(V.get('work_dir', os.path.join(cfg.get('work_dir', 'work'), name)), base)
    os.makedirs(work, exist_ok=True)
    shots = [dict(s) for s in V['shots']]
    print(f'\n=== {name}: {W}x{H} @ {fps} fps, {len(shots)} ujec' + (' [DRAFT]' if args.draft else ''))
    # --- obraz
    clips = []
    if not args.audio_only:
        for i, sh in enumerate(shots):
            p, n = normalize_shot(sh, Vx, base, work, i, args.draft)
            clips.append((p, n))
            print(f'  ujecie {sh.get("id", i)}: {n} kl.')
        assembled, starts, total_f = assemble(clips, shots, Vx, work)
    else:
        starts, L = [], 0
        for i, sh in enumerate(shots):
            n = sh.get('dur_f') or (int(round(sh['f'][1] - sh['f'][0])) if 'f' in sh else int(round(float(sh['dur']) * fps)))
            tr = sh.get('transition') or {}
            d = int(tr.get('frames', 0)) if i and tr.get('type', 'cut') != 'cut' else 0
            starts.append(L - d if i else 0)
            L = (L + n - d) if i else n
        total_f = L
    total_f = int(V.get('duration_f', total_f))
    total = total_f / fps
    for sh, st in zip(shots, starts):
        sh['_start_f'] = st
    print(f'  dlugosc: {total_f} kl. = {total:.2f} s; starty ujec [kl.]: {starts}')
    # --- zdarzenia -> cues (per ujecie, w oknie ujecia)
    acfg = dict(V.get('audio', {}))
    cues = []
    ev_path = acfg.pop('events', None)
    if args.events:
        ev_path = os.path.abspath(args.events)
    if ev_path:
        evp = absp(ev_path, base)
        if os.path.isfile(evp):
            efps, evs = timeline.load_events(evp)
            allc = timeline.build_cues(evs, efps, cfg.get('event_map'), float(acfg.get('pan_width', 0.8)))
            for sh in shots:
                if sh.get('events') is False or not ('f' in sh or 'dur' in sh):
                    continue                  # plansza (endcard) dostaje zdarzenia tylko gdy ma okno 'f'
                if 'f' in sh:     # numeracja klatek zrodla == numeracja klatek w events.json
                    s0, s1 = sh['f'][0] / efps, sh['f'][1] / efps
                else:
                    s0 = float(sh.get('in', 0.0))
                    s1 = s0 + float(sh['dur'])
                speed = float(sh.get('speed', 1.0))
                tail = float(sh.get('event_tail_s', 0.0))
                for c in allc:
                    te = c['t_src']
                    te_end = c.get('t_end', te) if c.get('kind') != 'silence' else te
                    # cue nalezy do ujecia, jesli jego zakres [start, koniec] zachodzi na okno ujecia
                    if te_end >= s0 - 0.02 and te < s1 + tail:
                        c2 = dict(c)
                        c2['at'] = sh['_start_f'] / fps + (te - s0) / speed
                        c2['shot'] = sh.get('id')
                        if te < s0 - 0.02:          # dzwiek zaczal sie przed cieciem -> przytnij do ciecia
                            c2['clip_from'] = sh['_start_f'] / fps
                        cues.append(c2)
            print(f'  zdarzenia: {len(evs)} -> {len(cues)} efektow w oknach ujec')
        else:
            print(f'  [uwaga] brak pliku zdarzen {evp}')
    # czasy w sfx/silence mozna podawac w klatkach montazu: 'f:285'
    def T(x):
        if isinstance(x, str) and x.startswith('f:'):
            return float(x[2:]) / fps
        if isinstance(x, str) and '.' in x and x.split('.')[0] in {s.get('id') for s in shots}:
            sid, what = x.split('.', 1)
            what, _, off = what.partition('+')
            sh = next(s for s in shots if s.get('id') == sid)
            return sh['_start_f'] / fps + (float(off) if off else 0.0)
        return float(x)
    acfg['sfx'] = [dict(c, at=T(c.get('at', 0))) for c in acfg.get('sfx', []) or []]
    acfg['silence'] = [[T(a), T(b)] for a, b in acfg.get('silence', []) or []]
    rep = {}
    audio, rep = mixer.mix(acfg, total, cues, base, rep)
    ecfg = V.get('export', {})
    out_path = absp(ecfg.get('output', f'out/{name}.mp4'), base)
    if args.out_suffix:
        out_path = os.path.splitext(out_path)[0] + args.out_suffix + '.mp4'
    if args.draft:
        out_path = os.path.splitext(out_path)[0] + '_draft.mp4'
    wav = os.path.splitext(out_path)[0] + '_mix.wav'
    dsp.write_wav(wav, audio)
    with open(os.path.splitext(out_path)[0] + '_cues.json', 'w', encoding='utf-8') as f:
        json.dump(dict(version=name, duration_s=total, shot_starts_f=starts, mix=rep), f, indent=1, ensure_ascii=False)
    if args.audio_only:
        print(f'  audio: {wav}')
        return dict(version=name, wav=wav, mix=rep)
    # --- typografia
    overlays = []
    for j, t in enumerate(V.get('titles', []) or []):
        d = os.path.join(work, f'title_{j:02d}')
        shutil.rmtree(d, ignore_errors=True)
        overlays.append(typo.render_title(t, style_set, W, H, fps, d, scale))
    for j, t in enumerate(V.get('dims', []) or []):
        d = os.path.join(work, f'dim_{j:02d}')
        shutil.rmtree(d, ignore_errors=True)
        overlays.append(typo.render_dim(t, style_set, W, H, fps, d, scale))
    dt = finalize(assembled, total_f, Vx, V.get('grade', {}), overlays, wav, out_path, ecfg, work, args.draft)
    # --- kontrola glosnosci po enkodzie AAC; jesli TP > -1.0 -> obniz limiter i zmiksuj ponownie
    lm = measure_loudness(out_path)
    if lm['ebur128_true_peak'] is not None and lm['ebur128_true_peak'] > -1.0:
        print(f"  TP po AAC {lm['ebur128_true_peak']} dBTP > -1.0 -> poprawka limitera")
        acfg.setdefault('master', {})['true_peak'] = float(acfg.get('master', {}).get('true_peak', -1.5)) - 0.5
        audio, rep = mixer.mix(acfg, total, cues, base, {}, verbose=False)
        dsp.write_wav(wav, audio)
        finalize(assembled, total_f, Vx, V.get('grade', {}), overlays, wav, out_path, ecfg, work, args.draft)
        lm = measure_loudness(out_path)
    info = dict(version=name, output=out_path, frames=total_f, duration_s=total, encode_s=round(dt, 1),
                loudness=lm, wall_s=round(time.time() - t_start, 1))
    print(f"  -> {out_path}\n     I={lm['ebur128_I']} LUFS (loudnorm {lm['loudnorm_input_i']}), "
          f"TP={lm['ebur128_true_peak']} dBTP, LRA={lm['loudnorm_input_lra']} LU, czas {info['wall_s']} s")
    with open(os.path.splitext(out_path)[0] + '_report.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=1)
    if not args.keep_work:
        for p, _ in clips:
            os.remove(p)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config')
    ap.add_argument('--version', action='append', help='nazwa wersji (domyslnie wszystkie)')
    ap.add_argument('--draft', action='store_true', help='polowa rozdzielczosci, szybki enkod, bez ziarna')
    ap.add_argument('--audio-only', action='store_true')
    ap.add_argument('--keep-work', action='store_true', help='zostaw posrednie pliki FFV1')
    ap.add_argument('--events', help='nadpisz audio.events (np. atrapa test/brief_events_mock.json)')
    ap.add_argument('--out-suffix', default='', help='dopisek do nazw plikow wyjsciowych')
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    base = os.path.dirname(os.path.abspath(args.config))
    vers = cfg['versions']
    names = args.version or list(vers)
    res = [build_version(n, vers[n], cfg, base, args) for n in names]
    print('\n' + json.dumps(res, indent=1, ensure_ascii=False)[:3000])


if __name__ == '__main__':
    main()
