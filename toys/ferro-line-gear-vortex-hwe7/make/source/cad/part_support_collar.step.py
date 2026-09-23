"""Separate printable support collar; bed datum Z=0."""
from parts.stand import make_support_collar

PRINTABLE = True

def gen_step():
    return make_support_collar()
