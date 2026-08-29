# Verification pipeline record

- Recorded: 2026-08-28T11:10:56+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 173.72 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' work/make-retry-r0001/full1` | rc=0 | 0.04 |
| 2 | `design_refs verify  # NOT RUN: no ref/external directory; no fetched design reference is declared` | skipped | 0.00 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' work/make-retry-r0001/full1/rainspell_dial.step.py work/make-retry-r0001/full1/part_base.step.py work/make-retry-r0001/full1/part_cap.step.py work/make-retry-r0001/full1/part_follower_keeper.step.py work/make-retry-r0001/full1/part_plectrum.step.py work/make-retry-r0001/full1/part_rib_deck.step.py work/make-retry-r0001/full1/part_wheel.step.py --write --json` | rc=0 | 17.75 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' work/make-retry-r0001/full1 --bed 220.0 220.0 --entry work/make-retry-r0001/full1/part_base.step.py --entry work/make-retry-r0001/full1/part_cap.step.py --entry work/make-retry-r0001/full1/part_follower_keeper.step.py --entry work/make-retry-r0001/full1/part_plectrum.step.py --entry work/make-retry-r0001/full1/part_rib_deck.step.py --entry work/make-retry-r0001/full1/part_wheel.step.py --strict` | rc=0 | 10.70 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 work/make-retry-r0001/full1/measure/check_fit.py` | rc=0 | 0.02 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_motion' work/make-retry-r0001/full1 --manifest work/make-retry-r0001/full1/measure/motion.json` | rc=0 | 75.21 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (15 JSONL requests)` | rc=0 | 47.19 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/rainspell_dial.step --glb --json` | rc=0 | 1.15 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/part_base.step --stl --json` | rc=0 | 0.67 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make-retry-r0001/full1/part_base.stl --bed 220x220x220` | rc=0 | 0.41 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make-retry-r0001/full1/part_base.stl --nozzle 0.4 --report work/make-retry-r0001/full1/measure/thickness-base.md` | rc=0 | 3.58 |
| 14 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/part_cap.step --stl --json` | rc=0 | 0.54 |
| 15 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make-retry-r0001/full1/part_cap.stl --bed 220x220x220` | rc=0 | 0.32 |
| 16 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make-retry-r0001/full1/part_cap.stl --nozzle 0.4 --report work/make-retry-r0001/full1/measure/thickness-cap.md` | rc=0 | 2.71 |
| 17 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/part_follower_keeper.step --stl --json` | rc=0 | 0.59 |
| 18 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make-retry-r0001/full1/part_follower_keeper.stl --bed 220x220x220` | rc=0 | 0.32 |
| 19 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make-retry-r0001/full1/part_follower_keeper.stl --nozzle 0.4 --report work/make-retry-r0001/full1/measure/thickness-follower_keeper.md` | rc=0 | 0.84 |
| 20 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/part_plectrum.step --stl --json` | rc=0 | 0.55 |
| 21 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make-retry-r0001/full1/part_plectrum.stl --bed 220x220x220` | rc=0 | 0.33 |
| 22 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make-retry-r0001/full1/part_plectrum.stl --nozzle 0.4 --report work/make-retry-r0001/full1/measure/thickness-plectrum.md` | rc=0 | 2.68 |
| 23 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/part_rib_deck.step --stl --json` | rc=0 | 0.73 |
| 24 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make-retry-r0001/full1/part_rib_deck.stl --bed 220x220x220` | rc=0 | 0.49 |
| 25 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make-retry-r0001/full1/part_rib_deck.stl --nozzle 0.4 --report work/make-retry-r0001/full1/measure/thickness-rib_deck.md` | rc=0 | 2.84 |
| 26 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' work/make-retry-r0001/full1/part_wheel.step --stl --json` | rc=0 | 0.67 |
| 27 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' work/make-retry-r0001/full1/part_wheel.stl --bed 220x220x220` | rc=0 | 0.52 |
| 28 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' work/make-retry-r0001/full1/part_wheel.stl --nozzle 0.4 --report work/make-retry-r0001/full1/measure/thickness-wheel.md` | rc=0 | 2.87 |
