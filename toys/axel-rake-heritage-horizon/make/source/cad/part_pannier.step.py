"""Printable pannier; isolated component entry."""
from parts.pannier import build
from features.common import printed, colored
from params import COLORS
PRINTABLE = True

def gen_step():
    return colored(printed(build(),(-90,0,0)),COLORS["brown"],"pannier")
