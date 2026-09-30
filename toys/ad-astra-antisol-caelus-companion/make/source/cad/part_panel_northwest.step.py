"""Board panel northwest -- one quarter of the field, printed flat.

The grid is cut into the surface, not moulded as wells: a piece stands on the
board rather than sinking into it, and depth is reserved for terrain.
"""

from parts.board import build_panel_at_origin

PRINTABLE = True


def gen_step():
    return build_panel_at_origin("northwest")
