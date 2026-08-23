"""Cube with a centered cylindrical hole.

Canonical example demonstrating: primitives, face selectors, hole.
"""

import cadquery as cq

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
