# Verification pipeline record

- Recorded: 2026-09-07T08:23:41+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 160.59 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad` | rc=0 | 0.15 |
| 2 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/part_boat_1.step.py artifacts/make/r0001/product/cad/part_boat_2.step.py artifacts/make/r0001/product/cad/part_boat_3.step.py artifacts/make/r0001/product/cad/part_boat_4.step.py artifacts/make/r0001/product/cad/part_boat_5.step.py artifacts/make/r0001/product/cad/part_inner.step.py artifacts/make/r0001/product/cad/part_outer.step.py artifacts/make/r0001/product/cad/part_shore.step.py --write --json` | rc=0 | 65.41 |
| 3 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cad/part_boat_1.step.py --entry artifacts/make/r0001/product/cad/part_boat_2.step.py --entry artifacts/make/r0001/product/cad/part_boat_3.step.py --entry artifacts/make/r0001/product/cad/part_boat_4.step.py --entry artifacts/make/r0001/product/cad/part_boat_5.step.py --entry artifacts/make/r0001/product/cad/part_inner.step.py --entry artifacts/make/r0001/product/cad/part_outer.step.py --entry artifacts/make/r0001/product/cad/part_shore.step.py` | rc=0 | 10.87 |
| 4 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_boat_1.step --stl --json` | rc=0 | 3.04 |
| 5 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_boat_1.stl --bed 220x220x220` | rc=0 | 0.85 |
| 6 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_boat_1.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boat_1.md` | rc=0 | 2.21 |
| 7 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_boat_2.step --stl --json` | rc=0 | 3.03 |
| 8 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_boat_2.stl --bed 220x220x220` | rc=0 | 0.86 |
| 9 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_boat_2.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boat_2.md` | rc=0 | 2.12 |
| 10 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_boat_3.step --stl --json` | rc=0 | 3.25 |
| 11 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_boat_3.stl --bed 220x220x220` | rc=0 | 1.05 |
| 12 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_boat_3.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boat_3.md` | rc=0 | 2.09 |
| 13 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_boat_4.step --stl --json` | rc=0 | 3.02 |
| 14 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_boat_4.stl --bed 220x220x220` | rc=0 | 0.63 |
| 15 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_boat_4.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boat_4.md` | rc=0 | 2.05 |
| 16 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_boat_5.step --stl --json` | rc=0 | 3.15 |
| 17 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_boat_5.stl --bed 220x220x220` | rc=0 | 0.86 |
| 18 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_boat_5.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boat_5.md` | rc=0 | 2.24 |
| 19 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_inner.step --stl --json` | rc=0 | 2.79 |
| 20 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_inner.stl --bed 220x220x220` | rc=0 | 0.81 |
| 21 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_inner.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-inner.md` | rc=0 | 16.66 |
| 22 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_outer.step --stl --json` | rc=0 | 2.77 |
| 23 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_outer.stl --bed 220x220x220` | rc=0 | 0.89 |
| 24 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_outer.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-outer.md` | rc=0 | 13.03 |
| 25 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_shore.step --stl --json` | rc=0 | 2.73 |
| 26 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_shore.stl --bed 220x220x220` | rc=0 | 0.90 |
| 27 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_shore.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-shore.md` | rc=0 | 13.09 |
