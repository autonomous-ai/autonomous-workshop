from build123d import Align, Box, Pos
from features.forms import color_part
from params import *


def build():
    body_width = 16.0
    body = Pos(yoke_length / 2, 0, 0) * Box(yoke_length, body_width, yoke_height, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    root_peg = Pos(-hip_peg_length / 2, 0, 0) * Box(hip_peg_length, hip_peg * 0.76, hip_peg, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    mortise = Pos(yoke_length - tenon_length / 2, 0, 0) * Box(tenon_length + 0.5, 13.5, tenon_socket_height, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return color_part((body + root_peg) - mortise, "hip_yoke", black_rgb)
