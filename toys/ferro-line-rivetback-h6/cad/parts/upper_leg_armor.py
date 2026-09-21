from build123d import Align, Box, Pos
from features.forms import color_part, xz_prism
from params import yellow_rgb, small_peg, small_peg_length, upper_dz, upper_dx, upper_height


def build():
    z_line = lambda x: (upper_dz / upper_dx) * x
    x0, x1 = 4.0, 21.0
    lower0, lower1 = z_line(x0) + upper_height / 2 + 0.5, z_line(x1) + upper_height / 2 + 0.5
    shell = xz_prism([(x0, lower0), (x1, lower1), (x1, lower1 + 3.0), (x0, lower0 + 3.0)], 12.0)
    pegs = [Pos(x, -4.0, z_line(x) + upper_height / 2 + 0.25) * Box(small_peg, small_peg, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (7.5, 13.5)]
    return color_part(shell + pegs, "upper_leg_armor", yellow_rgb)
