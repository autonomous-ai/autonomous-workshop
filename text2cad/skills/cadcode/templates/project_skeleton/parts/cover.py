"""The removable lid that mates to the base."""

from __future__ import annotations

import cadquery as cq

from params import Params


def make_cover(p: Params) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(p.width - p.lid_gap, p.depth - p.lid_gap, p.wall)
        .edges("|Z")
        .fillet(p.corner_radius - p.lid_gap / 2)
    )
