"""Blindcap: Duel -- exact two-player draft assembly.

A legal 2-player end-of-main-round scene: two loam_tiles dovetailed
edge-to-edge, a dozen stools planted across their sockets (a mix of all
four species and both owner marks -- every one of them the SAME body
above the collar, by construction, per stool.py), four claim_crowns
on rival stools, and all six owner-marked probes on rival stools -- one
pair visibly high (BLOCKED), the admitted pins exactly 3mm proud, tilted along the
same 70deg-from-vertical axis loam_tile itself cuts, so the read is visible at a
glance. Two spore_troughs frame the board. Every part the bill
requires is present: what is not staged on the board sits in a supply
pile beside it.
"""
import math

import cadquery as cq

import params as p
from blocks import add_piece_family, shared_positions
from loam_tile import build_loam_tile
from stool import build_stool
from claim_crown import build_claim_crown
from probe_pin import build_probe_pin
from spore_trough import build_spore_trough_with_owner


def _positions_for(species, owner, qty, counters, all_sockets, board_socket_idx,
                    pile_positions):
    positions = []
    for _ in range(qty):
        if counters["board"] < len(board_socket_idx):
            sidx = board_socket_idx[counters["board"]]
            x, y, _z = all_sockets[sidx]
            positions.append((x, y, p.SEATED_STOOL_Z))
            counters["board"] += 1
        else:
            positions.append(pile_positions[counters["pile"]])
            counters["pile"] += 1
    return positions


def _pin_location(center_xy, bit, proud_mm, top_z):
    """Return the assembly transform for one staged probe.

    Keeping the rigid pose in ``loc`` rather than baking it into the prototype
    preserves a canonical upright per-occurrence STL for the slicer while the
    assembled reader remains in the exact same world pose.
    """
    index = p.PROBE_BITS.index(bit)
    mx, my = p.PROBE_MOUTHS_XY[index]
    hx, hy = p.PROBE_INWARD_XY[index]
    ang = math.radians(p.PROBE_ANGLE_DEG)
    outward_azimuth_deg = math.degrees(math.atan2(-hy, -hx))
    ux, uy, uz = -math.sin(ang) * hx, -math.sin(ang) * hy, math.cos(ang)

    cx, cy = center_xy
    ex, ey = cx + mx, cy + my

    entry_local_z = p.PIN_LEN - proud_mm
    ox, oy, oz = ux * entry_local_z, uy * entry_local_z, uz * entry_local_z
    tx, ty, tz = ex - ox, ey - oy, top_z - oz

    return (
        cq.Location(cq.Vector(tx, ty, tz))
        * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), outward_azimuth_deg)
        * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), p.PROBE_ANGLE_DEG)
    )


def gen_step():
    asm = cq.Assembly()

    socket_positions = shared_positions(p.SOCKET_COLS, p.SOCKET_ROWS, p.SOCKET_PITCH,
                                         z=p.TILE_T)

    # --- two loam_tiles, dovetailed edge-to-edge (2-player setup) --------
    tile_shape = build_loam_tile(socket_positions)
    tile_centers = [(-p.TILE_SIZE / 2.0, 0.0, 0.0), (p.TILE_SIZE / 2.0, 0.0, 0.0)]
    add_piece_family(asm, tile_shape, tile_centers, "loam_tile")

    # global socket centres across both tiles, in board order
    all_sockets = []
    for (tcx, tcy, _tz) in tile_centers:
        for (sx, sy, sz) in socket_positions:
            all_sockets.append((tcx + sx, tcy + sy, sz))

    # stage 12 of the 18 sockets, leaving 6 empty so the socket/collar/
    # probe-hole detail is still visible in the hero render
    board_socket_idx = [0, 1, 2, 4, 5, 6, 8, 9, 11, 13, 15, 17]

    pile_positions = shared_positions(cols=4, rows=3, pitch=38.0, z=0.0)
    pile_positions = [(x + 200.0, y - 195.0, z) for (x, y, z) in pile_positions]

    counters = {"board": 0, "pile": 0}
    for species in ("deadhead", "bracket", "inkcap", "hollow"):
        for owner in (1, 2):
            qty = p.STOOL_QTY[species]
            shape = build_stool(species, owner)
            name = f"stool_{species}_p{owner}"
            positions = _positions_for(species, owner, qty, counters,
                                        all_sockets, board_socket_idx, pile_positions)
            add_piece_family(asm, shape, positions, name)
    # Four legal main-round crowns: two P1 crowns on P2 stools and two P2
    # crowns on P1 stools. Each player's third crown remains reserved.
    crown_board = [(1, 2), (1, 4), (2, 1), (2, 5)]
    crown_index = {1: 0, 2: 0}
    for owner, socket_id in crown_board:
        crown_index[owner] += 1
        cx, cy, _ = all_sockets[socket_id]
        asm.add(build_claim_crown(owner), name=f"claim_crown_p{owner}_{crown_index[owner]:02d}",
                loc=cq.Location(cq.Vector(cx, cy, p.SEATED_CROWN_Z)))
    for owner, x in ((1, 176.0), (2, 204.0)):
        crown_index[owner] += 1
        asm.add(build_claim_crown(owner), name=f"claim_crown_p{owner}_{crown_index[owner]:02d}",
                loc=cq.Location(cq.Vector(x, 88.0, 0.0)))

    # All six probes are legally spent on rival stools. P2 probes P1's
    # Deadhead (A/B blocked) and Inkcap (B admitted); P1 probes P2's Hollow
    # (A/B admitted) and Bracket (A admitted).
    pins = {1: build_probe_pin(1), 2: build_probe_pin(2)}
    top_z = p.TILE_T
    staged_defs = [
        (2, 0, "A", p.PIN_PROUD_BLOCKED_MM),
        (2, 0, "B", p.PIN_PROUD_BLOCKED_MM),
        (2, 11, "B", p.PIN_PROUD_ADMITTED_MM),
        (1, 17, "A", p.PIN_PROUD_ADMITTED_MM),
        (1, 17, "B", p.PIN_PROUD_ADMITTED_MM),
        (1, 8, "A", p.PIN_PROUD_ADMITTED_MM),
    ]
    owner_pin_index = {1: 0, 2: 0}
    for owner, socket_id, bit, proud in staged_defs:
        owner_pin_index[owner] += 1
        loc = _pin_location(all_sockets[socket_id][:2], bit, proud, top_z)
        # A numeric suffix lets the canonical gate collapse occurrences to
        # the owner-specific probe_pin_p1 / probe_pin_p2 moving families.
        asm.add(pins[owner], name=f"probe_pin_p{owner}_{owner_pin_index[owner]:02d}",
                loc=loc)

    # --- two spore_troughs frame the board, close in so the tile+stool
    #     mechanic still reads as the dominant shape in the hero frame ----
    trough_defs = [
        (0.0, 150.0, 0.0, 180.0, 1),
        (0.0, -150.0, 0.0, 0.0, 2),
    ]
    for i, (tx, ty, tz, rot, owner) in enumerate(trough_defs, 1):
        shape = build_spore_trough_with_owner(owner)
        shape = shape.rotate((0, 0, 0), (0, 0, 1), rot)
        asm.add(shape, name=f"spore_trough_p{owner}_01",
                loc=cq.Location(cq.Vector(tx, ty, tz)))

    return asm
