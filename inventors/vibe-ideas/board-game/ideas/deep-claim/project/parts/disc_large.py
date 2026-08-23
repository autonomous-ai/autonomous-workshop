"""disc_large_mark{3,4,5,6} -- the broad puck. Always catches a bore's
upper shelf; can never reach the floor (throat is narrower than it is).
Built with its bottom face at local Z=0 so it drops straight onto a
bore's shelf floor in the assembly.
"""

from __future__ import annotations

import cadquery as cq

from params import Params
from features.stud import add_owner_studs


def build(p: Params, stud_count: int) -> cq.Workplane:
    disc = (
        cq.Workplane("XY")
        .circle(p.disc_large_dia / 2.0)
        .extrude(p.disc_large_height)
    )
    disc = disc.faces(">Z").edges().chamfer(0.6)
    return add_owner_studs(
        disc,
        count=stud_count,
        top_z=p.disc_large_height,
        ring_radius=p.stud_ring_radius_large,
        base=p.stud_base_large,
        height=p.stud_height,
    )
