from build123d import Align, Box, Cylinder, Pos, Rot
from features.forms import color_part
from params import *


def build():
    body_width = 18.0
    body = Pos(yoke_length / 2, 0, 0) * Box(
        yoke_length, body_width, yoke_height,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    joint_center_x = yoke_length - tenon_length / 2
    root_peg = Pos(-hip_peg_length / 2, 0, 0) * Box(hip_peg_length, hip_peg * 0.76, hip_peg, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    mortise = Pos(yoke_length - tenon_length / 2, 0, 0) * Box(tenon_length + 0.5, 13.5, tenon_socket_height, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    axle_hole = Pos(joint_center_x, 0, 0) * Rot(90, 0, 0) * Cylinder(
        pin_hole / 2, body_width + 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    return color_part((body + root_peg) - mortise - axle_hole, "hip_yoke", black_rgb)
