# Verification pipeline record

- Recorded: 2026-09-09T01:15:24+00:00
- Mode: `print-preflight`
- Result: **PASS** (exit 0)
- Elapsed: 68.65 s
- Bed: 220 x 220 x 220 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_layout artifacts/make/r0001/product/cybercab` | rc=0 | 0.12 |
| 2 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/gen artifacts/make/r0001/product/cybercab/part_body.step.py artifacts/make/r0001/product/cybercab/part_chassis.step.py artifacts/make/r0001/product/cybercab/part_end_wheel.step.py artifacts/make/r0001/product/cybercab/part_front_wheelset.step.py artifacts/make/r0001/product/cybercab/part_rear_wheelset.step.py artifacts/make/r0001/product/cybercab/part_window.step.py --write --json` | rc=0 | 11.00 |
| 3 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_fit artifacts/make/r0001/product/cybercab --bed 220.0 220.0 --strict --entry artifacts/make/r0001/product/cybercab/part_body.step.py --entry artifacts/make/r0001/product/cybercab/part_chassis.step.py --entry artifacts/make/r0001/product/cybercab/part_end_wheel.step.py --entry artifacts/make/r0001/product/cybercab/part_front_wheelset.step.py --entry artifacts/make/r0001/product/cybercab/part_rear_wheelset.step.py --entry artifacts/make/r0001/product/cybercab/part_window.step.py` | rc=0 | 9.53 |
| 4 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/export artifacts/make/r0001/product/cybercab/part_body.step --stl --json` | rc=0 | 2.11 |
| 5 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/cybercab/part_body.stl --bed 220x220x220` | rc=0 | 0.58 |
| 6 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness artifacts/make/r0001/product/cybercab/part_body.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-body.md` | rc=0 | 6.27 |
| 7 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/export artifacts/make/r0001/product/cybercab/part_chassis.step --stl --json` | rc=0 | 2.14 |
| 8 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/cybercab/part_chassis.stl --bed 220x220x220` | rc=0 | 0.64 |
| 9 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness artifacts/make/r0001/product/cybercab/part_chassis.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-chassis.md` | rc=0 | 6.62 |
| 10 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/export artifacts/make/r0001/product/cybercab/part_end_wheel.step --stl --json` | rc=0 | 1.79 |
| 11 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/cybercab/part_end_wheel.stl --bed 220x220x220` | rc=0 | 0.45 |
| 12 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness artifacts/make/r0001/product/cybercab/part_end_wheel.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-end_wheel.md` | rc=0 | 4.18 |
| 13 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/export artifacts/make/r0001/product/cybercab/part_front_wheelset.step --stl --json` | rc=0 | 2.52 |
| 14 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/cybercab/part_front_wheelset.stl --bed 220x220x220` | rc=0 | 0.59 |
| 15 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness artifacts/make/r0001/product/cybercab/part_front_wheelset.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-front_wheelset.md` | rc=0 | 6.55 |
| 16 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/export artifacts/make/r0001/product/cybercab/part_rear_wheelset.step --stl --json` | rc=0 | 2.43 |
| 17 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/cybercab/part_rear_wheelset.stl --bed 220x220x220` | rc=0 | 0.72 |
| 18 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness artifacts/make/r0001/product/cybercab/part_rear_wheelset.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-rear_wheelset.md` | rc=0 | 6.07 |
| 19 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/export artifacts/make/r0001/product/cybercab/part_window.step --stl --json` | rc=0 | 2.19 |
| 20 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_mesh artifacts/make/r0001/product/cybercab/part_window.stl --bed 220x220x220` | rc=0 | 0.59 |
| 21 | `<HOME>/.local/share/autonomous-workshop-python/bin/python3.13 <WORKSHOP_RUN>/.agents/skills/cad/scripts/check_thickness artifacts/make/r0001/product/cybercab/part_window.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-window.md` | rc=0 | 1.58 |
