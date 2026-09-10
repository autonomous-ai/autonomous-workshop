"""Printable bishop; flat bed datum Z=0."""
from city_lib import build_bishop
PRINTABLE = True
def gen_step():
    part=build_bishop()
    part.label="bishop"
    return part
