from build123d import Align, Box, Pos
from features.forms import color_part, xz_prism
from params import yellow_rgb, small_peg, small_peg_length, upper_dz, upper_dx, upper_height


def build():
    z_line = lambda x: (upper_dz / upper_dx) * x
    x0, x1 = 4.0, 21.0
    inner = lambda x: z_line(x) + upper_height / 2 + 0.5
    outer = lambda x: inner(x) + 3.2
    bevel = 1.4
    shell = xz_prism([
        (x0 + bevel, inner(x0 + bevel)),
        (x1 - bevel, inner(x1 - bevel)),
        (x1, (inner(x1) + outer(x1)) / 2),
        (x1 - bevel, outer(x1 - bevel)),
        (x0 + bevel, outer(x0 + bevel)),
        (x0, (inner(x0) + outer(x0)) / 2),
    ], 12.0)
    crest_x0, crest_x1 = x0 + 3.2, x1 - 3.2
    crest = xz_prism([
        (crest_x0 + 1.0, outer(crest_x0 + 1.0) - 0.2),
        (crest_x1 - 1.0, outer(crest_x1 - 1.0) - 0.2),
        (crest_x1, outer(crest_x1) + 0.55),
        (crest_x1 - 1.0, outer(crest_x1 - 1.0) + 1.4),
        (crest_x0 + 1.0, outer(crest_x0 + 1.0) + 1.4),
        (crest_x0, outer(crest_x0) + 0.55),
    ], 12.0)
    pegs = [Pos(x, -4.0, z_line(x) + upper_height / 2 + 0.25) * Box(small_peg, small_peg, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (7.5, 13.5)]
    return color_part(shell + crest + pegs, "upper_leg_armor", yellow_rgb)
