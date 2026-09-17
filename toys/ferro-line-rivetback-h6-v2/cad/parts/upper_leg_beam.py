from build123d import Align, Box, Pos
from features.forms import color_part, keyed_box_peg, xz_prism
from params import *


def build():
    beam_width = 13.0
    profile = [(0, -upper_height / 2), (upper_dx, upper_dz - upper_height / 2), (upper_dx, upper_dz + upper_height / 2), (0, upper_height / 2)]
    body = xz_prism(profile, beam_width)
    proximal_housing = xz_prism([
        (0.0, -6.0), (1.8, -6.0), (3.2, -3.0),
        (3.2, 3.0), (1.8, 6.0), (0.0, 6.0),
    ], beam_width)
    distal_housing = Pos(upper_dx, 0, upper_dz) * xz_prism([
        (-7.0, -3.0), (-4.0, -6.0), (0.0, -6.0),
        (0.0, 6.0), (-4.0, 6.0), (-7.0, 3.0),
    ], beam_width)
    tenon = Pos(-tenon_length, 0, 0) * keyed_box_peg(tenon_length + 1.5, beam_width, tenon_height)
    mortise_x = upper_dx - tenon_length / 2
    mortise_z = (upper_dz / upper_dx) * mortise_x
    distal_mortise = Pos(mortise_x, 0, mortise_z) * Box(tenon_length + 0.5, lower_width + 0.5, 6.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    armor_slots = [Pos(x, 0, 4.2 + (upper_dz / upper_dx) * x) * Box(small_socket, beam_width + 2.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (7.5, 13.5)]
    return color_part(
        (body + proximal_housing + distal_housing + tenon)
        - distal_mortise
        - armor_slots,
        "upper_leg_beam",
        black_rgb,
    )
