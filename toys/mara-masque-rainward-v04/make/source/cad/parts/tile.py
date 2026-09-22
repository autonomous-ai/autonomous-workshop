"""One lane tile: a separate strip that seats in its pocket and carries the tone."""
from functools import lru_cache

from build123d import *

import params as P
from features import boundary_wedge, locating_key
from profiles import boundary_width, next_point, sector_profile, theta
from parts import finish


def tile_tone(point):
    """Strict alternation around the circle: odd points light, even points dark."""
    if point % 2 == 1:
        return P.LANE_LIGHT_COLOR, P.LANE_LIGHT_FILAMENT
    return P.LANE_DARK_COLOR, P.LANE_DARK_FILAMENT


def tile_label(point):
    return "lane_%02d_%s" % (point, tile_tone(point)[1])


@lru_cache(maxsize=None)
def lane_tile(point):
    """Tile in assembly pose: underside on the pocket floor, top at Z8.8.

    The outer edge follows the rim at 89.85 except where a skirt trough cuts
    inside it; there the tile retreats with the body, so nothing overhangs a
    notch and every notch shows body, not tile.
    """
    profile = sector_profile(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR,
                             clipped=True)
    body = Pos(0, 0, P.POCKET_FLOOR) * extrude(
        Polygon(*profile, align=None), amount=P.TILE_T, dir=(0, 0, 1)
    )
    # the outer 1.6 mm thins to a lip that laps the rim ring instead of seating
    relief = Pos(0, 0, P.POCKET_FLOOR - 1.0) * (
        Cylinder(P.SUN_R + 6.0, P.RIM_TOP - P.POCKET_FLOOR + 1.0,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Cylinder(P.SEAT_OUTER, P.RIM_TOP - P.POCKET_FLOOR + 1.0,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    body = body.cut(relief)
    body = fillet(
        body.edges().filter_by_position(Axis.Z, P.LANE_TOP, P.LANE_TOP),
        radius=P.EDGE_ROUND,
    )
    for boundary in (point, next_point(point)):
        body = body.cut(
            boundary_wedge(theta(boundary) - P.PITCH / 2.0,
                           boundary_width(boundary), P.CLEAR)
        )
    body = body.fuse(
        locating_key(point, P.POCKET_FLOOR - P.KEY_H, P.KEY_H, P.KEY_L, P.KEY_W)
    )
    colour, filament = tile_tone(point)
    return finish(body, "lane_%02d_%s" % (point, filament), colour)


@lru_cache(maxsize=None)
def lane_tile_print(point):
    """Same tile on the bed, top face down so the key points up and nothing overhangs."""
    tile = lane_tile(point)
    placed = Pos(0, 0, P.LANE_TOP) * Rot(X=180) * tile
    placed.label = tile.label
    placed.color = tile.color
    return placed
