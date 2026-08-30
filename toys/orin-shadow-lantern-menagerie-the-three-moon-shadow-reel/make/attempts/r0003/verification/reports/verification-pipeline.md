# Verification pipeline record

- Recorded: 2026-08-29T19:35:02+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 205.84 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' work/make/r0003/host-retry-project` | rc=0 | 0.07 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' work/make/r0003/host-retry-project/assembled.step.py work/make/r0003/host-retry-project/part_front_shell.step.py work/make/r0003/host-retry-project/part_kickstand.step.py work/make/r0003/host-retry-project/part_rear_shell.step.py work/make/r0003/host-retry-project/part_shadow_reel.step.py --write --json` | rc=0 | 29.27 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' work/make/r0003/host-retry-project --bed 220.0 220.0 --entry work/make/r0003/host-retry-project/part_front_shell.step.py --entry work/make/r0003/host-retry-project/part_kickstand.step.py --entry work/make/r0003/host-retry-project/part_rear_shell.step.py --entry work/make/r0003/host-retry-project/part_shadow_reel.step.py --strict` | rc=0 | 31.54 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 work/make/r0003/host-retry-project/measure/check_fit.py` | rc=0 | 7.80 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 work/make/r0003/host-retry-project/measure/check_spec.py` | rc=0 | 22.76 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' work/make/r0003/host-retry-project --manifest work/make/r0003/host-retry-project/measure/motion.json` | rc=0 | 40.28 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (11 JSONL requests)` | rc=0 | 55.75 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0003/host-retry-project/assembled.step --glb --json` | rc=0 | 1.27 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0003/host-retry-project/part_front_shell.step --stl --json` | rc=0 | 0.86 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0003/host-retry-project/part_front_shell.stl --bed 220x220x220` | rc=0 | 0.22 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0003/host-retry-project/part_front_shell.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-front_shell.md` | rc=0 | 2.94 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0003/host-retry-project/part_kickstand.step --stl --json` | rc=0 | 0.70 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0003/host-retry-project/part_kickstand.stl --bed 220x220x220` | rc=0 | 0.23 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0003/host-retry-project/part_kickstand.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-kickstand.md` | rc=0 | 2.46 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0003/host-retry-project/part_rear_shell.step --stl --json` | rc=0 | 0.87 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0003/host-retry-project/part_rear_shell.stl --bed 220x220x220` | rc=0 | 0.23 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0003/host-retry-project/part_rear_shell.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-rear_shell.md` | rc=0 | 3.47 |
| 20 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0003/host-retry-project/part_shadow_reel.step --stl --json` | rc=0 | 0.88 |
| 21 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0003/host-retry-project/part_shadow_reel.stl --bed 220x220x220` | rc=0 | 0.24 |
| 22 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0003/host-retry-project/part_shadow_reel.stl --nozzle 0.4 --report work/make/r0003/host-retry-project/measure/thickness-shadow_reel.md` | rc=0 | 4.01 |
