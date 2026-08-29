"""Functional assembled Lantern Menagerie in deployed projection stance."""

from lantern_menagerie_lib import make_assembly

PRINTABLE = False


def gen_step():
    return make_assembly(reel_angle_deg=0.0, stand_deployed=True)

