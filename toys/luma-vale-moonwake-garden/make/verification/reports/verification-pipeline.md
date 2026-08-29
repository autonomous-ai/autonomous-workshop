# Verification pipeline record

- Recorded: 2026-08-28T05:49:17+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 109.39 s
- Bed: 220 x 220 x 250 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' project` | rc=0 | 0.04 |
| 2 | `design_refs verify  # NOT RUN: no ref/external directory; no fetched design reference is declared` | skipped | 0.00 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' project/moonwake_garden.step.py project/part_front_garden_mask.step.py project/part_rear_chassis.step.py project/part_sector_rotor.step.py --write --json` | rc=0 | 16.97 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' project --bed 220.0 220.0 --entry project/part_front_garden_mask.step.py --entry project/part_rear_chassis.step.py --entry project/part_sector_rotor.step.py --strict` | rc=0 | 9.01 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 project/measure/check_fit.py` | rc=0 | 3.75 |
| 6 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 project/measure/check_spec.py` | rc=0 | 3.98 |
| 7 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 8 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' project --manifest project/measure/motion.json` | rc=0 | 23.49 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (9 JSONL requests)` | rc=0 | 40.49 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' project/moonwake_garden.step --glb --json` | rc=0 | 1.20 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' project/part_front_garden_mask.step --stl --json` | rc=0 | 0.72 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' project/part_front_garden_mask.stl --bed 220x220x250` | rc=0 | 0.35 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' project/part_front_garden_mask.stl --nozzle 0.4 --report project/measure/thickness-front_garden_mask.md` | rc=0 | 2.88 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' project/part_rear_chassis.step --stl --json` | rc=0 | 0.81 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' project/part_rear_chassis.stl --bed 220x220x250` | rc=0 | 0.38 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' project/part_rear_chassis.stl --nozzle 0.4 --report project/measure/thickness-rear_chassis.md` | rc=0 | 2.62 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' project/part_sector_rotor.step --stl --json` | rc=0 | 0.67 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' project/part_sector_rotor.stl --bed 220x220x250` | rc=0 | 0.32 |
| 20 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' project/part_sector_rotor.stl --nozzle 0.4 --report project/measure/thickness-sector_rotor.md` | rc=0 | 1.71 |
