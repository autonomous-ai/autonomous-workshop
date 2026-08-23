"""reef_board: the hexagonal limestone slab. 37 pan dishes on the ONE shared
triangular lattice (params.hex_lattice_positions), each a 30mm-across-flats,
3mm-deep hex dish with a 6.6mm/10mm-deep centre socket. 19 inner pans carry a
raised seed collar; the 6 outer-corner pans carry a raised landing barnacle
cluster. Single tile, single named part.
"""
import math

import cadquery as cq

import params as p


def _hex_pts(vertex_r: float):
    return p.polygon_pts(6, vertex_r)


def build_reef_board(positions):
    """positions: the SAME 37-point lattice list used for the pan dish cuts,
    the centre-socket cuts, and the seed/landing relief overlays."""
    slab = (
        cq.Workplane("XY")
        .polyline(_hex_pts(p.BOARD_VERTEX_R)).close()
        .extrude(p.BOARD_T)
    )
    slab = slab.edges("<Z").chamfer(p.BOARD_SKIRT_CHAMFER)

    dish_cutter = (
        cq.Workplane("XY").polyline(_hex_pts(p.PAN_VERTEX_R)).close()
        .extrude(p.PAN_DEPTH + 0.5)
    )
    socket_cutter = (
        cq.Workplane("XY").circle(p.PAN_SOCKET_D / 2.0)
        .extrude(p.PAN_SOCKET_DEPTH)
    )
    collar_ring = (
        cq.Workplane("XY").polyline(_hex_pts(p.PAN_VERTEX_R + 2.2)).close()
        .extrude(p.SEED_COLLAR_H)
        .cut(
            cq.Workplane("XY").polyline(_hex_pts(p.PAN_VERTEX_R)).close()
            .extrude(p.SEED_COLLAR_H + 0.2)
        )
    )
    barnacle_bump = cq.Workplane("XY").sphere(p.LANDING_BARNACLE_H)

    dish_top_z = p.BOARD_T
    dish_floor_z = p.BOARD_T - p.PAN_DEPTH

    for (x, y, ring, is_corner) in positions:
        dish = dish_cutter.translate((x, y, dish_top_z - p.PAN_DEPTH))
        slab = slab.cut(dish)
        socket = socket_cutter.translate((x, y, dish_floor_z - p.PAN_SOCKET_DEPTH))
        slab = slab.cut(socket)

        if ring in (0, 1, 2):  # 19 inner pans -- seed collar, raised
            collar = collar_ring.translate((x, y, dish_top_z))
            slab = slab.union(collar)
        elif is_corner:  # 6 landing-shelf corner pans -- barnacle cluster,
            # studding the DISH FLOOR (solid material below it) so the bumps
            # stay connected to the body rather than floating over the
            # already-cut pocket above.
            for a in range(0, 360, 72):
                bx = x + 8.0 * math.cos(math.radians(a))
                by = y + 8.0 * math.sin(math.radians(a))
                bump = barnacle_bump.translate((bx, by, dish_floor_z))
                slab = slab.union(bump)

    return slab
