"""Screw-removable roof over band path, pivot and overlapping tail tunnel.

This early-proof cover establishes material shielding and service access. Whole
apron/panel integration and finger-access assessment remain root dependencies.
"""
from build123d import Align, Axis, Box, Cone, Cylinder, Plane, Polygon, Pos, extrude
import params as p


def guard(side="left"):
    outline = p.FLIPPER_RIGHT_ROOF_OUTLINE if side == "right" else p.FLIPPER_GUARD_ROOF_OUTLINE
    mounts = p.FLIPPER_RIGHT_GUARD_MOUNTS if side == "right" else p.FLIPPER_GUARD_MOUNTS
    shape = Pos(0, 0, p.FLIPPER_GUARD_ROOF_Z) * extrude(
        Polygon(*outline, align=None), amount=p.FLIPPER_GUARD_ROOF_T)
    height = p.FLIPPER_GUARD_ROOF_Z-p.FLIPPER_GUARD_BASE_T
    for point in mounts:
        # Carry each complete annular column through the roof. A column that
        # ends at its underside leaves clipped crescents at the outline and
        # starts unsupported when the roof is printed against the bed.
        shape += Pos(*point, p.FLIPPER_GUARD_BASE_T) * Cylinder(
            p.FLIPPER_GUARD_MOUNT_R, height+p.FLIPPER_GUARD_ROOF_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
    x0, x1 = p.FLIPPER_RIGHT_WALL_X if side == "right" else p.FLIPPER_GUARD_WALL_X
    y0, y1 = p.FLIPPER_RIGHT_WALL_Y if side == "right" else p.FLIPPER_GUARD_WALL_Y
    shape += Pos(x0, y0, p.FLIPPER_GUARD_BASE_T) * Box(
        x1-x0, y1-y0, height, align=(Align.MIN, Align.MIN, Align.MIN))
    for point in mounts:
        shape -= Pos(*point, p.FLIPPER_GUARD_BASE_T) * Cylinder(
            p.M4_BORE/2, height+p.FLIPPER_GUARD_ROOF_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        # Tool-access counterbore reaches a low structural land. M4x16 head
        # top is Z6, tip Z-10, with the same thin nut at Z-8.2..-6.
        shape -= Pos(*point, p.FLIPPER_GUARD_SCREW_HEAD_Z) * Cylinder(
            p.CSK_RECESS_D/2,
            p.FLIPPER_GUARD_ROOF_Z+p.FLIPPER_GUARD_ROOF_T-p.FLIPPER_GUARD_SCREW_HEAD_Z,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        shape -= Pos(*point, p.FLIPPER_GUARD_SCREW_HEAD_Z-p.CSK_HEAD_MAX_H) * Cone(
            p.M4_BORE/2, p.CSK_RECESS_D/2, p.CSK_HEAD_MAX_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
    if side == "right":
        shape = shape.mirror(Plane.YZ)
    assert len(shape.solids()) == 1
    shape.label = f"flipper_{side}_guard"
    return shape


def print_guard(side="left"):
    return Pos(0, 0, p.FLIPPER_GUARD_ROOF_Z+p.FLIPPER_GUARD_ROOF_T) * guard(side).rotate(Axis.X, 180)
