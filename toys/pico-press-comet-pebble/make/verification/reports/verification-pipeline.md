# Verification pipeline record

- Recorded: 2026-08-29T22:18:45+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 83.50 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad` | rc=0 | 0.04 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/comet_pebble.step.py --write --json` | rc=0 | 8.63 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad --bed 220.0 220.0 --entry artifacts/make/r0001/product/cad/comet_pebble.step.py --strict` | rc=0 | 7.67 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python artifacts/make/r0001/product/cad/measure/check_fit.py` | rc=0 | 7.09 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python artifacts/make/r0001/product/cad/measure/check_spec.py` | rc=0 | 7.14 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python artifacts/make/r0001/product/cad/measure/check_landmarks.py` | rc=0 | 8.38 |
| 7 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 8 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 9 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (3 JSONL requests)` | rc=0 | 23.39 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/comet_pebble.step --glb --json` | rc=0 | 2.90 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/comet_pebble.step --stl --json` | rc=0 | 2.31 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/comet_pebble.stl --bed 220x220x220` | rc=0 | 1.05 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/comet_pebble.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-comet_pebble.md` | rc=0 | 14.88 |
