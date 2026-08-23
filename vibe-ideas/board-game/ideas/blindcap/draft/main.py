"""blindcap -- draft assembly.

A representative 2-player mid-game scene: two loam_tiles dovetailed
edge-to-edge, a dozen stools planted across their sockets (a mix of all
four species and all four owner marks -- every one of them the SAME body
above the collar, by construction, per stool.py), a few claim_crowns
already dropped on, and four probe_pins standing at two sockets -- one
pair fully proud (BLOCKED), one pair sunk low (ADMITTED), tilted along the
same 35deg hole axis loam_tile itself cuts, so the read is visible at a
glance. All four spore_troughs ring the board. Every part the bill
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
            positions.append(all_sockets[sidx])
            counters["board"] += 1
        else:
            positions.append(pile_positions[counters["pile"]])
            counters["pile"] += 1
    return positions


def _place_pin(pin_shape, center_xy, azimuth_deg, proud_mm, top_z):
    """Tilt the pin (built tip-at-origin, axis +Z toward the head) onto the
    same 35deg-from-vertical axis loam_tile cuts its holes on, then slide it
    along that axis so `proud_mm` of pin, measured axially from the head,
    sits above the tile's top face at the hole's entry point.
    """
    ang = math.radians(p.PROBE_ANGLE_DEG)
    az = math.radians(azimuth_deg)
    ux, uy, uz = math.sin(ang) * math.cos(az), math.sin(ang) * math.sin(az), math.cos(ang)

    cx, cy = center_xy
    ex = cx + p.PROBE_OFFSET * math.cos(az)
    ey = cy + p.PROBE_OFFSET * math.sin(az)

    entry_local_z = p.PIN_LEN - proud_mm
    ox, oy, oz = ux * entry_local_z, uy * entry_local_z, uz * entry_local_z
    tx, ty, tz = ex - ox, ey - oy, top_z - oz

    shape = pin_shape.rotate((0, 0, 0), (0, 1, 0), p.PROBE_ANGLE_DEG)
    shape = shape.rotate((0, 0, 0), (0, 0, 1), azimuth_deg)
    shape = shape.translate((tx, ty, tz))
    return shape


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
    crowned_stool_xy = []  # (x, y) of a few planted stools that get a crown

    for species in ("deadhead", "bracket", "inkcap", "hollow"):
        for owner in (1, 2, 3, 4):
            qty = p.STOOL_QTY[species]
            shape = build_stool(species, owner)
            name = f"stool_{species}_p{owner}"
            positions = _positions_for(species, owner, qty, counters,
                                        all_sockets, board_socket_idx, pile_positions)
            add_piece_family(asm, shape, positions, name)
            for (x, y, z) in positions:
                if abs(z - p.TILE_T) < 1e-6 and len(crowned_stool_xy) < 3:
                    crowned_stool_xy.append((x, y))

    # --- claim_crown: 3 dropped onto planted stools, 9 in supply ----------
    crown_board_positions = [(x, y, p.TILE_T + p.STOOL_H) for (x, y) in crowned_stool_xy]
    crown_pile = shared_positions(cols=3, rows=3, pitch=26.0, z=0.0)
    crown_pile = [(x + 200.0, y + 195.0, 0.0) for (x, y, z) in crown_pile]
    crown_positions = crown_board_positions + crown_pile[: p.N_CROWN - len(crown_board_positions)]
    for i, (cx, cy, cz) in enumerate(crown_positions, 1):
        holes = (i % 4) + 1
        asm.add(build_claim_crown(holes), name=f"claim_crown_{i:02d}",
                loc=cq.Location(cq.Vector(cx, cy, cz)))

    # --- probe_pin: 4 staged at two sockets (blocked pair + admitted pair),
    #     12 racked in a supply row -------------------------------------
    pin_shape = build_probe_pin()
    top_z = p.TILE_T
    socket_blocked = all_sockets[0]
    socket_admitted = all_sockets[9]
    # params.PIN_PROUD_ADMITTED_MM (3mm) is the brief-accurate target for
    # build-stage `slides` fit_checks, where the hole/groove geometry is
    # solved exactly. For this draft's staged visual, back it off slightly
    # so the disc head clears the collar with real margin -- the point is
    # "visibly much lower than blocked", not the exact millimetre.
    staged_admitted_proud = 9.0
    staged = [
        _place_pin(pin_shape, socket_blocked[:2], 45.0, p.PIN_PROUD_BLOCKED_MM, top_z),
        _place_pin(pin_shape, socket_blocked[:2], 225.0, p.PIN_PROUD_BLOCKED_MM, top_z),
        _place_pin(pin_shape, socket_admitted[:2], 45.0, staged_admitted_proud, top_z),
        _place_pin(pin_shape, socket_admitted[:2], 225.0, staged_admitted_proud, top_z),
    ]
    for i, shape in enumerate(staged, 1):
        asm.add(shape, name=f"probe_pin_{i:02d}")

    rack_positions = [(x, -195.0, 0.0) for (x, _y, _z) in
                       shared_positions(cols=12, rows=1, pitch=14.0, z=0.0)]
    for j, (x, y, z) in enumerate(rack_positions[: p.N_PIN - len(staged)],
                                   start=len(staged) + 1):
        asm.add(pin_shape, name=f"probe_pin_{j:02d}", loc=cq.Location(cq.Vector(x, y, z)))

    # --- four spore_troughs ring the board, close in so the tile+stool
    #     mechanic still reads as the dominant shape in the hero frame ----
    trough_defs = [
        (0.0, 115.0, 0.0, 180.0, 1),
        (0.0, -115.0, 0.0, 0.0, 2),
        (180.0, 0.0, 0.0, 90.0, 3),
        (-180.0, 0.0, 0.0, -90.0, 4),
    ]
    for i, (tx, ty, tz, rot, owner) in enumerate(trough_defs, 1):
        shape = build_spore_trough_with_owner(owner)
        shape = shape.rotate((0, 0, 0), (0, 0, 1), rot)
        asm.add(shape, name=f"spore_trough_{i:02d}",
                loc=cq.Location(cq.Vector(tx, ty, tz)))

    return asm
