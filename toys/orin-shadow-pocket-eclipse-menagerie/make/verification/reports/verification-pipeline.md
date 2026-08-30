# Verification pipeline record

- Recorded: 2026-08-30T07:49:23+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 26.61 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad/pocket_eclipse` | rc=0 | 0.12 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.step.py --write --json` | rc=0 | 8.05 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad/pocket_eclipse --bed 220.0 220.0 --entry artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.step.py --strict` | rc=0 | 4.89 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python artifacts/make/r0001/product/cad/pocket_eclipse/measure/check_spec.py` | rc=0 | 0.02 |
| 5 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 6 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 7 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (3 JSONL requests)` | rc=0 | 7.87 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.step --glb --json` | rc=0 | 1.17 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.step --stl --json` | rc=0 | 1.11 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.stl --bed 220x220x220` | rc=0 | 0.28 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/pocket_eclipse/pocket_eclipse.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/pocket_eclipse/measure/thickness-pocket_eclipse.md` | rc=0 | 3.08 |
