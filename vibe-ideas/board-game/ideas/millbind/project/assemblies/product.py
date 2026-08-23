"""Positioning of Millbind's separately printable / loose parts.

All part GEOMETRY lives in parts/; this module only places named copies in
the product frame, per cadcode's assembly discipline. Every pin position
(board pins, staged supply gears, millstones, the crank) reuses the ONE
shared 37-point lattice (features.lattice.hex_lattice_positions) that
yard_board itself was cut from -- a seated piece and its pin never drift
apart.

Staged as a representative mid-round scene: the crank driving a chain of
low gears, a stand of high gears alive on the other half of the yard (plus
the two scarce tandem bridges), four millstones docked on the rim, spare
supply gears piled beside the board, and four spindles of grain at visibly
different heights next to the granary_bin.
"""
from __future__ import annotations

import cadquery as cq

from params import Params
from blocks import add_piece_family, shared_positions
from features.lattice import hex_lattice_positions

from parts.board import make_yard_board
from parts.gears import make_gear_low, make_gear_high, make_gear_tandem
from parts.millstone import make_mill_gear
from parts.crank import make_crank_gear
from parts.misc import make_grain_pellet, make_sack_spindle, make_granary_bin


def make_assembly(p: Params) -> cq.Assembly:
    lattice = hex_lattice_positions(p.pin_pitch, p.n_rings)  # the ONE shared list
    ring0 = [pt for pt in lattice if pt[2] == 0]
    ring1 = [pt for pt in lattice if pt[2] == 1]
    ring2 = [pt for pt in lattice if pt[2] == 2]
    ring3 = [pt for pt in lattice if pt[2] == 3]
    assert len(ring0) == 1 and len(ring1) == 6 and len(ring2) == 12 and len(ring3) == 18

    asm = cq.Assembly()

    # --- yard_board: the 37 pins are INTEGRAL to this one board part -------
    board_shape = make_yard_board(p, lattice)
    asm.add(board_shape, name="yard_board",
            loc=cq.Location(cq.Vector(0, 0, 0)),
            color=cq.Color(0.30, 0.30, 0.32))

    pin_top_z = p.slab_t  # pieces seat at the top of the slab

    # --- staged low-tier train on the ring-1 pins --------------------------
    gear_low_shape = make_gear_low(p)
    low_positions = [(x, y, pin_top_z) for (x, y, _r) in ring1]  # 6

    # --- staged high-tier stand + 2 tandem bridges on ring-2 pins ----------
    gear_high_shape = make_gear_high(p)
    gear_tandem_shape = make_gear_tandem(p)
    high_positions = [(x, y, pin_top_z) for (x, y, _r) in ring2[0:6]]
    tandem_positions = [(x, y, pin_top_z) for (x, y, _r) in ring2[6:8]]

    # --- four millstones + the crank on 5 of the 18 outer "yard pins" ------
    mill_colors = {3: (0.55, 0.30, 0.20), 4: (0.55, 0.42, 0.20),
                   5: (0.45, 0.45, 0.22), 6: (0.35, 0.42, 0.45)}
    mill_shapes = {n: make_mill_gear(p, n) for n in (3, 4, 5, 6)}
    crank_shape = make_crank_gear(p)

    mill_pin_idx = {"mill_gear_tri": 0, "mill_gear_square": 4,
                    "mill_gear_penta": 9, "mill_gear_hex": 13}
    crank_pin_idx = 7

    for name, n_flats in (("mill_gear_tri", 3), ("mill_gear_square", 4),
                           ("mill_gear_penta", 5), ("mill_gear_hex", 6)):
        mx, my, _ = ring3[mill_pin_idx[name]]
        asm.add(mill_shapes[n_flats], name=name,
                loc=cq.Location(cq.Vector(mx, my, pin_top_z)),
                color=cq.Color(*mill_colors[n_flats]))

    cx, cy, _ = ring3[crank_pin_idx]
    asm.add(crank_shape, name="crank_gear",
            loc=cq.Location(cq.Vector(cx, cy, pin_top_z)),
            color=cq.Color(0.75, 0.65, 0.25))

    # --- remaining supply gears, piled beside the board (a grid, not on the
    #     lattice -- this is the open supply pile, not placed pieces) ------
    used_low = len(low_positions)
    used_high = len(high_positions)
    used_tandem = len(tandem_positions)
    n_low_left = p.n_gear_low - used_low
    n_high_left = p.n_gear_high - used_high
    n_tandem_left = p.n_gear_tandem - used_tandem

    pile_positions = shared_positions(cols=4, rows=3, pitch=38.0, z=0.0)
    pile_positions = [(x, y + 175.0, z) for (x, y, z) in pile_positions]
    idx = 0
    low_pile = [pile_positions[i] for i in range(idx, idx + n_low_left)]
    idx += n_low_left
    high_pile = [pile_positions[i] for i in range(idx, idx + n_high_left)]
    idx += n_high_left
    tandem_pile = [pile_positions[i] for i in range(idx, idx + n_tandem_left)]

    # One combined position list per family -> one add_piece_family call per
    # family, so the running _01, _02, ... index stays unique across both
    # the on-board pieces and the supply pile.
    add_piece_family(asm, gear_low_shape, low_positions + low_pile, "gear_low")
    add_piece_family(asm, gear_high_shape, high_positions + high_pile, "gear_high")
    add_piece_family(asm, gear_tandem_shape, tandem_positions + tandem_pile,
                      "gear_tandem")

    # --- four sack_spindles, one per player corner, stacked with grain at
    #     visibly different heights -----------------------------------------
    spindle_shape = make_sack_spindle(p)
    pellet_shape = make_grain_pellet(p)
    spindle_xy = [(-190, 130), (190, 130), (-190, -130), (190, -130)]
    pellet_counts = [9, 7, 4, 1]
    add_piece_family(asm, spindle_shape,
                      [(x, y, 0) for (x, y) in spindle_xy], "sack_spindle")

    pellet_positions = []
    for (sx, sy), n in zip(spindle_xy, pellet_counts):
        for i in range(n):
            z = p.spindle_base_h + p.pellet_h * (i + 0.5)
            pellet_positions.append((sx, sy, z))

    # --- remaining grain in the granary_bin ---------------------------------
    bin_shape = make_granary_bin(p)
    bin_center = (0.0, -170.0, 0.0)
    asm.add(bin_shape, name="granary_bin",
            loc=cq.Location(cq.Vector(*bin_center)),
            color=cq.Color(0.40, 0.30, 0.20))

    n_bin_used = sum(pellet_counts)
    n_bin_left = p.n_grain_pellet - n_bin_used
    bin_x0, bin_y0, _ = bin_center
    for i in range(n_bin_left):
        # A loose pile, not a stack: small xy jitter but Z strictly
        # increasing by index so no two pellets ever occupy the same
        # volume, however their xy happens to land.
        px = bin_x0 + (i % 3 - 1) * 8
        py = bin_y0 + (i % 2) * 6 - 3
        pz = p.bin_wall + p.pellet_h * (i + 0.5)
        pellet_positions.append((px, py, pz))

    add_piece_family(asm, pellet_shape, pellet_positions, "grain_pellet")

    return asm
