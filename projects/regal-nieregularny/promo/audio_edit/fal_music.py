#!/usr/bin/env python3
"""fal_music.py - muzyka (i opcjonalnie SFX) z modeli AI na fal.ai dla promo regalu.

Dziala na macOS / Linux, python3 >= 3.10. Jedyna zaleznosc: (opcjonalnie) `pip3 install fal-client`.
Bez fal-client skrypt uzywa HTTP queue API (urllib, biblioteka standardowa).

KLUCZ: FAL_KEY ze zmiennej srodowiskowej albo z pliku .env (--env). Klucz NIGDY nie jest
wypisywany, logowany ani zapisywany (metadane zawieraja tylko endpoint, argumenty, request_id).

Modele (stan katalogu fal: pazdziernik 2026, typy z @fal-ai/client):
  eleven25   elevenlabs/music/v2.5        ElevenLabs Music v2.5 - composition_plan z odcinkami (chunks)
                                          o zadanych dlugosciach -> reveal i end card trafiaja w czas.
                                          ~0.60 USD / rozpoczeta minute audio (30 s = 0.60 USD).   [DOMYSLNY]
  lyria3     fal-ai/lyria3                Google Lyria 3 Clip - zawsze 30 s, prompt + opcjonalny obraz
                                          (np. klatka renderu) jako inspiracja nastroju. ~0.04 USD/klip.
  eleven     fal-ai/elevenlabs/music      ElevenLabs Music v1 - composition_plan z sekcjami, ~0.80 USD/min.
  lyria2     fal-ai/lyria2                Lyria 2 - 30 s, WAV 48 kHz, negative_prompt, seed. ~0.10 USD/30 s.
  stable25   fal-ai/stable-audio-25/text-to-audio  Stable Audio 2.5 - seconds_total, seed. ~0.20 USD.
  minimax26  fal-ai/minimax-music/v2.6    MiniMax Music 2.6 z is_instrumental=true. cena: sprawdz w panelu.
  sfx        fal-ai/elevenlabs/sound-effects/v2    ElevenLabs SFX v2 (warstwa pod Foley), 0.5-22 s.
  mmaudio    fal-ai/mmaudio-v2            video-to-audio (Foley z renderu ujecia), --video.
Ceny sa szacunkowe (strony fal / cenniki dostawcow); rzeczywisty koszt sprawdz w panelu fal.ai -> Usage.

Przyklady:
  pip3 install fal-client
  export FAL_KEY=...            # albo plik .env z linia FAL_KEY=...
  python3 fal_music.py --dry-run                        # pokaz payloady i koszt, bez klucza
  python3 fal_music.py --env ~/sekrety/.env             # 30 s: eleven25 x3 warianty + lyria3 x2 (~1.9 USD)
  python3 fal_music.py --env ~/sekrety/.env --length 15 --models eleven25    # cutdown 15 s (~1.8 USD)
  python3 fal_music.py --env ~/.env --models eleven25 --variants nordic_marimba --seeds 11 12 13
  python3 fal_music.py --env ~/.env --models lyria3 --image ../renders/lookdev/a_hero_34_t3.png
  python3 fal_music.py --env ~/.env --sfx               # biblioteka SFX AI do sfx_ai/
  python3 fal_music.py --env ~/.env --mmaudio ../renders/shot03.mp4 --prompt "drawer sliding open on ball bearing runners"
Plan muzyki wg research-brief.md (6.1): 100 BPM, F-dur, takt 2,4 s, ciecia na uderzeniach; 30 s:
  [Hook 0-7.2: nuty polek, f60=2.4 s sub + pad] [Groove 7.2-16.2] [Breakdown 16.2-19.2, cisza 18.96]
  [Drop 19.2-26.4: drop, f585 akord, rozwiazanie 24.0] [Outro 26.4-30: sygnal RYTM]
Muzyka AI to "lozko": nuty zwiazane z obrazem (nuty polek, ladowania, sygnal) dokladamy z music_synth
(stem `motif`) albo z events.json - edit.py miesza je na wierzchu.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BRIEF = os.path.normpath(os.path.join(HERE, '..', 'research-brief.md'))

ENDPOINTS = {
    'eleven25': 'elevenlabs/music/v2.5',
    'eleven': 'fal-ai/elevenlabs/music',
    'lyria3': 'fal-ai/lyria3',
    'lyria3pro': 'fal-ai/lyria3/pro',
    'lyria2': 'fal-ai/lyria2',
    'stable25': 'fal-ai/stable-audio-25/text-to-audio',
    'minimax26': 'fal-ai/minimax-music/v2.6',
    'sfx': 'fal-ai/elevenlabs/sound-effects/v2',
    'mmaudio': 'fal-ai/mmaudio-v2',
}
# szacunkowy koszt jednego wywolania (USD) dla 30 s
EST_COST = {
    'eleven25': 0.60, 'eleven': 0.80, 'lyria3': 0.04, 'lyria3pro': 0.08, 'lyria2': 0.10,
    'stable25': 0.20, 'minimax26': 0.05, 'sfx': 0.03, 'mmaudio': 0.02,
}

# --------------------------------------------------------------------------
# styl i warianty
# --------------------------------------------------------------------------
BASE_STYLE = ("premium minimal product film score, Nordic, warm and woody, calm confidence, refined, "
              "high-end furniture commercial (Tylko, Vitsoe, USM, HAY), clean modern mix, wide stereo, "
              "100 BPM, F major, 4/4, half-time pulse, instrumental only")
NEGATIVE = ["vocals", "singing", "humming", "choir", "spoken words", "rap", "EDM build-up", "dubstep",
            "distorted guitars", "aggressive drums", "trap hi-hats", "cheesy corporate ukulele", "whistling",
            "lo-fi vinyl hiss", "busy lead melody"]

# warianty brzmienia (research-brief 6.1: marimba, pady, sub-kick, wood clap, shaker, bas w dropie)
VARIANTS = {
    'nordic_marimba': dict(
        label='A - brief: drewniana marimba + cieple pady (najblizej syntezy)',
        styles=["soft wooden marimba", "warm analog pads with gentle chorus", "deep round sub kick",
                "wooden clap on beat 3", "very quiet shaker 16ths", "warm sine bass in the drop"],
        logo="a 5-note marimba sonic logo F4 A4 C5 D5 F5"),
    'felt_piano': dict(
        label='B - felt piano + pady + miekki puls',
        styles=["intimate felt piano", "airy warm pads", "soft sub kick half-time", "wooden clicks",
                "subtle tape saturation"],
        logo="a short 5-note felt piano sonic logo rising F A C D F"),
    'ambient_pulse': dict(
        label='C - ambient, kalimba i pulsujacy arpeggiator',
        styles=["kalimba and plucked wooden textures", "slowly evolving ambient pad", "soft analog arpeggio pulse",
                "organic wooden percussion", "deep warm sub bass"],
        logo="a gentle 5-note kalimba sonic logo"),
}

# plan odcinkow (s) wg briefu: ciecia na uderzeniach, odcinki >= 3 s (wymog ElevenLabs)
PLAN = {
    30: [
        ('[Hook]', 0.0, 7.2, ["0-2.4 s: almost silent, sparse dry marimba notes only, airy",
                              "at 2.4 s a soft sub hit and the warm pad opens (Fmaj9 then Dm9)",
                              "minimal, leave space for sound effects"]),
        ('[Groove]', 7.2, 16.2, ["half-time groove: sub kick on beat 1, wooden clap on beat 3, quiet shaker",
                                 "chords Bbmaj7, Csus4 to C, Fmaj9, Dm9, one chord per bar",
                                 "short repeating marimba rhythm figure, never busy"]),
        ('[Breakdown]', 16.2, 19.2, ["groove ends at 16.8 s, then drums stop, pad Bbmaj7#11 and a rising riser",
                                     "riser cuts hard to complete silence for the last quarter second"]),
        ('[Drop]', 19.2, 26.4, ["the drop lands exactly on the downbeat: sub kick, warm bass, full pad Fmaj9 then Dm9",
                                "rising marimba melody, at 23.4 s a bright chord",
                                "at 24 s drums stop, calm resolution on Bbmaj7"]),
        ('[Outro]', 26.4, 30.0, ["final section starts on the downbeat", "{logo}", "deep F sub note and full Fmaj9 pad",
                                 "rings out and fades naturally to silence by 29.8 s"]),
    ],
    15: [
        ('[Intro]', 0.0, 4.2, ["sparse dry marimba notes, at 2.4 s soft sub hit and half-time groove starts"]),
        ('[Breakdown]', 4.2, 7.2, ["at 6.0 s drums stop, riser", "hard cut to silence at 6.96 s"]),
        ('[Drop]', 7.2, 12.0, ["drop on the downbeat: sub kick, bass, full pad, rising marimba melody"]),
        ('[Outro]', 12.0, 15.0, ["{logo}", "rings out, clean ending by 14.8 s"]),
    ],
}

SFX_PROMPTS = [
    ('roll_ballbearing_S09', 0.9, "extreme close-up foley: a birch plywood drawer pulled out smoothly on full-extension steel "
     "ball-bearing runners, fine rolling whirr of tiny steel balls, hollow wooden box resonance, quiet room, no music"),
    ('stop_full_extension', 1.0, "a plywood drawer reaching full extension and hitting the runner end stop: a soft deep "
     "wooden 'tunk' with a tiny metal click, close-up foley, quiet room"),
    ('softclose_drawer', 1.8, "close-up foley: a plywood drawer pushed closed, the soft-close mechanism catches with a small "
     "plastic click and slowly pulls it shut with a quiet damped hiss, ends with a soft muted felt 'thup'"),
    ('blumotion_door', 1.6, "close-up foley: a small inset plywood cabinet door closing on a soft-close hinge, quiet air, "
     "tiny metal catch, hydraulic slow-down and a gentle wooden 'tok' with a faint hinge click"),
    ('panel_landing', 1.0, "an 18 mm birch plywood shelf landing precisely into place, dull deep wooden 'tok', "
     "tight, close-up, studio, no echo"),
    ('panel_fly_whoosh', 0.7, "a flat plywood panel flying quickly past camera, short smooth airy whoosh, clean"),
    ('pop_parts', 0.6, "dozens of small wooden parts popping out of CNC-cut plywood sheets at once, tiny dry wooden "
     "clicks spreading outward, satisfying, close-up"),
    ('reveal_sub', 3.0, "elegant cinematic deep sub bass hit for a product reveal, warm, clean, short dark tail"),
]


# --------------------------------------------------------------------------
# klucz (nigdy nie logowany)
# --------------------------------------------------------------------------
_SECRET = {'v': None}


def load_key(env_path=None):
    key = os.environ.get('FAL_KEY')
    if env_path:
        p = os.path.expanduser(env_path)
        if not os.path.isfile(p):
            sys.exit(f'[blad] brak pliku .env: {p}')
        with open(p, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip().removeprefix('export ').strip()
                if k == 'FAL_KEY':
                    key = v.strip().strip('"').strip("'")
    if not key:
        sys.exit('[blad] brak FAL_KEY (ustaw zmienna srodowiskowa albo podaj --env sciezka/.env)')
    os.environ['FAL_KEY'] = key     # tylko dla tego procesu (fal-client czyta ja sam)
    _SECRET['v'] = key
    print('FAL_KEY: wczytany (wartosc ukryta)')
    return key


def scrub(text):
    s = str(text)
    k = _SECRET['v']
    if k:
        s = s.replace(k, '***')
        for part in k.split(':'):
            if len(part) >= 8:
                s = s.replace(part, '***')
    return s


# --------------------------------------------------------------------------
# brief -> parametry
# --------------------------------------------------------------------------
def _tc_to_s(tc):
    tc = tc.strip().replace(',', '.')
    if ':' in tc:
        parts = [float(x) for x in tc.split(':')]
        s = 0.0
        for p in parts:
            s = s * 60 + p
        return s
    return float(tc.rstrip('s'))


def parse_brief(path):
    """Wyciaga z research-brief.md: BPM, czas reveal i end card, opis stylu muzyki (heurystyki)."""
    out = {}
    if not path or not os.path.isfile(path):
        return out
    txt = open(path, encoding='utf-8').read()
    m = re.search(r'(\d{2,3}(?:[.,]\d)?)\s*(?:-|–)?\s*(?:\d{2,3}\s*)?BPM', txt, re.I)
    if m:
        out['bpm'] = float(m.group(1).replace(',', '.'))
    m = re.search(r'BPM[^\n]{0,20}?(\d{2,3})', txt, re.I)
    if 'bpm' not in out and m:
        out['bpm'] = float(m.group(1))
    tc = r'(\d{1,2}:\d{2}(?:[.,:]\d{1,2})?|\d{1,2}(?:[.,]\d+)?\s*s)'
    for key, pat in [('reveal', r'reveal'), ('endcard', r'end[\s-]?card|plansza ko[nń]cowa|packshot')]:
        m = re.search(tc + r'[^\n]{0,60}?(?:' + pat + r')', txt, re.I) or \
            re.search(r'(?:' + pat + r')[^\n]{0,40}?' + tc, txt, re.I)
        if m:
            try:
                out[key] = _tc_to_s(m.group(1))
            except ValueError:
                pass
    # sekcja o muzyce (pierwsze ~600 znakow po naglowku zawierajacym "muzyk"/"music")
    m = re.search(r'^#+[^\n]*(muzyk|music)[^\n]*\n(.{0,900}?)(?=^#+ |\Z)', txt, re.I | re.M | re.S)
    if m:
        body = re.sub(r'\s+', ' ', re.sub(r'[#*`>|]', ' ', m.group(2))).strip()
        out['music_notes'] = body[:600]
    out['_source'] = path
    return out


# --------------------------------------------------------------------------
# payloady
# --------------------------------------------------------------------------
def timing(bpm, reveal, endcard, duration):
    return dict(bpm=bpm, reveal=reveal, endcard=endcard, duration=duration)


def _plan(tm):
    L = 15 if tm['duration'] <= 16 else 30
    return L, PLAN[L]


def eleven25_payload(var, tm, seed, extra_notes=''):
    v = VARIANTS[var]
    L, plan = _plan(tm)
    common = [BASE_STYLE] + v['styles']
    if extra_notes:
        common.append(extra_notes[:180])
    chunks = []
    for i, (tag, t0, t1, styles) in enumerate(plan):
        st = [x.replace('{logo}', v['logo']) for x in styles]
        c = dict(text=tag, duration_ms=int(round((t1 - t0) * 1000)),
                 positive_styles=(common + st) if i == 0 else st + v['styles'][:2],
                 negative_styles=list(NEGATIVE))
        if i > 0:
            c['context_adherence'] = 'high'
        chunks.append(c)
    tot = sum(c['duration_ms'] for c in chunks)
    chunks[-1]['duration_ms'] += int(round(tm['duration'] * 1000)) - tot
    if min(c['duration_ms'] for c in chunks) < 3000:
        raise ValueError('kazdy odcinek musi miec >= 3 s')
    return {'composition_plan': {'chunks': chunks}, 'seed': int(seed), 'output_format': 'mp3_48000_320'}


def eleven_v1_payload(var, tm, seed, extra_notes=''):
    v = VARIANTS[var]
    L, plan = _plan(tm)
    secs = [dict(section_name=tag.strip('[]'), positive_local_styles=[x.replace('{logo}', v['logo']) for x in st],
                 negative_local_styles=NEGATIVE[:6], duration_ms=int(round((t1 - t0) * 1000)), lines=[])
            for tag, t0, t1, st in plan]
    return {'composition_plan': {'positive_global_styles': [BASE_STYLE] + v['styles'],
                                 'negative_global_styles': NEGATIVE, 'sections': secs},
            'respect_sections_durations': True, 'output_format': 'mp3_44100_192'}


def prose_prompt(var, tm, extra_notes=''):
    v = VARIANTS[var]
    L, plan = _plan(tm)
    parts = []
    for tag, t0, t1, st in plan:
        parts.append(f"{t0:.1f}-{t1:.1f} s: " + '; '.join(x.replace('{logo}', v['logo']) for x in st))
    s = (f"{L}-second instrumental music for a premium plywood furniture commercial. {BASE_STYLE}. "
         f"Instruments: {', '.join(v['styles'])}. Every change lands on a beat (one bar = 2.4 s). Timeline: "
         + ' | '.join(parts) + '. No vocals.')
    if extra_notes:
        s += ' Notes: ' + extra_notes[:300]
    return s


def build_jobs(models, variants, seeds, tm, notes, image=None):
    jobs = []
    for mk in models:
        for i, var in enumerate(variants):
            seed = seeds[i % len(seeds)] if seeds else 1000 + i
            if mk == 'eleven25':
                args = eleven25_payload(var, tm, seed, notes)
            elif mk == 'eleven':
                args = eleven_v1_payload(var, tm, seed, notes)
            elif mk in ('lyria3', 'lyria3pro'):
                args = {'prompt': prose_prompt(var, tm, notes)}
                if image:
                    args['image_url'] = ('@file', image)
                seed = None
            elif mk == 'lyria2':
                args = {'prompt': prose_prompt(var, tm, notes),
                        'negative_prompt': ', '.join(NEGATIVE + ['low quality']), 'seed': int(seed)}
            elif mk == 'stable25':
                args = {'prompt': prose_prompt(var, tm, notes), 'seconds_total': int(round(tm['duration'])),
                        'num_inference_steps': 8, 'guidance_scale': 1, 'seed': int(seed)}
            elif mk == 'minimax26':
                args = {'prompt': prose_prompt(var, tm, notes)[:1900], 'is_instrumental': True}
                seed = None
            else:
                raise ValueError(mk)
            jobs.append(dict(model=mk, endpoint=ENDPOINTS[mk], variant=var, seed=seed, args=args,
                             est_cost=EST_COST[mk]))
    return jobs


# --------------------------------------------------------------------------
# wykonanie: fal-client albo HTTP queue API
# --------------------------------------------------------------------------
def _resolve_files(args, use_client):
    """Zamienia ('@file', sciezka) na URL (upload fal-client) lub data URI (HTTP)."""
    out = {}
    for k, v in args.items():
        if isinstance(v, tuple) and v and v[0] == '@file':
            path = os.path.expanduser(v[1])
            if use_client:
                import fal_client
                out[k] = fal_client.upload_file(path)
            else:
                mt = mimetypes.guess_type(path)[0] or 'application/octet-stream'
                with open(path, 'rb') as f:
                    out[k] = f'data:{mt};base64,' + base64.b64encode(f.read()).decode()
        else:
            out[k] = v
    return out


def _http(method, url, body=None, timeout=60):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None)
    req.add_header('Authorization', 'Key ' + _SECRET['v'])
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(scrub(f'HTTP {e.code} {url}: {e.read().decode(errors="replace")[:800]}')) from None


def run_job(endpoint, args, use_client, timeout_s=900):
    t0 = time.time()
    args = _resolve_files(args, use_client)
    if use_client:
        import fal_client
        h = fal_client.submit(endpoint, arguments=args)
        rid = getattr(h, 'request_id', None)
        print(f'    request_id={rid}')
        last = None
        for ev in h.iter_events(with_logs=True, interval=1.0):
            name = type(ev).__name__
            if name != last:
                print(f'    status: {name}')
                last = name
            for lg in (getattr(ev, 'logs', None) or [])[-2:]:
                msg = lg.get('message') if isinstance(lg, dict) else str(lg)
                if msg:
                    print('     log:', scrub(msg)[:160])
            if time.time() - t0 > timeout_s:
                raise TimeoutError('przekroczono czas oczekiwania')
        res = h.get()
    else:
        sub = _http('POST', f'https://queue.fal.run/{endpoint}', args)
        rid = sub.get('request_id')
        print(f'    request_id={rid}')
        status_url, response_url = sub['status_url'], sub['response_url']
        last = None
        while True:
            st = _http('GET', status_url + '?logs=1')
            s = st.get('status')
            if s != last:
                print(f'    status: {s}')
                last = s
            if s == 'COMPLETED':
                break
            if time.time() - t0 > timeout_s:
                raise TimeoutError('przekroczono czas oczekiwania')
            time.sleep(2.0)
        res = _http('GET', response_url)
    return res, rid, time.time() - t0


def _find_audio_url(res):
    if isinstance(res, dict):
        for k in ('audio', 'audio_file', 'audio_url', 'video', 'file', 'output'):
            v = res.get(k)
            if isinstance(v, dict) and v.get('url'):
                return v['url'], v
            if isinstance(v, str) and v.startswith(('http', 'data:')):
                return v, {}
            if isinstance(v, list) and v and isinstance(v[0], dict) and v[0].get('url'):
                return v[0]['url'], v[0]
    raise RuntimeError('nie znaleziono URL audio w odpowiedzi: ' + json.dumps(res)[:400])


def download(url, path):
    if url.startswith('data:'):
        head, b64 = url.split(',', 1)
        with open(path, 'wb') as f:
            f.write(base64.b64decode(b64))
        return path
    with urllib.request.urlopen(url, timeout=300) as r, open(path, 'wb') as f:
        shutil.copyfileobj(r, f)
    return path


def to_wav48(src):
    """Konwersja do WAV 48 kHz/24 bit (ffmpeg lub soundfile), zwraca sciezke albo None."""
    dst = os.path.splitext(src)[0] + '_48k.wav'
    ff = shutil.which('ffmpeg')
    try:
        if ff:
            subprocess.run([ff, '-v', 'error', '-y', '-i', src, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', dst],
                           check=True)
            return dst
        import soundfile as sf
        x, sr = sf.read(src, always_2d=True)
        if sr != 48000:
            from scipy.signal import resample_poly
            from math import gcd
            g = gcd(sr, 48000)
            x = resample_poly(x, 48000 // g, sr // g, axis=0)
        sf.write(dst, x, 48000, subtype='PCM_24')
        return dst
    except Exception as e:  # noqa: BLE001
        print('    (konwersja do WAV pominieta:', scrub(e), ')')
        return None


def measure(path):
    try:
        import numpy as np
        import pyloudnorm as pyln
        import soundfile as sf
        x, sr = sf.read(path, always_2d=True)
        return {'duration_s': round(len(x) / sr, 3), 'lufs': round(pyln.Meter(sr).integrated_loudness(x), 2),
                'peak_dbfs': round(20 * float(np.log10(np.max(np.abs(x)) + 1e-12)), 2)}
    except Exception:  # noqa: BLE001
        return {}


def _safe_args_for_meta(args):
    out = {}
    for k, v in args.items():
        if isinstance(v, tuple) and v and v[0] == '@file':
            out[k] = {'local_file': v[1]}
        elif isinstance(v, str) and v.startswith('data:'):
            out[k] = '<data-uri>'
        else:
            out[k] = v
    return out


def execute(jobs, out_dir, use_client, tag=''):
    os.makedirs(out_dir, exist_ok=True)
    done = []
    for j in jobs:
        stamp = _dt.datetime.now().strftime('%Y%m%d-%H%M%S')
        name = f"fal_{j['model']}_{j['variant']}" + (f"_s{j['seed']}" if j.get('seed') is not None else '') + \
               (f'_{tag}' if tag else '') + f'_{stamp}'
        print(f"\n>> {j['endpoint']}  [{j['variant']}]  seed={j.get('seed')}  ~{j['est_cost']:.2f} USD")
        try:
            res, rid, dt = run_job(j['endpoint'], j['args'], use_client)
            url, info = _find_audio_url(res)
            ext = os.path.splitext(url.split('?')[0])[1] if not url.startswith('data:') else '.mp3'
            if ext.lower() not in ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.opus', '.mp4'):
                ext = '.mp3' if 'mp3' in (info.get('content_type') or 'mp3') else '.wav'
            path = os.path.join(out_dir, name + ext)
            download(url, path)
            wav = to_wav48(path) if ext != '.mp4' else None
            sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
            meta = {
                'model_key': j['model'], 'endpoint': j['endpoint'], 'variant': j['variant'],
                'variant_label': VARIANTS.get(j['variant'], {}).get('label', j['variant']),
                'seed': j.get('seed'), 'arguments': _safe_args_for_meta(j['args']),
                'request_id': rid, 'elapsed_s': round(dt, 1), 'file': os.path.basename(path),
                'wav_48k': os.path.basename(wav) if wav else None, 'sha256': sha,
                'est_cost_usd': j['est_cost'], 'cost_note': 'szacunek; faktyczny koszt w panelu fal.ai (Usage)',
                'response_extra': {k: v for k, v in res.items() if k not in ('audio', 'audio_file', 'video')} if isinstance(res, dict) else None,
                'measure': measure(wav or path), 'created': stamp,
            }
            with open(os.path.join(out_dir, name + '.json'), 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=1, ensure_ascii=False)
            print(f'    OK -> {path}  ({meta["measure"]})')
            done.append(meta)
        except Exception as e:  # noqa: BLE001
            print('    BLAD:', scrub(e)[:1200])
    return done


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--env', help='plik .env z FAL_KEY=... (klucz nie jest wypisywany)')
    ap.add_argument('--models', nargs='+', default=['eleven25', 'lyria3'],
                    choices=['eleven25', 'eleven', 'lyria3', 'lyria3pro', 'lyria2', 'stable25', 'minimax26'])
    ap.add_argument('--variants', nargs='+', default=None, choices=list(VARIANTS),
                    help='domyslnie: eleven25 -> wszystkie 3, inne modele -> 2 pierwsze')
    ap.add_argument('--seeds', nargs='+', type=int, default=[11, 23, 37])
    ap.add_argument('--brief', default=DEFAULT_BRIEF, help='research-brief.md (BPM, reveal, end card, notatki)')
    ap.add_argument('--length', type=int, choices=[30, 15], default=30,
                    help='30 = wersja glowna 16:9, 15 = cutdown 9:16 (plan odcinkow z briefu)')
    ap.add_argument('--notes', default='', help='dodatkowy opis stylu dopisywany do promptu')
    ap.add_argument('--image', help='obraz (klatka renderu) jako inspiracja dla Lyria 3')
    ap.add_argument('--out', default=os.path.join(HERE, 'music'))
    ap.add_argument('--budget', type=float, default=3.0, help='max szacowany koszt [USD] bez --yes')
    ap.add_argument('--yes', action='store_true', help='pomin limit budzetu')
    ap.add_argument('--dry-run', action='store_true', help='pokaz payloady i koszt, nic nie wysylaj')
    ap.add_argument('--http', action='store_true', help='wymus HTTP queue API zamiast fal-client')
    ap.add_argument('--sfx', action='store_true', help='generuj biblioteke SFX (ElevenLabs SFX v2) do sfx_ai/')
    ap.add_argument('--mmaudio', metavar='VIDEO', help='video-to-audio (MMAudio v2) dla pliku wideo')
    ap.add_argument('--prompt', help='prompt dla --mmaudio')
    ap.add_argument('--list-models', action='store_true')
    a = ap.parse_args()

    if a.list_models:
        for k, e in ENDPOINTS.items():
            print(f'{k:10s} {e:42s} ~{EST_COST[k]:.2f} USD / wywolanie (30 s)')
        return

    br = parse_brief(a.brief)
    bpm = br.get('bpm') or 100.0
    if br:
        print(f"research-brief: {br['_source']} (BPM z briefu: {br.get('bpm')})")
    if abs(bpm - 100.0) > 0.5:
        print(f'[uwaga] brief podaje {bpm} BPM, plan odcinkow jest liczony dla 100 BPM (takt 2,4 s)')
    tm = timing(100.0, 2.4, 26.4 if a.length == 30 else 12.0, float(a.length))
    notes = a.notes
    print(f'plan {a.length} s: ' + ' | '.join(f'{t} {t0:.1f}-{t1:.1f}' for t, t0, t1, _ in PLAN[a.length]))

    jobs = []
    if a.sfx:
        for name, dur, text in SFX_PROMPTS:
            jobs.append(dict(model='sfx', endpoint=ENDPOINTS['sfx'], variant=name, seed=None,
                             args={'text': text, 'duration_seconds': dur, 'prompt_influence': 0.55,
                                   'output_format': 'mp3_44100_192'}, est_cost=EST_COST['sfx']))
        out_dir = os.path.join(HERE, 'sfx_ai')
    elif a.mmaudio:
        jobs.append(dict(model='mmaudio', endpoint=ENDPOINTS['mmaudio'], variant='v2a', seed=42,
                         args={'video_url': ('@file', a.mmaudio),
                               'prompt': a.prompt or 'quiet studio foley of plywood furniture, drawers on ball-bearing '
                                                      'runners, soft-close hinges, no music',
                               'negative_prompt': 'music, speech, voices, noise, hum', 'num_steps': 25,
                               'cfg_strength': 4.5, 'seed': 42}, est_cost=EST_COST['mmaudio']))
        out_dir = os.path.join(HERE, 'sfx_ai')
    else:
        for mk in a.models:
            if a.length == 15 and mk in ('lyria3', 'lyria2'):
                print(f'[pominieto] {mk}: model zawsze daje 30 s - dla 15 s uzyj eleven25 / stable25 albo '
                      f'zmontuj 15 s z wersji 30 s (edit.py: music.edit)')
                continue
            vs = a.variants or (list(VARIANTS) if mk == 'eleven25' else list(VARIANTS)[:2])
            jobs += build_jobs([mk], vs, a.seeds, tm, notes, a.image)
        out_dir = a.out

    total = sum(j['est_cost'] for j in jobs)
    print(f'\nZadania: {len(jobs)}, szacowany koszt ~{total:.2f} USD (limit {a.budget:.2f})')
    for j in jobs:
        print(f"  - {j['endpoint']:40s} {j['variant']:22s} seed={j.get('seed')}")
    if a.dry_run:
        for j in jobs:
            print(f"\n### {j['endpoint']} [{j['variant']}]\n" + json.dumps(_safe_args_for_meta(j['args']), indent=1,
                                                                        ensure_ascii=False))
        return
    if total > a.budget and not a.yes:
        sys.exit(f'[stop] szacowany koszt {total:.2f} USD > --budget {a.budget:.2f}. Dodaj --yes albo zmniejsz liczbe zadan.')
    load_key(a.env)
    use_client = False
    if not a.http:
        try:
            import fal_client  # noqa: F401
            use_client = True
        except ImportError:
            print('fal-client nie jest zainstalowany -> HTTP queue API (pip3 install fal-client zalecane)')
    done = execute(jobs, out_dir, use_client, tag=f'{a.length}s')
    print(f'\nGotowe: {len(done)}/{len(jobs)} plikow w {out_dir}')
    with open(os.path.join(out_dir, 'fal_last_run.json'), 'w', encoding='utf-8') as f:
        json.dump({'timing': tm, 'results': done}, f, indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
