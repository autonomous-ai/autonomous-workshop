"""Printable occurrence fork_02_dark_brown; flat on the bed at Z0."""
from build123d import Location

from parts.counter import counter

PRINTABLE = True


def gen_step():
    result = counter("fork").moved(Location())
    result.label = "fork_02_dark_brown"
    result.color = counter("fork").color
    return result
