"""Small reusable solids. Plan outlines live in the kernel-free `profiles` module."""
from math import cos, radians, sin

from build123d import *

import params as P
from profiles import theta, tongue_face_curves, tongue_ramp


def prism(points, height):
    """Extrude one closed plan outline upward from Z0."""
    return extrude(Polygon(*points, align=None), amount=height, dir=(0, 0, 1))


def _edges(curves):
    """Exact edges for one closed boundary of lines, arcs and flank Beziers."""
    out = []
    for kind, args in curves:
        if kind == "line":
            p0, p1 = args
            out.append(Edge.make_line((p0[0], p0[1], 0.0), (p1[0], p1[1], 0.0)))
        elif kind == "spline":
            points = [(x, y, 0.0) for x, y in args]
            out.append(Edge.make_spline(points))
        elif kind == "arc3":
            out.append(Edge.make_three_point_arc(
                *[(p[0], p[1], 0.0) for p in args]))
        elif kind == "bezier":
            out.append(Edge.make_bezier(*[(x, y, 0.0) for x, y in args]))
        else:
            centre, radius, a0, a1 = args
            out.append(Edge.make_three_point_arc(*[
                (centre[0] + radius * cos(radians(a)),
                 centre[1] + radius * sin(radians(a)), 0.0)
                for a in (a0, 0.5 * (a0 + a1), a1)]))
    return out


def curve_face(curves):
    """A planar face from one closed boundary given as exact segments."""
    return Face(Wire(_edges(curves)))


def curve_prism(curves, height):
    """Extrude a closed boundary given as exact Bezier, arc and line segments.

    A flame carries three or four exact edges instead of a hundred chords and a
    tile carries four instead of forty, so the flanks stay smooth and the
    exported solids stay small.
    """
    return extrude(curve_face(curves), amount=height, dir=(0, 0, 1))


def ramped_flame(index):
    """One corona flame: a flat-bottomed blade whose top falls as it runs out.

    The plan face is the flame's two flanks, its tip cap and its own arc of the
    disc's edge circle, so the flame lies wholly outside that circle and meets
    the disc along the arc alone. A single plane then takes the top down from
    the deck height at the root to this flame's own tip height. Material comes
    off the top only, so the underside stays flat on the bed, the flanks stay
    vertical, and the ramp meets each flank along one straight crisp edge.
    """
    blade = curve_prism(tongue_face_curves(index), P.CORONA_TOP)
    ramp = tongue_ramp(index)
    crest = Vector(*ramp["crest"])
    side = Vector(*ramp["crest_side"]) - crest
    down = Vector(*ramp["foot"]) - crest
    normal = side.cross(down)
    if normal.Z < 0:
        normal = -normal
    plane = Plane(origin=ramp["crest"], x_dir=side, z_dir=normal)
    lid = plane * Box(80.0, 80.0, 40.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    blade = blade - lid
    assert len(blade.solids()) == 1, "flame %d was cut into pieces" % index
    return blade


def bank_marker(angle):
    """Engraved radial tick on the centre bar top, marking one bank boundary.

    Cut, not raised: the bar has to stay a flat unobstructed landing for every
    displaced drop, so a raised rib is not available. The section is a shallow
    V rather than a flat-bottomed slot, because a groove with vertical walls
    is invisible from straight above while two sloped faces read as a dark
    tick. A drop simply bridges it.
    """
    half = P.MARKER_W / 2.0
    section = Plane.YZ * Polygon(
        (-half, P.BAR_TOP + 1.0),
        (half, P.BAR_TOP + 1.0),
        (half, P.BAR_TOP),
        (0.0, P.BAR_TOP - P.MARKER_DEPTH),
        (-half, P.BAR_TOP),
        align=None,
    )
    groove = extrude(section, amount=P.MARKER_L)
    return Rot(Z=angle) * Pos(P.MARKER_R - P.MARKER_L / 2.0, 0, 0) * groove


def boundary_wedge(angle, width, extra, radius_limit=None, inner_limit=None):
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
    if inner_limit is not None:
        # twenty-four wedges all reaching the axis pile up into slivers under
        # the centre bar; none of them is needed inside the hub ring
        wedge = wedge - Cylinder(
            inner_limit, P.DECK + 1.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return Rot(Z=angle) * wedge


def locating_key(point, base_z, height, length, width):
    """Radial stadium key for one lane, in world coordinates.

    It sits beside the lane axis, clear of every counter landing region, and
    its radial length is what stops a seated tile turning or creeping.
    """
    key = extrude(SlotOverall(length, width), amount=height)
    return Rot(Z=theta(point)) * Pos(P.KEY_R, P.KEY_OFFSET, base_z) * key
