"""Raised pyramid ownership studs -- the one feature every disc_large and
disc_small variant carries, told apart only by count (3/4/5/6).
"""

from __future__ import annotations

import math

import cadquery as cq

from params import Params


def pyramid_stud(base: float, height: float) -> cq.Workplane:
    """A single square-based pyramid, base centered at local origin, apex
    at local +Z. Loft from the base square to a near-point square."""
    return (
        cq.Workplane("XY")
        .rect(base, base)
        .workplane(offset=height)
        .rect(0.02, 0.02)
        .loft()
    )


def add_owner_studs(
    disc: cq.Workplane,
    *,
    count: int,
    top_z: float,
    ring_radius: float,
    base: float,
    height: float,
) -> cq.Workplane:
    """Union `count` pyramid studs, evenly spaced on a ring on the disc's
    top face, onto `disc`. One stud shape, reused at every position."""
    stud = pyramid_stud(base, height)
    for i in range(count):
        angle = math.radians(i * 360.0 / count)
        x = ring_radius * math.cos(angle)
        y = ring_radius * math.sin(angle)
        disc = disc.union(stud.translate((x, y, top_z)))
    return disc
