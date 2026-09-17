# Verification pipeline record

- Recorded: 2026-09-15T11:23:15+00:00
- Mode: `final`
- Result: **PASS** (exit 0)
- Elapsed: 182.24 s
- Bed: 180 x 180 x 180 mm

| # | command | result | seconds |
|---:|---|---:|---:|
| 1 | `signature review  # NOTE: schema=6 sha256=fa37f9a82ac62b7fc0c8c8dad85dd6aea18c9505ff3693d3d67ae314bba5f2e4` | note | 0.00 |
| 2 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_layout .` | rc=0 | 0.11 |
| 3 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/gen rivetback.step.py part_cannon_body.step.py part_carapace_aft.step.py part_carapace_center.step.py part_carapace_fore.step.py part_chassis_core.step.py part_energy_conduit.step.py part_foot.step.py part_hip_yoke.step.py part_hub_pedestal.step.py part_joint_lock_pin.step.py part_lower_leg_armor.step.py part_lower_leg_beam.step.py part_muzzle_collar.step.py part_sensor_insert.step.py part_upper_leg_armor.step.py part_upper_leg_beam.step.py --write --json` | rc=0 | 7.20 |
| 4 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_fit . --bed 180.0 180.0 --entry part_cannon_body.step.py --entry part_carapace_aft.step.py --entry part_carapace_center.step.py --entry part_carapace_fore.step.py --entry part_chassis_core.step.py --entry part_energy_conduit.step.py --entry part_foot.step.py --entry part_hip_yoke.step.py --entry part_hub_pedestal.step.py --entry part_joint_lock_pin.step.py --entry part_lower_leg_armor.step.py --entry part_lower_leg_beam.step.py --entry part_muzzle_collar.step.py --entry part_sensor_insert.step.py --entry part_upper_leg_armor.step.py --entry part_upper_leg_beam.step.py --strict` | rc=0 | 3.61 |
| 5 | `${WORKSHOP_REPOSITORY}/.venv/bin/python measure/check_fit.py` | rc=0 | 0.03 |
| 6 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_spec_numbers .` | rc=0 | 0.04 |
| 7 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_spec_format .` | rc=0 | 0.04 |
| 8 | `check_mount  # NOT RUN: no measure/mounts.json; no bought part is declared seated` | skipped | 0.00 |
| 9 | `check_power  # NOT RUN: no measure/power.json; no functional powered system is declared` | skipped | 0.00 |
| 10 | `check_motion  # NOT RUN: no documented mating/assembly action and no moving joint is declared` | skipped | 0.00 |
| 11 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/inspect batch (35 JSONL requests)` | rc=0 | 15.51 |
| 12 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_cannon_body.step.py --bed 180x180x180` | rc=0 | 2.58 |
| 13 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_cannon_body.step.py --angle 45.0 --report measure/overhang-cannon_body.md` | rc=0 | 2.51 |
| 14 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_cannon_body.step.py --nozzle 0.4 --report measure/thickness-cannon_body.md` | rc=0 | 4.57 |
| 15 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_carapace_aft.step.py --bed 180x180x180` | rc=0 | 2.58 |
| 16 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_carapace_aft.step.py --angle 45.0 --report measure/overhang-carapace_aft.md` | rc=0 | 2.55 |
| 17 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_carapace_aft.step.py --nozzle 0.4 --report measure/thickness-carapace_aft.md` | rc=0 | 6.37 |
| 18 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_carapace_center.step.py --bed 180x180x180` | rc=0 | 2.54 |
| 19 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_carapace_center.step.py --angle 45.0 --report measure/overhang-carapace_center.md` | rc=0 | 2.54 |
| 20 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_carapace_center.step.py --nozzle 0.4 --report measure/thickness-carapace_center.md` | rc=0 | 6.67 |
| 21 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_carapace_fore.step.py --bed 180x180x180` | rc=0 | 2.62 |
| 22 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_carapace_fore.step.py --angle 45.0 --report measure/overhang-carapace_fore.md` | rc=0 | 2.57 |
| 23 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_carapace_fore.step.py --nozzle 0.4 --report measure/thickness-carapace_fore.md` | rc=0 | 5.19 |
| 24 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_chassis_core.step.py --bed 180x180x180` | rc=0 | 2.74 |
| 25 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_chassis_core.step.py --angle 45.0 --report measure/overhang-chassis_core.md` | rc=0 | 2.87 |
| 26 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_chassis_core.step.py --nozzle 0.4 --report measure/thickness-chassis_core.md` | rc=0 | 11.75 |
| 27 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_energy_conduit.step.py --bed 180x180x180` | rc=0 | 2.65 |
| 28 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_energy_conduit.step.py --angle 45.0 --report measure/overhang-energy_conduit.md` | rc=0 | 2.49 |
| 29 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_energy_conduit.step.py --nozzle 0.4 --report measure/thickness-energy_conduit.md` | rc=0 | 2.98 |
| 30 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_foot.step.py --bed 180x180x180` | rc=0 | 2.57 |
| 31 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_foot.step.py --angle 45.0 --report measure/overhang-foot.md` | rc=0 | 2.57 |
| 32 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_foot.step.py --nozzle 0.4 --report measure/thickness-foot.md` | rc=0 | 3.04 |
| 33 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_hip_yoke.step.py --bed 180x180x180` | rc=0 | 2.51 |
| 34 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_hip_yoke.step.py --angle 45.0 --report measure/overhang-hip_yoke.md` | rc=0 | 2.50 |
| 35 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_hip_yoke.step.py --nozzle 0.4 --report measure/thickness-hip_yoke.md` | rc=0 | 3.15 |
| 36 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_hub_pedestal.step.py --bed 180x180x180` | rc=0 | 2.54 |
| 37 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_hub_pedestal.step.py --angle 45.0 --report measure/overhang-hub_pedestal.md` | rc=0 | 2.56 |
| 38 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_hub_pedestal.step.py --nozzle 0.4 --report measure/thickness-hub_pedestal.md` | rc=0 | 6.58 |
| 39 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_joint_lock_pin.step.py --bed 180x180x180` | rc=0 | 2.52 |
| 40 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_joint_lock_pin.step.py --angle 45.0 --report measure/overhang-joint_lock_pin.md` | rc=0 | 2.54 |
| 41 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_joint_lock_pin.step.py --nozzle 0.4 --report measure/thickness-joint_lock_pin.md` | rc=0 | 2.62 |
| 42 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_lower_leg_armor.step.py --bed 180x180x180` | rc=0 | 2.48 |
| 43 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_lower_leg_armor.step.py --angle 45.0 --report measure/overhang-lower_leg_armor.md` | rc=0 | 2.56 |
| 44 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_lower_leg_armor.step.py --nozzle 0.4 --report measure/thickness-lower_leg_armor.md` | rc=0 | 3.29 |
| 45 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_lower_leg_beam.step.py --bed 180x180x180` | rc=0 | 2.61 |
| 46 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_lower_leg_beam.step.py --angle 45.0 --report measure/overhang-lower_leg_beam.md` | rc=0 | 2.55 |
| 47 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_lower_leg_beam.step.py --nozzle 0.4 --report measure/thickness-lower_leg_beam.md` | rc=0 | 3.68 |
| 48 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_muzzle_collar.step.py --bed 180x180x180` | rc=0 | 2.64 |
| 49 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_muzzle_collar.step.py --angle 45.0 --report measure/overhang-muzzle_collar.md` | rc=0 | 2.62 |
| 50 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_muzzle_collar.step.py --nozzle 0.4 --report measure/thickness-muzzle_collar.md` | rc=0 | 3.26 |
| 51 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_sensor_insert.step.py --bed 180x180x180` | rc=0 | 2.52 |
| 52 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_sensor_insert.step.py --angle 45.0 --report measure/overhang-sensor_insert.md` | rc=0 | 2.54 |
| 53 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_sensor_insert.step.py --nozzle 0.4 --report measure/thickness-sensor_insert.md` | rc=0 | 2.88 |
| 54 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_upper_leg_armor.step.py --bed 180x180x180` | rc=0 | 2.53 |
| 55 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_upper_leg_armor.step.py --angle 45.0 --report measure/overhang-upper_leg_armor.md` | rc=0 | 2.56 |
| 56 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_upper_leg_armor.step.py --nozzle 0.4 --report measure/thickness-upper_leg_armor.md` | rc=0 | 2.90 |
| 57 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_mesh part_upper_leg_beam.step.py --bed 180x180x180` | rc=0 | 2.62 |
| 58 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_overhang part_upper_leg_beam.step.py --angle 45.0 --report measure/overhang-upper_leg_beam.md` | rc=0 | 2.62 |
| 59 | `${WORKSHOP_REPOSITORY}/.venv/bin/python ${RUN_WORKSPACE}/.agents/skills/cad/scripts/check_thickness part_upper_leg_beam.step.py --nozzle 0.4 --report measure/thickness-upper_leg_beam.md` | rc=0 | 4.37 |
