"""Printable knight; flat bed datum Z=0."""
from city_lib import build_knight
PRINTABLE = True
def gen_step():
    part=build_knight()
    part.label="knight"
    return part
