from build123d import Align, Box, Polygon, Pos, extrude, make_face
from features.forms import color_part, xz_prism
from params import *


def build():
    profile = [(0, 0), (foot_length - 2.0, 0), (foot_length, 2.0), (foot_length - 1.5, 5.0), (7.0, foot_height), (0, 8.0)]
    plan = make_face(Polygon(
        (0, -foot_width / 2),
        (6.0, -foot_width / 2),
        (foot_length, -2.5),
        (foot_length, 2.5),
        (6.0, foot_width / 2),
        (0, foot_width / 2),
    ))
    body = xz_prism(profile, foot_width) & extrude(plan, amount=foot_height)
    # Keep the heel reinforcement at or ahead of the foot datum so it meets,
    # but does not overlap, the lower beam's reinforced endpoint.
    heel = Pos(3.5, 0, 2.5) * Box(7.0, foot_width, 5.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # Rear-opening keyed receiver aligned to the beam's outward-growing peg.
    socket = Pos(1.25, -1.0, 5.25) * Box(5.5, 7.5, 3.5, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # A full-height center trench forms two broad printable toe prongs; the
    # widened nose retains at least 1.4 mm per side at the tip.
    toe_split = Pos(13.5, 0, 5.0) * Box(
        9.0, 2.2, 12.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    return color_part((body + heel) - socket - toe_split, "foot", black_rgb)
