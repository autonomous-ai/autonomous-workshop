# Verification pipeline record

- Recorded: 2026-08-29T13:56:54+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 54.80 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' work/make/r0002/determinism-final` | rc=0 | 0.11 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' work/make/r0002/determinism-final/moon_moth_bloom.step.py work/make/r0002/determinism-final/part_chassis.step.py work/make/r0002/determinism-final/part_left_wing.step.py work/make/r0002/determinism-final/part_right_wing.step.py --write --json` | rc=0 | 10.07 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' work/make/r0002/determinism-final --bed 220.0 220.0 --entry work/make/r0002/determinism-final/part_chassis.step.py --entry work/make/r0002/determinism-final/part_left_wing.step.py --entry work/make/r0002/determinism-final/part_right_wing.step.py --strict` | rc=0 | 5.25 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 work/make/r0002/determinism-final/measure/check_fit.py` | rc=0 | 0.04 |
| 5 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 6 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 7 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' work/make/r0002/determinism-final --manifest work/make/r0002/determinism-final/measure/motion.json` | rc=0 | 8.33 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (9 JSONL requests)` | rc=0 | 16.23 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0002/determinism-final/moon_moth_bloom.step --glb --json` | rc=0 | 1.46 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0002/determinism-final/part_chassis.step --stl --json` | rc=0 | 1.10 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0002/determinism-final/part_chassis.stl --bed 220x220x220` | rc=0 | 0.46 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0002/determinism-final/part_chassis.stl --nozzle 0.4 --report work/make/r0002/determinism-final/measure/thickness-chassis.md` | rc=0 | 6.24 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0002/determinism-final/part_left_wing.step --stl --json` | rc=0 | 0.98 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0002/determinism-final/part_left_wing.stl --bed 220x220x220` | rc=0 | 0.24 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0002/determinism-final/part_left_wing.stl --nozzle 0.4 --report work/make/r0002/determinism-final/measure/thickness-left_wing.md` | rc=0 | 1.58 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0002/determinism-final/part_right_wing.step --stl --json` | rc=0 | 0.87 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0002/determinism-final/part_right_wing.stl --bed 220x220x220` | rc=0 | 0.43 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0002/determinism-final/part_right_wing.stl --nozzle 0.4 --report work/make/r0002/determinism-final/measure/thickness-right_wing.md` | rc=0 | 1.41 |
