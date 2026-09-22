"""Small reusable solids. Plan outlines live in the kernel-free `profiles` module."""
from math import cos, radians, sin

from build123d import *

import params as P
from profiles import theta


def prism(points, height):
    """Extrude one closed plan outline upward from Z0."""
    return extrude(Polygon(*points, align=None), amount=height, dir=(0, 0, 1))


def curve_prism(curves, height):
    """Extrude a closed boundary given as exact Bezier and arc segments.

    The corona skirt is built this way rather than as a dense polygon: 38
    tongues carry 152 exact edges instead of two thousand chords, so the flanks
    stay smooth and the solid stays cheap enough to tessellate.
    """
    edges = []
    for kind, args in curves:
        if kind == "bezier":
            edges.append(Edge.make_bezier(*[(x, y, 0.0) for x, y in args]))
        else:
            centre, radius, a0, a1 = args
            edges.append(Edge.make_three_point_arc(*[
                (centre[0] + radius * cos(radians(a)),
                 centre[1] + radius * sin(radians(a)), 0.0)
                for a in (a0, 0.5 * (a0 + a1), a1)]))
    return extrude(Face(Wire(edges)), amount=height, dir=(0, 0, 1))


def capsule_marker(angle):
    """Preserved short rounded boundary dash: floor Z8.0 to maximum Z9.0."""
    marker = extrude(SlotOverall(P.MARKER_L, P.MARKER_W),
                     amount=P.MARKER_TOP - P.DECK)
    marker = fillet(
        marker.edges().filter_by_position(
            Axis.Z, P.MARKER_TOP - P.DECK, P.MARKER_TOP - P.DECK),
        radius=P.MARKER_ROUND,
    )
    return Rot(Z=angle) * Pos(P.MARKER_R, 0, P.DECK) * marker


def boundary_wedge(angle, width, extra, radius_limit=None):
    """The drafted body wedge that widens one lane boundary below the surface.

    Half-width is `width/2 + extra` at the deck surface and adds BOUNDARY_DRAFT
    at the pocket floor. Fused into the Sun body with `extra=0` it thickens the
    boundary; cut from a tile with `extra=CLEAR` it drafts the tile to match.
    """
    half_top = width / 2.0 + extra
    half_bottom = half_top + P.BOUNDARY_DRAFT
    section = Plane.YZ * Polygon(
        (-half_bottom, P.POCKET_FLOOR),
        (half_bottom, P.POCKET_FLOOR),
        (half_top, P.DECK),
        (-half_top, P.DECK),
        align=None,
    )
    wedge = extrude(section, amount=P.SUN_R + 6.0)
    if radius_limit is not None:
        wedge = wedge & Cylinder(
            radius_limit, P.DECK, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return Rot(Z=angle) * wedge


def locating_key(point, base_z, height, length, width):
    """Radial stadium key for one lane, in world coordinates.

    It sits beside the lane axis, clear of every counter landing region, and
    its radial length is what stops a seated tile turning or creeping.
    """
    key = extrude(SlotOverall(length, width), amount=height)
    return Rot(Z=theta(point)) * Pos(P.KEY_R, P.KEY_OFFSET, base_z) * key
