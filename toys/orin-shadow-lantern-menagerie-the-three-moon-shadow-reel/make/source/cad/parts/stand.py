"""Captured U-stand builder."""

from build123d import Align, Box, BuildSketch, Plane, Polygon, Pos, extrude

from features.common import fuse_all, rounded_plate
from params import *


def make_kickstand():
    arm_length = STAND_L - TRUNNION_Y
    arm_center_y = TRUNNION_Y + arm_length / 2
    left_arm = Pos(-STAND_W / 2 + STAND_ARM_W / 2, arm_center_y, STAND_BODY_Z) * rounded_plate(STAND_ARM_W, arm_length, 2.0, STAND_BODY_T)
    right_arm = Pos(STAND_W / 2 - STAND_ARM_W / 2, arm_center_y, STAND_BODY_Z) * rounded_plate(STAND_ARM_W, arm_length, 2.0, STAND_BODY_T)
    foot = Pos(0, STAND_L - STAND_BAR_H / 2, STAND_BODY_Z) * rounded_plate(STAND_W, STAND_BAR_H, 3.0, STAND_BODY_T)
    left_lug = Pos(-STAND_W / 2 + STAND_ARM_W / 2, TRUNNION_Y, 0) * Box(STAND_ARM_W, 8.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    right_lug = Pos(STAND_W / 2 - STAND_ARM_W / 2, TRUNNION_Y, 0) * Box(STAND_ARM_W, 8.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    stand = fuse_all([left_arm, right_arm, foot, left_lug, right_lug])
    stand = stand.fuse(*(Pos(x, TRUNNION_Y, 4.5) * Box(6.0, 3.0, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN)) for x in (-40.0, 40.0)))
    pin_profile = [
        (TRUNNION_Y - 3.0, 1.7), (TRUNNION_Y - 1.3, 0.0),
        (TRUNNION_Y + 1.3, 0.0), (TRUNNION_Y + 3.0, 1.7),
        (TRUNNION_Y + 3.0, 4.3), (TRUNNION_Y + 1.3, 6.0),
        (TRUNNION_Y - 1.3, 6.0), (TRUNNION_Y - 3.0, 4.3),
    ]
    with BuildSketch(Plane.YZ.offset(-STAND_W / 2 + 2.0)) as left_sketch:
        Polygon(*pin_profile)
    left_pin = extrude(left_sketch.sketch, amount=-TRUNNION_LEN)
    with BuildSketch(Plane.YZ.offset(STAND_W / 2 - 2.0)) as right_sketch:
        Polygon(*pin_profile)
    right_pin = extrude(right_sketch.sketch, amount=TRUNNION_LEN)
    stand = stand.fuse(left_pin, right_pin)
    stand.label = "kickstand"
    assert len(stand.solids()) == 1
    return stand
