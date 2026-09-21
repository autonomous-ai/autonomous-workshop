"""Rainward Sunflare review entry: fifty-five loose solids in one presentation state.

RAINWARD_STATE selects setup, before, after, or board (the Sun and its tiles
with no counters); RAINWARD_TONE=neutral renders the single-material evidence
view. Not a print target: print the part entries.
"""
import os

from assemblies.product import assembly

PRINTABLE = False


def gen_step():
    state = os.environ.get("RAINWARD_STATE", "setup")
    if state not in ("setup", "before", "after", "board"):
        raise ValueError("RAINWARD_STATE must be setup, before, after or board")
    neutral = os.environ.get("RAINWARD_TONE", "colour") == "neutral"
    return assembly(state, neutral=neutral)
