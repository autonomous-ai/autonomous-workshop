"""Printable king; flat bed datum Z=0."""
from city_lib import build_king
PRINTABLE = True
def gen_step():
    part=build_king()
    part.label="king"
    return part
