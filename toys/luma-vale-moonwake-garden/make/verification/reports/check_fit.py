"""Cheap source-level mate and assembly-order audit; generic gates own geometry."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT))

import moonwake_garden_lib as m  # noqa: E402


def main() -> None:
    m.validate_parameters()
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    require(math.isclose(m.ROTOR_BORE_D, m.cadfits.slot_for(m.SPINDLE_D, m.SPINDLE_CLEARANCE_RADIAL)), "spindle/bore derivation drift")
    require(math.isclose(m.GUIDE_ID, m.cadfits.slot_for(m.ROTOR_D, m.GUIDE_CLEARANCE_RADIAL)), "rotor/guide derivation drift")
    require(math.isclose(m.SNAP_HOLE_D, m.cadfits.slot_for(m.SNAP_STEM_D, m.SNAP_STEM_CLEARANCE_RADIAL)), "snap stem/hole derivation drift")
    require(math.isclose(m.SNAP_RELIEF_D, m.cadfits.slot_for(m.SNAP_HEAD_D, m.SNAP_RELIEF_CLEARANCE_RADIAL)), "snap head/relief derivation drift")
    require(m.REAR_PLATE_Z < m.ROTOR_SEAT_Z < m.ROTOR_SEAT_Z + m.ROTOR_Z < m.FRONT_SEAT_Z, "assembly Z order is invalid")
    require(math.isclose(m.FRONT_SEAT_Z - (m.ROTOR_SEAT_Z + m.ROTOR_Z), 0.30), "axial clearance drift")
    require(math.isclose(m.GUIDE_ID - m.ROTOR_D, 0.80), "guide diametral clearance drift")
    require(math.isclose(m.ROTOR_BORE_D - m.SPINDLE_D, 0.60), "spindle diametral clearance drift")

    entries = {
        "rear_chassis": PROJECT / "part_rear_chassis.step.py",
        "sector_rotor": PROJECT / "part_sector_rotor.step.py",
        "front_garden_mask": PROJECT / "part_front_garden_mask.step.py",
    }
    for role, path in entries.items():
        text = path.read_text()
        require("PRINTABLE = True" in text, f"{role} is not a declared print target")
        require("def gen_step():" in text, f"{role} lacks an entry generator")
    assembly_text = (PROJECT / "moonwake_garden.step.py").read_text()
    require("PRINTABLE = False" in assembly_text, "combined assembly must not be sliced as one part")
    for stable_label in ("rear_chassis", "sector_rotor", "front_garden_mask"):
        require(f'"{stable_label}"' in assembly_text, f"assembly lacks stable label {stable_label}")

    source_text = (PROJECT / "moonwake_garden_lib.py").read_text()
    for derivation in (
        "ROTOR_BORE_D = cadfits.slot_for(SPINDLE_D",
        "GUIDE_ID = cadfits.slot_for(ROTOR_D",
        "SNAP_HOLE_D = cadfits.slot_for(SNAP_STEM_D",
        "SNAP_RELIEF_D = cadfits.slot_for(SNAP_HEAD_D",
    ):
        require(derivation in source_text, f"missing auditable mate derivation: {derivation}")

    result = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "printable_entries": list(entries),
        "derived_fits_mm": {
            "spindle_diameter": m.SPINDLE_D,
            "rotor_bore_diameter": m.ROTOR_BORE_D,
            "spindle_radial_clearance": (m.ROTOR_BORE_D - m.SPINDLE_D) / 2.0,
            "rotor_diameter": m.ROTOR_D,
            "guide_id": m.GUIDE_ID,
            "guide_radial_clearance": (m.GUIDE_ID - m.ROTOR_D) / 2.0,
            "snap_stem_diameter": m.SNAP_STEM_D,
            "snap_hole_diameter": m.SNAP_HOLE_D,
            "snap_head_diameter": m.SNAP_HEAD_D,
            "snap_relief_diameter": m.SNAP_RELIEF_D,
            "axial_rotor_clearance": m.FRONT_SEAT_Z - (m.ROTOR_SEAT_Z + m.ROTOR_Z),
        },
        "assembly_order_z_mm": [0.0, m.REAR_PLATE_Z, m.ROTOR_SEAT_Z, m.ROTOR_SEAT_Z + m.ROTOR_Z, m.FRONT_SEAT_Z, m.ASSEMBLED_Z],
        "evidence_limit": "Source derivations do not establish printer-process fit or elastic force; generic fit/mesh gates and physical coupons remain distinct.",
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
