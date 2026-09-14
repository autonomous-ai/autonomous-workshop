"""Canonical complete RIDGELINE R01. Source revision 3: G2 ID thickened."""
from ridgeline_lib import build_state
from states import STATES

def gen_step():
    return build_state(STATES["R01"])
