#!/bin/bash
# Render finalny ujęcie po ujęciu (osobny proces Blendera na ujęcie, wznawialny: istniejące klatki są pomijane).
# Użycie: scene/render_shots.sh S01 S02 ...   Log: frames/logs/render.log
set -u
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
RES=${RES:-2560x1440}
mkdir -p frames/logs
for s in "$@"; do
  echo "=== $s start $(date '+%F %T')" >> frames/logs/render.log
  RENDER_DEVICE=${RENDER_DEVICE:-METAL} caffeinate -i "$BLENDER" -b -P scene/film.py -- --shot "$s" --res "$RES" \
    > "frames/logs/$s.log" 2>&1
  rc=$?
  grep "\[film\] $s f" "frames/logs/$s.log" | tail -1 >> frames/logs/render.log
  echo "=== $s koniec $(date '+%F %T') rc=$rc klatek: $(ls frames/$s 2>/dev/null | wc -l | tr -d ' ')" >> frames/logs/render.log
done
