"""Non-printing motion proxy with only the elastic detent tooth suppressed."""

from build123d import Align, Cylinder, Pos
from cadgen.assembly import AssemblyHelper

from moonwake_garden_lib import (
    DETENT_FREE_ANGLE_DEG,
    DETENT_TOOTH_CENTER_R,
    FRONT_SEAT_Z,
    ROTOR_SEAT_Z,
    build_front_garden_mask,
    build_rear_chassis,
    build_sector_rotor,
    _polar_location,
)

PRINTABLE = False


def gen_step():
    tooth_suppression = _polar_location(DETENT_TOOTH_CENTER_R, DETENT_FREE_ANGLE_DEG, -0.1) * Cylinder(
        0.75,
        FRONT_SEAT_Z + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    rear_proxy = build_rear_chassis() - tooth_suppression
    asm = AssemblyHelper("moonwake_garden_motion_proxy")
    asm.add(rear_proxy, "rear_chassis:flexed_tooth_proxy")
    asm.add(Pos(0, 0, ROTOR_SEAT_Z) * build_sector_rotor(), "sector_rotor", "cassiopeia_pose")
    asm.add(Pos(0, 0, FRONT_SEAT_Z) * build_front_garden_mask(), "front_garden_mask")
    return asm.build()
