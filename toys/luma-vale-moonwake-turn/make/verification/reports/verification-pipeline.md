# Verification pipeline record

- Recorded: 2026-08-30T11:08:51+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 41.77 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad/moonwake` | rc=0 | 0.07 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/moonwake/moonwake.step.py --write --json` | rc=0 | 13.30 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad/moonwake --bed 220.0 220.0 --entry artifacts/make/r0001/product/cad/moonwake/moonwake.step.py` | rc=0 | 11.35 |
| 4 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 5 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 6 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 7 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (3 JSONL requests)` | rc=0 | 11.22 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/moonwake/moonwake.step --glb --json` | rc=0 | 0.99 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/moonwake/moonwake.step --stl --json` | rc=0 | 0.88 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/moonwake/moonwake.stl --bed 220x220x220` | rc=0 | 0.22 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/moonwake/moonwake.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moonwake/measure/thickness-moonwake.md` | rc=0 | 3.72 |
