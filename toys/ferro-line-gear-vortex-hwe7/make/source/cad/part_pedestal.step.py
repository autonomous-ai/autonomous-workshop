"""Separate printable pedestal; bed datum Z=0."""
from parts.stand import make_pedestal

PRINTABLE = True

def gen_step():
    return make_pedestal()
