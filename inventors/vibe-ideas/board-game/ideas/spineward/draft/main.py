"""spineward -- draft assembly.

A reef of 37 hexagonal pans carries four domed urchin shells (one per
player, identified by a 3/4/5/6-flat grip-knob prism), each shell's six
sockets filled with a mix of spines (quills) and pearls (cargo). A couple
of empty pans show off the pan lattice itself; two more pans carry a lone
pearl straight on the reef. Four pearl racks (one per player, finial
matching that player's shell) sit around the board, two holding a pearl.
The tide_pot sits off to one side with the loose spine supply spilling
into its scalloped tray and two pearls still inside its blind drum,
waiting to be drawn.
"""
import math

import cadquery as cq

import params as p
from blocks import add_piece_family
from reef_board import build_reef_board
from urchin_shell import build_urchin_shell, shell_socket_positions
from spine import build_spine
from pearl import build_pearl
from pearl_rack import build_pearl_rack, well_positions
from tide_pot import build_tide_pot


def gen_step():
    lattice = p.hex_lattice_positions(p.PAN_PITCH, p.PAN_RINGS)  # ONE shared list, 37 pts

    asm = cq.Assembly()

    # --- reef_board ---------------------------------------------------
    asm.add(build_reef_board(lattice), name="reef_board",
            loc=cq.Location(cq.Vector(0, 0, 0)))

    dish_floor_z = p.BOARD_T - p.PAN_DEPTH        # 11
    pan_socket_bottom_z = dish_floor_z - p.PAN_SOCKET_DEPTH  # 1
    shell_socket_bottom_z = dish_floor_z + (p.SHELL_DOME_H - p.SHELL_SOCKET_DEPTH)  # 17

    # --- pearl grade queue: consumed in placement order, exactly matching
    #     the brief's 8/5/3 counts ------------------------------------
    grade_queue = [1] * p.N_PEARL_ONE + [2] * p.N_PEARL_TWO + [3] * p.N_PEARL_THREE
    pearl_positions = {1: [], 2: [], 3: []}

    def take_pearl(x, y, z):
        g = grade_queue.pop(0)
        pearl_positions[g].append((x, y, z))

    # --- 4 urchin_shells, one per pan index, each with a distinct
    #     grip-knob identity, sockets filled with a spine/pearl mix -----
    shell_pan_idx = [0, 3, 12, 25]
    shell_split = [(4, 2), (3, 3), (5, 1), (2, 4)]  # (n_spine, n_pearl) per shell, sums to 6

    spine_positions = []
    for shell_i, (pan_i, (n_spine, n_pearl)) in enumerate(zip(shell_pan_idx, shell_split)):
        n_flats = p.SHELL_FLATS[shell_i]
        shell_shape = build_urchin_shell(n_flats)
        sx, sy = lattice[pan_i][0], lattice[pan_i][1]
        asm.add(shell_shape, name=f"urchin_shell_{shell_i + 1:02d}",
                loc=cq.Location(cq.Vector(sx, sy, dish_floor_z)))

        sockets = shell_socket_positions()  # 6 local (dx, dy) offsets
        for k, (dx, dy) in enumerate(sockets):
            wx, wy, wz = sx + dx, sy + dy, shell_socket_bottom_z
            if k < n_spine:
                spine_positions.append((wx, wy, wz))
            else:
                take_pearl(wx, wy, wz)

    # --- 2 pans carry a lone pearl straight on the reef ----------------
    board_pearl_pan_idx = [2, 15]
    for pan_i in board_pearl_pan_idx:
        bx, by = lattice[pan_i][0], lattice[pan_i][1]
        take_pearl(bx, by, pan_socket_bottom_z)

    # --- 4 pearl_racks around the board, finial matching each shell ----
    rack_r = p.BOARD_VERTEX_R + p.RACK_L / 2.0 + 6.0
    rack_defs = [
        ("north", (0.0, rack_r), 0.0),
        ("south", (0.0, -rack_r), 180.0),
        ("east", (rack_r, 0.0), 90.0),
        ("west", (-rack_r, 0.0), -90.0),
    ]
    rack_gets_pearl = [True, False, True, False]
    for i, ((label, (rx, ry), ang_deg), give_pearl) in enumerate(
            zip(rack_defs, rack_gets_pearl)):
        n_flats = p.RACK_FLATS[i]
        rack_shape = build_pearl_rack(n_flats)
        pos = cq.Vector(rx, ry, 0.0)
        asm.add(rack_shape, name=f"pearl_rack_{i + 1:02d}",
                loc=cq.Location(pos, cq.Vector(0, 0, 1), ang_deg))
        if give_pearl:
            wdx, wdy, _ = well_positions()[0]
            # rotate the local well offset by ang_deg to match the rack's
            # placed orientation
            a = math.radians(ang_deg)
            wx = rx + wdx * math.cos(a) - wdy * math.sin(a)
            wy = ry + wdx * math.sin(a) + wdy * math.cos(a)
            take_pearl(wx, wy, p.RACK_H)

    # --- tide_pot, tucked in the NE gap between the north and east racks
    #     (closer to the board than stacking it past a rack): loose spine
    #     supply in the tray, 2 pearls still inside the drum ------------
    pot_r = 195.0
    pot_center = (pot_r * math.cos(math.radians(45.0)),
                  pot_r * math.sin(math.radians(45.0)), 0.0)
    asm.add(build_tide_pot(), name="tide_pot",
            loc=cq.Location(cq.Vector(*pot_center)))

    n_spare_spine = p.N_SPINE - len(spine_positions)
    tray_ring_r = p.POT_DRUM_D / 2.0 + (p.POT_TRAY_D / 2.0 - p.POT_DRUM_D / 2.0) * 0.55
    for i in range(n_spare_spine):
        a = math.radians(i * 360.0 / n_spare_spine)
        px = pot_center[0] + tray_ring_r * math.cos(a)
        py = pot_center[1] + tray_ring_r * math.sin(a)
        spine_positions.append((px, py, pot_center[2] + p.POT_TRAY_H))

    for i in range(2):
        a = math.radians(90.0 + i * 180.0)
        px = pot_center[0] + 15.0 * math.cos(a)
        py = pot_center[1] + 15.0 * math.sin(a)
        take_pearl(px, py, pot_center[2] + p.POT_DRUM_H - p.PEARL_TOTAL_H + 6.0)

    # --- place every family as SEPARATELY NAMED assembly children -----
    add_piece_family(asm, build_spine(), spine_positions, "spine")
    add_piece_family(asm, build_pearl(1), pearl_positions[1], "pearl_one_ring")
    add_piece_family(asm, build_pearl(2), pearl_positions[2], "pearl_two_ring")
    add_piece_family(asm, build_pearl(3), pearl_positions[3], "pearl_three_ring")

    assert len(grade_queue) == 0, "every pearl in the bill must be placed"
    assert len(spine_positions) == p.N_SPINE

    return asm
