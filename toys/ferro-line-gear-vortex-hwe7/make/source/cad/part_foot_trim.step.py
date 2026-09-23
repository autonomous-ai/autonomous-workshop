"""Separate printable foot trim; bed datum Z=0."""
from parts.stand import make_foot_trim

PRINTABLE = True

def gen_step():
    return make_foot_trim()
