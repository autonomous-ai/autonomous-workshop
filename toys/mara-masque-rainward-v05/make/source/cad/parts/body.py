"""The Sun body: deck, corona rim, twenty-four lane pockets, centre bar, markers."""
from functools import lru_cache

from build123d import *

import params as P
from features import (
    boundary_wedge,
    capsule_marker,
    curve_prism,
    locating_key,
    prism,
    ramped_tongue,
)
from profiles import (
    bank_boundary_points,
    boundary_radius_limit,
    boundary_width,
    core_curves,
    hero_profile,
    sector_curves,
    skirt_curves,
    theta,
)
from parts import finish


def deck_blank():
    """The deck core, its thirty-eight ramped tongues, and the hero arch.

    There is no plain disc underneath: the core's boundary is the trough floors
    themselves, closed by each tongue's root chord, and every tongue is fused
    onto the chord it shares. Each tongue is the same material as the deck, and
    no notch between two tongues can ever be a gap of air between separate
    slivers. The core and every tongue reach the deck height at that shared
    chord, so the flame leaves the board flush and only then falls away.
    """
    deck = curve_prism(core_curves(), P.DECK)
    tongues = [ramped_tongue(index) for index in range(P.CORONA_COUNT)]
    return deck.fuse(prism(hero_profile(), P.DECK), *tongues)


def lane_pocket_cutters():
    """One blind pocket per lane inside the rim ring, plus its locating recess."""
    cutters = []
    lift = P.DECK - P.POCKET_FLOOR + 4.0
    for point in range(1, P.LANES + 1):
        curves = sector_curves(point, P.POCKET_INNER, P.POCKET_OUTER, 0.0)
        cutters.append(Pos(0, 0, P.POCKET_FLOOR) * curve_prism(curves, lift))
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


def boundary_buttresses():
    """Drafted body under every lane boundary, so no boundary is a thin fin.

    Each wedge stops at the skirt: where a trough cuts inside radius 90 the
    ridge ends with it instead of hanging out over the notch.
    """
    return [
        boundary_wedge(theta(point) - P.PITCH / 2.0, boundary_width(point),
                       0.0, boundary_radius_limit(point))
        for point in range(1, P.LANES + 1)
    ]


def rim_collar():
    """Put the rim ring back under the tile lips after the tongues are ramped.

    Every tongue now starts falling at its own root chord, which is inside
    radius 90 on the deeper troughs, so the ramp would otherwise eat the outer
    millimetres of the ring the tile lips rest on. This restores the body to
    the ring top across the band the lips occupy, clipped to the skirt plan so
    no trough is filled in and no material appears where the flame is not.
    """
    annulus = (Cylinder(P.RIM_COLLAR_R, P.RIM_TOP,
                        align=(Align.CENTER, Align.CENTER, Align.MIN))
               - Cylinder(P.RIM_INNER, P.RIM_TOP,
                          align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return annulus & curve_prism(skirt_curves(), P.RIM_TOP)


def lip_relief():
    """Drop the body to the rim-ring top across the band the tile lips occupy.

    Every tile laps the ring between RIM_INNER and its own outer edge, over
    Z7.8 to Z8.8. Cutting that 0.2 mm band out of the body gives the ring its
    7.8 top and keeps the assembly clash-free. Beyond radius 90 nothing is cut,
    so the flame keeps its own ramped top everywhere it shows.
    """
    height = P.DECK - P.RIM_TOP
    outer = Cylinder(P.TILE_OUTER + P.CLEAR, height,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Cylinder(P.RIM_INNER, height,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(0, 0, P.RIM_TOP) * (outer - inner)


def centre_bar():
    """Preserved radius-24 capture platform, broad uninterrupted top at Z9.0."""
    return Pos(0, 0, P.DECK) * Cylinder(
        P.BAR_R, P.BAR_TOP - P.DECK, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


@lru_cache(maxsize=None)
def sun_body():
    body = deck_blank().fuse(rim_collar())
    body = body.cut(*lane_pocket_cutters(), lip_relief())
    body = body.fuse(*boundary_buttresses())
    markers = [capsule_marker(theta(point) - P.PITCH / 2.0)
               for point in bank_boundary_points()]
    body = body.fuse(centre_bar(), *markers)
    return finish(body, "sun_" + P.SUN_FILAMENT, P.SUN_COLOR)
