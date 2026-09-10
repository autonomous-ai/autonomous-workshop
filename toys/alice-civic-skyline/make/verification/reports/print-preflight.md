# Verification pipeline record

- Recorded: 2026-09-09T17:31:59+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 290.71 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' artifacts/make/r0001/product/cad` | rc=0 | 0.16 |
| 2 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' artifacts/make/r0001/product/cad/part_bishop.step.py artifacts/make/r0001/product/cad/part_board_0_0.step.py artifacts/make/r0001/product/cad/part_board_0_1.step.py artifacts/make/r0001/product/cad/part_board_1_0.step.py artifacts/make/r0001/product/cad/part_board_1_1.step.py artifacts/make/r0001/product/cad/part_dark_tile.step.py artifacts/make/r0001/product/cad/part_king.step.py artifacts/make/r0001/product/cad/part_knight.step.py artifacts/make/r0001/product/cad/part_pawn.step.py artifacts/make/r0001/product/cad/part_queen.step.py artifacts/make/r0001/product/cad/part_rook.step.py --write --json` | rc=0 | 69.48 |
| 3 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' artifacts/make/r0001/product/cad --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cad/part_bishop.step.py --entry artifacts/make/r0001/product/cad/part_board_0_0.step.py --entry artifacts/make/r0001/product/cad/part_board_0_1.step.py --entry artifacts/make/r0001/product/cad/part_board_1_0.step.py --entry artifacts/make/r0001/product/cad/part_board_1_1.step.py --entry artifacts/make/r0001/product/cad/part_dark_tile.step.py --entry artifacts/make/r0001/product/cad/part_king.step.py --entry artifacts/make/r0001/product/cad/part_knight.step.py --entry artifacts/make/r0001/product/cad/part_pawn.step.py --entry artifacts/make/r0001/product/cad/part_queen.step.py --entry artifacts/make/r0001/product/cad/part_rook.step.py` | rc=0 | 14.54 |
| 4 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_bishop.step --stl --json` | rc=0 | 3.07 |
| 5 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_bishop.stl --bed 220x220x220` | rc=0 | 0.70 |
| 6 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_bishop.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-bishop.md` | rc=0 | 15.13 |
| 7 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_board_0_0.step --stl --json` | rc=0 | 3.47 |
| 8 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_board_0_0.stl --bed 220x220x220` | rc=0 | 0.82 |
| 9 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_board_0_0.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-board_0_0.md` | rc=0 | 13.96 |
| 10 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_board_0_1.step --stl --json` | rc=0 | 3.03 |
| 11 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_board_0_1.stl --bed 220x220x220` | rc=0 | 0.82 |
| 12 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_board_0_1.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-board_0_1.md` | rc=0 | 13.48 |
| 13 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_board_1_0.step --stl --json` | rc=0 | 2.87 |
| 14 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_board_1_0.stl --bed 220x220x220` | rc=0 | 0.64 |
| 15 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_board_1_0.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-board_1_0.md` | rc=0 | 12.49 |
| 16 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_board_1_1.step --stl --json` | rc=0 | 2.97 |
| 17 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_board_1_1.stl --bed 220x220x220` | rc=0 | 0.84 |
| 18 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_board_1_1.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-board_1_1.md` | rc=0 | 13.16 |
| 19 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_dark_tile.step --stl --json` | rc=0 | 2.77 |
| 20 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_dark_tile.stl --bed 220x220x220` | rc=0 | 0.70 |
| 21 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_dark_tile.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-dark_tile.md` | rc=0 | 5.73 |
| 22 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_king.step --stl --json` | rc=0 | 2.99 |
| 23 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_king.stl --bed 220x220x220` | rc=0 | 0.71 |
| 24 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_king.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-king.md` | rc=0 | 13.60 |
| 25 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_knight.step --stl --json` | rc=0 | 2.86 |
| 26 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_knight.stl --bed 220x220x220` | rc=0 | 0.83 |
| 27 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_knight.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-knight.md` | rc=0 | 16.70 |
| 28 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_pawn.step --stl --json` | rc=0 | 3.02 |
| 29 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_pawn.stl --bed 220x220x220` | rc=0 | 0.81 |
| 30 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_pawn.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-pawn.md` | rc=0 | 16.21 |
| 31 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_queen.step --stl --json` | rc=0 | 3.81 |
| 32 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_queen.stl --bed 220x220x220` | rc=0 | 0.97 |
| 33 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_queen.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-queen.md` | rc=0 | 16.33 |
| 34 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' artifacts/make/r0001/product/cad/part_rook.step --stl --json` | rc=0 | 3.39 |
| 35 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' artifacts/make/r0001/product/cad/part_rook.stl --bed 220x220x220` | rc=0 | 0.79 |
| 36 | `<HOME>/miniconda/bin/python3.12 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' artifacts/make/r0001/product/cad/part_rook.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-rook.md` | rc=0 | 26.78 |
