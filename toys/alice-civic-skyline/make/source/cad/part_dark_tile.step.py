"""Printable dark_tile; flat bed datum Z=0."""
from city_lib import build_dark_tile
PRINTABLE = True
def gen_step():
    part=build_dark_tile()
    part.label="dark_tile"
    return part
