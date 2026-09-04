# Verification pipeline record

- Recorded: 2026-09-03T11:51:02+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 164.82 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad/gutterfall` | rc=0 | 0.18 |
| 2 | `delete cache <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/gutterfall/__cadgen__` | rc=0 | 0.01 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.step.py --write --json` | rc=0 | 74.38 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad/gutterfall --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.step.py` | rc=0 | 50.90 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.step --stl --json` | rc=0 | 8.82 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.stl --bed 220x220x220` | rc=0 | 2.70 |
| 7 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/gutterfall/gutterfall_final.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/gutterfall/measure/thickness-gutterfall_final.md` | rc=0 | 27.83 |
