#!/usr/bin/env bash
# Rebuild every number in the README from a clean checkout. CPU-only, ~3 min, ~2.5 GB peak RAM.
set -euo pipefail
cd "$(dirname "$0")"
REV=4b567ba98acc6ddf27b2abb9004844581083c5d8   # pinned CohereLabs/ATE dataset revision
B=https://huggingface.co/datasets/CohereLabs/ATE/resolve/$REV
[ -x .venv/bin/python ] || uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
mkdir -p data/raw
for c in tools onet_matches servers; do
  [ -s data/raw/$c.parquet ] || curl -fsSL -o data/raw/$c.parquet "$B/data/$c/train-00000-of-00001.parquet"
done
sha256sum -c data/SHA256SUMS
.venv/bin/python -m pytest -q tests
.venv/bin/python src/validate.py > /dev/null
.venv/bin/python src/analyze.py --B 500
.venv/bin/python src/report.py   # regenerates the results section of README.md from results/*.json
.venv/bin/python scripts/make_figures.py   # redraws docs/figures/*.png from results/*.json
