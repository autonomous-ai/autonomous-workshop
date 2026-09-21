"""Printable occurrence single_11_beige; flat on the bed at Z0."""
from build123d import Location

from parts.counter import counter

PRINTABLE = True


def gen_step():
    result = counter("single").moved(Location())
    result.label = "single_11_beige"
    result.color = counter("single").color
    return result
