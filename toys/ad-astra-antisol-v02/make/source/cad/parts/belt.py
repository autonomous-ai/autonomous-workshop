"""belt_cell -- one tile per water square, not a slab over several.

The belt is a run of tiles laid on the grid, so the cell lines survive across
the water exactly as they do on land.  The tile is symmetric under a 90 degree
turn, so orientation is never a fit question.
"""

from __future__ import annotations

from build123d import Align, Box, Cylinder, Pos

import params as P
from features import rounded_square_sketch, rubble_field
from build123d import extrude


def build_belt_cell():
    """One belt tile, printed flat, bed datum at Z = 0, top at Z = 6.00."""
    floor_z = P.BELT_TILE_H - P.BELT_FLOOR_DROP          # 4.00
    base = extrude(rounded_square_sketch(P.TILE_SIZE, P.POCKET_CORNER_R), floor_z)

    pad = Pos(0, 0, floor_z) * Cylinder(
        radius=P.BELT_PAD_D / 2.0,
        height=P.BELT_FLOOR_DROP,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    rocks = rubble_field(
        half_size=P.TILE_SIZE / 2.0,
        pad_radius=P.BELT_PAD_D / 2.0,
        floor_z=floor_z,
        crest_z=P.BELT_TILE_H,
        seed=P.BELT_RUBBLE_SEED,
    )

    body = base + pad
    if rocks is not None:
        body = body + rocks

    # Trim to the tile envelope: every crest a seated disc can touch is then
    # coplanar with the landing pad, to within one layer, and nothing overhangs
    # the pocket it drops into.
    envelope = extrude(
        rounded_square_sketch(P.TILE_SIZE, P.POCKET_CORNER_R), P.BELT_TILE_H
    )
    body = body & envelope
    body.label = "belt_cell"
    return body
