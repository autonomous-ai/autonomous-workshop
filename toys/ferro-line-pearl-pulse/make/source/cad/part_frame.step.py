"""Isolated printable frame; print datum Z=0."""
from build123d import Rot
from parts.support import frame
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(frame(), invert=True)
