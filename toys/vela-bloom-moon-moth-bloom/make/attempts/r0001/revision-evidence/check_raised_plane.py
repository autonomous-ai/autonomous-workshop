#!/usr/bin/env python3
"""Deterministically test the sealed service-plane stack for Z collision."""

import json
from pathlib import Path


evidence_dir = Path(__file__).resolve().parent
sealed = json.loads((evidence_dir / "sealed-z-stack.json").read_text())
dims = sealed["sealed_dimensions_mm"]
sequence = sealed["sealed_sequence"]
horizontal = sealed["sealed_horizontal_overlap"]

moving_min = dims["service_moving_z_min"]
moving_max = dims["service_moving_z_max"]
fixed_min = dims["fixed_guard_lip_bridge_z_min"]
fixed_max = dims["fixed_guard_lip_bridge_z_max"]
overlap_min = max(moving_min, fixed_min)
overlap_max = min(moving_max, fixed_max)
overlap = round(max(0.0, overlap_max - overlap_min), 6)

assert moving_min == dims["operating_moving_z_min"] + dims["service_raise"]
assert moving_max == dims["operating_moving_z_max"] + dims["service_raise"]
assert sequence["raised_during_rotation"] is True
assert sequence["service_rotation_end_degrees"] == sequence["drop_at_degrees"] == 0
assert horizontal["closing_interval_degrees"] > 0
assert horizontal["minimum_depth_under_entry_lip_mm"] > 0
assert overlap > 0

result = {
    "schema_version": 1,
    "check": "sealed-raised-service-plane-versus-fixed-roof",
    "checkpoint_sha256": sealed["checkpoint_sha256"],
    "subject_sha256": sealed["subject_sha256"],
    "invented_sha256": sealed["invented_sha256"],
    "moving_service_interval_mm": [moving_min, moving_max],
    "fixed_roof_interval_mm": [fixed_min, fixed_max],
    "intersection_interval_mm": [overlap_min, overlap_max],
    "intersection_thickness_mm": overlap,
    "horizontal_overlap_proven_by": {
        "closing_interval_degrees": horizontal["closing_interval_degrees"],
        "minimum_depth_under_entry_lip_mm": horizontal[
            "minimum_depth_under_entry_lip_mm"
        ],
    },
    "drop_occurs_after_conflicting_interval": True,
    "verdict": "block",
}
print(json.dumps(result, indent=2, sort_keys=True))
