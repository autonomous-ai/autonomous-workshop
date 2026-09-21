"""The Sun body: disc, corona of separate flames, 24 lane pockets, bar, markers."""
from functools import lru_cache

from build123d import *

import params as P
from features import (
    bank_marker,
    boundary_wedge,
    curve_prism,
    locating_key,
    ramped_flame,
)
from profiles import (
    bank_boundary_points,
    boundary_width,
    sector_curves,
    theta,
)
from parts import finish


def disc():
    """The deck: one plain cylinder whose edge circle is the flame base.

    This is the continuous base the correction asks for. The disc's own
    circular edge runs unbroken all the way round at radius 79.70; nothing is
    cut into it and no flame reaches inside it.
    """
    return Cylinder(P.SUN_R, P.DECK, align=(Align.CENTER, Align.CENTER, Align.MIN))


def lane_cutters():
    """Per lane: the blind seat pocket and the tile's locating-key recess."""
    cutters = []
    lift = P.DECK - P.POCKET_FLOOR + 4.0
    for point in range(1, P.LANES + 1):
        seat = sector_curves(point, P.POCKET_INNER, P.POCKET_OUTER, 0.0)
        cutters.append(Pos(0, 0, P.POCKET_FLOOR) * curve_prism(seat, lift))
        cutters.append(
            locating_key(
                point,
                P.POCKET_FLOOR - P.KEY_RECESS_D,
                P.KEY_RECESS_D + lift,
                P.KEY_L + 2 * P.KEY_CLEAR,
                P.KEY_W + 2 * P.KEY_CLEAR,
            )
        )
    return cutters


def lip_relief():
    """Drop the rim ring to RIM_TOP across the band the tile lips occupy.

    One plain annulus, not twenty-four sectors, so the ring the flames stand
    on is a single uninterrupted surface and nothing but the disc itself meets
    the edge circle. The valley between two flames is that ring, 0.4 mm under
    the deck, running out to the disc's own edge.
    """
    lift = P.DECK - P.RIM_TOP + 4.0
    outer = Cylinder(P.SUN_R + 4.0, lift,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Cylinder(P.SEAT_OUTER, lift,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(0, 0, P.RIM_TOP) * (outer - inner)


def boundary_buttresses():
    """Drafted body under every lane boundary, so no boundary is a thin fin.

    Each wedge runs the whole length of the tile fan and stops on the tile's
    own outer arc, which keeps the constant 0.70 mm orange margin visible from
    the hub to the end of every lip and keeps every rib clear of the disc edge.
    """
    return [
        boundary_wedge(theta(point) - P.PITCH / 2.0, boundary_width(point),
                       0.0, P.TILE_OUTER, P.BAR_R - 1.0)
        for point in range(1, P.LANES + 1)
    ]


def corona():
    """The forty flames, each rooted on its own arc of the disc edge."""
    return [ramped_flame(index) for index in range(P.CORONA_COUNT)]


def centre_bar():
    """Preserved radius-24 capture platform, broad uninterrupted top at Z6.2."""
    return Pos(0, 0, P.DECK) * Cylinder(
        P.BAR_R, P.BAR_TOP - P.DECK, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def bank_markers():
    """Four engraved ticks on the bar top, one per bank boundary."""
    return [bank_marker(theta(point) - P.PITCH / 2.0)
            for point in bank_boundary_points()]


@lru_cache(maxsize=None)
def sun_body():
    body = disc()
    body = body.cut(*lane_cutters(), lip_relief())
    body = body.fuse(*boundary_buttresses())
    body = body.fuse(*corona())
    body = body.fuse(centre_bar())
    body = body.cut(*bank_markers())
    return finish(body, "sun_" + P.SUN_FILAMENT, P.SUN_COLOR)
