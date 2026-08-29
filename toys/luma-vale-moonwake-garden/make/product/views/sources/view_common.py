"""Product-derived review assemblies for Moonwake Garden image evidence."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2] / "cad/moonwake_garden"
sys.path.insert(0, str(PROJECT))

from build123d import Pos, Rot  # noqa: E402
from cadgen import srgb  # noqa: E402
from cadgen.assembly import AssemblyHelper  # noqa: E402
from moonwake_garden_lib import (  # noqa: E402
    FRONT_SEAT_Z,
    ROTOR_SEAT_Z,
    build_front_garden_mask,
    build_rear_chassis,
    build_sector_rotor,
)


def state_assembly(name: str, pose_deg: float):
    asm = AssemblyHelper(f"moonwake_garden_{name}")
    asm.add(build_rear_chassis(), "rear_chassis", color=srgb("#2F4052"))
    asm.add(Pos(0, 0, ROTOR_SEAT_Z) * Rot(0, 0, pose_deg) * build_sector_rotor(), "sector_rotor", name, color=srgb("#B08A55"))
    asm.add(Pos(0, 0, FRONT_SEAT_Z) * build_front_garden_mask(), "front_garden_mask", color=srgb("#536B5B"))
    return asm.build()


def exploded_assembly():
    asm = AssemblyHelper("moonwake_garden_exploded")
    asm.add(build_rear_chassis(), "rear_chassis", color=srgb("#2F4052"))
    asm.add(Pos(0, 0, 8.0) * build_sector_rotor(), "sector_rotor", "home", color=srgb("#B08A55"))
    asm.add(Pos(0, 0, 12.0) * build_front_garden_mask(), "front_garden_mask", color=srgb("#536B5B"))
    return asm.build()
