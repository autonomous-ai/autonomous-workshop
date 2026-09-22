"""Printable occurrence sun_orange; flat on the bed at Z0."""
from build123d import Location

from parts.body import sun_body

PRINTABLE = True


def gen_step():
    result = sun_body().moved(Location())
    result.label = "sun_orange"
    result.color = sun_body().color
    return result
