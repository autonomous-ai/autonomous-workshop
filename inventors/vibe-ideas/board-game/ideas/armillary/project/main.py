"""Armillary — project entrypoint.

Order: load Params -> validate (hard asserts on every bill number) ->
build the assembly -> return the envelope the runner exports as STEP/STL.
"""
from __future__ import annotations

from params import Params
from validation import functional_warnings, validate_params
from assemblies.product import make_assembly


PART_DESCRIPTIONS = {
    "plinth_ring": "Drum plinth: ten face-down tile wells on an 80mm ring + central axle post",
    "mask_disc_a": "Bottom rotating mask, broad rounded paddle grip-tab",
    "mask_disc_b": "Middle rotating mask, pointed triangular fin grip-tab",
    "mask_disc_c": "Top rotating mask, notched double-prong grip-tab",
    "reserve_column_lower": "Tile silo obelisk, base segment (0-180mm), spigot tenon on top",
    "reserve_column_upper": "Tile silo obelisk, cap segment (180-306mm), socket + chamfered mouth",
    "score_rail_tri": "Player score rail, triangular finial",
    "score_rail_square": "Player score rail, square finial",
    "score_rail_penta": "Player score rail, pentagonal finial",
    "score_rail_hex": "Player score rail, hexagonal finial",
}


def gen_step():
    p = Params()
    validate_params(p)
    return {"shape": make_assembly(p), "warnings": functional_warnings(p)}
