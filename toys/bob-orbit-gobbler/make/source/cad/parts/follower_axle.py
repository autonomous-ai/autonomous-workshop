"""Vertical-print follower axle with integral head and snap collar."""

from cadgen.assembly import label_shape
from features.common import box_from, cylinder_from
import params as p


def build_follower_axle():
    head_t = p.RETAINER_SOLID
    axle = cylinder_from(p.FOLLOWER_D / 2.0, head_t)
    short_lug = box_from(
        0.0, -p.MOON_LUG_W / 2.0, 0.0,
        p.FOLLOWER_D / 2.0 + p.MOON_LUG_L_SHORT, p.MOON_LUG_W, head_t,
    )
    long_lug = box_from(
        -p.FOLLOWER_D / 2.0 - p.MOON_LUG_L_LONG, -p.MOON_LUG_W / 2.0, 0.0,
        p.FOLLOWER_D / 2.0 + p.MOON_LUG_L_LONG, p.MOON_LUG_W, head_t,
    )
    shaft = cylinder_from(p.FOLLOWER_AXLE_D / 2.0, p.FOLLOWER_AXLE_L, z=head_t)
    flat_cut = box_from(
        p.FOLLOWER_SHAFT_FLAT, -p.FOLLOWER_AXLE_D, head_t,
        p.FOLLOWER_AXLE_D, 2.0 * p.FOLLOWER_AXLE_D, p.FOLLOWER_AXLE_L,
    )
    axle = axle + short_lug + long_lug + (shaft - flat_cut)
    axle = axle + cylinder_from(p.FOLLOWER_D / 2.0, p.RETAINER_SOLID, z=head_t + p.FOLLOWER_AXLE_L)
    return label_shape(axle, "follower_axle")
