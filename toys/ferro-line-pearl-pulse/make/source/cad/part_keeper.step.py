"""Isolated printable keeper; print datum Z=0."""
from build123d import Rot
from parts.moving import keeper
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(keeper(), invert=False)
