"""Review-only crop of the fixed tooth and governing +75-degree notch state."""

from view_common import PROJECT

from build123d import Align, Box, Pos, Rot
from cadgen import srgb
from cadgen.assembly import AssemblyHelper
from moonwake_garden_lib import ROTOR_SEAT_Z, build_rear_chassis, build_sector_rotor

PRINTABLE = False


def gen_step():
    crop = Pos(26, -26, -0.1) * Box(20, 24, 4.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rear = build_rear_chassis() & crop
    rotor = (Pos(0, 0, ROTOR_SEAT_Z) * Rot(0, 0, -120) * build_sector_rotor()) & crop
    asm = AssemblyHelper("moonwake_garden_detent_close")
    asm.add(rear, "rear_detent_crop", color=srgb("#2F4052"))
    asm.add(rotor, "rotor_plus75_notch_crop", color=srgb("#B08A55"))
    return asm.build()
