"""Isolated printable carrier; print datum Z=0."""
from build123d import Rot
from parts.support import carrier
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(carrier(), invert=False)
