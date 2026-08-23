"""millbind -- draft assembly.

A hexagonal yard bristling with 37 pins carries real meshing gears at two
tooth heights, four furrowed millstones, one crank, and the grain economy
that scores them. This draft stages a representative mid-game scene: the
crank driving a chain of low gears, a stand of high gears alive on the
other half of the yard, two tandem bridges, four millstones docked on the
rim, spare supply beside the board, and four spindles of grain at visibly
different heights.
"""
import cadquery as cq

import params as p
from blocks import add_piece_family, shared_positions
from board import build_yard_board
from gears import build_gear_low, build_gear_high, build_gear_tandem
from millstones import build_mill_gear
from crank import build_crank_gear
from misc import build_grain_pellet, build_sack_spindle, build_granary_bin


def gen_step():
    lattice = p.hex_lattice_positions(p.PIN_PITCH, 3)  # the ONE shared list
    ring0 = [pt for pt in lattice if pt[2] == 0]
    ring1 = [pt for pt in lattice if pt[2] == 1]
    ring2 = [pt for pt in lattice if pt[2] == 2]
    ring3 = [pt for pt in lattice if pt[2] == 3]

    asm = cq.Assembly()

    # --- yard_board: the pins are INTEGRAL to this one board part --------
    board_shape = build_yard_board(lattice)
    asm.add(board_shape, name="yard_board",
            loc=cq.Location(cq.Vector(0, 0, 0)))

    pin_top_z = p.SLAB_T  # pieces seat at the top of the 12mm slab

    # --- staged low-tier train on the ring-1 pins -------------------------
    gear_low_shape = build_gear_low()
    low_positions = [(x, y, pin_top_z) for (x, y, _r) in ring1]         # 6

    # --- staged high-tier stand + 2 tandem bridges on ring-2 pins --------
    gear_high_shape = build_gear_high()
    gear_tandem_shape = build_gear_tandem()
    ring2_sorted = ring2
    high_positions = [(x, y, pin_top_z) for (x, y, _r) in ring2_sorted[0:6]]
    tandem_positions = [(x, y, pin_top_z) for (x, y, _r) in ring2_sorted[6:8]]

    # --- millstones + crank on 5 of the 18 outer "yard pins" -------------
    mill_tri = build_mill_gear(3)
    mill_square = build_mill_gear(4)
    mill_penta = build_mill_gear(5)
    mill_hex = build_mill_gear(6)
    crank_shape = build_crank_gear()

    mx1, my1, _ = ring3[0]
    mx2, my2, _ = ring3[4]
    mx3, my3, _ = ring3[9]
    mx4, my4, _ = ring3[13]
    cx, cy, _ = ring3[7]

    asm.add(mill_tri, name="mill_gear_tri",
            loc=cq.Location(cq.Vector(mx1, my1, pin_top_z)))
    asm.add(mill_square, name="mill_gear_square",
            loc=cq.Location(cq.Vector(mx2, my2, pin_top_z)))
    asm.add(mill_penta, name="mill_gear_penta",
            loc=cq.Location(cq.Vector(mx3, my3, pin_top_z)))
    asm.add(mill_hex, name="mill_gear_hex",
            loc=cq.Location(cq.Vector(mx4, my4, pin_top_z)))
    asm.add(crank_shape, name="crank_gear",
            loc=cq.Location(cq.Vector(cx, cy, pin_top_z)))

    # --- remaining supply gears, piled beside the board (grid, not on the
    #     lattice -- these are in the open supply pile, not placed) -------
    used_low = len(low_positions)
    used_high = len(high_positions)
    used_tandem = len(tandem_positions)
    n_low_left = p.N_GEAR_LOW - used_low
    n_high_left = p.N_GEAR_HIGH - used_high
    n_tandem_left = p.N_GEAR_TANDEM - used_tandem

    pile_positions = shared_positions(cols=4, rows=3, pitch=38.0, z=0.0)
    pile_positions = [(x, y + 175.0, z) for (x, y, z) in pile_positions]
    idx = 0
    low_pile = [pile_positions[i] for i in range(idx, idx + n_low_left)]
    idx += n_low_left
    high_pile = [pile_positions[i] for i in range(idx, idx + n_high_left)]
    idx += n_high_left
    tandem_pile = [pile_positions[i] for i in range(idx, idx + n_tandem_left)]

    # One combined position list per family -> one add_piece_family call
    # per family, so the running _01, _02, ... index stays unique across
    # both the on-board pieces and the supply pile.
    add_piece_family(asm, gear_low_shape, low_positions + low_pile, "gear_low")
    add_piece_family(asm, gear_high_shape, high_positions + high_pile, "gear_high")
    add_piece_family(asm, gear_tandem_shape, tandem_positions + tandem_pile,
                      "gear_tandem")

    # --- four sack_spindles, one per player corner, stacked with grain at
    #     visibly different heights ---------------------------------------
    spindle_shape = build_sack_spindle()
    pellet_shape = build_grain_pellet()
    spindle_xy = [(-190, 130), (190, 130), (-190, -130), (190, -130)]
    pellet_counts = [9, 7, 4, 1]
    add_piece_family(asm, spindle_shape,
                      [(x, y, 0) for (x, y) in spindle_xy], "sack_spindle")

    pellet_positions = []
    for (sx, sy), n in zip(spindle_xy, pellet_counts):
        for i in range(n):
            z = p.SPINDLE_BASE_H + p.PELLET_H * (i + 0.5)
            pellet_positions.append((sx, sy, z))

    # --- remaining grain in the granary_bin -------------------------------
    bin_shape = build_granary_bin()
    bin_center = (0.0, -170.0, 0.0)
    asm.add(bin_shape, name="granary_bin",
            loc=cq.Location(cq.Vector(*bin_center)))

    n_bin_used = sum(pellet_counts)
    n_bin_left = p.N_GRAIN_PELLET - n_bin_used
    bin_x0, bin_y0, _ = bin_center
    for i in range(n_bin_left):
        # A loose pile, not a stack: small xy jitter but Z strictly
        # increasing by index so no two pellets ever occupy the same
        # volume, however their xy happens to land.
        px = bin_x0 + (i % 3 - 1) * 8
        py = bin_y0 + (i % 2) * 6 - 3
        pz = p.BIN_WALL + p.PELLET_H * (i + 0.5)
        pellet_positions.append((px, py, pz))

    add_piece_family(asm, pellet_shape, pellet_positions, "grain_pellet")

    return asm
