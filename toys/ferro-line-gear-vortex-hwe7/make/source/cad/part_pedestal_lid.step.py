"""Separate printable pedestal lid; bed datum Z=0."""
from parts.stand import make_pedestal_lid

PRINTABLE = True

def gen_step():
    return make_pedestal_lid()
