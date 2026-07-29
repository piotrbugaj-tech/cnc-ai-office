"""
Skleja shelf_model.py + blender_emit.py w jeden plik do wklejenia w Blendera.

Powod: w zakladce Scripting import lokalnego modulu wymaga grzebania w sys.path,
a chcemy zeby uzytkownik po prostu wkleil jeden plik i wcisnal Run.

Uruchomienie:  python3 make_blender_script.py
Wynik:         build_shelf_blender.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build_shelf_blender.py")

HEADER = '''"""
Regal R150 - generator bryly w Blenderze.

PLIK WYGENEROWANY AUTOMATYCZNIE - nie edytuj recznie.
Zrodlo: shelf_model.py + blender_emit.py, sklejone przez make_blender_script.py

Jak uzyc na Mac mini:
  1. Blender -> zakladka Scripting -> New
  2. Wklej cala zawartosc tego pliku
  3. Run Script (Alt+P)

Bryla powstaje w kolekcji "Regal_R150". Skrypt jest idempotentny -
kolejne uruchomienie podmienia poprzednia wersje zamiast dokladac druga.

Scena przechodzi na jednostki milimetrowe, wiec panel N pokazuje wymiary w mm.
"""

'''


def strip_module_docstring(src):
    """Usuwa docstring modulu - w pliku wynikowym jest juz naglowek."""
    match = re.match(r'\s*("""|\'\'\')', src)
    if not match:
        return src
    quote = match.group(1)
    start = src.index(quote)
    end = src.index(quote, start + 3) + 3
    return src[end:].lstrip("\n")


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


def main():
    model = strip_module_docstring(read("shelf_model.py"))

    emit = strip_module_docstring(read("blender_emit.py"))
    # w wersji sklejonej nazwy sa juz globalne - usuwamy fallbackowy import
    emit = re.sub(
        r"try:.*?\n    \)\n",
        "",
        emit,
        count=1,
        flags=re.S,
    )

    body = (
        HEADER
        + "# " + "-" * 74 + "\n"
        + "# czesc 1/2: model parametryczny (zrodlo: shelf_model.py)\n"
        + "# " + "-" * 74 + "\n\n"
        + model.rstrip()
        + "\n\n\n"
        + "# " + "-" * 74 + "\n"
        + "# czesc 2/2: emisja do Blendera (zrodlo: blender_emit.py)\n"
        + "# " + "-" * 74 + "\n\n"
        + emit.rstrip()
        + "\n"
    )

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(body)

    lines = body.count("\n")
    print("zapisano %s (%d linii)" % (os.path.relpath(OUT, HERE), lines))
    if "from shelf_model import" in body:
        raise SystemExit("BLAD: w pliku wynikowym zostal import shelf_model")
    print("kontrola: brak zaleznosci od shelf_model.py - plik jest samodzielny")
    verify()


def verify():
    """Sklejony plik musi odtwarzac model 1:1 - inaczej Blender pokaze co innego
    niz podglad. Import nie moze tez wymagac bpy (bpy wchodzi w build_scene)."""
    import importlib
    import shelf_model as source

    sys.path.insert(0, HERE)
    generated = importlib.import_module("build_shelf_blender")

    a, b = source.build_parts(), generated.build_parts()
    if len(a) != len(b):
        raise SystemExit("BLAD: %d elementow w zrodle, %d w pliku wynikowym"
                         % (len(a), len(b)))
    for pa, pb in zip(a, b):
        if (pa.name, pa.kind, pa.grain) != (pb.name, pb.kind, pb.grain) \
                or pa.mesh() != pb.mesh():
            raise SystemExit("BLAD: rozbieznosc geometrii na elemencie %s" % pa.name)
    print("kontrola: %d elementow odtworzonych 1:1 wzgledem shelf_model.py" % len(a))


if __name__ == "__main__":
    main()
