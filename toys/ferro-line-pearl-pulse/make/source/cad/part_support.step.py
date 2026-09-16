"""Isolated printable support; print datum Z=0."""
from build123d import Rot
from parts.support import support
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(support(), invert=False)
