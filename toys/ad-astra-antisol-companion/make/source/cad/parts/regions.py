"""The two region helpers `parts/world.py`'s colour split needs.

They live here rather than in `parts/world.py` for the reason the layout rule
gives: that module is the whole world -- disc, numeral, globe, seat, rings,
the clip loop and the split -- and it is at its line budget.  Both functions
below are about a REGION rather than about a world, they have no state, and
neither of them knows what a piece is.

They take the region-tool builder as an argument instead of importing it, so
this module never imports `parts/world.py` and the two cannot form a cycle.
"""

from __future__ import annotations

import params as P
from features import blob_tool, outline_tool


def subtrahend(planet: str, other, table, region_tool):
    """What one entry of a marking's `subtract` tuple takes away.

    A plain string names a SIBLING MARKING, and the sibling's own solid is
    removed -- that is how Earth's land gives way to its dryland, and how every
    subtraction in this set worked until Neptune's companion cloud.

    A `("spec", <region spec>)` pair names a region that is never drawn and
    exists only to be removed.  It is here for that one case: the companion has
    to stand a printable strip of bare globe clear of the dark spot it sits
    against, and a strip of bare globe is not a marking -- nothing is printed
    in it.  Subtracting the sibling itself leaves the two colours sharing a
    boundary, which an independent reader of the renders called a notched
    figure-eight; subtracting the sibling grown by one nozzle width leaves the
    blue between them.  `parts/neptune_atlas.py` carries the dilation and
    `measure/neptune-atlas-resolution.md` measures what it buys.
    """
    if isinstance(other, str):
        return table[other]
    kind, spec = other
    if kind != "spec":
        raise ValueError("unknown subtraction %r" % (other,))
    return region_tool(planet, spec, solid=True)


def region_pieces(planet: str, spec, nudge: float, first: int, region_tool):
    """One tool per patch, so each can be clipped on its own.

    A `blob` spec is several round patches that overlap.  Fusing them first and
    intersecting the union with the globe's own sphere is what the earlier
    build did, and `inspect validate` measured the result as self-intersecting
    on Mercury, Mars and Venus: the union's outer face IS the globe sphere, and
    a neighbouring patch's tool sphere runs tangent to it along the seam where
    two patches meet.  Clipping each patch separately gives a stack of clean
    lenses whose fuse meets along ordinary edges instead.

    `nudge` widens patch *n* by `n * nudge` degrees rather than widening them
    all equally.  A common widening slides every seam along by the same amount
    and can land a second pair on the tangency it just left; a graded one
    cannot, because no two patches move together.
    """
    radius = P.globe_radius(planet)
    depth = P.RELIEF_DEPTH
    kind = spec[0]
    if kind == "blob":
        return [
            blob_tool(radius, [(lat, lon, ang + nudge * (first + n))], depth)
            for n, (lat, lon, ang) in enumerate(spec[1])
        ]
    if kind == "outline":
        return [
            outline_tool(radius, ring, depth, nudge * (first + n))
            for n, ring in enumerate(spec[1])
        ]
    return [region_tool(planet, spec, nudge * first)]
