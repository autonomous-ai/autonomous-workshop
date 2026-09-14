"""Exact-state helper shared by the combined entry and open-state export."""
from moon_assembly import assemble
from moon_lib import SWING

def closed_state():
    return assemble(0)

def gen_step():
    return assemble(SWING)
