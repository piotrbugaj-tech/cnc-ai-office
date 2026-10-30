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
  python3 fal_music.py --env ~/sekrety/.env             # domyslnie: eleven25 x3 warianty + lyria3 x2 (~1.9 USD)
  python3 fal_music.py --env ~/.env --models eleven25 --variants warm_marimba --seeds 11 12 13
  python3 fal_music.py --env ~/.env --models lyria3 --image ../renders/lookdev/a_hero_34_t3.png
  python3 fal_music.py --env ~/.env --sfx               # biblioteka SFX AI do sfx_ai/
  python3 fal_music.py --env ~/.env --mmaudio ../renders/shot03.mp4 --prompt "drawer sliding open on ball bearing runners"
Parametry czasowe (BPM, reveal, end card) sa brane z research-brief.md (jesli istnieje) albo z flag.
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
BASE_STYLE = ("premium minimal product commercial score, Scandinavian design, birch plywood furniture, "
              "warm, refined, calm confidence, optimistic, high-end product film (Apple, Vitsoe, USM, Tylko), "
              "clean modern mix, wide stereo, tasteful, instrumental only")
NEGATIVE = ["vocals", "singing", "humming", "choir", "spoken words", "rap", "EDM drop", "dubstep",
            "distorted guitars", "aggressive drums", "cheesy corporate ukulele", "whistling", "lo-fi hiss"]

VARIANTS = {
    'warm_marimba': dict(
        label='A - cieple pady + marimba',
        styles=["warm analog synth pads with gentle detune", "soft marimba and kalimba plucks",
                "woodblock and shaker minimal groove", "deep round sub bass"],
        logo="a 4-note marimba sonic logo"),
    'felt_piano': dict(
        label='B - felt piano + elektronika',
        styles=["intimate felt piano motif", "soft airy synth pads", "subtle electronic pulse",
                "light finger snaps and soft kick", "warm sub bass"],
        logo="a short felt piano sonic logo"),
    'organic_pluck': dict(
        label='C - organiczne szarpane',
        styles=["plucked nylon guitar harmonics and kalimba", "pizzicato upright bass",
                "brushed soft percussion and wooden clicks", "warm string pad swells"],
        logo="a gentle plucked 4-note sonic logo"),
}

SFX_PROMPTS = [
    ('drawer_open_ballbearing', 1.6, "close-up foley: a birch plywood drawer sliding open smoothly on full-extension "
     "steel ball-bearing runners, soft rolling whirr, subtle ball rattle, hollow wooden box resonance, quiet studio"),
    ('drawer_softclose', 1.8, "close-up foley: a plywood drawer pushed closed, the soft-close mechanism catches with a tiny "
     "click and gently pulls it shut with a damped pneumatic hiss, ending with a soft muted wooden tap, quiet room"),
    ('door_blumotion_close', 1.6, "close-up foley: small inset plywood cabinet door closing with a soft-close hinge, "
     "damped hydraulic slow-down and a very quiet final tick, premium furniture, quiet room"),
    ('plywood_panel_land', 1.2, "a single 18 mm birch plywood panel dropped flat onto a stack of plywood boards, "
     "dull deep wooden thunk with a short air cushion puff, studio, no echo"),
    ('panel_whoosh', 1.0, "a large flat wooden panel flying quickly past the camera, smooth airy whoosh with slight "
     "flutter, cinematic, clean"),
    ('cordless_screwdriver', 1.2, "short burst of a cordless screwdriver driving a wood screw into plywood, motor whine "
     "with slight load, screw head seating, close-up workshop foley"),
    ('reveal_sub_boom', 3.0, "elegant cinematic sub bass boom hit for a product reveal, deep, warm, clean, short tail"),
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


def eleven25_payload(var, tm, seed, extra_notes=''):
    v = VARIANTS[var]
    D = int(round(tm['duration'] * 1000))
    r = int(round(tm['reveal'] * 1000))
    e = int(round(tm['endcard'] * 1000))
    hit = min(4600, max(3000, (e - r) // 3))
    chunks_ms = [r, hit, e - r - hit, D - e]
    if min(chunks_ms) < 3000:
        raise ValueError(f'kazdy odcinek >= 3 s, a wyszlo {chunks_ms} - zmien reveal/endcard')
    common = [BASE_STYLE, f"{tm['bpm']:.0f} BPM", "F major"] + v['styles']
    if extra_notes:
        common.append(extra_notes[:180])
    chunks = [
        dict(text='[Intro]', duration_ms=chunks_ms[0],
             positive_styles=common + ["sparse, airy intro", "slowly building anticipation",
                                       "soft ticking percussion", "filter slowly opening",
                                       "short riser and a brief breath of silence right before the next section"],
             negative_styles=NEGATIVE + ["full drums", "loud bass"]),
        dict(text='[Reveal]', duration_ms=chunks_ms[1], context_adherence='high',
             positive_styles=["product reveal moment on the very first downbeat", "elegant deep sub-bass boom hit",
                              "full warm chord", "beat enters", "uplifting, confident"],
             negative_styles=NEGATIVE),
        dict(text='[Groove]', duration_ms=chunks_ms[2], context_adherence='high',
             positive_styles=["light steady groove", "same instruments and tempo",
                              "melodic arpeggios", "gentle variation, never busy",
                              "short drum break right before the final section"],
             negative_styles=NEGATIVE),
        dict(text='[Outro]', duration_ms=chunks_ms[3], context_adherence='high',
             positive_styles=["final resolving cadence on the downbeat", v['logo'], "end card",
                              "warm sustained final chord ringing out", "clean natural ending"],
             negative_styles=NEGATIVE + ["fade in of new instruments", "abrupt cut"]),
    ]
    return {'composition_plan': {'chunks': chunks}, 'seed': int(seed), 'output_format': 'mp3_48000_320'}


def eleven_v1_payload(var, tm, seed, extra_notes=''):
    p = eleven25_payload(var, tm, seed, extra_notes)
    secs = []
    for c, name in zip(p['composition_plan']['chunks'], ['Intro', 'Reveal', 'Groove', 'End card']):
        secs.append(dict(section_name=name, positive_local_styles=c['positive_styles'][-5:],
                         negative_local_styles=c['negative_styles'][:6], duration_ms=c['duration_ms'], lines=[]))
    v = VARIANTS[var]
    return {'composition_plan': {'positive_global_styles': [BASE_STYLE, f"{tm['bpm']:.0f} BPM"] + v['styles'],
                                 'negative_global_styles': NEGATIVE, 'sections': secs},
            'respect_sections_durations': True, 'output_format': 'mp3_44100_128'}


def prose_prompt(var, tm, extra_notes=''):
    v = VARIANTS[var]
    s = (f"30-second instrumental music for a premium furniture commercial. {BASE_STYLE}. "
         f"{', '.join(v['styles'])}. Tempo {tm['bpm']:.0f} BPM, F major. Structure: sparse airy intro building "
         f"anticipation with soft ticking and a short riser; at {tm['reveal']:.1f} seconds a clear reveal accent - "
         f"elegant deep sub-bass hit, full warm chord and the light groove begins; steady gentle groove; at "
         f"{tm['endcard']:.1f} seconds a final resolving chord with {v['logo']}, ringing out to a clean ending at "
         f"{tm['duration']:.0f} seconds. No vocals.")
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
    ap.add_argument('--bpm', type=float)
    ap.add_argument('--reveal', type=float, help='czas akcentu reveal [s]')
    ap.add_argument('--endcard', type=float, help='poczatek end card [s]')
    ap.add_argument('--duration', type=float, default=30.0)
    ap.add_argument('--notes', default=None, help='dodatkowy opis stylu (nadpisuje notatki z briefu)')
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
    if br:
        print('research-brief:', {k: v for k, v in br.items() if k != 'music_notes'})
    bpm = a.bpm or br.get('bpm') or 104.0
    beat = 60.0 / bpm
    reveal = a.reveal or br.get('reveal') or 16 * beat            # takt 5
    endcard = a.endcard or br.get('endcard') or 44 * beat         # takt 12
    tm = timing(bpm, reveal, endcard, a.duration)
    notes = a.notes if a.notes is not None else br.get('music_notes', '')
    print(f'timing: BPM {bpm:.1f}, reveal {reveal:.2f} s, end card {endcard:.2f} s, dlugosc {a.duration:.0f} s')

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
    done = execute(jobs, out_dir, use_client)
    print(f'\nGotowe: {len(done)}/{len(jobs)} plikow w {out_dir}')
    with open(os.path.join(out_dir, 'fal_last_run.json'), 'w', encoding='utf-8') as f:
        json.dump({'timing': tm, 'results': done}, f, indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()
