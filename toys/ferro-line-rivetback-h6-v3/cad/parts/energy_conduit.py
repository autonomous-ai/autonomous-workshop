from build123d import Box, Pos
from features.forms import color_part, flat_crescent
from params import cable_rgb


def build():
    # The thicker radial band keeps both clipped ends above the minimum FDM
    # wall while preserving the pale cable arc seen in the reference.
    crescent = flat_crescent(18.0, 12.5, 3.5)
    return color_part(
        crescent,
        "energy_conduit",
        cable_rgb,
    )
