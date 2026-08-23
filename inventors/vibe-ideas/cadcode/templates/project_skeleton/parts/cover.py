"""Removable cover, built with its mating underside at local Z=0."""

from __future__ import annotations

import cadquery as cq

from cadlib.enclosure import lid_with_skirt
from params import Params


def make_cover(p: Params) -> cq.Workplane:
    # The plate underside is local Z=0 and the annular locating skirt extends
    # downward into the base cavity. Clearance is lateral, never a fake Z gap.
    return lid_with_skirt(
        length=p.width,
        width=p.depth,
        thickness=p.lid_thickness,
        corner_radius=p.corner_radius,
        lip_clearance=p.lid_clearance,
        wall=p.wall,
        lip_height=p.lid_skirt_depth,
    ).translate((0, 0, p.lid_thickness / 2))
