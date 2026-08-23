"""disc_small_mark{3,4,5,6} -- the slim puck. Always slips past an open
shelf throat to rest on the bore's floor chamber. Built with its bottom
face at local Z=0 so it drops straight onto a bore's floor in the
assembly.
"""

from __future__ import annotations

import cadquery as cq

from params import Params
from features.stud import add_owner_studs


def build(p: Params, stud_count: int) -> cq.Workplane:
    disc = (
        cq.Workplane("XY")
        .circle(p.disc_small_dia / 2.0)
        .extrude(p.disc_small_height)
    )
    disc = disc.faces(">Z").edges().chamfer(0.4)
    return add_owner_studs(
        disc,
        count=stud_count,
        top_z=p.disc_small_height,
        ring_radius=p.stud_ring_radius_small,
        base=p.stud_base_small,
        height=p.stud_height,
    )
