"""Product and isolated validation-station placement."""

from build123d import Pos, Rot
from cadgen.assembly import AssemblyHelper

from params import *
from parts.reel import make_shadow_reel
from parts.shells import make_front_shell, make_rear_shell
from parts.stand import make_kickstand


def make_assembly(
    reel_angle_deg: float = 0.0,
    stand_deployed: bool = True,
):
    asm = AssemblyHelper("lantern_menagerie")
    upright = Pos(0, 0, -FRAME_BOTTOM_Y) * Rot(90, 0, 0)
    asm.add(upright * make_front_shell(), "front_shell")
    wheel = Pos(0, 0, REEL_Z) * Rot(0, 0, -reel_angle_deg) * make_shadow_reel()
    asm.add(upright * wheel, "shadow_reel")
    rear = Pos(0, 0, REAR_INNER_Z) * make_rear_shell()
    asm.add(upright * rear, "rear_shell")
    stand = make_kickstand()
    if stand_deployed:
        stand = Pos(0, STAND_HINGE_Y, STAND_HINGE_Z) * Rot(STAND_DEPLOY_DEG, 0, 0) * Pos(0, -TRUNNION_Y, -3.0) * stand
    else:
        stand = Pos(0, STAND_HINGE_Y - TRUNNION_Y, STAND_HINGE_Z - 3.0) * stand
    asm.add(upright * stand, "kickstand")
    return asm.build()
