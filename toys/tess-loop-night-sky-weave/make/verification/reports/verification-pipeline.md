# Verification pipeline record

- Recorded: 2026-08-29T11:16:32+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 27.77 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' _verification/make-r0001-7fbab280/project` | rc=0 | 0.03 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' _verification/make-r0001-7fbab280/project/night_sky_weave.step.py _verification/make-r0001-7fbab280/project/part_comet.step.py _verification/make-r0001-7fbab280/project/part_crescent.step.py _verification/make-r0001-7fbab280/project/part_star.step.py --write --json` | rc=0 | 3.93 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' _verification/make-r0001-7fbab280/project --bed 220.0 220.0 --entry _verification/make-r0001-7fbab280/project/part_comet.step.py --entry _verification/make-r0001-7fbab280/project/part_crescent.step.py --entry _verification/make-r0001-7fbab280/project/part_star.step.py --strict` | rc=0 | 2.22 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 _verification/make-r0001-7fbab280/project/measure/check_fit.py` | rc=0 | 1.80 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 _verification/make-r0001-7fbab280/project/measure/check_spec.py` | rc=0 | 1.80 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (9 JSONL requests)` | rc=0 | 8.00 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' _verification/make-r0001-7fbab280/project/night_sky_weave.step --glb --json` | rc=0 | 1.07 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' _verification/make-r0001-7fbab280/project/part_comet.step --stl --json` | rc=0 | 0.64 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' _verification/make-r0001-7fbab280/project/part_comet.stl --bed 220x220x220` | rc=0 | 0.19 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' _verification/make-r0001-7fbab280/project/part_comet.stl --nozzle 0.4 --report _verification/make-r0001-7fbab280/project/measure/thickness-comet.md` | rc=0 | 2.04 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' _verification/make-r0001-7fbab280/project/part_crescent.step --stl --json` | rc=0 | 0.64 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' _verification/make-r0001-7fbab280/project/part_crescent.stl --bed 220x220x220` | rc=0 | 0.19 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' _verification/make-r0001-7fbab280/project/part_crescent.stl --nozzle 0.4 --report _verification/make-r0001-7fbab280/project/measure/thickness-crescent.md` | rc=0 | 2.21 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' _verification/make-r0001-7fbab280/project/part_star.step --stl --json` | rc=0 | 0.65 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' _verification/make-r0001-7fbab280/project/part_star.stl --bed 220x220x220` | rc=0 | 0.20 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' _verification/make-r0001-7fbab280/project/part_star.stl --nozzle 0.4 --report _verification/make-r0001-7fbab280/project/measure/thickness-star.md` | rc=0 | 2.15 |
