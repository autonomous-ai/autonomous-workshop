# Verification pipeline record

- Recorded: 2026-09-03T03:22:30+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 238.13 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/neststomp` | rc=0 | 0.45 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/neststomp/part_chick.step.py artifacts/make/r0001/product/neststomp/part_owl.step.py --write --json` | rc=0 | 44.91 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/neststomp --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/neststomp/part_chick.step.py --entry artifacts/make/r0001/product/neststomp/part_owl.step.py` | rc=0 | 27.16 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/neststomp/part_chick.step --stl --json` | rc=0 | 6.35 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/neststomp/part_chick.stl --bed 220x220x220` | rc=0 | 1.57 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/neststomp/part_chick.stl --nozzle 0.4 --report artifacts/make/r0001/product/neststomp/measure/thickness-chick.md` | rc=0 | 89.23 |
| 7 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/neststomp/part_owl.step --stl --json` | rc=0 | 5.96 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/neststomp/part_owl.stl --bed 220x220x220` | rc=0 | 1.84 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/neststomp/part_owl.stl --nozzle 0.4 --report artifacts/make/r0001/product/neststomp/measure/thickness-owl.md` | rc=0 | 60.65 |
