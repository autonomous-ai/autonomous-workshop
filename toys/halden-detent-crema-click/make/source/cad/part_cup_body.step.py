"""Printable demitasse body. Foot plane on the bed, rim up."""

from build123d import Pos

from crema_click_lib import PLUG_TOP, build_cup_body

PRINTABLE = True


def gen_step():
    return Pos(0, 0, -PLUG_TOP) * build_cup_body()
