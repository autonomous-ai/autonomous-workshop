"""Millbind -- project entrypoint.

Order: load Params -> validate (hard asserts on every bill number) -> build
the assembly -> return the envelope the runner exports as STEP/STL.
"""
from __future__ import annotations

from params import Params
from validation import functional_warnings, validate_params
from assemblies.product import make_assembly


PART_DESCRIPTIONS = {
    "yard_board": "Hexagonal mill floor, 37 integral pins, 18 outer pins ringed with a raised sill",
    "gear_low": "Low-tier supply gear, teeth start at the floor, partial pin engagement",
    "gear_high": "High-tier supply gear, lamppost column with teeth at the top",
    "gear_tandem": "Full-height supply gear that bridges both tooth tiers",
    "mill_gear_tri": "Millstone, three-sided hub -- a player's identity mark",
    "mill_gear_square": "Millstone, four-sided hub",
    "mill_gear_penta": "Millstone, five-sided hub",
    "mill_gear_hex": "Millstone, six-sided hub",
    "crank_gear": "The only power in the box -- offset arm, knurled knob, direction arrow",
    "grain_pellet": "Score washer, threads onto a sack_spindle",
    "sack_spindle": "Player score post, holds up to 12 grain_pellet",
    "granary_bin": "Open bin holding the loose grain_pellet supply",
}


def gen_step():
    p = Params()
    validate_params(p)
    return {"shape": make_assembly(p), "warnings": functional_warnings(p)}
