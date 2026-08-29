# Verification pipeline record

- Recorded: 2026-08-29T20:23:26+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 215.04 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' work/make/r0004/final-clean-r2` | rc=0 | 0.05 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' work/make/r0004/final-clean-r2/assembled.step.py work/make/r0004/final-clean-r2/part_front_shell.step.py work/make/r0004/final-clean-r2/part_kickstand.step.py work/make/r0004/final-clean-r2/part_rear_shell.step.py work/make/r0004/final-clean-r2/part_shadow_reel.step.py --write --json` | rc=0 | 34.11 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' work/make/r0004/final-clean-r2 --bed 220.0 220.0 --entry work/make/r0004/final-clean-r2/part_front_shell.step.py --entry work/make/r0004/final-clean-r2/part_kickstand.step.py --entry work/make/r0004/final-clean-r2/part_rear_shell.step.py --entry work/make/r0004/final-clean-r2/part_shadow_reel.step.py --strict` | rc=0 | 9.32 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 work/make/r0004/final-clean-r2/measure/check_fit.py` | rc=0 | 2.48 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 work/make/r0004/final-clean-r2/measure/check_spec.py` | rc=0 | 13.85 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' work/make/r0004/final-clean-r2 --manifest work/make/r0004/final-clean-r2/measure/motion.json` | rc=0 | 64.15 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (11 JSONL requests)` | rc=0 | 56.16 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0004/final-clean-r2/assembled.step --glb --json` | rc=0 | 2.28 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0004/final-clean-r2/part_front_shell.step --stl --json` | rc=0 | 1.71 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0004/final-clean-r2/part_front_shell.stl --bed 220x220x220` | rc=0 | 0.24 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0004/final-clean-r2/part_front_shell.stl --nozzle 0.4 --report work/make/r0004/final-clean-r2/measure/thickness-front_shell.md` | rc=0 | 3.33 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0004/final-clean-r2/part_kickstand.step --stl --json` | rc=0 | 1.56 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0004/final-clean-r2/part_kickstand.stl --bed 220x220x220` | rc=0 | 0.33 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0004/final-clean-r2/part_kickstand.stl --nozzle 0.4 --report work/make/r0004/final-clean-r2/measure/thickness-kickstand.md` | rc=0 | 4.75 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0004/final-clean-r2/part_rear_shell.step --stl --json` | rc=0 | 3.33 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0004/final-clean-r2/part_rear_shell.stl --bed 220x220x220` | rc=0 | 1.03 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0004/final-clean-r2/part_rear_shell.stl --nozzle 0.4 --report work/make/r0004/final-clean-r2/measure/thickness-rear_shell.md` | rc=0 | 5.24 |
| 20 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make/r0004/final-clean-r2/part_shadow_reel.step --stl --json` | rc=0 | 4.54 |
| 21 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make/r0004/final-clean-r2/part_shadow_reel.stl --bed 220x220x220` | rc=0 | 1.00 |
| 22 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make/r0004/final-clean-r2/part_shadow_reel.stl --nozzle 0.4 --report work/make/r0004/final-clean-r2/measure/thickness-shadow_reel.md` | rc=0 | 5.55 |
