"""Printable bar riser; DESIGN.md r2 stance."""
from parts.bar_riser import build
from features.common import printed, colored
from params import COLORS
PRINTABLE = True

def gen_step():
    return colored(printed(build(), rotation=(90,0,0)),COLORS['gray'],'bar_riser')
