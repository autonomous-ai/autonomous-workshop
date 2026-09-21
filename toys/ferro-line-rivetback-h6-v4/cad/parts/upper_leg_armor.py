from build123d import Align, Box, Pos
from features.forms import color_part, xz_prism
from params import yellow_rgb, small_peg, small_peg_length, upper_dz, upper_dx, upper_height


def build():
    z_line = lambda x: (upper_dz / upper_dx) * x
    x0, x1 = 5.0, 27.0
    inner = lambda x: z_line(x) + upper_height / 2 + 0.8
    outer = lambda x: inner(x) + 3.4
    bevel = 1.4
    shell = xz_prism([
        (x0 + bevel, inner(x0 + bevel)),
        (x1 - bevel, inner(x1 - bevel)),
        (x1, (inner(x1) + outer(x1)) / 2),
        (x1 - bevel, outer(x1 - bevel)),
        (x0 + bevel, outer(x0 + bevel)),
        (x0, (inner(x0) + outer(x0)) / 2),
    ], 12.0)
    slot = xz_prism([
        (10.0, outer(10.0) - 2.5), (22.0, outer(22.0) - 2.5),
        (22.0, outer(22.0) - 1.3), (10.0, outer(10.0) - 1.3),
    ], 14.0)
    pegs = [Pos(x, -4.0, z_line(x) + upper_height / 2 + 0.25) * Box(small_peg, small_peg, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (9.0, 19.0)]
    return color_part((shell + pegs) - slot, "upper_leg_armor", yellow_rgb)
