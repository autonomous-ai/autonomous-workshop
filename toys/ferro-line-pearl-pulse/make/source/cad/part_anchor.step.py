"""Isolated printable anchor; print datum Z=0."""
from build123d import Rot
from parts.support import anchor
from features.common import bed
PRINTABLE = True
def gen_step():
    return bed(anchor(), invert=False)
