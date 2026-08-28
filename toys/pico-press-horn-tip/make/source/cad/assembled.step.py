"""Horn Tip: one-piece crescent desk rocker, print-on-cheek.

CAD project lives in cad/ so the host verifier finds the combined entry.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    BuildSketch,
    Circle,
    Cylinder,
    Locations,
    Mode,
    Polygon,
    Pos,
    extrude,
)
from cadgen import srgb
from cadgen.assembly import label_shape

PRINTABLE = True

# Envelope and rocking curve [assumed], mm. Print: XY silhouette, +Z thickness.
OUTER_R = 42.0
INNER_R = 30.0
HALF_ANGLE_DEG = 50.0
THICKNESS = 18.0
# Shallow top-face dishes mark the horns without changing the rocking cylinder.
PAD_RADIUS = 5.0
PAD_DEPTH = 0.6

HORN_R = (OUTER_R - INNER_R) / 2.0
MID_R = (OUTER_R + INNER_R) / 2.0
ARC_CENTER = (0.0, OUTER_R)


def _polar(radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return (radius * math.cos(angle), radius * math.sin(angle))


def _horn_center(sign: float) -> tuple[float, float]:
    dx, dy = _polar(MID_R, 270.0 + sign * HALF_ANGLE_DEG)
    return (ARC_CENTER[0] + dx, ARC_CENTER[1] + dy)


def _annular_sector_com_radius() -> float:
    """Radial COM of a concentric annular sector, measured from the arc center."""
    alpha = math.radians(HALF_ANGLE_DEG)
    return (
        (2.0 / 3.0)
        * (OUTER_R**3 - INNER_R**3)
        / (OUTER_R**2 - INNER_R**2)
        * (math.sin(alpha) / alpha)
    )


def _assert_parameters() -> None:
    assert OUTER_R > INNER_R > 0
    assert math.isclose(HORN_R, (OUTER_R - INNER_R) / 2.0)
    assert 16.0 <= THICKNESS <= 24.0
    assert 40.0 <= HALF_ANGLE_DEG <= 58.0
    assert PAD_DEPTH >= 0.5 and PAD_RADIUS <= HORN_R
    com_r = _annular_sector_com_radius()
    # Stable rocker: COM below the outer-arc center of curvature.
    assert 0.0 < com_r < OUTER_R


def build_rocker():
    _assert_parameters()
    a1 = 270.0 - HALF_ANGLE_DEG
    a2 = 270.0 + HALF_ANGLE_DEG
    # Chord of the clip triangle must sit outside the outer arc, else it
    # shaves the rocking belly into a flat. Need reach * cos(half-angle) > OUTER_R.
    reach = OUTER_R / math.cos(math.radians(HALF_ANGLE_DEG)) + 8.0
    p1 = (ARC_CENTER[0] + _polar(reach, a1)[0], ARC_CENTER[1] + _polar(reach, a1)[1])
    p2 = (ARC_CENTER[0] + _polar(reach, a2)[0], ARC_CENTER[1] + _polar(reach, a2)[1])
    left = _horn_center(-1.0)
    right = _horn_center(1.0)

    with BuildSketch() as profile:
        with Locations(ARC_CENTER):
            Circle(OUTER_R)
            Circle(INNER_R, mode=Mode.SUBTRACT)
        Polygon(*[ARC_CENTER, p1, p2], mode=Mode.INTERSECT)
        with Locations(left):
            Circle(HORN_R)
        with Locations(right):
            Circle(HORN_R)

    body = extrude(profile.sketch, amount=THICKNESS)
    pad_h = PAD_DEPTH + 1.0
    pads = []
    for hx, hy in (left, right):
        pads.append(
            Pos(hx, hy, THICKNESS - PAD_DEPTH)
            * Cylinder(
                PAD_RADIUS,
                pad_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
    body = body - pads
    solids = body.solids()
    assert len(solids) == 1
    solid = solids[0]
    assert solid.volume > 0.0
    bbox = solid.bounding_box()
    assert abs(bbox.min.Z) < 1e-6
    # Belly of the outer cylinder must reach the print-Y origin (desk contact).
    assert bbox.min.Y < 0.5
    return solid


def gen_step():
    rocker = build_rocker()
    rocker.color = srgb("#7C838C")
    return label_shape(rocker, "crescent_rocker")
