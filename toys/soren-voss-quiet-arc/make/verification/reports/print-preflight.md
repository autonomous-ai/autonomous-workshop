# Verification pipeline record

- Recorded: 2026-09-07T03:40:03+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 90.85 s
- Bed: 220 x 220 x 250 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad` | rc=0 | 0.10 |
| 2 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/part_rocker.step.py --write --json` | rc=0 | 46.21 |
| 3 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cad/part_rocker.step.py` | rc=0 | 10.99 |
| 4 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_rocker.step --stl --json` | rc=0 | 3.38 |
| 5 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_rocker.stl --bed 220x220x250` | rc=0 | 0.95 |
| 6 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_rocker.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-rocker.md` | rc=0 | 29.21 |
