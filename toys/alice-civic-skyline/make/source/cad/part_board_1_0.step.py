"""Printable board quadrant 1,0; flat at Z=0."""
from city_lib import build_panel
PRINTABLE = True
def gen_step():
    part=build_panel(1,0)
    part.label="board_1_0"
    return part
