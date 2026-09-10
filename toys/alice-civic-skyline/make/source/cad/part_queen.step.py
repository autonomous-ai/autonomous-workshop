"""Printable queen; flat bed datum Z=0."""
from city_lib import build_queen
PRINTABLE = True
def gen_step():
    part=build_queen()
    part.label="queen"
    return part
