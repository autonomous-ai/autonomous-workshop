# Verification pipeline record

- Recorded: 2026-08-30T06:22:09+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 31.14 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad/moonchase_fox` | rc=0 | 0.05 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.step.py --write --json` | rc=0 | 9.24 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad/moonchase_fox --bed 220.0 220.0 --entry artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.step.py --strict` | rc=0 | 3.37 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python artifacts/make/r0001/product/cad/moonchase_fox/measure/check_spec.py` | rc=0 | 3.03 |
| 5 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 6 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 7 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (3 JSONL requests)` | rc=0 | 4.83 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.step --glb --json` | rc=0 | 0.84 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.step --stl --json` | rc=0 | 0.84 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.stl --bed 220x220x220` | rc=0 | 0.20 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/moonchase_fox/moonchase_fox.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/moonchase_fox/measure/thickness-moonchase_fox.md` | rc=0 | 8.74 |
