"""yard_board: the hexagonal mill floor. 37 integral pins on the ONE shared
triangular lattice (params.hex_lattice_positions), 18 outer pins sitting in
a raised sill, 1mm plank ribs between them. Single tile, single named part.
"""
import math

import cadquery as cq

import params as p


def _hex_pts(vertex_r: float):
    return [
        (vertex_r * math.cos(math.radians(a)), vertex_r * math.sin(math.radians(a)))
        for a in range(0, 360, 60)
    ]


def build_yard_board(positions):
    """positions: the SAME 37-point lattice list used to place supply gears
    on the pins -- consumed here once, never regenerated.
    """
    slab = (
        cq.Workplane("XY")
        .polyline(_hex_pts(p.BOARD_VERTEX_R)).close()
        .extrude(p.SLAB_T)
    )
    # chamfered skirt
    slab = slab.edges("<Z").chamfer(p.BOARD_SKIRT_CHAMFER)

    # plank ribs: raised strips across the floor, clipped to the hex outline
    hex_prism_full = (
        cq.Workplane("XY").polyline(_hex_pts(p.BOARD_VERTEX_R)).close()
        .extrude(p.RIB_H).translate((0, 0, p.SLAB_T))
    )
    ribs = cq.Workplane("XY")
    first = True
    n_ribs = 9
    spacing = (2 * p.BOARD_VERTEX_R * math.sqrt(3) / 2.0) / n_ribs
    for i in range(n_ribs):
        y = -p.BOARD_VERTEX_R + (i + 0.5) * spacing
        strip = (
            cq.Workplane("XY")
            .rect(2 * p.BOARD_VERTEX_R, 4.0, centered=True)
            .extrude(p.RIB_H)
            .translate((0, y, p.SLAB_T))
        )
        ribs = strip if first else ribs.union(strip)
        first = False
    ribs = ribs.intersect(hex_prism_full)
    slab = slab.union(ribs)

    pin_cyl = cq.Workplane("XY").circle(p.PIN_D / 2.0).extrude(p.PIN_H)
    sill_cyl = cq.Workplane("XY").circle(p.SILL_D / 2.0).extrude(p.SILL_H)

    for (x, y, ring) in positions:
        pin = pin_cyl.translate((x, y, p.SLAB_T))
        slab = slab.union(pin)
        if ring == 3:  # the 18 outer "yard pins"
            sill = sill_cyl.translate((x, y, p.SLAB_T))
            slab = slab.union(sill)

    return slab
