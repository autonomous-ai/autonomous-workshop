"""Printable footboard; DESIGN.md r2 stance."""
from parts.footboard import build
from features.common import printed, colored
from params import COLORS
PRINTABLE = True

def gen_step():
    return colored(printed(build(), rotation=(0,0,0)),COLORS['charcoal'],'footboard')
