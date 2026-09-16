"""Isolated printable pivot_pin; print datum Z=0."""
from build123d import Rot
from parts.support import pivot_pin
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(pivot_pin(), invert=False)
