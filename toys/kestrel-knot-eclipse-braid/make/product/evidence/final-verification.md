# Verification pipeline record

- Recorded: 2026-08-28T10:10:50+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 849.99 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout' project` | rc=0 | 0.03 |
| 2 | `design_refs verify  # NOT RUN: no ref/external directory; no fetched design reference is declared` | skipped | 0.00 |
| 3 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/gen' project/eclipse_braid.step.py --write --json` | rc=0 | 37.07 |
| 4 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit' project --bed 220.0 220.0 --entry project/eclipse_braid.step.py --strict` | rc=0 | 36.43 |
| 5 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 project/measure/check_spec.py` | rc=0 | 3.87 |
| 6 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 7 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 8 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 9 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/inspect' batch (3 JSONL requests)` | rc=0 | 763.57 |
| 10 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' project/eclipse_braid.step --glb --json` | rc=0 | 3.02 |
| 11 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/export' project/eclipse_braid.step --stl --json` | rc=0 | 2.80 |
| 12 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh' project/eclipse_braid.stl --bed 220x220x220` | rc=0 | 0.61 |
| 13 | `<HOME>/code/autonomous-workshop/.venv/bin/python3 '<WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness' project/eclipse_braid.stl --nozzle 0.4 --report project/measure/thickness-eclipse_braid.md` | rc=0 | 2.59 |
