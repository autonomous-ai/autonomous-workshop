"""Review-only Ursa Minor indexed state."""

from view_common import state_assembly

PRINTABLE = False


def gen_step():
    return state_assembly("ursa_minor", -240.0)
