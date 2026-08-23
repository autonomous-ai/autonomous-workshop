"""Cube with a centered cylindrical hole.

Canonical example demonstrating: primitives, face selectors, hole.
"""

import cadquery as cq

from cadlib.validation import verify_bbox, verify_through_hole_pattern

# --- Parameters (mm) ---
CUBE = 30.0
HOLE_DIAMETER = 10.0

# --- Model ---
result = (
    cq.Workplane("XY")
    .box(CUBE, CUBE, CUBE)
    .faces(">Z")
    .workplane()
    .hole(HOLE_DIAMETER)
)

# Keep literal proofs in source so a later EDIT/REMIX cannot move, resize,
# refill, duplicate, or delete the requested bore while still building green.
cube_extent_proof = verify_bbox(
    shape=result,
    expected_size=(CUBE, CUBE, CUBE),
    label="cube",
)
center_bore_proof = verify_through_hole_pattern(
    part=result,
    axis="z",
    centers=[(0, 0)],
    diameter=HOLE_DIAMETER,
    span=(-CUBE / 2, CUBE / 2),
    label="center bore",
)
