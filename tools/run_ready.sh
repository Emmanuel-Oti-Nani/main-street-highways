#!/bin/bash
# process every state whose road file exists and whose segment output does not
cd "$(dirname "$0")/.."
for f in data/raw/hpms/hpms_*_2024.geojson; do
  st=$(basename $f | cut -d_ -f2)
  [ -f data/processed/by_state/qa_${st}.json ] && [ data/processed/by_state/qa_${st}.json -nt code/04_segments.py ] && continue
  python3 code/04_segments.py $st >> data/processed/by_state/run.log 2>&1 || echo "FAILED $st" >> data/processed/by_state/run.log
done
