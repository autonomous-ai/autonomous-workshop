"""Exact auxiliary state, using the same production geometry and placements."""
from tidal_states import build_state
def gen_step():
    return build_state("crowded")
