"""The ONE radial position list plinth_ring and all three mask discs share.

`blocks.shared_positions` (board-game/blocks/blocks.py) is a rectangular
cols x rows x pitch grid generator, not a radial one, so it does not apply to
a 10-well ring. `cadlib.layout.circle_points` is the generic (non board-game
specific) helper that already does exactly this — evenly spaced points on a
circle — so it is used here instead of hand-rolling the trig a second time.

Every consumer (well cutter, disc window cutters, zenith-collar placer,
index-groove placer, witness-notch placer) imports `RING_XY` / `RING_ANGLES`
from this module. Nobody re-derives the ring elsewhere: two coordinate lists
that happen to agree today stop agreeing after one edit (lessons.md).
"""
from __future__ import annotations

from cadlib.layout import circle_points

from params import Params

_p = Params()

# Index 0 sits at +X (0 deg) and the ring runs counter-clockwise in 36 deg
# steps — this IS the index the rules mean by "index groove 0" / "window
# index position N".
RING_ANGLES: list[float] = [i * 360.0 / _p.well_count for i in range(_p.well_count)]
RING_XY: list[tuple[float, float]] = circle_points(
    n=_p.well_count, radius=_p.well_ring_r
)


def ring_point(index: int, z: float = 0.0) -> tuple[float, float, float]:
    """The (x, y, z) of one ring index, reusing the single shared XY list."""
    x, y = RING_XY[index]
    return (x, y, z)
