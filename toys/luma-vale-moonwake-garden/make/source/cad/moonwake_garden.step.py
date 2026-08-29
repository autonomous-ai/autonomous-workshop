"""Labeled review assembly at the Cassiopeia detent; not a print target."""

from build123d import Pos, Rot
from cadgen.assembly import AssemblyHelper

from moonwake_garden_lib import (
    FRONT_SEAT_Z,
    ROTOR_SEAT_Z,
    ROTOR_STATES_DEG,
    build_front_garden_mask,
    build_rear_chassis,
    build_sector_rotor,
)

PRINTABLE = False


def gen_step():
    asm = AssemblyHelper("moonwake_garden")
    asm.add(build_rear_chassis(), "rear_chassis")
    asm.add(
        Pos(0, 0, ROTOR_SEAT_Z) * Rot(0, 0, ROTOR_STATES_DEG["cassiopeia"]) * build_sector_rotor(),
        "sector_rotor",
        "cassiopeia_pose",
    )
    asm.add(
        Pos(0, 0, FRONT_SEAT_Z) * build_front_garden_mask(),
        "front_garden_mask",
    )
    return asm.build()
