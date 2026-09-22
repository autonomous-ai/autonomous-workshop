"""Separate printable stem; bed datum Z=0."""
from parts.stand import make_stem

PRINTABLE = True

def gen_step():
    return make_stem()
