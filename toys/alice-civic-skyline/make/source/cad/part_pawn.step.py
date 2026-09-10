"""Printable pawn; flat bed datum Z=0."""
from city_lib import build_pawn
PRINTABLE = True
def gen_step():
    part=build_pawn()
    part.label="pawn"
    return part
