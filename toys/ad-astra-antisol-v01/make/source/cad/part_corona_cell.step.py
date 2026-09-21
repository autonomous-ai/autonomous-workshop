"""One corona cell -- the trap, floored three millimetres below the field.

The tile is the floor of the well, not its wall; the board's own pocket makes
the wall.  Its flames are engraved, because raised relief under a seated disc
would make a trapped piece rock.
"""

from parts.corona import build_corona_cell

PRINTABLE = True


def gen_step():
    return build_corona_cell()
