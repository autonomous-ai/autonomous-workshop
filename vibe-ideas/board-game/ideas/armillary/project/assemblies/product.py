"""Positioning of Armillary's separately printable / loose parts.

All part GEOMETRY lives in parts/; this module only places named copies in
the product frame, per cadcode's assembly discipline. Tile positions reuse
the ONE shared radial ring list (features.ring) — the same list plinth_ring
cut its wells from — so a seeded tile and its well never drift apart.

Each tile family is added to the assembly with exactly ONE
`add_piece_family` call over its FULL position list (setup wells + reserve
stack combined), so the numbering `star_tile_01..star_tile_12` stays one
continuous sequence instead of two calls colliding on the same suffixes.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params
from blocks import add_piece_family
from features.ring import RING_XY

from parts.plinth_ring import make_plinth_ring
from parts.mask_disc import make_mask_disc_a, make_mask_disc_b, make_mask_disc_c
from parts.tile import make_star_tile, make_moon_tile, make_void_tile
from parts.reserve_column import make_reserve_column_lower, make_reserve_column_upper
from parts.score_rail import (
    make_score_rail_tri, make_score_rail_square,
    make_score_rail_penta, make_score_rail_hex,
)


# Distribution of the ten wells seeded at setup (rules: "drop one tile
# knob-up into each of the ten wells"). Indices refer to the shared ring.
_SEEDED_STAR = (0, 1, 2, 3)
_SEEDED_MOON = (4, 5, 6)
_SEEDED_VOID = (7, 8, 9)

_COLUMN_CENTER = (178.0, 0.0, 0.0)
_RAIL_R = 155.0


def _mask_disc_colors() -> dict:
    return {
        "mask_disc_a": cq.Color(0.72, 0.55, 0.25),
        "mask_disc_b": cq.Color(0.80, 0.63, 0.30),
        "mask_disc_c": cq.Color(0.87, 0.70, 0.35),
    }


def _reserve_slot_position(global_index: int, p: Params) -> tuple[float, float, float]:
    """One position for the Nth reserve tile (0-based, counted across all
    three families in one stream). idea.json's 150mm column height and its
    20-tile reserve capacity don't reconcile against a single stacking
    pitch (flagged in brief.json's unstated_in_spec) — a true non-colliding
    stack (15mm pitch = 6mm body + 9mm knob) only fits
    floor(column_h / 15) tiles inside the bore. Tiles beyond that land in a
    flat, non-overlapping waiting grid beside the column instead of forcing
    a shorter pitch that would visibly interpenetrate."""
    true_pitch = p.tile_thickness + p.knob_h
    inside_count = int((p.column_h - p.column_top_chamfer * 2) // true_pitch)
    cx, cy, _ = _COLUMN_CENTER

    if global_index < inside_count:
        return (cx, cy, global_index * true_pitch)

    outside_index = global_index - inside_count
    cols = 4
    spacing = p.tile_dia + 4.0
    row, col = divmod(outside_index, cols)
    gx = cx + 42.0 + col * spacing
    gy = cy - 46.0 - row * spacing
    return (gx, gy, 0.0)


def _tile_positions(p: Params, seeded_indices: tuple[int, ...], reserve_count: int,
                     reserve_offset: int) -> list[tuple[float, float, float]]:
    well_floor_z = p.plinth_drum_h - p.well_depth
    seeded = [(*RING_XY[i], well_floor_z) for i in seeded_indices]
    reserve = [_reserve_slot_position(reserve_offset + i, p) for i in range(reserve_count)]
    return seeded + reserve


def make_assembly(p: Params) -> cq.Assembly:
    asm = cq.Assembly()

    # ---- plinth_ring ----------------------------------------------------
    asm.add(make_plinth_ring(p), name="plinth_ring", color=cq.Color(0.55, 0.38, 0.15))

    # ---- three stacked mask discs, each rotated a different amount so the
    # hero render reads as "mid-session" rather than a static setup pose.
    colors = _mask_disc_colors()
    asm.add(make_mask_disc_a(p), name="mask_disc_a",
            loc=cq.Location(cq.Vector(0, 0, p.plinth_drum_h)),
            color=colors["mask_disc_a"])
    asm.add(make_mask_disc_b(p), name="mask_disc_b",
            loc=cq.Location(cq.Vector(0, 0, p.plinth_drum_h + p.disc_rim_h),
                             cq.Vector(0, 0, 1), 72.0),
            color=colors["mask_disc_b"])
    asm.add(make_mask_disc_c(p), name="mask_disc_c",
            loc=cq.Location(cq.Vector(0, 0, p.plinth_drum_h + 2 * p.disc_rim_h),
                             cq.Vector(0, 0, 1), 36.0),
            color=colors["mask_disc_c"])

    # ---- tiles: ten seeded knob-up in the wells (reusing the ring list
    # plinth_ring's wells were cut from) + the 20 remaining stacked knob-up
    # in reserve_column. One add_piece_family call per family, over the
    # combined position list, keeps the numbering contiguous.
    reserve_star = p.tile_counts["star_tile"] - len(_SEEDED_STAR)
    reserve_moon = p.tile_counts["moon_tile"] - len(_SEEDED_MOON)
    reserve_void = p.tile_counts["void_tile"] - len(_SEEDED_VOID)

    star_positions = _tile_positions(p, _SEEDED_STAR, reserve_star, 0)
    moon_positions = _tile_positions(p, _SEEDED_MOON, reserve_moon, reserve_star)
    void_positions = _tile_positions(p, _SEEDED_VOID, reserve_void, reserve_star + reserve_moon)

    add_piece_family(asm, make_star_tile(p), star_positions, "star_tile")
    add_piece_family(asm, make_moon_tile(p), moon_positions, "moon_tile")
    add_piece_family(asm, make_void_tile(p), void_positions, "void_tile")

    # ---- reserve_column, standing off to one side, holding the 20
    # reserve tiles stacked knob-up inside its bore. AMENDED: 306mm now
    # exceeds the 251mm bed z-limit as one print, so it is TWO separately
    # named printed segments (lower carries the base taper, upper carries
    # the shaft + chamfered mouth), registered on each other by a spigot/
    # socket seam built into both parts' own geometry (see
    # parts/reserve_column.py) -- positioned here so the upper segment's
    # local z=0 sits flush at column_seg_lower_h in world Z, matching
    # exactly where its socket meets the lower segment's tenon.
    column_color = cq.Color(0.30, 0.28, 0.33)
    cx, cy, cz = _COLUMN_CENTER
    asm.add(make_reserve_column_lower(p), name="reserve_column_lower",
            loc=cq.Location(cq.Vector(cx, cy, cz)),
            color=column_color)
    asm.add(make_reserve_column_upper(p), name="reserve_column_upper",
            loc=cq.Location(cq.Vector(cx, cy, cz + p.column_seg_lower_h)),
            color=column_color)

    # ---- four score rails, one per seat, ringed TANGENTIALLY around the
    # plinth (like seats around a table) so each sits close in without its
    # 130mm length reaching past the disc grip-tabs radially. Angles are
    # spaced away from 0 deg, which is where reserve_column and
    # mask_disc_a's grip-tab both sit.
    rail_defs = [
        ("score_rail_tri", make_score_rail_tri(p), 72.0),
        ("score_rail_square", make_score_rail_square(p), 144.0),
        ("score_rail_penta", make_score_rail_penta(p), 216.0),
        ("score_rail_hex", make_score_rail_hex(p), 288.0),
    ]
    for name, shape, ang_deg in rail_defs:
        ang = math.radians(ang_deg)
        pos = cq.Vector(_RAIL_R * math.cos(ang), _RAIL_R * math.sin(ang), 0)
        asm.add(shape, name=name,
                loc=cq.Location(pos, cq.Vector(0, 0, 1), ang_deg + 90.0),
                color=cq.Color(0.65, 0.50, 0.22))

    return asm
