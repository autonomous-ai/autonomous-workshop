# Verification pipeline record

- Recorded: 2026-09-08T05:22:48+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 24.57 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad` | rc=0 | 0.06 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/knockseed.step.py --write --json` | rc=0 | 9.89 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cad/knockseed.step.py` | rc=0 | 9.07 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/knockseed.step --stl --json` | rc=0 | 1.70 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/knockseed.stl --bed 220x220x220` | rc=0 | 0.74 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/knockseed.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-knockseed.md` | rc=0 | 3.12 |
