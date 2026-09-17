from math import atan2, degrees, hypot

from build123d import Align, Box, Pos, Rot
from features.forms import color_part, xz_prism
from params import lower_dz, lower_dx, lower_height, small_peg, small_peg_length, yellow_rgb


def build():
    z_line = lambda x: (lower_dz / lower_dx) * x
    # Start beyond the 3 mm proximal reinforcement block after accounting
    # for the shield's normal-direction thickness projection.
    x0, x1 = 4.5, 15.0
    slope = lower_dz / lower_dx
    scale = hypot(1.0, slope)
    normal = (-slope / scale, 1.0 / scale)
    shell_thickness = 3.5
    half = shell_thickness / 2
    # Match the beam's one-millimetre cosmetic-shell stand-off exactly.
    inner_intercept = lower_height / 2 + 1.0 * scale
    center_intercept = inner_intercept + half * scale
    c0 = (x0, z_line(x0) + center_intercept)
    c1 = (x1, z_line(x1) + center_intercept)
    tangent = (1.0 / scale, slope / scale)
    bevel = 1.2
    inner0 = (c0[0] - normal[0] * half, c0[1] - normal[1] * half)
    inner1 = (c1[0] - normal[0] * half, c1[1] - normal[1] * half)
    outer0 = (c0[0] + normal[0] * half, c0[1] + normal[1] * half)
    outer1 = (c1[0] + normal[0] * half, c1[1] + normal[1] * half)
    shell = xz_prism([
        (inner0[0] + tangent[0] * bevel, inner0[1] + tangent[1] * bevel),
        (inner1[0] - tangent[0] * bevel, inner1[1] - tangent[1] * bevel),
        c1,
        (outer1[0] - tangent[0] * bevel, outer1[1] - tangent[1] * bevel),
        (outer0[0] + tangent[0] * bevel, outer0[1] + tangent[1] * bevel),
        c0,
    ], 11.0)
    crest_start = (
        c0[0] + tangent[0] * 3.0 + normal[0] * (half - 0.2),
        c0[1] + tangent[1] * 3.0 + normal[1] * (half - 0.2),
    )
    crest_end = (
        c1[0] - tangent[0] * 3.0 + normal[0] * (half - 0.2),
        c1[1] - tangent[1] * 3.0 + normal[1] * (half - 0.2),
    )
    crest_height = 1.5
    crest = xz_prism([
        crest_start,
        crest_end,
        (crest_end[0] + normal[0] * crest_height, crest_end[1] + normal[1] * crest_height),
        (crest_start[0] + normal[0] * crest_height, crest_start[1] + normal[1] * crest_height),
    ], 11.0)
    mount_y = -3.5
    normal_angle = degrees(atan2(-lower_dz, lower_dx))
    pegs = []
    for x in (6.0, 13.0):
        inner_z = z_line(x) + inner_intercept
        center = (x - normal[0] * 1.05, mount_y, inner_z - normal[1] * 1.05)
        pegs.append(Pos(*center) * Rot(0, normal_angle, 0) * Box(small_peg, small_peg, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)))
    return color_part(shell + crest + pegs, "lower_leg_armor", yellow_rgb)
