from build123d import Align, Box, Cylinder, Pos, Rot
from features.forms import clipped_prism, color_part
from params import *


def build():
    lower = clipped_prism(hub_width, hub_depth, hub_height, 5.0)
    # Front-facing round motor housing gives the compact insect-head profile.
    face_drum = Pos(0, hub_depth / 2 - 1.0, hub_height / 2) * Rot(
        -90, 0, 0
    ) * Cylinder(7.2, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    key = Pos(0, -hub_depth / 2 + 4.0, -3.0) * Box(10.0, 8.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # Run the receiver through the print axis so it has no unsupported roof
    # when this part is printed on its rear face.
    cannon_socket = Pos(0, 2.5, hub_height / 2) * Box(
        8.5,
        29.0,
        6.5,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return color_part((lower + face_drum + key) - cannon_socket, "hub_pedestal", black_rgb)
