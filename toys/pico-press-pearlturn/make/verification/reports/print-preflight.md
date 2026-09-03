# Verification pipeline record

- Recorded: 2026-09-03T08:15:28+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 174.34 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/pearlturn` | rc=0 | 0.31 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/pearlturn/part_pearl.step.py artifacts/make/r0001/product/pearlturn/part_shell.step.py --write --json` | rc=0 | 32.77 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/pearlturn --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/pearlturn/part_pearl.step.py --entry artifacts/make/r0001/product/pearlturn/part_shell.step.py` | rc=0 | 27.27 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/pearlturn/part_pearl.step --stl --json` | rc=0 | 8.51 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/pearlturn/part_pearl.stl --bed 220x220x220` | rc=0 | 2.74 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/pearlturn/part_pearl.stl --nozzle 0.4 --report artifacts/make/r0001/product/pearlturn/measure/thickness-pearl.md` | rc=0 | 39.62 |
| 7 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/pearlturn/part_shell.step --stl --json` | rc=0 | 8.44 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/pearlturn/part_shell.stl --bed 220x220x220` | rc=0 | 3.36 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/pearlturn/part_shell.stl --nozzle 0.4 --report artifacts/make/r0001/product/pearlturn/measure/thickness-shell.md` | rc=0 | 51.29 |
