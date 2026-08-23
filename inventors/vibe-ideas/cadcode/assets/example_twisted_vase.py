"""Twisted polygon vase — lofted from rotating cross-sections.

Sweeps an N-sided polygon up the Z axis while rotating each cross-section
by a fixed angle. Produces a smooth helical twist. Hollowed for printing
in spiral / vase mode.

Demonstrates: chained ``.workplane(offset=)`` for stacking, pre-rotated
polyline vertices to bake the twist into each cross-section, ``.loft()``
across many wires, ``.shell()`` for a uniform wall thickness on a curved
body.
"""

import math

import cadquery as cq

# --- Vase parameters ---
HEIGHT = 120.0
BASE_DIAMETER = 70.0
TOP_DIAMETER = 50.0
N_SIDES = 6                  # polygon sides — 4=square, 6=hex, 8=oct
TOTAL_TWIST_DEG = 180.0      # total twist from bottom to top
N_LEVELS = 12                # cross-sections used for the loft (more = smoother)
WALL_THICKNESS = 2.0


def _polygon_pts(diameter: float, rotation_deg: float) -> list[tuple[float, float]]:
    """N_SIDES vertices around a circle, rotated by `rotation_deg`."""
    r = diameter / 2.0
    start = math.radians(rotation_deg)
    step = 2 * math.pi / N_SIDES
    return [
        (r * math.cos(start + step * i), r * math.sin(start + step * i))
        for i in range(N_SIDES)
    ]


# Build the loft in one chain. Each level adds a wire by drawing a
# polyline at the workplane's current Z. Rotation is baked into the
# polyline vertices so chained workplanes never need .transformed().
wp = cq.Workplane("XY").polyline(_polygon_pts(BASE_DIAMETER, 0.0)).close()
step_h = HEIGHT / (N_LEVELS - 1)
for i in range(1, N_LEVELS):
    t = i / (N_LEVELS - 1)
    dia = BASE_DIAMETER + (TOP_DIAMETER - BASE_DIAMETER) * t
    angle = TOTAL_TWIST_DEG * t
    wp = (
        wp
        .workplane(offset=step_h)
        .polyline(_polygon_pts(dia, angle))
        .close()
    )

body = wp.loft(combine=True)

# Hollow shell — open top, closed bottom (negative thickness = inward shell)
vase = body.faces(">Z").shell(-WALL_THICKNESS)

result = vase
