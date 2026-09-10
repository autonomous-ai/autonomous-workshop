"""Printable rook; flat bed datum Z=0."""
from city_lib import build_rook
PRINTABLE = True
def gen_step():
    part=build_rook()
    part.label="rook"
    return part
