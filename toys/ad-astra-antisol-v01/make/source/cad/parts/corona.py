"""corona_cell -- the trap, and the ring of three cells around each star.

Dou Shou Qi already puts three cells around every den.  That ring is the
corona: a piece standing there has strength 0, which is the star stripping a
world of its rank.  The tile is the FLOOR of the well, not its wall -- the
board's own 34.80 pocket makes the wall, so a seated disc drops exactly
3.00 mm below the field and has 0.40 mm of slip per side.
"""

from __future__ import annotations

import math

from build123d import Pos, extrude

import params as P
from features import engraved_tongue_sketch, rounded_square_sketch, tapered_flame


def build_corona_cell():
    """One corona tile with its two tongues, printed flat, bed datum Z = 0.

    Local frame: the tile centre is the origin, +Y points away from the den, so
    the two tongues stand at the +Y corners and every tongue points away from
    the star.
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
    face = engraved_tongue_sketch(
        count=P.CORONA_ENGRAVE_COUNT,
        inner=P.CORONA_ENGRAVE_INNER,
        outer=P.CORONA_TILE / 2.0 - 1.2,
        width=2.4,
        eye=P.CORONA_ENGRAVE_EYE_D / 2.0,
    )
    engraving = extrude(face, P.CORONA_ENGRAVE_D + 0.4)
    tile = tile - Pos(0, 0, P.CORONA_TILE_H - P.CORONA_ENGRAVE_D) * engraving

    # Two tongues, at the two corners of the edge furthest from the den.
    reach = P.CORONA_TONGUE_DIAGONAL / math.sqrt(2.0)
    rise = P.CORONA_TONGUE_H + P.CORONA_WELL_DROP   # above the tile's own top face
    tongues = []
    for sign in (-1.0, 1.0):
        flame = tapered_flame(
            base_radius=P.CORONA_TONGUE_BASE_D / 2.0,
            tip_radius=P.CORONA_TONGUE_TIP_R,
            height=rise,
            lean_deg=P.FLARE_LEAN_DEG,
            heading_deg=math.degrees(math.atan2(1.0, sign)),
        )
        tongues.append(Pos(sign * reach, reach, P.CORONA_TILE_H) * flame)

    body = tile + tongues
    body.label = "corona_cell"
    return body


def build_corona_tile_only():
    """The tile without tongues -- used to state the well's own dimensions."""
    return extrude(rounded_square_sketch(P.CORONA_TILE, P.POCKET_CORNER_R), P.CORONA_TILE_H)
