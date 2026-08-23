"""yard_board: the hexagonal mill floor. 37 integral pins on the ONE shared
triangular lattice (features.lattice.hex_lattice_positions), 18 outer pins
sitting inside a raised sill, 1mm plank ribs texturing the floor between
them. Single tile, single named part -- no dovetail tiling needed, the
230x200x42mm envelope fits the P2S bed in one piece.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params


def _hex_pts(vertex_r: float) -> list[tuple[float, float]]:
    return [
        (vertex_r * math.cos(math.radians(a)), vertex_r * math.sin(math.radians(a)))
        for a in range(0, 360, 60)
    ]


def make_yard_board(p: Params, positions: list[tuple[float, float, int]]) -> cq.Workplane:
    """`positions`: the SAME 37-point lattice list the assembly places
    supply/millstone/crank pieces onto -- consumed here once, never
    regenerated (see features/lattice.py).
    """
    slab = (
        cq.Workplane("XY")
        .polyline(_hex_pts(p.board_vertex_r)).close()
        .extrude(p.slab_t)
    )
    # chamfered skirt
    slab = slab.edges("<Z").chamfer(p.board_skirt_chamfer)

    # plank ribs: raised strips across the floor, clipped to the hex outline
    hex_prism_full = (
        cq.Workplane("XY").polyline(_hex_pts(p.board_vertex_r)).close()
        .extrude(p.rib_h).translate((0, 0, p.slab_t))
    )
    ribs = cq.Workplane("XY")
    first = True
    n_ribs = 9
    spacing = (2 * p.board_vertex_r * math.sqrt(3) / 2.0) / n_ribs
    for i in range(n_ribs):
        y = -p.board_vertex_r + (i + 0.5) * spacing
        strip = (
            cq.Workplane("XY")
            .rect(2 * p.board_vertex_r, 4.0, centered=True)
            .extrude(p.rib_h)
            .translate((0, y, p.slab_t))
        )
        ribs = strip if first else ribs.union(strip)
        first = False
    ribs = ribs.intersect(hex_prism_full)
    slab = slab.union(ribs)

    pin_cyl = cq.Workplane("XY").circle(p.pin_d / 2.0).extrude(p.pin_h)
    sill_cyl = cq.Workplane("XY").circle(p.sill_d / 2.0).extrude(p.sill_h)

    for (x, y, ring) in positions:
        pin = pin_cyl.translate((x, y, p.slab_t))
        slab = slab.union(pin)
        if ring == p.n_rings:  # the 18 outer "yard pins"
            sill = sill_cyl.translate((x, y, p.slab_t))
            slab = slab.union(sill)

    return slab
