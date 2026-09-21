"""corona_cell -- the trap, and the ring of three cells around each star.

Dou Shou Qi already puts three cells around every den.  That ring is the
corona: a piece standing there has strength 0, which is the star stripping a
world of its rank.  The tile is the FLOOR of the well, not its wall -- the
board's own 34.80 pocket makes the wall, so a seated disc drops exactly
3.00 mm below the field and has 0.40 mm of slip per side.

The tile is now that floor and its engraving and nothing else.  Until the
owner's second pass it also carried two raised tongues at its far corners, and
`params.py` carried the four constants that sized them; both are gone.  What
the tile lost is recorded at `build_corona_cell` below, and what the board
gained by it is measured in `measure/corona-flat.md`.
"""

from __future__ import annotations

from build123d import Pos, extrude

import params as P
from features import engraved_tongue_sketch, rounded_square_sketch


def build_corona_cell():
    """One corona tile, printed flat, bed datum Z = 0.

    Local frame: the tile centre is the origin.  The tile is square, its
    engraving is sixteen-fold, and nothing on it points anywhere, so the piece
    has no preferred heading -- which it had while it carried tongues, and
    which `assemblies/product.py` no longer has to solve for.
    """
    tile = extrude(
        rounded_square_sketch(P.CORONA_TILE, P.POCKET_CORNER_R), P.CORONA_TILE_H
    )

    # Flame tongues radiating from the centre, engraved rather than raised: a
    # raised relief under a seated disc would make a trapped piece rock, which
    # is the one thing a corona well must not do.
    # The tongues start well out from the centre and a separate disc stands in
    # for the star itself.  Run in to the middle, sixteen tongues merge into
    # one blob whose boundary leaves 0.13 mm webs the nozzle cannot print --
    # measured, not guessed.
    #
    # These sixteen are now the whole tile.  The two RAISED tongues that used
    # to stand 4.00 mm above the field at the two corners furthest from the
    # star were removed on the owner's instruction, so that the star's own two
    # flames are the only raised flames on the board.  Nothing here changed to
    # compensate: the engraving keeps its count, its inner radius, its eye and
    # its 0.40 mm depth exactly as they were, because it was never the thing
    # the owner objected to -- it is the star's light on the floor of the well,
    # and it is the reason a trap reads as a trap with a world standing in it.
    face = engraved_tongue_sketch(
        count=P.CORONA_ENGRAVE_COUNT,
        inner=P.CORONA_ENGRAVE_INNER,
        outer=P.CORONA_TILE / 2.0 - 1.2,
        width=2.4,
        eye=P.CORONA_ENGRAVE_EYE_D / 2.0,
    )
    engraving = extrude(face, P.CORONA_ENGRAVE_D + 0.4)
    body = tile - Pos(0, 0, P.CORONA_TILE_H - P.CORONA_ENGRAVE_D) * engraving

    body.label = "corona_cell"
    return body


def build_corona_tile_only():
    """The bare tile without its engraving -- used to state the well's own
    dimensions, and to measure what the engraving takes out of it."""
    return extrude(rounded_square_sketch(P.CORONA_TILE, P.POCKET_CORNER_R), P.CORONA_TILE_H)
