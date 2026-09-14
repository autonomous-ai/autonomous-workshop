"""Printable tank_cover; isolated component entry."""
from parts.tank_cover import build
from features.common import printed, colored
from params import COLORS
PRINTABLE = True

def gen_step():
    return colored(printed(build(),(0,0,0)),COLORS["teal"],"tank_cover")
