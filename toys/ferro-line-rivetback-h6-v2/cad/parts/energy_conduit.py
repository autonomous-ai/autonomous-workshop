from build123d import Box, Pos
from features.forms import color_part, flat_crescent
from params import cyan_rgb


def build():
    # A broad 5.5 mm radial band reads as a protected conduit rather than a
    # dangling claw, while the flat print datum stays supportless.
    crescent = flat_crescent(14.8, 8.0, 5.0)
    keyed_ends = Pos(8.5, 0, 2.0) * Box(6.0, 5.0, 4.0) + Pos(3.0, 9.5, 2.0) * Box(6.0, 5.0, 4.0)
    return color_part(
        crescent + keyed_ends,
        "energy_conduit",
        cyan_rgb,
    )
