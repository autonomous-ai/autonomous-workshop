# Verification pipeline record

- Recorded: 2026-09-03T03:13:08+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 72.45 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad` | rc=0 | 0.06 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/ember_knock.step.py --write --json` | rc=0 | 31.85 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cad/ember_knock.step.py` | rc=0 | 21.94 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/ember_knock.step --stl --json` | rc=0 | 6.35 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/ember_knock.stl --bed 220x220x220` | rc=0 | 1.67 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/ember_knock.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-ember_knock.md` | rc=0 | 10.58 |
