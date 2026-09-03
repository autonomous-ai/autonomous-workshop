# Verification pipeline record

- Recorded: 2026-09-03T04:20:32+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 51.08 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/frosting-aloft` | rc=0 | 0.06 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/frosting-aloft/part_base.step.py artifacts/make/r0001/product/frosting-aloft/part_cap.step.py --write --json` | rc=0 | 9.50 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/frosting-aloft --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/frosting-aloft/part_base.step.py --entry artifacts/make/r0001/product/frosting-aloft/part_cap.step.py` | rc=0 | 9.97 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/frosting-aloft/part_base.step --stl --json` | rc=0 | 3.53 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/frosting-aloft/part_base.stl --bed 220x220x220` | rc=0 | 0.34 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/frosting-aloft/part_base.stl --nozzle 0.4 --report artifacts/make/r0001/product/frosting-aloft/measure/thickness-base.md` | rc=0 | 13.89 |
| 7 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/frosting-aloft/part_cap.step --stl --json` | rc=0 | 2.53 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/frosting-aloft/part_cap.stl --bed 220x220x220` | rc=0 | 0.66 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/frosting-aloft/part_cap.stl --nozzle 0.4 --report artifacts/make/r0001/product/frosting-aloft/measure/thickness-cap.md` | rc=0 | 10.59 |
