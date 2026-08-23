"""The witness collar: a shallow ring recessed into the top face around
each bore's rim, so a plugged shelf reads visibly different from an open
one from across the table (idea.json's own surface_treatment language).
"""

from __future__ import annotations

import cadquery as cq

from params import Params


def cut_collar(board: cq.Workplane, p: Params, top_z: float, x: float, y: float) -> cq.Workplane:
    """Cut one witness-collar ring, centered at (x, y), starting just
    outside the shelf's lead-in chamfer so it never touches the bore
    opening itself."""
    inner_r = p.shelf_dia / 2.0 + p.shelf_chamfer
    outer_r = inner_r + p.collar_width
    ring = (
        cq.Workplane("XY")
        .circle(outer_r)
        .circle(inner_r)
        .extrude(p.collar_depth)
        .translate((x, y, top_z - p.collar_depth))
    )
    return board.cut(ring)
