"""Review-only crop of the home grip patch beneath the fixed polar portal."""

from view_common import PROJECT

from build123d import Align, Box, Pos
from cadgen import srgb
from cadgen.assembly import AssemblyHelper
from moonwake_garden_lib import FRONT_SEAT_Z, ROTOR_SEAT_Z, build_front_garden_mask, build_sector_rotor

PRINTABLE = False


def gen_step():
    crop = Pos(33.5, 0, 1.9) * Box(11, 20, 4.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rotor = (Pos(0, 0, ROTOR_SEAT_Z) * build_sector_rotor()) & crop
    front = (Pos(0, 0, FRONT_SEAT_Z) * build_front_garden_mask()) & crop
    asm = AssemblyHelper("moonwake_garden_portal_close")
    asm.add(rotor, "home_grip_crop", color=srgb("#B08A55"))
    asm.add(front, "front_portal_crop", color=srgb("#536B5B"))
    return asm.build()
