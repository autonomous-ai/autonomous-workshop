"""Review-only partial-bloom state halfway to Cygnus."""

from view_common import state_assembly

PRINTABLE = False


def gen_step():
    return state_assembly("intermediate_minus_60", -60.0)
