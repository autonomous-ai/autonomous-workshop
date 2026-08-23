"""assay_board -- the fixed slab. A single carved-stone round block, six
two-stage assay bores on a ring, radial vein relief between them, and a
witness collar around every shelf rim. No layers, no stacking, no posts.

Built centered on Z (top face at +board_thickness/2) so the board's own
local frame is symmetric; the assembly places it at world Z=0.
"""

from __future__ import annotations

import math

import cadquery as cq

from cadlib.layout import circle_points
from params import Params
from features.bore import bore_cutter
from features.vein import cut_veins
from features.collar import cut_collar


def bore_positions(p: Params) -> list[tuple[float, float]]:
    """The ONE position list for the six bores -- reused for cutting the
    board, cutting the witness collars, and (in the assembly) seating the
    demo pucks, so all three can never drift apart."""
    return circle_points(n=p.bore_count, radius=p.bore_ring_radius, start_deg=90.0)


def build(p: Params) -> cq.Workplane:
    top_z = p.board_thickness / 2.0
    board = (
        cq.Workplane("XY")
        .circle(p.board_diameter / 2.0)
        .extrude(p.board_thickness)
        .translate((0, 0, -top_z))
    )

    positions = bore_positions(p)
    cutter = bore_cutter(p, top_z)
    for x, y in positions:
        board = board.cut(cutter.translate((x, y, 0)))
        board = cut_collar(board, p, top_z, x, y)

    # Radial vein-relief lines, one between each adjacent pair of bores.
    bore_angles = [90.0 + i * 360.0 / p.bore_count for i in range(p.bore_count)]
    vein_angles = [a + 180.0 / p.bore_count for a in bore_angles]
    board = cut_veins(board, p, top_z, vein_angles)

    return board
