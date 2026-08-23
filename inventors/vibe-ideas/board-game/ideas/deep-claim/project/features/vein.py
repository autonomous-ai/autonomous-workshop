"""Radial vein-relief grooves cut across the slab's top face, between the
six bores -- the surface treatment idea.json calls for so the board reads
as quarried stone rather than a bare disc.
"""

from __future__ import annotations

import math

import cadquery as cq

from params import Params


def cut_veins(board: cq.Workplane, p: Params, top_z: float, angles_deg: list[float]) -> cq.Workplane:
    """Cut one straight radial groove per angle in `angles_deg` (typically
    the midpoints between adjacent bores), each `vein_depth` deep, running
    from `vein_inner_r` to `vein_outer_r`."""
    span = p.vein_outer_r - p.vein_inner_r
    mid_r = (p.vein_inner_r + p.vein_outer_r) / 2.0
    for angle in angles_deg:
        groove = (
            cq.Workplane("XY")
            .box(span, p.vein_width, p.vein_depth)
            .translate((mid_r, 0, top_z - p.vein_depth / 2.0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        board = board.cut(groove)
    return board
