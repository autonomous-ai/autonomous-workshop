"""Unique swept-back front spine, broad adhesive base on bed Z=0."""
from parts.decor import front_spike_print
PRINTABLE = True
def gen_step():
    return front_spike_print()
