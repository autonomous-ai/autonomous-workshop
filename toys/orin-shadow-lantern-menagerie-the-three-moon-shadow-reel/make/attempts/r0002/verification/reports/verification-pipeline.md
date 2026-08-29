# Verification pipeline record

- Recorded: 2026-08-29T17:28:30+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 153.43 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' .host-cad-gate-r2b.7VCS7W/project` | rc=0 | 0.05 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' .host-cad-gate-r2b.7VCS7W/project/assembled.step.py .host-cad-gate-r2b.7VCS7W/project/part_front_shell.step.py .host-cad-gate-r2b.7VCS7W/project/part_kickstand.step.py .host-cad-gate-r2b.7VCS7W/project/part_rear_shell.step.py .host-cad-gate-r2b.7VCS7W/project/part_shadow_reel.step.py --write --json` | rc=0 | 20.59 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' .host-cad-gate-r2b.7VCS7W/project --bed 220.0 220.0 --entry .host-cad-gate-r2b.7VCS7W/project/part_front_shell.step.py --entry .host-cad-gate-r2b.7VCS7W/project/part_kickstand.step.py --entry .host-cad-gate-r2b.7VCS7W/project/part_rear_shell.step.py --entry .host-cad-gate-r2b.7VCS7W/project/part_shadow_reel.step.py --strict` | rc=0 | 12.68 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 .host-cad-gate-r2b.7VCS7W/project/measure/check_fit.py` | rc=0 | 7.68 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 .host-cad-gate-r2b.7VCS7W/project/measure/check_spec.py` | rc=0 | 10.79 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' .host-cad-gate-r2b.7VCS7W/project --manifest .host-cad-gate-r2b.7VCS7W/project/measure/motion.json` | rc=0 | 26.41 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (11 JSONL requests)` | rc=0 | 46.82 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-r2b.7VCS7W/project/assembled.step --glb --json` | rc=0 | 2.24 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-r2b.7VCS7W/project/part_front_shell.step --stl --json` | rc=0 | 1.10 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-r2b.7VCS7W/project/part_front_shell.stl --bed 220x220x220` | rc=0 | 0.25 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-r2b.7VCS7W/project/part_front_shell.stl --nozzle 0.4 --report .host-cad-gate-r2b.7VCS7W/project/measure/thickness-front_shell.md` | rc=0 | 2.96 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-r2b.7VCS7W/project/part_kickstand.step --stl --json` | rc=0 | 0.73 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-r2b.7VCS7W/project/part_kickstand.stl --bed 220x220x220` | rc=0 | 0.23 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-r2b.7VCS7W/project/part_kickstand.stl --nozzle 0.4 --report .host-cad-gate-r2b.7VCS7W/project/measure/thickness-kickstand.md` | rc=0 | 3.03 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-r2b.7VCS7W/project/part_rear_shell.step --stl --json` | rc=0 | 1.28 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-r2b.7VCS7W/project/part_rear_shell.stl --bed 220x220x220` | rc=0 | 0.27 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-r2b.7VCS7W/project/part_rear_shell.stl --nozzle 0.4 --report .host-cad-gate-r2b.7VCS7W/project/measure/thickness-rear_shell.md` | rc=0 | 4.81 |
| 20 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-r2b.7VCS7W/project/part_shadow_reel.step --stl --json` | rc=0 | 4.76 |
| 21 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-r2b.7VCS7W/project/part_shadow_reel.stl --bed 220x220x220` | rc=0 | 1.13 |
| 22 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-r2b.7VCS7W/project/part_shadow_reel.stl --nozzle 0.4 --report .host-cad-gate-r2b.7VCS7W/project/measure/thickness-shadow_reel.md` | rc=0 | 5.62 |
