#!/bin/sh
# Run from anywhere; paths below are repo-root relative.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
uv run workshop wish "$(cat toys-spec/antisol/antisol.md)" \
  --inventor ad-astra \
  --workflow spark \
  --agent claude \
  --model claude-opus-5 \
  --effort high \
  --max-rounds 6 \
  --ref toys-spec/antisol/refs/ref-01-mercury-sol.png \
  --ref toys-spec/antisol/refs/ref-02-mars-sol.png \
  --ref toys-spec/antisol/refs/ref-03-venus-sol.png \
  --ref toys-spec/antisol/refs/ref-04-earth-sol.png \
  --ref toys-spec/antisol/refs/ref-05-neptune-sol.png \
  --ref toys-spec/antisol/refs/ref-06-uranus-sol.png \
  --ref toys-spec/antisol/refs/ref-07-saturn-sol.png \
  --ref toys-spec/antisol/refs/ref-08-jupiter-sol.png \
  --ref toys-spec/antisol/refs/ref-09-mercury-anti.png \
  --ref toys-spec/antisol/refs/ref-10-mars-anti.png \
  --ref toys-spec/antisol/refs/ref-11-venus-anti.png \
  --ref toys-spec/antisol/refs/ref-12-earth-anti.png \
  --ref toys-spec/antisol/refs/ref-13-neptune-anti.png \
  --ref toys-spec/antisol/refs/ref-14-uranus-anti.png \
  --ref toys-spec/antisol/refs/ref-15-saturn-anti.png \
  --ref toys-spec/antisol/refs/ref-16-jupiter-anti.png \
  --ref toys-spec/antisol/refs/ref-17-sun-den-star.png \
  --ref toys-spec/antisol/refs/ref-18-corona-cell.png \
  --ref toys-spec/antisol/refs/ref-19-belt-cell.png \
  --ref toys-spec/antisol/refs/ref-20-orbit-tray.png
