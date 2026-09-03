# Verification pipeline record

- Recorded: 2026-08-29T16:40:16+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 97.78 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' .host-cad-gate-final.9dbroV/project` | rc=0 | 0.05 |
| 2 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' .host-cad-gate-final.9dbroV/project/assembled.step.py .host-cad-gate-final.9dbroV/project/part_front_shell.step.py .host-cad-gate-final.9dbroV/project/part_kickstand.step.py .host-cad-gate-final.9dbroV/project/part_rear_shell.step.py .host-cad-gate-final.9dbroV/project/part_shadow_reel.step.py --write --json` | rc=0 | 12.82 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' .host-cad-gate-final.9dbroV/project --bed 220.0 220.0 --entry .host-cad-gate-final.9dbroV/project/part_front_shell.step.py --entry .host-cad-gate-final.9dbroV/project/part_kickstand.step.py --entry .host-cad-gate-final.9dbroV/project/part_rear_shell.step.py --entry .host-cad-gate-final.9dbroV/project/part_shadow_reel.step.py --strict` | rc=0 | 7.56 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 .host-cad-gate-final.9dbroV/project/measure/check_fit.py` | rc=0 | 3.45 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 .host-cad-gate-final.9dbroV/project/measure/check_spec.py` | rc=0 | 11.52 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' .host-cad-gate-final.9dbroV/project --manifest .host-cad-gate-final.9dbroV/project/measure/motion.json` | rc=0 | 20.04 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (11 JSONL requests)` | rc=0 | 23.16 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-final.9dbroV/project/assembled.step --glb --json` | rc=0 | 1.19 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-final.9dbroV/project/part_front_shell.step --stl --json` | rc=0 | 0.72 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-final.9dbroV/project/part_front_shell.stl --bed 220x220x220` | rc=0 | 0.22 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-final.9dbroV/project/part_front_shell.stl --nozzle 0.4 --report .host-cad-gate-final.9dbroV/project/measure/thickness-front_shell.md` | rc=0 | 3.35 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-final.9dbroV/project/part_kickstand.step --stl --json` | rc=0 | 0.77 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-final.9dbroV/project/part_kickstand.stl --bed 220x220x220` | rc=0 | 0.21 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-final.9dbroV/project/part_kickstand.stl --nozzle 0.4 --report .host-cad-gate-final.9dbroV/project/measure/thickness-kickstand.md` | rc=0 | 3.07 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-final.9dbroV/project/part_rear_shell.step --stl --json` | rc=0 | 0.77 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-final.9dbroV/project/part_rear_shell.stl --bed 220x220x220` | rc=0 | 0.20 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-final.9dbroV/project/part_rear_shell.stl --nozzle 0.4 --report .host-cad-gate-final.9dbroV/project/measure/thickness-rear_shell.md` | rc=0 | 3.21 |
| 20 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' .host-cad-gate-final.9dbroV/project/part_shadow_reel.step --stl --json` | rc=0 | 0.91 |
| 21 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' .host-cad-gate-final.9dbroV/project/part_shadow_reel.stl --bed 220x220x220` | rc=0 | 0.26 |
| 22 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' .host-cad-gate-final.9dbroV/project/part_shadow_reel.stl --nozzle 0.4 --report .host-cad-gate-final.9dbroV/project/measure/thickness-shadow_reel.md` | rc=0 | 4.29 |
