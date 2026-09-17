from build123d import Align, Box, Pos
from features.forms import color_part, xz_prism
from params import black_rgb


def build():
    profile = [(-7.0, -5.0), (7.0, -5.0), (8.0, 0.0), (5.0, 6.0), (-5.0, 6.0), (-8.0, 0.0)]
    barrel = Pos(0, 24.5, 0) * xz_prism(profile, 49.0)
    peg = Pos(0, -6.0, 0) * Box(8.0, 12.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    top_rail = Pos(0, 27.0, 5.7) * Box(4.0, 44.0, 2.3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return color_part(
        barrel + peg + top_rail,
        "cannon_body",
        black_rgb,
    )
