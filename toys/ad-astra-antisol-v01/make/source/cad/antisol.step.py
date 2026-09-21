"""Antisol -- the whole set, laid out in the opening position.

This is the review entry, not a print target: it is sixteen worlds, four board
panels, twelve belt tiles, two stars with their coronas, and the two trays,
each placed where it belongs.  The printable parts are the `part_*.step.py`
entries beside it.
"""

from assemblies import product_compound

PRINTABLE = False


def gen_step():
    return product_compound()
