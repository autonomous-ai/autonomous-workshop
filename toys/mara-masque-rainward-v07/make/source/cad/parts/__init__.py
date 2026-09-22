"""One module per physical part of the Rainward set."""
from build123d import Color

import validation

validation.check()   # algebraic parameter checks run before any geometry


def finish(shape, label, color):
    """Name and colour one leaf solid, and refuse a part that is not one solid."""
    assert len(shape.solids()) == 1, label
    shape.label = label
    shape.color = Color(*color)
    return shape
