from math import atan2, degrees, hypot

from build123d import Align, Box, Pos, Rot
from features.forms import color_part, keyed_box_peg, xz_prism
from params import *


def build():
    profile = [(0, -lower_height / 2), (lower_dx, lower_dz - lower_height / 2), (lower_dx, lower_dz + lower_height / 2), (0, lower_height / 2)]
    body = xz_prism(profile, lower_width)
    proximal_housing = xz_prism([
        (0.0, -6.0), (1.8, -6.0), (3.2, -3.0),
        (3.2, 3.0), (1.8, 6.0), (0.0, 6.0),
    ], lower_width)
    distal_housing = Pos(lower_dx, 0, lower_dz) * xz_prism([
        (-6.0, -3.0), (-3.5, -6.0), (0.0, -6.0),
        (0.0, 6.0), (-3.5, 6.0), (-6.0, 3.0),
    ], lower_width)
    tenon = Pos(-tenon_length, 0, 1.0) * keyed_box_peg(tenon_length + 1.5, lower_width, 5.5)
    foot_peg = Pos(lower_dx - 1.5, -1.0, lower_dz) * keyed_box_peg(5.5, 7.0, 3.0)
    slope = lower_dz / lower_dx
    scale = hypot(1.0, slope)
    normal = (-slope / scale, 1.0 / scale)
    normal_angle = degrees(atan2(-lower_dz, lower_dx))
    armor_slots = []
    for x in (6.0, 13.0):
        # Hold the cosmetic shield one millimetre off the structural beam.
        # The paired slot/peg centres use this same datum, so the extra air
        # gap removes coplanar-kernel clashes without weakening the mount.
        inner_intercept = lower_height / 2 + 1.0 * scale
        inner_z = slope * x + inner_intercept
        center = (x - normal[0] * 1.05, 0, inner_z - normal[1] * 1.05)
        armor_slots.append(Pos(*center) * Rot(0, normal_angle, 0) * Box(small_socket, lower_width + 2.0, small_peg_length + 0.6, align=(Align.CENTER, Align.CENTER, Align.CENTER)))
    return color_part(
        (body + proximal_housing + distal_housing + tenon + foot_peg)
        - armor_slots,
        "lower_leg_beam",
        black_rgb,
    )
