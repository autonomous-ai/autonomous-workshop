"""Deterministically prove the sealed Moonwake Garden rotor-web contradiction.

This is a narrow evidence calculation, not a workflow controller. It reads the
host-sealed Invent artifact, confirms the authoritative phrases and structured
minimum, performs the radial/angle arithmetic, and emits canonical JSON.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[4]
INVENTED_PATH = WORKSPACE / "artifacts/invent/invented.json"


def main() -> None:
    invented_bytes = INVENTED_PATH.read_bytes()
    invented = json.loads(invented_bytes)
    concept = invented["concept"]
    rotor = next(item for item in concept["components"] if item["key"] == "sector_rotor")

    # Guard the exact sealed source statements before calculating from them.
    assert "68.0 mm diameter" in rotor["form"]
    assert "radius 9.0 to 31.5 mm" in rotor["form"]
    assert "110 degrees total width" in rotor["form"]
    assert "+75" in rotor["form"]
    assert "0.55 mm radial depth" in rotor["form"]
    assert concept["minimum_geometry_mm"]["rotor_outer_web"] == 2.5

    rotor_radius_mm = 68.0 / 2.0
    sector_outer_radius_mm = 31.5
    sector_center_angle_deg = 90.0
    sector_width_deg = 110.0
    notch_angle_deg = 75.0
    notch_depth_mm = 0.55
    required_minimum_web_mm = 2.5

    sector_start_deg = sector_center_angle_deg - sector_width_deg / 2.0
    sector_end_deg = sector_center_angle_deg + sector_width_deg / 2.0
    notch_inside_sector = sector_start_deg <= notch_angle_deg <= sector_end_deg
    notch_root_radius_mm = rotor_radius_mm - notch_depth_mm
    local_web_mm = notch_root_radius_mm - sector_outer_radius_mm
    shortfall_mm = required_minimum_web_mm - local_web_mm

    result = {
        "calculation": {
            "local_web_mm": round(local_web_mm, 6),
            "notch_angle_deg": notch_angle_deg,
            "notch_depth_mm": notch_depth_mm,
            "notch_inside_sector": notch_inside_sector,
            "notch_root_radius_mm": round(notch_root_radius_mm, 6),
            "required_minimum_web_mm": required_minimum_web_mm,
            "rotor_radius_mm": rotor_radius_mm,
            "sector_angular_span_deg": [sector_start_deg, sector_end_deg],
            "sector_outer_radius_mm": sector_outer_radius_mm,
            "shortfall_mm": round(shortfall_mm, 6),
        },
        "conclusion": "block: exact sealed geometry yields 1.95 mm web at +75 degrees, below the sealed 2.50 mm minimum",
        "invented_artifact_file_sha256": hashlib.sha256(invented_bytes).hexdigest(),
        "invented_identity_sha256": invented["invented_sha256"],
        "schema_version": 1,
    }
    assert notch_inside_sector
    assert round(local_web_mm, 6) == 1.95
    assert round(shortfall_mm, 6) == 0.55
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
