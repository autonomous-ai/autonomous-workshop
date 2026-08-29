"""Review-only Cygnus indexed state."""

from view_common import state_assembly

PRINTABLE = False


def gen_step():
    return state_assembly("cygnus", -120.0)
