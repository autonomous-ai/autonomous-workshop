"""Non-printing seating proxy with snap heads compressed to stem diameter."""

from build123d import Align, Cylinder, Pos
from cadgen.assembly import AssemblyHelper

from moonwake_garden_lib import (
    FRONT_SEAT_Z,
    ROTOR_SEAT_Z,
    SNAP_HEAD_D,
    SNAP_STEM_D,
    SNAP_XY,
    build_front_garden_mask,
    build_rear_chassis,
    build_sector_rotor,
)

PRINTABLE = False
Z_MIN_ALIGN = (Align.CENTER, Align.CENTER, Align.MIN)


def gen_step():
    rear_proxy = build_rear_chassis()
    for x, y in SNAP_XY:
        rear_proxy -= Pos(x, y, 4.69) * Cylinder(SNAP_HEAD_D / 2.0 + 0.1, 1.42, align=Z_MIN_ALIGN)
        rear_proxy += Pos(x, y, 4.69) * Cylinder(SNAP_STEM_D / 2.0, 1.31, align=Z_MIN_ALIGN)
    asm = AssemblyHelper("moonwake_garden_snap_proxy")
    asm.add(rear_proxy, "rear_chassis:compressed_heads_proxy")
    asm.add(Pos(0, 0, ROTOR_SEAT_Z) * build_sector_rotor(), "sector_rotor", "cassiopeia_pose")
    asm.add(Pos(0, 0, FRONT_SEAT_Z) * build_front_garden_mask(), "front_garden_mask")
    return asm.build()
