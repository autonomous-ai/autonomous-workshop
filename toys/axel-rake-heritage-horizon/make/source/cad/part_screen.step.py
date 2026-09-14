"""Printable screen; DESIGN.md r2 stance."""
from parts.screen import build, print_shape
from features.common import printed, colored
from params import COLORS
PRINTABLE = True

def gen_step():
    return colored(print_shape(),COLORS['screen'],'screen')
