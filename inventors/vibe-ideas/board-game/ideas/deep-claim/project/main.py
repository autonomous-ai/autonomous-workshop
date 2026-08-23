"""Deep Claim -- draft entrypoint. See board-game/ideas/deep-claim/brief.json."""
from __future__ import annotations

from params import Params
from validation import functional_warnings, validate_params
from assemblies.product import make_assembly

PART_DESCRIPTIONS = {
    "assay_board": "190mm slab, six two-stage assay bores on a 62mm ring, radial vein relief + witness collars.",
    "disc_large_mark3": "Broad puck, 28x9mm, 3 ownership studs. Catches a bore's shelf, seals it forever.",
    "disc_large_mark4": "Broad puck, 28x9mm, 4 ownership studs.",
    "disc_large_mark5": "Broad puck, 28x9mm, 5 ownership studs.",
    "disc_large_mark6": "Broad puck, 28x9mm, 6 ownership studs.",
    "disc_small_mark3": "Slim puck, 14x8mm, 3 ownership studs. Passes an open shelf, rests on the floor.",
    "disc_small_mark4": "Slim puck, 14x8mm, 4 ownership studs.",
    "disc_small_mark5": "Slim puck, 14x8mm, 5 ownership studs.",
    "disc_small_mark6": "Slim puck, 14x8mm, 6 ownership studs.",
}


def gen_step():
    p = Params()
    validate_params(p)
    return {"shape": make_assembly(p), "warnings": functional_warnings(p)}
