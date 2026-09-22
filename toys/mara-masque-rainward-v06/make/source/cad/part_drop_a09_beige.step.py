"""Printable occurrence drop_a09_beige; flat on the bed at Z0."""
from build123d import Location

from parts.counter import counter

PRINTABLE = True


def gen_step():
    result = counter("single").moved(Location())
    result.label = "drop_a09_beige"
    result.color = counter("single").color
    return result
