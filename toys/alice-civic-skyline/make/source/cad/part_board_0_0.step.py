"""Printable board quadrant 0,0; flat at Z=0."""
from city_lib import build_panel
PRINTABLE = True
def gen_step():
    part=build_panel(0,0)
    part.label="board_0_0"
    return part
