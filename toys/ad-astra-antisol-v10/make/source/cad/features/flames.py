"""The star's prominences and its corona's tongues.

Both are tapered flames that lean outward from vertical.  They are built as
lofts between horizontal circles so the base stays flat on the plate it grows
from, and every face stays steeper than the overhang limit.
"""

from __future__ import annotations

import math

from build123d import Circle, Plane, Polygon, Pos, Rot, loft


def tapered_flame(
    base_radius: float,
    tip_radius: float,
    height: float,
    lean_deg: float,
    heading_deg: float,
    waist: float = 0.46,
):
    """One flame, base centred on the origin of Plane.XY, rising to `height`.

    `heading_deg` is the compass direction it leans toward, `lean_deg` how far
    from vertical.  The lean is applied as a shear -- each station is a
    horizontal circle offset along the heading -- so the base is a flat disc on
    the plate and no face is shallower than the taper itself.
    """
    reach = height * math.tan(math.radians(lean_deg))
    dx = math.cos(math.radians(heading_deg))
    dy = math.sin(math.radians(heading_deg))
    # A flame, not a cone: full at the foot, a fast pull-in through the first
    # third, then a long thin tongue.  The lean is applied as f**1.6 rather
    # than f, so the body rises almost straight and only the tongue leans out
    # -- which is what stops a pair of these reading as horns.
    stations = (
        (0.00, 1.00),
        (0.14, 0.94),
        (0.34, 0.66),
        (0.58, 0.38),
        (0.80, 0.19),
        (1.00, 0.00),
    )
    sections = []
    for fraction, factor in stations:
        radius = tip_radius + (base_radius - tip_radius) * factor
        z = height * fraction
        offset = reach * (fraction ** 1.6)
        plane = Plane(origin=(dx * offset, dy * offset, z))
        sections.append(plane * Circle(max(radius, tip_radius)))
    return loft(sections)


def engraved_tongue_sketch(count: int, inner: float, outer: float, width: float, eye: float = 0.0):
    """Flame tongues radiating from a star, as one 2D sketch.

    Each tongue is a slim kite that narrows to a point at its outer end; the
    set alternates two lengths so the ring reads as fire rather than as a gear.
    `eye` adds the disc they radiate from.

    Every polygon is wound counter-clockwise on purpose.  A clockwise one
    fuses as a reversed face: the union reports success, shatters into
    mixed-normal fragments, and the extrude that follows runs the other way --
    which is exactly how sixteen tongues once turned into no tongues at all.
    """
    pieces = []
    if eye > 0.0:
        pieces.append(Circle(eye))
    for index in range(count):
        angle = 360.0 * index / count
        long = outer if index % 2 == 0 else inner + (outer - inner) * 0.62
        half = width / 2.0
        shoulder = inner + (long - inner) * 0.30
        points = (
            (inner, 0.0),
            (shoulder, -half * 0.55),
            (long * 0.985, -half * 0.06),
            (long, half * 0.10),
            (shoulder, half),
        )
        pieces.append(Rot(0, 0, angle) * Polygon(*points, align=None))
    return pieces[0] if len(pieces) == 1 else pieces[0] + pieces[1:]
