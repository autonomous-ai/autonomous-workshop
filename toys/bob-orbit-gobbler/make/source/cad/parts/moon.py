"""Thick moon token with crescent relief and unequal-lug round bayonet cavity."""

from build123d import Pos
from cadgen.assembly import label_shape
from features.common import box_from, cylinder_from
from features.profiles import polar_sector
import params as p


def build_moon():
    moon = cylinder_from(p.MOON_R, p.MOON_T)
    cavity = cylinder_from(p.MOON_PILOT_CLEAR_D / 2.0, p.MOON_PILOT_DEPTH)
    short_slot = box_from(
        0.0, -p.MOON_LUG_W / 2.0 - p.RUN_CLEAR, 0.0,
        p.MOON_PILOT_CLEAR_D / 2.0 + p.MOON_LUG_L_SHORT + p.RUN_CLEAR,
        p.MOON_LUG_W + 2.0 * p.RUN_CLEAR,
        p.MOON_PILOT_DEPTH,
    )
    long_slot = box_from(
        -p.MOON_PILOT_CLEAR_D / 2.0 - p.MOON_LUG_L_LONG - p.RUN_CLEAR,
        -p.MOON_LUG_W / 2.0 - p.RUN_CLEAR,
        0.0,
        p.MOON_PILOT_CLEAR_D / 2.0 + p.MOON_LUG_L_LONG + p.RUN_CLEAR,
        p.MOON_LUG_W + 2.0 * p.RUN_CLEAR,
        p.MOON_PILOT_DEPTH,
    )
    # A bounded curved engraving reads as a crescent without intersecting the
    # token perimeter.  The previous offset circular recess crossed the rim
    # and created two vanishing horns.
    crescent = polar_sector(6.0, 9.0, 110.0, 250.0, p.MIN_WALL, samples=32)
    crescent = Pos(0.0, 0.0, p.MOON_T - p.MIN_WALL) * crescent
    return label_shape(moon - cavity - short_slot - long_slot - crescent, "moon")
