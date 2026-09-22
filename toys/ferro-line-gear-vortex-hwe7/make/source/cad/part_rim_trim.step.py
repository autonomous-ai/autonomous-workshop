"""Separate printable rim trim; bed datum Z=0."""
from parts.stand import make_rim_trim

PRINTABLE = True

def gen_step():
    return make_rim_trim()
